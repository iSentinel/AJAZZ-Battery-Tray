#ifndef AJAZZ_OPERATIONAL_QUEUE_H
#define AJAZZ_OPERATIONAL_QUEUE_H

#include "AjazzOperationalEvent.h"

#define AJAZZ_QUEUE_CAPACITY 64u

/// No strings, pointers, device data or heap allocations in a queued event.
typedef struct {
    AjazzOperationalEvent event;
    AjazzOperationalReason reason;
    time_t timestamp;
    int64_t durationMs;
} AjazzQueuedEvent;

typedef struct {
    AjazzQueuedEvent records[AJAZZ_QUEUE_CAPACITY];
    size_t head, count;
    bool sealed, inFlight;
    uint64_t dropped, written, failed;
} AjazzOperationalQueue;

/// Zero initialize once. All operations require caller-owned serialization.
/// No filesystem access, waiting, worker creation or implicit synchronization.
static inline void AjazzQueueIncrement(uint64_t *counter) {
    if (*counter < UINT64_MAX) ++*counter;
}

static inline bool AjazzQueueValid(AjazzQueuedEvent value) {
    if ((unsigned)value.event >= AjazzEventCount ||
        (unsigned)value.reason >= AjazzReasonCount ||
        value.durationMs < -1 || value.durationMs > 86400000) return false;
    return value.durationMs == -1 || value.event == AjazzEventIsolatedPollTimedOut ||
        value.event == AjazzEventDockClockSucceeded || value.event == AjazzEventDockClockFailed;
}

static inline void AjazzQueuePush(AjazzOperationalQueue *queue, AjazzQueuedEvent value) {
    size_t tail = (queue->head + queue->count) % AJAZZ_QUEUE_CAPACITY;
    queue->records[tail] = value;
    ++queue->count;
}

/// Drop newest on overflow; keep one reserved slot for the final lifecycle event.
static inline bool AjazzQueueOffer(AjazzOperationalQueue *queue, AjazzQueuedEvent value) {
    if (queue->sealed || queue->count >= AJAZZ_QUEUE_CAPACITY - 1 ||
        value.event == AjazzEventStopped || !AjazzQueueValid(value)) {
        AjazzQueueIncrement(&queue->dropped);
        return false;
    }
    AjazzQueuePush(queue, value);
    return true;
}

/// Seal once, append one final event even when the ordinary buffer is full.
/// Does not flush, wait for I/O, or guarantee persistence before process exit.
static inline bool AjazzQueueSeal(AjazzOperationalQueue *queue, time_t timestamp) {
    if (queue->sealed) return false;
    queue->sealed = true;
    AjazzQueuedEvent stopped = {AjazzEventStopped, AjazzReasonNone, timestamp, -1};
    AjazzQueuePush(queue, stopped);
    return true;
}

/// Exactly one consumer may claim a record before completing it.
static inline bool AjazzQueueClaim(AjazzOperationalQueue *queue, AjazzQueuedEvent *out) {
    if (!out || queue->inFlight || !queue->count) return false;
    *out = queue->records[queue->head];
    queue->head = (queue->head + 1) % AJAZZ_QUEUE_CAPACITY;
    --queue->count;
    queue->inFlight = true;
    return true;
}

static inline bool AjazzQueueComplete(AjazzOperationalQueue *queue, bool written) {
    if (!queue->inFlight) return false;
    queue->inFlight = false;
    AjazzQueueIncrement(written ? &queue->written : &queue->failed);
    return true;
}

#endif
