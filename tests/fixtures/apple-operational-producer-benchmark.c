/* Synthetic paced producer benchmark; no AppKit, user profile or HID access. */
#include "../../macos/AjazzGuiJournal.h"
#include <sys/resource.h>

#define SAMPLES 4096u
#define BATCH 32u

typedef struct {
    uint64_t samples[SAMPLES], elapsed_ns, cpu_us, peak_rss_bytes, stop_ns;
    bool initial_stop_complete;
} ProducerBenchmark;

static bool monotonic_ns(uint64_t *out) {
    struct timespec stamp;
    if (clock_gettime(CLOCK_MONOTONIC, &stamp) != 0) return false;
    *out = (uint64_t)stamp.tv_sec * UINT64_C(1000000000) + (uint64_t)stamp.tv_nsec;
    return true;
}

static uint64_t cpu_us(struct rusage value) {
    return ((uint64_t)value.ru_utime.tv_sec + (uint64_t)value.ru_stime.tv_sec) *
        UINT64_C(1000000) + (uint64_t)value.ru_utime.tv_usec +
        (uint64_t)value.ru_stime.tv_usec;
}

/// Wait outside the measured offer path; a paced batch must never drop events.
static bool drain(AjazzGuiJournal *journal) {
    uint64_t start, now;
    if (!AjazzWriterNow(&start)) return false;
    for (;;) {
        AjazzGuiJournalStatus status = AjazzGuiJournalSnapshot(journal);
        if (status.writer.failed || status.writer.dropped || status.unavailable) return false;
        if (!status.writer.queued && !status.writer.inFlight) return true;
        if (!AjazzWriterNow(&now) || now - start >= 5000) return false;
        struct timespec delay = {0, 1000000};
        nanosleep(&delay, NULL);
    }
}

static bool offer_samples(AjazzGuiJournal *journal, ProducerBenchmark *result) {
    for (size_t i = 0; i < SAMPLES; ++i) {
        uint64_t t0, t1;
        if (!monotonic_ns(&t0) ||
            !AjazzGuiJournalOffer(journal, AjazzEventIsolatedPollTimedOut,
                AjazzReasonTimeout, (time_t)(i + 1), 1250) ||
            !monotonic_ns(&t1) || t1 < t0) return false;
        result->samples[i] = t1 - t0;
        if ((i + 1) % BATCH == 0 && !drain(journal)) return false;
    }
    return true;
}

/// Record the first stop observation separately; retry only for benchmark cleanup.
static bool stop_and_collect(AjazzGuiJournal *journal, ProducerBenchmark *result) {
    uint64_t t0, t1;
    if (!monotonic_ns(&t0)) return false;
    bool stopped = AjazzGuiJournalStop(journal, SAMPLES + 1, AJAZZ_GUI_JOURNAL_STOP_MS);
    if (!monotonic_ns(&t1) || t1 < t0) return false;
    result->stop_ns = t1 - t0;
    result->initial_stop_complete = stopped;
    for (unsigned i = 0; !stopped && i < 50; ++i)
        stopped = AjazzGuiJournalStop(journal, SAMPLES + 1, AJAZZ_GUI_JOURNAL_STOP_MS);
    if (!stopped) return false;
    AjazzGuiJournalStatus status = AjazzGuiJournalSnapshot(journal);
    return status.initialized && status.writer.finished && !status.writer.queued &&
        !status.writer.inFlight && !status.writer.failed && !status.writer.dropped &&
        !status.unavailable && status.writer.written == SAMPLES + 2;
}

static bool measure(const char *root, ProducerBenchmark *result) {
    AjazzGuiJournal journal = {0};
    struct rusage before, after;
    uint64_t start, end;
    if (getrusage(RUSAGE_SELF, &before) != 0 || !monotonic_ns(&start) ||
        !AjazzGuiJournalStart(&journal, root, false, 0)) return false;
    bool offered = drain(&journal) && offer_samples(&journal, result);
    bool stopped = stop_and_collect(&journal, result);
    if (!offered || !stopped || !monotonic_ns(&end) || end < start ||
        getrusage(RUSAGE_SELF, &after) != 0 || cpu_us(after) < cpu_us(before) ||
        after.ru_maxrss <= 0) return false;
    result->elapsed_ns = end - start;
    result->cpu_us = cpu_us(after) - cpu_us(before);
    result->peak_rss_bytes = (uint64_t)after.ru_maxrss;
#ifndef __APPLE__
    result->peak_rss_bytes *= 1024;
#endif
    return true;
}

