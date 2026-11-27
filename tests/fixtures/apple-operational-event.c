/* Standalone synthetic encoder checks; no application or device is opened. */
#include "../../macos/AjazzOperationalEvent.h"
#include <string.h>
#include <math.h>

static bool check_records(void) {
    const char *events[] = {
        "ApplicationStarted", "ApplicationStopped", "IsolatedPollingEnabled",
        "PollFailed", "IsolatedPollTimedOut", "IsolatedPollUnavailable",
        "HistorySaveFailed", "HistoryReadFailed", "DockClockSucceeded", "DockClockFailed"
    };
    const char *levels[] = {
        "INFO", "INFO", "INFO", "ERROR", "WARN", "WARN", "WARN", "WARN", "INFO", "WARN"
    };
    const char *reasons[] = {
        "none", "io_error", "access_denied", "timeout", "cancelled",
        "unsuccessful", "unexpected_error"
    };
    if (sizeof(events) / sizeof(events[0]) != AjazzEventCount ||
        sizeof(reasons) / sizeof(reasons[0]) != AjazzReasonCount) return false;
    for (int event = 0; event < AjazzEventCount; ++event) {
        for (int reason = 0; reason < AjazzReasonCount; ++reason) {
            char actual[256], expected[256];
            int n = snprintf(expected, sizeof(expected),
                "{\"schema\":1,\"utc\":\"1970-01-01T00:00:00Z\","
                "\"level\":\"%s\",\"event\":\"%s\",\"reason\":\"%s\"}\n",
                levels[event], events[event], reasons[reason]);
            if (n <= 0 || (size_t)n >= sizeof(expected)) return false;
            size_t size = AjazzEncodeOperationalEvent(actual, sizeof(actual),
                (AjazzOperationalEvent)event, (AjazzOperationalReason)reason, 0);
            if (size != (size_t)n || strcmp(actual, expected) != 0) return false;
        }
    }
    return true;
}

static bool check_refusals(void) {
    char buffer[256];
    const AjazzOperationalEvent event = AjazzEventStarted;
    const AjazzOperationalReason reason = AjazzReasonNone;
    return AjazzEncodeOperationalEvent(NULL, sizeof(buffer), event, reason, 0) == 0 &&
        AjazzEncodeOperationalEvent(buffer, 0, event, reason, 0) == 0 &&
        AjazzEncodeOperationalEvent(buffer, 1, event, reason, 0) == 0 &&
        buffer[0] == '\0' &&
        AjazzEncodeOperationalEvent(buffer, sizeof(buffer), AjazzEventCount, reason, 0) == 0 &&
        AjazzEncodeOperationalEvent(buffer, sizeof(buffer), event, AjazzReasonCount, 0) == 0 &&
        AjazzEncodeOperationalEvent(buffer, sizeof(buffer), (AjazzOperationalEvent)-1, reason, 0) == 0 &&
        AjazzEncodeOperationalEvent(buffer, sizeof(buffer), event, (AjazzOperationalReason)-1, 0) == 0;
}

static bool check_durations(void) {
    char actual[256];
    const char expected[] =
        "{\"schema\":1,\"utc\":\"1970-01-01T00:00:00Z\",\"level\":\"WARN\","
        "\"event\":\"IsolatedPollTimedOut\",\"reason\":\"timeout\",\"duration_ms\":1250}\n";
    size_t n = AjazzEncodeTimedOperationalEvent(actual, sizeof(actual),
        AjazzEventIsolatedPollTimedOut, AjazzReasonTimeout, 0, 1250);
    return n == strlen(expected) && strcmp(actual, expected) == 0 &&
        AjazzElapsedMilliseconds(10, 11.25) == 1250 &&
        AjazzElapsedMilliseconds(10, 10) == 0 &&
        AjazzElapsedMilliseconds(10, 9) == -1 &&
        AjazzElapsedMilliseconds(-1, 0) == -1 &&
        AjazzElapsedMilliseconds(NAN, 0) == -1 &&
        AjazzElapsedMilliseconds(0, INFINITY) == -1 &&
        AjazzElapsedMilliseconds(0, 86400) == 86400000 &&
        AjazzElapsedMilliseconds(0, 86401) == -1 &&
        AjazzEncodeTimedOperationalEvent(actual, sizeof(actual),
            AjazzEventStarted, AjazzReasonNone, 0, 1) == 0 &&
        AjazzEncodeTimedOperationalEvent(actual, sizeof(actual),
            AjazzEventDockClockFailed, AjazzReasonUnsuccessful, 0, -2) == 0 &&
        AjazzEncodeTimedOperationalEvent(actual, sizeof(actual),
            AjazzEventDockClockFailed, AjazzReasonUnsuccessful, 0, 86400001) == 0 &&
        AjazzEncodeTimedOperationalEvent(actual, sizeof(actual),
            AjazzEventDockClockSucceeded, AjazzReasonNone, 0, 86400000) > 0;
}

int main(void) {
    if (!check_records() || !check_refusals() || !check_durations()) {
        fputs("FAIL: Apple operational event encoding\n", stderr);
        return 1;
    }
    puts("PASS: 70 closed event/reason records and invalid-input refusals");
    puts("PASS: bounded monotonic duration conversion and exact optional JSON field");
    return 0;
}
