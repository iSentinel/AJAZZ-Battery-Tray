#ifndef AJAZZ_SESSION_ARCHIVE_H
#define AJAZZ_SESSION_ARCHIVE_H

#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/time.h>
#include <time.h>

// The common importer accepts stored ZIP entries. Apple reports are capped at 64 KiB.
#define AJAZZ_SESSION_LIMIT 32
#define AJAZZ_SESSION_REPORT_LIMIT 65536
typedef struct {
    uint8_t *data;
    size_t size;
    unsigned marker;
    char captured[21], added[28];
} AjazzSessionEntry;
typedef struct {
    bool active;
    unsigned count;
    AjazzSessionEntry reports[AJAZZ_SESSION_LIMIT];
} AjazzDiagnosticSession;

static inline AjazzDiagnosticSession *AjazzSessionCreate(void) {
    return (AjazzDiagnosticSession *)calloc(1, sizeof(AjazzDiagnosticSession));
}

static inline void AjazzSessionClear(AjazzDiagnosticSession *s) {
    if (!s) return;
    for (unsigned i = 0; i < s->count; i++) free(s->reports[i].data);
    memset(s, 0, sizeof(*s));
}

static inline void AjazzSessionDestroy(AjazzDiagnosticSession *s) {
    AjazzSessionClear(s);
    free(s);
}

static inline bool AjazzSessionActive(const AjazzDiagnosticSession *s) { return s && s->active; }
static inline unsigned AjazzSessionCount(const AjazzDiagnosticSession *s) { return s ? s->count : 0; }
static inline void AjazzSessionStart(AjazzDiagnosticSession *s) {
    if (s && !s->active) { AjazzSessionClear(s); s->active = true; }
}

static inline const char *AjazzSessionMarker(unsigned index) {
    static const char *names[] = {"Baseline", "UsbSelected", "BluetoothSelected",
        "Sleep", "Wake", "Other", "ReviewedReport"};
    return index < sizeof(names) / sizeof(names[0]) ? names[index] : NULL;
}

// Exact UTC syntax used by the existing Apple snapshot and the local manifest.
static inline bool AjazzSessionTime(const char *s, size_t length) {
    if (!s || (length != 20 && length != 27)) return false;
    for (size_t i = 0; i < length; i++) {
        char required = i == 4 || i == 7 ? '-' : i == 10 ? 'T' :
            i == 13 || i == 16 ? ':' : i == length - 1 ? 'Z' : i == 19 ? '.' : 0;
        if (required ? s[i] != required : s[i] < '0' || s[i] > '9') return false;
    }
    return true;
}

static inline bool AjazzSessionCaptureTime(const uint8_t *data, size_t size, char out[21]) {
    unsigned matches = 0;
    // A report uses a single top-level UTC header, not a timestamp embedded in a trace.
    for (size_t i = 0; i + 26 <= size && i < 1024; i++) {
        if (memcmp(data + i, "\nUTC: ", 6) != 0) continue;
        if (!AjazzSessionTime((const char *)data + i + 6, 20) ||
            i + 26 == size || data[i + 26] != '\n') return false;
        memcpy(out, data + i + 6, 20);
        out[20] = 0;
        matches++;
    }
    return matches == 1;
}

static inline bool AjazzSessionAddAt(AjazzDiagnosticSession *s, unsigned marker,
    const uint8_t *data, size_t size, const char *added) {
    char captured[21];
    if (!AjazzSessionActive(s) || s->count >= AJAZZ_SESSION_LIMIT ||
        !AjazzSessionMarker(marker) || !data || !size || size > AJAZZ_SESSION_REPORT_LIMIT ||
        !added || strlen(added) != 27 || !AjazzSessionTime(added, 27) ||
        !AjazzSessionCaptureTime(data, size, captured) ||
        strncmp(captured, added, 19) > 0 ||
        (s->count && strcmp(added, s->reports[s->count - 1].added) <= 0)) return false;
    for (unsigned i = 0; i < s->count; i++)
        if (!strcmp(captured, s->reports[i].captured)) return false;
    uint8_t *copy = (uint8_t *)malloc(size);
    if (!copy) return false;
    memcpy(copy, data, size);
    AjazzSessionEntry *entry = &s->reports[s->count++];
    entry->data = copy; entry->size = size; entry->marker = marker;
    memcpy(entry->captured, captured, sizeof(captured));
    memcpy(entry->added, added, sizeof(entry->added));
    return true;
}

static inline bool AjazzSessionAdd(AjazzDiagnosticSession *s, unsigned marker,
    const uint8_t *data, size_t size) {
    struct timeval now;
    struct tm utc;
    char seconds[20], stamp[28];
    if (gettimeofday(&now, NULL) != 0 || !gmtime_r(&now.tv_sec, &utc) ||
        strftime(seconds, sizeof(seconds), "%Y-%m-%dT%H:%M:%S", &utc) != 19) return false;
    if (snprintf(stamp, sizeof(stamp), "%s.%06ldZ", seconds, (long)now.tv_usec) != 27)
        return false;
    return AjazzSessionAddAt(s, marker, data, size, stamp);
}

