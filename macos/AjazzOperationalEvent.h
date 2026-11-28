#ifndef AJAZZ_OPERATIONAL_EVENT_H
#define AJAZZ_OPERATIONAL_EVENT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>
#include <time.h>

/// Closed operational events shared by the Swift and Objective-C editions.
typedef enum {
    AjazzEventStarted = 0,
    AjazzEventStopped,
    AjazzEventIsolatedPollingEnabled,
    AjazzEventPollFailed,
    AjazzEventIsolatedPollTimedOut,
    AjazzEventIsolatedPollUnavailable,
    AjazzEventHistorySaveFailed,
    AjazzEventHistoryReadFailed,
    AjazzEventDockClockSucceeded,
    AjazzEventDockClockFailed,
    AjazzEventCount
} AjazzOperationalEvent;

/// Closed reason codes; no error strings, device names or paths are accepted.
typedef enum {
    AjazzReasonNone = 0,
    AjazzReasonIoError,
    AjazzReasonAccessDenied,
    AjazzReasonTimeout,
    AjazzReasonCancelled,
    AjazzReasonUnsuccessful,
    AjazzReasonUnexpectedError,
    AjazzReasonBusy,
    AjazzReasonCount
} AjazzOperationalReason;

typedef struct {
    const char *name;
    const char *level;
} AjazzOperationalEventInfo;

/// Supervisor outcome, distinct from the battery state returned by a valid reply.
typedef enum {
    AjazzRoutineReply = 0,
    AjazzRoutineTimeout,
    AjazzRoutineCancelled,
    AjazzRoutineBusy,
    AjazzRoutineFailed
} AjazzRoutineOutcome;

/// Only supervisor failures/timeouts produce journal events; cancellation is not failure.
static inline AjazzOperationalEvent AjazzRoutineJournalEvent(AjazzRoutineOutcome outcome) {
    switch (outcome) {
        case AjazzRoutineTimeout: return AjazzEventIsolatedPollTimedOut;
        case AjazzRoutineBusy:
        case AjazzRoutineFailed: return AjazzEventIsolatedPollUnavailable;
        default: return AjazzEventCount;
    }
}

/// Use closed reasons; no exception messages or device data.
static inline AjazzOperationalReason AjazzRoutineJournalReason(AjazzRoutineOutcome outcome) {
    switch (outcome) {
        case AjazzRoutineTimeout: return AjazzReasonTimeout;
        case AjazzRoutineBusy: return AjazzReasonBusy;
        case AjazzRoutineFailed: return AjazzReasonUnsuccessful;
        default: return AjazzReasonNone;
    }
}

/// Convert measured monotonic elapsed time to whole milliseconds, or -1.
static inline int64_t AjazzElapsedMilliseconds(double started, double ended) {
    double elapsed = ended - started;
    if (!(started >= 0.0 && ended >= started && elapsed >= 0.0 && elapsed <= 86400.0))
        return -1;
    return (int64_t)(elapsed * 1000.0);
}

/// Encode one bounded schema-1 JSONL record using caller-supplied UTC time.
/// Return zero on failure; callers must not write a partially encoded buffer.
static inline size_t AjazzEncodeTimedOperationalEvent(
    char *output, size_t capacity, AjazzOperationalEvent event,
    AjazzOperationalReason reason, time_t timestamp, int64_t durationMs) {
    static const AjazzOperationalEventInfo events[] = {
        {"ApplicationStarted", "INFO"}, {"ApplicationStopped", "INFO"},
        {"IsolatedPollingEnabled", "INFO"}, {"PollFailed", "ERROR"},
        {"IsolatedPollTimedOut", "WARN"}, {"IsolatedPollUnavailable", "WARN"},
        {"HistorySaveFailed", "WARN"}, {"HistoryReadFailed", "WARN"},
        {"DockClockSucceeded", "INFO"}, {"DockClockFailed", "WARN"}
    };
    static const char *const reasons[] = {
        "none", "io_error", "access_denied", "timeout", "cancelled",
        "unsuccessful", "unexpected_error", "busy"
    };
    if (!output || !capacity) return 0;
    output[0] = '\0';
    if ((unsigned)event >= AjazzEventCount ||
        (unsigned)reason >= AjazzReasonCount || durationMs < -1 || durationMs > 86400000)
        return 0;
    if (durationMs >= 0 && event != AjazzEventIsolatedPollTimedOut &&
        event != AjazzEventDockClockSucceeded && event != AjazzEventDockClockFailed)
        return 0;
    struct tm utc;
    if (!gmtime_r(&timestamp, &utc) || utc.tm_year < -1899 || utc.tm_year > 8099)
        return 0;
    char stamp[21];
    if (strftime(stamp, sizeof(stamp), "%Y-%m-%dT%H:%M:%SZ", &utc) != 20)
        return 0;
    char duration[48] = "";
    if (durationMs >= 0) {
        int n = snprintf(duration, sizeof(duration), ",\"duration_ms\":%" PRId64, durationMs);
        if (n < 0 || (size_t)n >= sizeof(duration)) return 0;
    }
    int length = snprintf(output, capacity,
        "{\"schema\":1,\"utc\":\"%s\",\"level\":\"%s\",\"event\":\"%s\","
        "\"reason\":\"%s\"%s}\n", stamp, events[event].level, events[event].name,
        reasons[reason], duration);
    if (length < 0 || (size_t)length >= capacity) {
        output[0] = '\0';
        return 0;
    }
    return (size_t)length;
}

/// Preserve the original byte format for unmeasured events.
static inline size_t AjazzEncodeOperationalEvent(
    char *output, size_t capacity, AjazzOperationalEvent event,
    AjazzOperationalReason reason, time_t timestamp) {
    return AjazzEncodeTimedOperationalEvent(output, capacity, event, reason, timestamp, -1);
}

#endif
