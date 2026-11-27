/* Deterministic queue state tests; no app, filesystem or hardware. */
#include "../../macos/AjazzOperationalQueue.h"
#include <string.h>

static AjazzQueuedEvent sample(time_t timestamp) {
    AjazzQueuedEvent value = {AjazzEventIsolatedPollTimedOut, AjazzReasonTimeout,
                             timestamp, 1250};
    return value;
}

static bool saturation_and_seal(void) {
    AjazzOperationalQueue q = {0};
    AjazzQueuedEvent value;
    for (size_t i = 0; i < AJAZZ_QUEUE_CAPACITY - 1; ++i)
        if (!AjazzQueueOffer(&q, sample((time_t)i))) return false;
    if (AjazzQueueOffer(&q, sample(99)) || q.dropped != 1 ||
        !AjazzQueueSeal(&q, 100) || AjazzQueueSeal(&q, 101) ||
        AjazzQueueOffer(&q, sample(102)) || q.dropped != 2 ||
        q.count != AJAZZ_QUEUE_CAPACITY) return false;
    for (size_t i = 0; i < AJAZZ_QUEUE_CAPACITY; ++i) {
        if (!AjazzQueueClaim(&q, &value) || AjazzQueueClaim(&q, &value)) return false;
        bool last = i == AJAZZ_QUEUE_CAPACITY - 1;
        if (value.event != (last ? AjazzEventStopped : AjazzEventIsolatedPollTimedOut) ||
            value.timestamp != (last ? 100 : (time_t)i) ||
            value.durationMs != (last ? -1 : 1250) ||
            !AjazzQueueComplete(&q, !last)) return false;
    }
    return !q.count && !q.inFlight && q.written == AJAZZ_QUEUE_CAPACITY - 1 &&
        q.failed == 1 && !AjazzQueueComplete(&q, true) && !AjazzQueueClaim(&q, &value);
}

static bool wraparound_and_refusals(void) {
    AjazzOperationalQueue q = {0};
    AjazzQueuedEvent value;
    for (size_t i = 0; i < 256; ++i) {
        if (!AjazzQueueOffer(&q, sample((time_t)i)) ||
            !AjazzQueueClaim(&q, &value) || value.timestamp != (time_t)i ||
            !AjazzQueueComplete(&q, true)) return false;
    }
    value = sample(0);
    value.event = AjazzEventStopped;
    if (AjazzQueueOffer(&q, value)) return false;
    value.event = AjazzEventStarted;
    if (AjazzQueueOffer(&q, value)) return false;
    value = sample(0);
    value.reason = AjazzReasonCount;
    if (AjazzQueueOffer(&q, value) || q.dropped != 3 || q.written != 256) return false;
    q.dropped = UINT64_MAX;
    q.written = UINT64_MAX;
    return !AjazzQueueOffer(&q, value) && q.dropped == UINT64_MAX &&
        AjazzQueueOffer(&q, sample(1)) && AjazzQueueClaim(&q, &value) &&
        AjazzQueueComplete(&q, true) && q.written == UINT64_MAX;
}

int main(void) {
    if (!saturation_and_seal() || !wraparound_and_refusals()) {
        fputs("FAIL: bounded Apple journal queue state\n", stderr);
        return 1;
    }
    puts("PASS: bounded FIFO, reserved stop, overflow, wraparound and loss accounting");
    return 0;
}