/// Expected record identity includes a unique synthetic timestamp for ordering.
static size_t expected_record(size_t index, char *record, size_t capacity) {
    if (index == 0 || index == SAMPLES + 1)
        return AjazzEncodeOperationalEvent(record, capacity,
            index == 0 ? AjazzEventStarted : AjazzEventStopped, AjazzReasonNone, (time_t)index);
    return AjazzEncodeTimedOperationalEvent(record, capacity,
        AjazzEventIsolatedPollTimedOut, AjazzReasonTimeout, (time_t)index, 1250);
}

static bool generations(size_t *previous, size_t *active) {
    size_t bytes = 0;
    *previous = 0;
    *active = 0;
    char record[256];
    for (size_t i = 0; i < SAMPLES + 2; ++i) {
        size_t n = expected_record(i, record, sizeof(record));
        if (!n) return false;
        if (bytes + n > AJAZZ_JOURNAL_LIMIT) {
            *previous = *active;
            *active = i;
            bytes = 0;
        }
        bytes += n;
    }
    return *active > 0;
}

static bool verify_generation(int dir, const char *name, size_t first, size_t end) {
    int fd = AjazzJournalOpen(dir, name, O_RDONLY, AJAZZ_JOURNAL_LIMIT);
    if (fd < 0) return false;
    // The caller must not create missing files; O_RDONLY is intentional.
    char expected[256], actual[256];
    bool ok = first < end;
    for (size_t i = first; ok && i < end; ++i) {
        size_t n = expected_record(i, expected, sizeof(expected));
        ok = n && read(fd, actual, n) == (ssize_t)n && memcmp(actual, expected, n) == 0;
    }
    char tail;
    ok = ok && read(fd, &tail, 1) == 0;
    return close(fd) == 0 && ok;
}

static bool verify_and_cleanup(const char *root) {
    size_t previous, active;
    if (!generations(&previous, &active)) return false;
    int parent = open(root, O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    if (parent < 0) return false;
    const char *name = "AJAZZBatteryTray-Journal";
    int dir = openat(parent, name, O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    bool ok = dir >= 0;
    if (dir >= 0) {
        ok = verify_generation(dir, AJAZZ_JOURNAL_PREVIOUS, previous, active) &&
            verify_generation(dir, AJAZZ_JOURNAL_ACTIVE, active, SAMPLES + 2);
        const char *entries[] = {AJAZZ_JOURNAL_ACTIVE, AJAZZ_JOURNAL_PREVIOUS, AJAZZ_JOURNAL_LEASE};
        for (size_t i = 0; i < sizeof(entries) / sizeof(entries[0]); ++i)
            if (unlinkat(dir, entries[i], 0) != 0) ok = false;
        close(dir);
        if (unlinkat(parent, name, AT_REMOVEDIR) != 0) ok = false;
    }
    close(parent);
    return rmdir(root) == 0 && ok;
}

static int compare_ns(const void *a, const void *b) {
    uint64_t left = *(const uint64_t *)a, right = *(const uint64_t *)b;
    return (left > right) - (left < right);
}

static void print_result(ProducerBenchmark *result) {
    qsort(result->samples, SAMPLES, sizeof(result->samples[0]), compare_ns);
    printf("{\"schema\":\"apple-journal-producer-benchmark-v1\",\"scope\":\"SYNTHETIC_PACED_PRODUCER\","
        "\"offers\":%u,\"written\":%u,\"batch\":%u,\"dropped\":0,\"failed\":0,\"unavailable\":0,"
        "\"offer_p50_ns\":%" PRIu64 ",\"offer_p95_ns\":%" PRIu64 ",\"offer_max_ns\":%" PRIu64
        ",\"elapsed_ns\":%" PRIu64 ",\"cpu_us\":%" PRIu64 ",\"peak_rss_bytes\":%" PRIu64
        ",\"first_stop_ns\":%" PRIu64 ",\"first_stop_complete\":%s",
        SAMPLES, SAMPLES + 2, BATCH, result->samples[(SAMPLES * 50 + 99) / 100 - 1],
        result->samples[(SAMPLES * 95 + 99) / 100 - 1], result->samples[SAMPLES - 1],
        result->elapsed_ns, result->cpu_us, result->peak_rss_bytes, result->stop_ns,
        result->initial_stop_complete ? "true" : "false");
    puts(",\"retained_records\":\"MATCH\",\"gui\":\"NOT_RUN\",\"hardware\":\"NOT_RUN\"}");
}

int main(void) {
    char root[] = "/tmp/ajazz-producer-bench-XXXXXX";
    static ProducerBenchmark result;
    if (!mkdtemp(root) || !measure(root, &result) || !verify_and_cleanup(root)) {
        fputs("FAIL: paced producer benchmark or exact retained records\n", stderr);
        return 1;
    }
    print_result(&result);
    return 0;
}
