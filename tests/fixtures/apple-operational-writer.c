/* Synthetic concurrency test; no filesystem, GUI, device or real profile. */
#include "../../macos/AjazzOperationalWriter.h"

typedef struct {
    pthread_mutex_t lock;
    pthread_cond_t ready;
    bool entered, released;
    size_t count;
    AjazzQueuedEvent records[AJAZZ_QUEUE_CAPACITY + 1];
} TestSink;

typedef struct {
    AjazzOperationalWriter *writer;
    size_t offset, accepted;
} Producer;

static AjazzQueuedEvent sample(time_t timestamp) {
    return (AjazzQueuedEvent){AjazzEventIsolatedPollTimedOut, AjazzReasonTimeout,
                              timestamp, 1250};
}

/// Block only the first write; all other work is deterministic.
static bool gated_sink(void *context, AjazzQueuedEvent value) {
    TestSink *sink = context;
    pthread_mutex_lock(&sink->lock);
    sink->entered = true;
    pthread_cond_signal(&sink->ready);
    while (!sink->released) pthread_cond_wait(&sink->ready, &sink->lock);
    pthread_mutex_unlock(&sink->lock);
    if (sink->count >= AJAZZ_QUEUE_CAPACITY + 1) return false;
    sink->records[sink->count++] = value;
    return value.event != AjazzEventStopped;
}

static void *produce(void *argument) {
    Producer *producer = argument;
    for (size_t i = 0; i < 16; ++i)
        if (AjazzWriterOffer(producer->writer, sample((time_t)(producer->offset + i))))
            ++producer->accepted;
    return NULL;
}

static bool fill_while_blocked(AjazzOperationalWriter *writer) {
    Producer producers[4];
    pthread_t threads[4];
    for (size_t i = 0; i < 4; ++i) {
        producers[i] = (Producer){writer, 1 + i * 16, 0};
        if (pthread_create(&threads[i], NULL, produce, &producers[i]) != 0) return false;
    }
    size_t accepted = 0;
    for (size_t i = 0; i < 4; ++i) {
        if (pthread_join(threads[i], NULL) != 0) return false;
        accepted += producers[i].accepted;
    }
    AjazzWriterStatus status = AjazzWriterSnapshot(writer);
    return accepted == 63 && status.queued == 63 && status.inFlight &&
           status.dropped == 1 && status.written == 0 && status.failed == 0;
}

static bool validate_records(TestSink *sink) {
    bool seen[65] = {0};
    if (sink->count != 65 || sink->records[0].timestamp != 0 ||
        sink->records[64].event != AjazzEventStopped ||
        sink->records[64].timestamp != 100) return false;
    for (size_t i = 1; i < 64; ++i) {
        AjazzQueuedEvent event = sink->records[i];
        if (event.timestamp < 1 || event.timestamp > 64 ||
            seen[event.timestamp] || event.event != AjazzEventIsolatedPollTimedOut ||
            event.durationMs != 1250) return false;
        seen[event.timestamp] = true;
    }
    return true;
}

static bool blocked_writer(void) {
    TestSink sink = {.lock = PTHREAD_MUTEX_INITIALIZER, .ready = PTHREAD_COND_INITIALIZER};
    AjazzOperationalWriter writer;
    if (!AjazzWriterStart(&writer, gated_sink, &sink) ||
        !AjazzWriterOffer(&writer, sample(0))) return false;
    pthread_mutex_lock(&sink.lock);
    while (!sink.entered) pthread_cond_wait(&sink.ready, &sink.lock);
    pthread_mutex_unlock(&sink.lock);
    if (!fill_while_blocked(&writer) || !AjazzWriterSeal(&writer, 100) ||
        AjazzWriterSeal(&writer, 101) || AjazzWriterOffer(&writer, sample(102)) ||
        AjazzWriterWait(&writer, 20) || AjazzWriterJoin(&writer)) return false;
    pthread_mutex_lock(&sink.lock);
    sink.released = true;
    pthread_cond_signal(&sink.ready);
    pthread_mutex_unlock(&sink.lock);
    if (!AjazzWriterWait(&writer, 5000)) return false;
    AjazzWriterStatus status = AjazzWriterSnapshot(&writer);
    if (!AjazzWriterJoin(&writer)) return false;
    bool ok = status.finished && status.sealed && !status.inFlight &&
              !status.queued && status.written == 64 && status.failed == 1 &&
              status.dropped == 2 && validate_records(&sink);
    pthread_cond_destroy(&sink.ready);
    pthread_mutex_destroy(&sink.lock);
    return ok;
}

/// Idle seal must wake the consumer and deliver the stop even without offers.
static bool idle_writer(void) {
    TestSink sink = {.lock = PTHREAD_MUTEX_INITIALIZER, .ready = PTHREAD_COND_INITIALIZER,
                     .released = true};
    AjazzOperationalWriter writer;
    if (AjazzWriterStart(&writer, NULL, &sink) ||
        !AjazzWriterStart(&writer, gated_sink, &sink) ||
        !AjazzWriterSeal(&writer, 100) || !AjazzWriterWait(&writer, 5000)) return false;
    AjazzWriterStatus status = AjazzWriterSnapshot(&writer);
    if (!AjazzWriterJoin(&writer)) return false;
    bool ok = status.failed == 1 && status.written == 0 && sink.count == 1 &&
              sink.records[0].event == AjazzEventStopped;
    pthread_cond_destroy(&sink.ready);
    pthread_mutex_destroy(&sink.lock);
    return ok;
}

int main(void) {
    if (!blocked_writer() || !idle_writer()) {
        fputs("FAIL: Apple background journal writer\n", stderr);
        return 1;
    }
    puts("PASS: concurrent offers, blocked sink, reserved stop, bounded wait and idle wake");
    return 0;
}
