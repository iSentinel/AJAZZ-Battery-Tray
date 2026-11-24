#ifndef AJAZZ_BATTERY_REPORT_H
#define AJAZZ_BATTERY_REPORT_H

#include <stddef.h>
#include <stdint.h>

// IOKit can return the requested 05 report with or without its report ID.
static inline int AjazzBatteryPercent(const uint8_t *bytes, size_t length) {
    if (!bytes || length == 0) return -1;
    if (bytes[0] == 0x05) {
        bytes++;
        length--;
    }
    if (length < 3) return -1;

    // GearHub F7 mouse or combined slot, with the same gates as Windows.
    if (length >= 9 && bytes[6] >= 1 && bytes[6] <= 3) {
        if (bytes[6] == 1 || bytes[3] > 1 || bytes[0] != 1 || bytes[4] != 0 ||
            bytes[5] != 1 || bytes[8] != 0) return -1;
    } else if (bytes[0] != 0 || bytes[1] != 0) {
        return -1;
    }
    return bytes[2] >= 1 && bytes[2] <= 100 ? bytes[2] : -1;
}

#endif
