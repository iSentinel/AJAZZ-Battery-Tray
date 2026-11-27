#ifndef AJAZZ_OPERATIONAL_JOURNAL_H
#define AJAZZ_OPERATIONAL_JOURNAL_H

#include "AjazzOperationalEvent.h"
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>

#define AJAZZ_JOURNAL_LIMIT (256u * 1024u)
#define AJAZZ_JOURNAL_ACTIVE "app-events.jsonl"
#define AJAZZ_JOURNAL_PREVIOUS "app-events.previous.jsonl"
#define AJAZZ_JOURNAL_LEASE "app-events.lock"

/// Accept only a private, owner-controlled regular single-link file.
static inline bool AjazzJournalFileSafe(const struct stat *info, size_t limit) {
    return S_ISREG(info->st_mode) && info->st_uid == geteuid() &&
        info->st_nlink == 1 && (info->st_mode & 07777) == 0600 &&
        info->st_size >= 0 && (uintmax_t)info->st_size <= limit;
}

/// Check existing entries without following a symlink.
static inline bool AjazzJournalEntrySafe(int directory, const char *name, size_t limit) {
    struct stat info;
    if (fstatat(directory, name, &info, AT_SYMLINK_NOFOLLOW) != 0)
        return errno == ENOENT;
    return AjazzJournalFileSafe(&info, limit);
}

/// Open a bounded regular file without following the final entry.
static inline int AjazzJournalOpen(int directory, const char *name, int flags,
                                   size_t limit) {
    if (!AjazzJournalEntrySafe(directory, name, limit)) return -1;
    int fd = openat(directory, name,
        flags | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK, 0600);
    struct stat info;
    if (fd < 0) return -1;
    if (fstat(fd, &info) != 0 || !AjazzJournalFileSafe(&info, limit)) {
        close(fd);
        return -1;
    }
    return fd;
}

/// Under the cooperating writer lease, preserve a torn tail by rotating it.
static inline bool AjazzJournalAppend(int directory, const char *record,
                                      size_t size, size_t limit) {
    if (!AjazzJournalEntrySafe(directory, AJAZZ_JOURNAL_PREVIOUS, limit)) return false;
    int fd = AjazzJournalOpen(directory, AJAZZ_JOURNAL_ACTIVE,
                              O_RDWR | O_CREAT | O_APPEND, limit);
    if (fd < 0) return false;
    struct stat info;
    char last = '\n';
    if (fstat(fd, &info) != 0 || !AjazzJournalFileSafe(&info, limit) ||
        (info.st_size > 0 && pread(fd, &last, 1, info.st_size - 1) != 1)) {
        close(fd);
        return false;
    }
    if ((uintmax_t)info.st_size + size > limit || last != '\n') {
        if (close(fd) != 0 ||
            renameat(directory, AJAZZ_JOURNAL_ACTIVE,
                     directory, AJAZZ_JOURNAL_PREVIOUS) != 0) return false;
        fd = AjazzJournalOpen(directory, AJAZZ_JOURNAL_ACTIVE,
                              O_WRONLY | O_CREAT | O_EXCL | O_APPEND, limit);
        if (fd < 0) return false;
    }
    // Do not retry partial writes; the next append rotates an interrupted tail.
    ssize_t written = write(fd, record, size);
    int closed = close(fd);
    return written == (ssize_t)size && closed == 0;
}

/// Append only a closed event to an existing private directory.
/// Nonblocking cooperating-writer coordination, not an adversarial sandbox.
static inline bool AjazzJournalWrite(const char *path, AjazzOperationalEvent event,
    AjazzOperationalReason reason, time_t timestamp, size_t limit) {
    if (!path || limit < 128 || limit > AJAZZ_JOURNAL_LIMIT) return false;
    char record[256];
    size_t size = AjazzEncodeOperationalEvent(record, sizeof(record), event, reason, timestamp);
    if (!size || size > limit) return false;
    int directory = open(path, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    struct stat info;
    if (directory < 0) return false;
    if (fstat(directory, &info) != 0 || !S_ISDIR(info.st_mode) ||
        info.st_uid != geteuid() || (info.st_mode & 07777) != 0700) {
        close(directory);
        return false;
    }
    int lease = AjazzJournalOpen(directory, AJAZZ_JOURNAL_LEASE, O_RDWR | O_CREAT, 0);
    bool ok = lease >= 0 && flock(lease, LOCK_EX | LOCK_NB) == 0 &&
        AjazzJournalAppend(directory, record, size, limit);
    if (lease >= 0) close(lease);
    close(directory);
    return ok;
}

#endif
