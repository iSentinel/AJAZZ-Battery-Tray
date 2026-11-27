#ifndef AJAZZ_GUI_JOURNAL_H
#define AJAZZ_GUI_JOURNAL_H

#include "AjazzOperationalEditionWriter.h"

#define AJAZZ_GUI_JOURNAL_STOP_MS 100u

/// Main-thread lifecycle state. The worker owns only its independent heap
/// context and never calls the GUI. Zero initialize once per app delegate.
typedef struct {
    AjazzOperationalEditionWriter *owner;
    AjazzWriterStatus finalStatus;
    uint64_t unavailable;
    bool started, stopped, initialized;
} AjazzGuiJournal;

typedef struct {
    AjazzWriterStatus writer;
    uint64_t unavailable;
    bool initialized;
} AjazzGuiJournalStatus;

/// Count unavailable separately from queue refusal and actual storage failure.
static inline bool AjazzGuiJournalOffer(AjazzGuiJournal *journal,
    AjazzOperationalEvent event, AjazzOperationalReason reason, time_t timestamp,
    int64_t durationMs) {
    if (!journal->owner || journal->stopped) {
        AjazzQueueIncrement(&journal->unavailable);
        return false;
    }
    return AjazzEditionWriterOffer(journal->owner, event, reason, timestamp, durationMs);
}

/// Initialize only on actual GUI launch. No fallback to synchronous writes.
static inline bool AjazzGuiJournalStart(AjazzGuiJournal *journal, const char *support,
                                        bool legacy, time_t timestamp) {
    if (journal->started || journal->stopped) return false;
    journal->started = true;
    journal->owner = AjazzEditionWriterCreate(support, legacy);
    journal->initialized = journal->owner != NULL;
    return AjazzGuiJournalOffer(journal, AjazzEventStarted, AjazzReasonNone, timestamp, -1);
}

/// Snapshot pending and completed outcomes without exposing a filesystem path.
static inline AjazzGuiJournalStatus AjazzGuiJournalSnapshot(AjazzGuiJournal *journal) {
    AjazzGuiJournalStatus status = {
        journal->owner ? AjazzEditionWriterSnapshot(journal->owner) : journal->finalStatus,
        journal->unavailable, journal->initialized
    };
    return status;
}

/// Stop once; subsequent calls may collect a completed writer, not add another
/// stop record. Timeout retains heap ownership; only process exit may abandon it.
static inline bool AjazzGuiJournalStop(AjazzGuiJournal *journal, time_t timestamp,
                                       uint32_t timeoutMs) {
    if (!journal->stopped) {
        journal->stopped = true;
        if (journal->owner) AjazzEditionWriterSeal(journal->owner, timestamp);
        else if (journal->started) AjazzQueueIncrement(&journal->unavailable);
    }
    if (!journal->owner) return true;
    if (timeoutMs > AJAZZ_GUI_JOURNAL_STOP_MS) timeoutMs = AJAZZ_GUI_JOURNAL_STOP_MS;
    if (!AjazzEditionWriterWait(journal->owner, timeoutMs)) return false;
    journal->finalStatus = AjazzEditionWriterSnapshot(journal->owner);
    if (!AjazzEditionWriterDestroy(journal->owner)) return false;
    journal->owner = NULL;
    return true;
}

#endif
