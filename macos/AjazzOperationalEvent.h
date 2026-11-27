#ifndef AJAZZ_OPERATIONAL_EVENT_H
#define AJAZZ_OPERATIONAL_EVENT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
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
    AjazzReasonCount
} AjazzOperationalReason;

typedef struct {
    const char *name;
    const char *level;
} AjazzOperationalEventInfo;

/// Encode one bounded schema-1 JSONL record using caller-supplied UTC time.
/// Return zero on failure; callers must not write a partially encoded buffer.
static inline size_t AjazzEncodeOperationalEvent(
    char *output, size_t capacity, AjazzOperationalEvent event,
    AjazzOperationalReason reason, time_t timestamp) {
    static const AjazzOperationalEventInfo events[] = {
        {"ApplicationStarted", "INFO"}, {"ApplicationStopped", "INFO"},
        {"IsolatedPollingEnabled", "INFO"}, {"PollFailed", "ERROR"},
        {"IsolatedPollTimedOut", "WARN"}, {"IsolatedPollUnavailable", "WARN"},
        {"HistorySaveFailed", "WARN"}, {"HistoryReadFailed", "WARN"},
        {"DockClockSucceeded", "INFO"}, {"DockClockFailed", "WARN"}
    };
    static const char *const reasons[] = {
        "none", "io_error", "access_denied", "timeout", "cancelled",
        "unsuccessful", "unexpected_error"
    };
    if (!output || !capacity) return 0;
    output[0] = '\0';
    if ((unsigned)event >= AjazzEventCount ||
        (unsigned)reason >= AjazzReasonCount) return 0;
    struct tm utc;
    if (!gmtime_r(&timestamp, &utc) || utc.tm_year < -1899 || utc.tm_year > 8099)
        return 0;
    char stamp[21];
    if (strftime(stamp, sizeof(stamp), "%Y-%m-%dT%H:%M:%SZ", &utc) != 20)
        return 0;
    int length = snprintf(output, capacity,
        "{\"schema\":1,\"utc\":\"%s\",\"level\":\"%s\",\"event\":\"%s\","
        "\"reason\":\"%s\"}\n", stamp, events[event].level, events[event].name,
        reasons[reason]);
    if (length < 0 || (size_t)length >= capacity) {
        output[0] = '\0';
        return 0;
    }
    return (size_t)length;
}

#endif
