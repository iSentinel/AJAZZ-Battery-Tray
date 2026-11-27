/* Synthetic filesystem and background worker integration; no app or HID. */
#include "../../macos/AjazzOperationalEditionWriter.h"

static const char *edition_name(bool legacy) {
    return legacy ? "AJAZZBatteryTrayHighSierra-Journal" : "AJAZZBatteryTray-Journal";
}

static bool invalid_paths(void) {
    char tooLong[AJAZZ_EDITION_SUPPORT_LIMIT + 1];
    memset(tooLong, 'x', sizeof(tooLong));
    tooLong[0] = '/';
    tooLong[sizeof(tooLong) - 1] = '\0';
    return !AjazzEditionWriterCreate(NULL, false) &&
        !AjazzEditionWriterCreate("", false) &&
        !AjazzEditionWriterCreate("relative", false) &&
        !AjazzEditionWriterCreate(tooLong, false) &&
        !AjazzEditionWriterOffer(NULL, AjazzEventStarted, AjazzReasonNone, 0, -1) &&
        !AjazzEditionWriterSeal(NULL, 0) && !AjazzEditionWriterWait(NULL, 0) &&
        !AjazzEditionWriterDestroy(NULL);
}

static bool exact_records(int parent, bool legacy) {
    char expected[1024], actual[1024];
    size_t n = AjazzEncodeOperationalEvent(expected, sizeof(expected),
        AjazzEventStarted, AjazzReasonNone, 1);
    if (!n) return false;
    size_t m = AjazzEncodeTimedOperationalEvent(expected + n, sizeof(expected) - n,
        AjazzEventIsolatedPollTimedOut, AjazzReasonTimeout, 2, 1250);
    if (!m) return false;
    size_t k = AjazzEncodeOperationalEvent(expected + n + m, sizeof(expected) - n - m,
        AjazzEventStopped, AjazzReasonNone, 3);
    if (!k) return false;
    int dir = openat(parent, edition_name(legacy), O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    if (dir < 0) return false;
    struct stat info;
    int fd = AjazzJournalOpen(dir, AJAZZ_JOURNAL_ACTIVE, O_RDONLY, AJAZZ_JOURNAL_LIMIT);
    bool ok = fstat(dir, &info) == 0 && (info.st_mode & 07777) == 0700 &&
        fd >= 0 && read(fd, actual, sizeof(actual)) == (ssize_t)(n + m + k) &&
        memcmp(actual, expected, n + m + k) == 0;
    if (fd >= 0) close(fd);
    close(dir);
    return ok;
}

static bool edition_records(const char *root, int parent, bool legacy) {
    char path[128];
    size_t length = strlen(root);
    if (length >= sizeof(path)) return false;
    memcpy(path, root, length + 1);
    AjazzOperationalEditionWriter *owner = AjazzEditionWriterCreate(path, legacy);
    if (!owner) return false;
    path[0] = '\0'; // The writer must not borrow this storage.
    struct stat info;
    bool absent = fstatat(parent, edition_name(legacy), &info, AT_SYMLINK_NOFOLLOW) < 0 &&
        errno == ENOENT;
    bool early = !AjazzEditionWriterDestroy(owner);
    if (!early) return false; // Unexpected destruction invalidates the handle.
    bool offered = AjazzEditionWriterOffer(owner, AjazzEventStarted, AjazzReasonNone, 1, -1);
    offered = AjazzEditionWriterOffer(owner, AjazzEventIsolatedPollTimedOut,
                                      AjazzReasonTimeout, 2, 1250) && offered;
    bool sealed = AjazzEditionWriterSeal(owner, 3);
    bool refused = !AjazzEditionWriterOffer(owner, AjazzEventStarted, AjazzReasonNone, 4, -1);
    if (!AjazzEditionWriterWait(owner, 5000)) return false;
    AjazzWriterStatus status = AjazzEditionWriterSnapshot(owner);
    bool destroyed = AjazzEditionWriterDestroy(owner);
    return absent && offered && sealed && refused && destroyed && status.finished &&
        status.written == 3 && status.failed == 0 && status.dropped == 1 &&
        !status.queued && !status.inFlight && exact_records(parent, legacy);
}

static bool refused_directory(const char *root, int parent) {
    const char *name = edition_name(false);
    if (mkdirat(parent, name, 0700) != 0 || fchmodat(parent, name, 0755, 0) != 0)
        return false;
    AjazzOperationalEditionWriter *owner = AjazzEditionWriterCreate(root, false);
    if (!owner) return false;
    bool offered = AjazzEditionWriterOffer(owner, AjazzEventStarted, AjazzReasonNone, 0, -1);
    bool sealed = AjazzEditionWriterSeal(owner, 1);
    if (!AjazzEditionWriterWait(owner, 5000)) return false;
    AjazzWriterStatus status = AjazzEditionWriterSnapshot(owner);
    bool destroyed = AjazzEditionWriterDestroy(owner);
    int dir = openat(parent, name, O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    if (dir < 0) return false;
    struct stat info;
    bool ok = fstat(dir, &info) == 0 && (info.st_mode & 07777) == 0755;
    ok = ok && fstatat(dir, AJAZZ_JOURNAL_ACTIVE, &info, AT_SYMLINK_NOFOLLOW) < 0 &&
        errno == ENOENT;
    ok = ok && fstatat(dir, AJAZZ_JOURNAL_LEASE, &info, AT_SYMLINK_NOFOLLOW) < 0 &&
        errno == ENOENT;
    close(dir);
    return offered && sealed && destroyed && status.failed == 2 &&
        status.written == 0 && status.finished && ok;
}

static bool remove_edition(int parent, bool legacy) {
    const char *name = edition_name(legacy);
    int dir = openat(parent, name, O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    if (dir < 0) return false;
    const char *entries[] = {AJAZZ_JOURNAL_ACTIVE, AJAZZ_JOURNAL_LEASE, AJAZZ_JOURNAL_PREVIOUS};
    bool ok = true;
    for (size_t i = 0; i < sizeof(entries) / sizeof(entries[0]); ++i)
        if (unlinkat(dir, entries[i], 0) != 0 && errno != ENOENT) ok = false;
    close(dir);
    return unlinkat(parent, name, AT_REMOVEDIR) == 0 && ok;
}

int main(void) {
    char root[] = "/tmp/ajazz-edition-writer-XXXXXX";
    if (!mkdtemp(root)) return 1;
    int parent = open(root, O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    bool ok = parent >= 0 && invalid_paths() &&
        edition_records(root, parent, false) && edition_records(root, parent, true) &&
        remove_edition(parent, false) && remove_edition(parent, true) &&
        refused_directory(root, parent) && remove_edition(parent, false);
    if (parent >= 0) close(parent);
    if (rmdir(root) != 0) ok = false;
    if (!ok) {
        fputs("FAIL: Apple background edition journal\n", stderr);
        return 1;
    }
    puts("PASS: owned path, both edition journals, exact FIFO records and unsafe-directory refusal");
    return 0;
}