static inline uint32_t AjazzSessionCRC(const uint8_t *data, size_t size) {
    uint32_t crc = UINT32_MAX;
    for (size_t i = 0; i < size; i++) {
        crc ^= data[i];
        for (unsigned bit = 0; bit < 8; bit++) crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

static inline void AjazzZip16(uint8_t *p, uint16_t x) {
    p[0] = (uint8_t)x; p[1] = (uint8_t)(x >> 8);
}
static inline void AjazzZip32(uint8_t *p, uint32_t x) {
    AjazzZip16(p, (uint16_t)x); AjazzZip16(p + 2, (uint16_t)(x >> 16));
}

static inline bool AjazzZipWrite(int fd, const void *data, size_t size) {
    const uint8_t *p = (const uint8_t *)data;
    while (size) {
        ssize_t n = write(fd, p, size);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return false;
        p += n; size -= (size_t)n;
    }
    return true;
}

typedef struct { char name[32]; uint32_t offset, crc, size; } AjazzZipMember;

static inline bool AjazzZipLocal(int fd, AjazzZipMember *m, const uint8_t *data, size_t size,
    uint32_t *offset) {
    uint8_t header[30] = {0};
    size_t length = strlen(m->name);
    m->offset = *offset; m->size = (uint32_t)size; m->crc = AjazzSessionCRC(data, size);
    AjazzZip32(header, 0x04034b50); AjazzZip16(header + 4, 20);
    AjazzZip16(header + 12, 33); // 1980-01-01; actual observation times are in the manifest.
    AjazzZip32(header + 14, m->crc); AjazzZip32(header + 18, m->size);
    AjazzZip32(header + 22, m->size); AjazzZip16(header + 26, (uint16_t)length);
    if (!AjazzZipWrite(fd, header, sizeof(header)) || !AjazzZipWrite(fd, m->name, length) ||
        !AjazzZipWrite(fd, data, size)) return false;
    *offset += (uint32_t)(sizeof(header) + length + size);
    return true;
}

static inline bool AjazzZipCentral(int fd, const AjazzZipMember *m, uint32_t *offset) {
    uint8_t header[46] = {0};
    size_t length = strlen(m->name);
    AjazzZip32(header, 0x02014b50); AjazzZip16(header + 4, 20); AjazzZip16(header + 6, 20);
    AjazzZip16(header + 14, 33); AjazzZip32(header + 16, m->crc);
    AjazzZip32(header + 20, m->size); AjazzZip32(header + 24, m->size);
    AjazzZip16(header + 28, (uint16_t)length); AjazzZip32(header + 42, m->offset);
    if (!AjazzZipWrite(fd, header, sizeof(header)) || !AjazzZipWrite(fd, m->name, length)) return false;
    *offset += (uint32_t)(sizeof(header) + length);
    return true;
}

static inline size_t AjazzSessionManifest(const AjazzDiagnosticSession *s, char *out, size_t cap) {
    int n = snprintf(out, cap, "{\"schema\":\"diagnostic-session-v1\",\"identityBinding\":"
        "\"NOT_VERIFIED\",\"markers\":\"OWNER_ANNOTATED\",\"entries\":[");
    if (n < 0 || (size_t)n >= cap) return 0;
    size_t used = (size_t)n;
    for (unsigned i = 0; i < s->count; i++) {
        const AjazzSessionEntry *r = &s->reports[i];
        n = snprintf(out + used, cap - used, "%s{\"file\":\"snapshot-%02u.txt\","
            "\"marker\":\"%s\",\"addedUtc\":\"%s\",\"bytes\":%zu}", i ? "," : "",
            i + 1, AjazzSessionMarker(r->marker), r->added, r->size);
        if (n < 0 || (size_t)n >= cap - used) return 0;
        used += (size_t)n;
    }
    if (cap - used < 3) return 0;
    memcpy(out + used, "]}", 3);
    return used + 2;
}

static inline bool AjazzSessionZip(int fd, const AjazzDiagnosticSession *s) {
    AjazzZipMember members[AJAZZ_SESSION_LIMIT + 1] = {0};
    char manifest[8192];
    size_t size = AjazzSessionManifest(s, manifest, sizeof(manifest));
    uint32_t offset = 0;
    if (!size) return false;
    for (unsigned i = 0; i < s->count; i++) {
        snprintf(members[i].name, sizeof(members[i].name), "snapshot-%02u.txt", i + 1);
        if (!AjazzZipLocal(fd, &members[i], s->reports[i].data, s->reports[i].size, &offset)) return false;
    }
    strcpy(members[s->count].name, "manifest.json");
    if (!AjazzZipLocal(fd, &members[s->count], (const uint8_t *)manifest, size, &offset)) return false;
    uint32_t central = offset;
    for (unsigned i = 0; i <= s->count; i++)
        if (!AjazzZipCentral(fd, &members[i], &offset)) return false;
    uint8_t end[22] = {0};
    AjazzZip32(end, 0x06054b50); AjazzZip16(end + 8, (uint16_t)(s->count + 1));
    AjazzZip16(end + 10, (uint16_t)(s->count + 1)); AjazzZip32(end + 12, offset - central);
    AjazzZip32(end + 16, central);
    return AjazzZipWrite(fd, end, sizeof(end));
}

// Private exclusive export. Retain the session on failure; do not replace a path.
static inline bool AjazzSessionSave(const AjazzDiagnosticSession *s, const char *path) {
    if (!AjazzSessionActive(s) || s->count < 2 || s->count > AJAZZ_SESSION_LIMIT || !path) return false;
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    if (fd < 0) return false;
    bool ok = AjazzSessionZip(fd, s);
    return close(fd) == 0 && ok;
}

#endif
