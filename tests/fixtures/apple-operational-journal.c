/* Synthetic private journal fixtures; no app profile or hardware is accessed. */
#include "../../macos/AjazzOperationalJournal.h"
#include <stdlib.h>
#include <string.h>

static bool append_event(const char *root, size_t limit) {
    return AjazzJournalWrite(root, AjazzEventStarted, AjazzReasonNone, 0, limit);
}

static bool rotation(const char *root, int dir) {
    char record[256];
    size_t n = AjazzEncodeOperationalEvent(record, sizeof(record),
        AjazzEventStarted, AjazzReasonNone, 0);
    struct stat active, previous;
    if (!n || !append_event(root, 256) || !append_event(root, 256) ||
        !append_event(root, 256)) return false;
    return fstatat(dir, AJAZZ_JOURNAL_ACTIVE, &active, AT_SYMLINK_NOFOLLOW) == 0 &&
        fstatat(dir, AJAZZ_JOURNAL_PREVIOUS, &previous, AT_SYMLINK_NOFOLLOW) == 0 &&
        AjazzJournalFileSafe(&active, 256) && AjazzJournalFileSafe(&previous, 256) &&
        active.st_size == (off_t)n && previous.st_size == (off_t)(2 * n);
}

static bool tail_and_contention(const char *root, int dir) {
    int fd = openat(dir, AJAZZ_JOURNAL_ACTIVE, O_WRONLY | O_APPEND);
    if (fd < 0) return false;
    bool ok = write(fd, "torn", 4) == 4;
    close(fd);
    if (!ok || !append_event(root, 256)) return false;
    fd = openat(dir, AJAZZ_JOURNAL_PREVIOUS, O_RDONLY);
    if (fd < 0) return false;
    char tail[4];
    struct stat info;
    ok = fstat(fd, &info) == 0 && info.st_size >= 4 &&
        pread(fd, tail, 4, info.st_size - 4) == 4 && memcmp(tail, "torn", 4) == 0;
    close(fd);
    int lease = openat(dir, AJAZZ_JOURNAL_LEASE, O_RDWR);
    if (lease < 0) return false;
    ok = ok && flock(lease, LOCK_EX | LOCK_NB) == 0 && !append_event(root, 256);
    close(lease);
    return ok && append_event(root, 256);
}

static bool refusals(const char *root, int dir) {
    if (fchmodat(dir, AJAZZ_JOURNAL_ACTIVE, 0644, 0) != 0 ||
        append_event(root, 256) ||
        fchmodat(dir, AJAZZ_JOURNAL_ACTIVE, 0600, 0) != 0) return false;
    if (linkat(dir, AJAZZ_JOURNAL_ACTIVE, dir, "alias", 0) != 0) return false;
    bool ok = !append_event(root, 256);
    if (unlinkat(dir, "alias", 0) != 0 || !ok) return false;
    if (unlinkat(dir, AJAZZ_JOURNAL_PREVIOUS, 0) != 0 ||
        symlinkat(AJAZZ_JOURNAL_ACTIVE, dir, AJAZZ_JOURNAL_PREVIOUS) != 0 ||
        append_event(root, 256)) return false;
    if (unlinkat(dir, AJAZZ_JOURNAL_PREVIOUS, 0) != 0) return false;
    int fd = openat(dir, AJAZZ_JOURNAL_PREVIOUS, O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (fd < 0) return false;
    ok = ftruncate(fd, 257) == 0;
    close(fd);
    return ok && !append_event(root, 256) && !append_event(root, 127);
}

/// Confirm edition separation and the exact lifecycle records in private storage.
static bool lifecycle_records(const char *root, int parent, bool legacy) {
    const char *name = legacy ? "AJAZZBatteryTrayHighSierra-Journal" :
                                "AJAZZBatteryTray-Journal";
    char actual[512] = {0}, expected[512];
    size_t n = AjazzEncodeOperationalEvent(expected, sizeof(expected),
        AjazzEventStarted, AjazzReasonNone, 0);
    size_t m = AjazzEncodeOperationalEvent(expected + n, sizeof(expected) - n,
        AjazzEventStopped, AjazzReasonNone, 1);
    bool ok = AjazzJournalLifecycle(root, legacy, false, 0) &&
        AjazzJournalLifecycle(root, legacy, true, 1);
    int dir = openat(parent, name, O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    if (dir < 0) return false;
    struct stat info;
    ok = ok && fstat(dir, &info) == 0 && (info.st_mode & 07777) == 0700;
    int fd = openat(dir, AJAZZ_JOURNAL_ACTIVE, O_RDONLY | O_NOFOLLOW);
    if (fd >= 0) {
        ok = ok && n && m && read(fd, actual, sizeof(actual)) == (ssize_t)(n + m) &&
            memcmp(actual, expected, n + m) == 0;
        close(fd);
    } else ok = false;
    unlinkat(dir, AJAZZ_JOURNAL_ACTIVE, 0);
    unlinkat(dir, AJAZZ_JOURNAL_LEASE, 0);
    close(dir);
    return unlinkat(parent, name, AT_REMOVEDIR) == 0 && ok;
}

/// Refuse unsafe preexisting directories without modifying their permissions.
static bool lifecycle_refusals(const char *root, int parent) {
    const char *name = "AJAZZBatteryTray-Journal";
    if (mkdirat(parent, name, 0755) != 0) return false;
    struct stat info;
    bool ok = !AjazzJournalLifecycle(root, false, false, 0) &&
        fstatat(parent, name, &info, AT_SYMLINK_NOFOLLOW) == 0 &&
        (info.st_mode & 0777) == 0755;
    if (unlinkat(parent, name, AT_REMOVEDIR) != 0 ||
        symlinkat(".", parent, name) != 0) return false;
    ok = ok && !AjazzJournalLifecycle(root, false, false, 0);
    if (unlinkat(parent, name, 0) != 0) return false;
    return ok && !AjazzJournalLifecycle(NULL, false, false, 0);
}

int main(void) {
    char root[] = "/tmp/ajazz-journal-test-XXXXXX";
    if (!mkdtemp(root)) return 1;
    int dir = open(root, O_RDONLY | O_DIRECTORY);
    bool ok = dir >= 0 && rotation(root, dir) && tail_and_contention(root, dir) &&
        refusals(root, dir) && lifecycle_records(root, dir, false) &&
        lifecycle_records(root, dir, true) && lifecycle_refusals(root, dir);
    if (dir >= 0) {
        unlinkat(dir, "alias", 0);
        unlinkat(dir, AJAZZ_JOURNAL_ACTIVE, 0);
        unlinkat(dir, AJAZZ_JOURNAL_PREVIOUS, 0);
        unlinkat(dir, AJAZZ_JOURNAL_LEASE, 0);
        close(dir);
    }
    if (rmdir(root) != 0) ok = false;
    if (!ok) {
        fputs("FAIL: synthetic Apple journal storage\n", stderr);
        return 1;
    }
    puts("PASS: private journal rotation, torn tail, contention and unsafe-file refusals");
    puts("PASS: edition-specific lifecycle records and unsafe-directory refusals");
    return 0;
}
