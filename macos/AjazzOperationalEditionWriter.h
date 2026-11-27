#ifndef AJAZZ_OPERATIONAL_EDITION_WRITER_H
#define AJAZZ_OPERATIONAL_EDITION_WRITER_H

#include "AjazzOperationalJournal.h"
#include "AjazzOperationalWriter.h"
#include <stdlib.h>
#include <string.h>

#define AJAZZ_EDITION_SUPPORT_LIMIT 4096u

/// Own all sink state until the worker has finished and been joined.
typedef struct {
    AjazzOperationalWriter writer;
    char support[AJAZZ_EDITION_SUPPORT_LIMIT];
    bool legacy;
} AjazzOperationalEditionWriter;

/// The only filesystem operation on this path runs in the single consumer.
static inline bool AjazzEditionWriterSink(void *context, AjazzQueuedEvent value) {
    AjazzOperationalEditionWriter *owner = context;
    return AjazzJournalEditionTimedEvent(owner->support, owner->legacy,
        value.event, value.reason, value.timestamp, value.durationMs);
}

/// Copy a bounded absolute path; no filesystem access during creation.
/// The caller retains ownership, including after a timed-out wait.
static inline AjazzOperationalEditionWriter *AjazzEditionWriterCreate(
    const char *support, bool legacy) {
    if (!support || support[0] != '/') return NULL;
    size_t length = strnlen(support, AJAZZ_EDITION_SUPPORT_LIMIT);
    if (length >= AJAZZ_EDITION_SUPPORT_LIMIT) return NULL;
    AjazzOperationalEditionWriter *owner = calloc(1, sizeof(*owner));
    if (!owner) return NULL;
    memcpy(owner->support, support, length + 1);
    owner->legacy = legacy;
    if (!AjazzWriterStart(&owner->writer, AjazzEditionWriterSink, owner)) {
        free(owner);
        return NULL;
    }
    return owner;
}

/// A successful offer means queued, not persisted.
static inline bool AjazzEditionWriterOffer(AjazzOperationalEditionWriter *owner,
    AjazzOperationalEvent event, AjazzOperationalReason reason, time_t timestamp,
    int64_t durationMs) {
    if (!owner) return false;
    AjazzQueuedEvent value = {event, reason, timestamp, durationMs};
    return AjazzWriterOffer(&owner->writer, value);
}

/// The lifecycle owner seals once, before waiting or destroying.
static inline bool AjazzEditionWriterSeal(AjazzOperationalEditionWriter *owner,
                                         time_t timestamp) {
    return owner && AjazzWriterSeal(&owner->writer, timestamp);
}

/// No filesystem access; null is an unavailable, empty snapshot.
static inline AjazzWriterStatus AjazzEditionWriterSnapshot(
    AjazzOperationalEditionWriter *owner) {
    if (!owner) return (AjazzWriterStatus){0};
    return AjazzWriterSnapshot(&owner->writer);
}

/// Best effort only: timeout is not a flush or cancellation.
static inline bool AjazzEditionWriterWait(AjazzOperationalEditionWriter *owner,
                                         uint32_t timeoutMs) {
    return owner && AjazzWriterWait(&owner->writer, timeoutMs);
}

/// Only one lifecycle owner, after producers have stopped. False leaves the
/// handle valid. True invalidates it and releases all owned storage.
static inline bool AjazzEditionWriterDestroy(AjazzOperationalEditionWriter *owner) {
    if (!owner || !AjazzWriterJoin(&owner->writer)) return false;
    free(owner);
    return true;
}

#endif
