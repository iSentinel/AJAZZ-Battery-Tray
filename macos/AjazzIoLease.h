#ifndef AJAZZ_IO_LEASE_H
#define AJAZZ_IO_LEASE_H

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>

/// Shared per-user vendor I/O gate for both Apple editions.
/// Returns a held fd, or -1 on contention or unsafe/unavailable storage.
/// Never unlink the lock file: all participants must lock the same inode.
static inline int AjazzAcquireIoLease(void) {
    char directory[PATH_MAX], path[PATH_MAX];
    size_t n = confstr(_CS_DARWIN_USER_TEMP_DIR, directory, sizeof(directory));
    if (n == 0 || n > sizeof(directory)) return -1;
    int count = snprintf(path, sizeof(path), "%s/ajazz-apex-vendor-io-v1.lock", directory);
    if (count < 0 || (size_t)count >= sizeof(path)) return -1;
    int fd = open(path, O_CREAT | O_RDWR | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK, 0600);
    if (fd < 0) return -1;
    struct stat info;
    if (fstat(fd, &info) != 0 || !S_ISREG(info.st_mode) ||
        info.st_uid != geteuid() || info.st_nlink != 1 || (info.st_mode & 077) != 0 ||
        flock(fd, LOCK_EX | LOCK_NB) != 0) {
        close(fd);
        return -1;
    }
    return fd;
}

static inline void AjazzReleaseIoLease(int fd) {
    if (fd >= 0) close(fd);
}

#endif
