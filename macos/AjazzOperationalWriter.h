#ifndef AJAZZ_OPERATIONAL_WRITER_H
#define AJAZZ_OPERATIONAL_WRITER_H

#include "AjazzOperationalQueue.h"
#include <pthread.h>

/// The single writer invokes this outside the queue lock. Context must remain
/// valid until successful join; callback may block and is never force-cancelled.
typedef bool (*AjazzWriterSink)(void *context, AjazzQueuedEvent value);

typedef struct {
    pthread_mutex_t lock;
    pthread_cond_t ready;
    pthread_t thread;
    AjazzOperationalQueue queue;
    AjazzWriterSink sink;
    void *context;
    bool finished;
} AjazzOperationalWriter;

typedef struct {
    size_t queued;
    bool sealed, inFlight, finished;
    uint64_t dropped, written, failed;
} AjazzWriterStatus;

/// Wait only while no events are available; never hold the lock across I/O.
static inline void *AjazzWriterRun(void *argument) {
    AjazzOperationalWriter *writer = argument;
    pthread_mutex_lock(&writer->lock);
    for (;;) {
        AjazzQueuedEvent value;
        if (AjazzQueueClaim(&writer->queue, &value)) {
            pthread_mutex_unlock(&writer->lock);
            bool written = writer->sink(writer->context, value);
            pthread_mutex_lock(&writer->lock);
            AjazzQueueComplete(&writer->queue, written);
        } else if (writer->queue.sealed) {
            writer->finished = true;
            pthread_mutex_unlock(&writer->lock);
            return NULL;
        } else {
            pthread_cond_wait(&writer->ready, &writer->lock);
        }
    }
}

/// Initialize once on fresh caller-owned storage; unwind partial startup.
static inline bool AjazzWriterStart(AjazzOperationalWriter *writer,
                                    AjazzWriterSink sink, void *context) {
    if (!writer || !sink) return false;
    *writer = (AjazzOperationalWriter){0};
    if (pthread_mutex_init(&writer->lock, NULL) != 0) return false;
    if (pthread_cond_init(&writer->ready, NULL) != 0) {
        pthread_mutex_destroy(&writer->lock);
        return false;
    }
    writer->sink = sink;
    writer->context = context;
    if (pthread_create(&writer->thread, NULL, AjazzWriterRun, writer) != 0) {
        pthread_cond_destroy(&writer->ready);
        pthread_mutex_destroy(&writer->lock);
        return false;
    }
    return true;
}

/// Producers serialize short state operations only; no I/O or capacity wait.
static inline bool AjazzWriterOffer(AjazzOperationalWriter *writer, AjazzQueuedEvent value) {
    pthread_mutex_lock(&writer->lock);
    bool accepted = AjazzQueueOffer(&writer->queue, value);
    if (accepted) pthread_cond_signal(&writer->ready);
    pthread_mutex_unlock(&writer->lock);
    return accepted;
}

/// Reserve the final stop event and wake an idle writer; does not join.
static inline bool AjazzWriterSeal(AjazzOperationalWriter *writer, time_t timestamp) {
    pthread_mutex_lock(&writer->lock);
    bool accepted = AjazzQueueSeal(&writer->queue, timestamp);
    if (accepted) pthread_cond_signal(&writer->ready);
    pthread_mutex_unlock(&writer->lock);
    return accepted;
}

/// Snapshot counters without copying the event buffer or calling the sink.
static inline AjazzWriterStatus AjazzWriterSnapshot(AjazzOperationalWriter *writer) {
    pthread_mutex_lock(&writer->lock);
    AjazzOperationalQueue *q = &writer->queue;
    AjazzWriterStatus status = {q->count, q->sealed, q->inFlight, writer->finished,
                                q->dropped, q->written, q->failed};
    pthread_mutex_unlock(&writer->lock);
    return status;
}

/// Convert a monotonic reading to milliseconds; no wall-clock deadline.
static inline bool AjazzWriterNow(uint64_t *milliseconds) {
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return false;
    *milliseconds = (uint64_t)now.tv_sec * 1000u + (uint64_t)now.tv_nsec / 1000000u;
    return true;
}

/// Bounded best-effort observation, never joins or cancels a blocked sink.
/// A false result requires retaining the writer and context for later cleanup.
static inline bool AjazzWriterWait(AjazzOperationalWriter *writer, uint32_t timeoutMs) {
    uint64_t start, now;
    if (!AjazzWriterNow(&start)) return false;
    for (;;) {
        if (AjazzWriterSnapshot(writer).finished) return true;
        if (!AjazzWriterNow(&now) || now - start >= timeoutMs) return false;
        struct timespec delay = {0, 1000000};
        nanosleep(&delay, NULL);
    }
}

/// Single lifecycle owner only, after all producers stop. On timeout no resources
/// are destroyed. After true, no operation may access this writer until restart.
static inline bool AjazzWriterJoin(AjazzOperationalWriter *writer) {
    if (!AjazzWriterSnapshot(writer).finished) return false;
    if (pthread_join(writer->thread, NULL) != 0) return false;
    pthread_cond_destroy(&writer->ready);
    pthread_mutex_destroy(&writer->lock);
    return true;
}

#endif
