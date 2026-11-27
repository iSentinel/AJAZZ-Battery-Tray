/* Fixed synthetic benchmark; no tray process, user profile or HID access. */
#include "../../macos/AjazzOperationalJournal.h"
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>

#define SAMPLES 4096u

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

static int compare_ns(const void *a, const void *b) {
    uint64_t left = *(const uint64_t *)a, right = *(const uint64_t *)b;
    return (left > right) - (left < right);
}

static void print_stats(uint64_t *values, size_t count) {
    qsort(values, count, sizeof(values[0]), compare_ns);
    printf("{\"count\":%zu,\"p50_ns\":%" PRIu64 ",\"p95_ns\":%" PRIu64
        ",\"max_ns\":%" PRIu64 "}", count, values[(count * 50 + 99) / 100 - 1],
        values[(count * 95 + 99) / 100 - 1], values[count - 1]);
}

/// Reopen retained generations and compare every synthetic record exactly.
static bool verify_generation(int directory, const char *name, const char *record,
                              size_t size, size_t count) {
    int fd = openat(directory, name, O_RDONLY | O_NOFOLLOW);
    if (fd < 0) return false;
    struct stat info;
    bool ok = fstat(fd, &info) == 0 && AjazzJournalFileSafe(&info, AJAZZ_JOURNAL_LIMIT) &&
        info.st_size == (off_t)(size * count);
    char actual[256];
    for (size_t i = 0; ok && i < count; ++i)
        ok = read(fd, actual, size) == (ssize_t)size && memcmp(actual, record, size) == 0;
    return close(fd) == 0 && ok;
}

typedef struct {
    uint64_t normal[SAMPLES], rotation[SAMPLES];
    size_t normal_count, rotation_count;
    uint64_t elapsed_ns, cpu_delta_us, peak_rss_bytes;
} Benchmark;

/// Measure the production edition helper, including path and lease overhead.
static bool measure(const char *root, size_t per_generation, Benchmark *result) {
    struct rusage before, after;
    uint64_t start, end, t0, t1;
    if (getrusage(RUSAGE_SELF, &before) != 0 || !monotonic_ns(&start)) return false;
    for (size_t i = 0; i < SAMPLES; ++i) {
        if (!monotonic_ns(&t0) ||
            !AjazzJournalEditionTimedEvent(root, false, AjazzEventIsolatedPollTimedOut,
                AjazzReasonTimeout, 0, 1250) || !monotonic_ns(&t1) || t1 < t0)
            return false;
        if (i && i % per_generation == 0)
            result->rotation[result->rotation_count++] = t1 - t0;
        else
            result->normal[result->normal_count++] = t1 - t0;
    }
    if (!monotonic_ns(&end) || end < start || getrusage(RUSAGE_SELF, &after) != 0 ||
        cpu_us(after) < cpu_us(before) || after.ru_maxrss <= 0) return false;
    result->elapsed_ns = end - start;
    result->cpu_delta_us = cpu_us(after) - cpu_us(before);
    result->peak_rss_bytes = (uint64_t)after.ru_maxrss;
#ifndef __APPLE__
    result->peak_rss_bytes *= 1024;
#endif
    return result->rotation_count > 0 && result->normal_count > 0;
}

static bool verify_and_cleanup(const char *root, const char *record, size_t size,
                               size_t per_generation, bool measured) {
    int parent = open(root, O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    if (parent < 0) return false;
    const char *name = "AJAZZBatteryTray-Journal";
    int dir = openat(parent, name, O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    bool ok = false;
    if (dir >= 0) {
        size_t active_count = (SAMPLES - 1) % per_generation + 1;
        ok = measured && verify_generation(dir, AJAZZ_JOURNAL_ACTIVE, record, size, active_count) &&
            verify_generation(dir, AJAZZ_JOURNAL_PREVIOUS, record, size, per_generation);
        unlinkat(dir, AJAZZ_JOURNAL_ACTIVE, 0);
        unlinkat(dir, AJAZZ_JOURNAL_PREVIOUS, 0);
        unlinkat(dir, AJAZZ_JOURNAL_LEASE, 0);
        close(dir);
        if (unlinkat(parent, name, AT_REMOVEDIR) != 0) ok = false;
    }
    close(parent);
    return rmdir(root) == 0 && ok;
}

int main(void) {
    char record[256], root[] = "/tmp/ajazz-journal-bench-XXXXXX";
    size_t size = AjazzEncodeTimedOperationalEvent(record, sizeof(record),
        AjazzEventIsolatedPollTimedOut, AjazzReasonTimeout, 0, 1250);
    if (!size || !mkdtemp(root)) return 1;
    size_t per_generation = AJAZZ_JOURNAL_LIMIT / size;
    static Benchmark result;
    bool measured = measure(root, per_generation, &result);
    if (!verify_and_cleanup(root, record, size, per_generation, measured)) {
        fputs("FAIL: synthetic journal benchmark or retained record verification\n", stderr);
        return 1;
    }
    printf("{\"schema\":\"apple-journal-benchmark-v1\",\"scope\":\"SYNTHETIC_STORAGE\","
        "\"writes\":%u,\"limit_bytes\":%u,\"record_bytes\":%zu,"
        "\"elapsed_ns\":%" PRIu64 ",\"cpu_us\":%" PRIu64 ",\"peak_rss_bytes\":%" PRIu64
        ",\"normal\":", SAMPLES, AJAZZ_JOURNAL_LIMIT, size, result.elapsed_ns,
        result.cpu_delta_us, result.peak_rss_bytes);
    print_stats(result.normal, result.normal_count);
    printf(",\"rotation\":");
    print_stats(result.rotation, result.rotation_count);
    puts(",\"retained_records\":\"MATCH\",\"gui\":\"NOT_RUN\",\"hardware\":\"NOT_RUN\"}");
    return 0;
}
