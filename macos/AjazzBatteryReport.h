#ifndef AJAZZ_BATTERY_REPORT_H
#define AJAZZ_BATTERY_REPORT_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#ifdef __APPLE__
#include "AjazzIoLease.h"
#include "AjazzDiagnosticExport.h"
#include "AjazzSessionArchive.h"
#endif

// Presentation only: absent, future, non-finite and expired sample ages are invalid.
static inline bool AjazzSampleAgeIsCurrent(double ageSeconds) {
    return ageSeconds >= 0.0 && ageSeconds <= 300.0;
}

// Classify the existing admission policy; do not infer physical sleep state.
typedef enum {
    AjazzF7Unrecognized = 0,
    AjazzF7KeyboardOnly,
    AjazzF7InvalidStatus,
    AjazzF7ReadUnavailable,
    AjazzF7Offline,
    AjazzF7CannotSend,
    AjazzF7RadioBoot,
    AjazzF7ZeroField,
    AjazzF7OutOfRange,
    AjazzF7Accepted
} AjazzF7Gate;

typedef struct {
    AjazzF7Gate gate;
    int reportedField;
    int verifiedPercent;
} AjazzF7Observation;

static inline AjazzF7Gate AjazzF7Classify(const uint8_t *bytes) {
    if (bytes[6] == 1) return AjazzF7KeyboardOnly;
    if (bytes[3] > 1) return AjazzF7InvalidStatus;
    if (bytes[0] != 1) return AjazzF7ReadUnavailable;
    if (bytes[4] != 0) return AjazzF7Offline;
    if (bytes[5] != 1) return AjazzF7CannotSend;
    if (bytes[8] != 0) return AjazzF7RadioBoot;
    if (bytes[2] == 0) return AjazzF7ZeroField;
    if (bytes[2] > 100) return AjazzF7OutOfRange;
    return AjazzF7Accepted;
}

// Input is the payload after optional report-ID removal.
static inline AjazzF7Observation AjazzObserveF7(const uint8_t *bytes, size_t length) {
    AjazzF7Observation result = {AjazzF7Unrecognized, -1, -1};
    if (!bytes || length < 9 || bytes[6] < 1 || bytes[6] > 3) return result;
    result.gate = AjazzF7Classify(bytes);
    if (bytes[6] != 1 && bytes[2] >= 1 && bytes[2] <= 100)
        result.reportedField = bytes[2];
    if (result.gate == AjazzF7Accepted) result.verifiedPercent = result.reportedField;
    return result;
}

// IOKit can return the requested 05 report with or without its report ID.
static inline int AjazzBatteryPercent(const uint8_t *bytes, size_t length) {
    if (!bytes || length == 0) return -1;
    if (bytes[0] == 0x05) {
        bytes++;
        length--;
    }
    if (length < 3) return -1;

    AjazzF7Observation observation = AjazzObserveF7(bytes, length);
    if (observation.gate != AjazzF7Unrecognized) return observation.verifiedPercent;
    if (bytes[0] != 0 || bytes[1] != 0) return -1;
    return bytes[2] >= 1 && bytes[2] <= 100 ? bytes[2] : -1;
}

#endif
