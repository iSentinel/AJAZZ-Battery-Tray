#ifndef AJAZZ_DIAGNOSTIC_EXPORT_H
#define AJAZZ_DIAGNOSTIC_EXPORT_H
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>
#include <stdlib.h>
#include <stdio.h>

// Explicit GUI export: create a new private file, never replace or follow a link.
static inline int AjazzWriteDiagnostic(const char *path, const uint8_t *data, size_t size) {
    if (!path || !data || !size || size > 65536) return -1;
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    if (fd < 0) return -1;
    size_t offset = 0;
    while (offset < size) {
        ssize_t n = write(fd, data + offset, size - offset);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) { close(fd); return -1; }
        offset += (size_t)n;
    }
    return close(fd);
}

// Synthetic no-device test, executed by each native CI build.
static inline bool AjazzDiagnosticExportSelfTest(void) {
    char root[] = "/tmp/ajazz-diag-test-XXXXXX";
    if (!mkdtemp(root)) return false;
    char file[128], link[128];
    snprintf(file, sizeof(file), "%s/report.txt", root);
    snprintf(link, sizeof(link), "%s/link.txt", root);
    const uint8_t sample[] = {65, 66};
    struct stat info;
    bool ok = AjazzWriteDiagnostic(file, sample, sizeof(sample)) == 0 &&
        stat(file, &info) == 0 && (info.st_mode & 0777) == 0600 &&
        info.st_size == 2 && AjazzWriteDiagnostic(file, sample, 1) != 0 &&
        symlink(file, link) == 0 && AjazzWriteDiagnostic(link, sample, 1) != 0;
    int fd = open(file, O_RDONLY | O_NOFOLLOW);
    uint8_t readback[2] = {0};
    ok = ok && fd >= 0 && read(fd, readback, sizeof(readback)) == 2 &&
        readback[0] == sample[0] && readback[1] == sample[1];
    if (fd >= 0) close(fd);
    unlink(link);
    unlink(file);
    rmdir(root);
    return ok;
}
#endif
