#import "diagnostic_runner.h"

#include <crt_externs.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

int LegacyPrepareOutput(NSString *path) {
    const char *name = path.fileSystemRepresentation;
    int fd = open(name, O_CREAT | O_WRONLY | O_TRUNC | O_NOFOLLOW, 0600);
    if (fd < 0) {
        perror("FAIL: cannot open diagnostic output");
        return 1;
    }
    if (fchmod(fd, 0600) != 0 ||
        dup2(fd, STDOUT_FILENO) < 0 ||
        dup2(fd, STDERR_FILENO) < 0) {
        perror("FAIL: cannot prepare diagnostic output");
        close(fd);
        return 1;
    }
    close(fd);
    return 0;
}

static double MonotonicSeconds(void) {
    struct timespec now = {0, 0};
    if (clock_gettime(CLOCK_MONOTONIC, &now) == 0)
        return (double)now.tv_sec + (double)now.tv_nsec / 1000000000.0;
    struct timeval fallback = {0, 0};
    gettimeofday(&fallback, NULL);
    return (double)fallback.tv_sec + (double)fallback.tv_usec / 1000000.0;
}

static int WorkerResult(int status, double elapsed) {
    if (WIFEXITED(status)) {
        int code = WEXITSTATUS(status);
        printf("END: exit=%d elapsed_ms=%.0f\n", code, elapsed * 1000.0);
        return code;
    }
    if (WIFSIGNALED(status)) {
        printf("FAIL: worker signal=%d elapsed_ms=%.0f\n",
               WTERMSIG(status), elapsed * 1000.0);
    } else {
        puts("FAIL: worker stopped without an exit status");
    }
    return 1;
}

/// Do not report a timeout as complete until the child is reaped.
static BOOL StopAndReap(pid_t child) {
    if (kill(child, SIGKILL) < 0 && errno != ESRCH) {
        printf("FAIL: cannot stop worker errno=%d\n", errno);
        return NO;
    }
    int status = 0;
    pid_t observed;
    do {
        observed = waitpid(child, &status, 0);
    } while (observed < 0 && errno == EINTR);
    if (observed == child || (observed < 0 && errno == ECHILD)) return YES;
    printf("FAIL: cannot reap worker errno=%d\n", errno);
    return NO;
}

int LegacyRunBoundedWorker(const char *worker, int timeoutSeconds) {
    NSString *path = [[NSBundle mainBundle] executablePath];
    if (!path.length) {
        puts("FAIL: cannot locate diagnostic executable");
        return 1;
    }
    const char *binary = path.fileSystemRepresentation;
    char *const args[] = {(char *)binary, (char *)worker, NULL};
    pid_t child = -1;
    printf("BEGIN: diagnostic=%s timeout_seconds=%d\n",
           worker, timeoutSeconds);
    int spawnError = posix_spawn(&child, binary, NULL, NULL, args, *_NSGetEnviron());
    if (spawnError) {
        printf("FAIL: posix_spawn error=%d\n", spawnError);
        return 1;
    }
    double start = MonotonicSeconds();
    for (;;) {
        int status = 0;
        pid_t observed = waitpid(child, &status, WNOHANG);
        double elapsed = MonotonicSeconds() - start;
        if (observed == child) return WorkerResult(status, elapsed);
        if (observed < 0 && errno != EINTR) {
            int waitError = errno;
            printf("FAIL: waitpid error=%d\n", waitError);
            if (waitError != ECHILD) StopAndReap(child);
            return 1;
        }
        if (elapsed >= (double)timeoutSeconds) {
            if (!StopAndReap(child)) return 1;
            printf("TIMEOUT: worker exceeded %d seconds; no battery "
                   "value is claimed\n", timeoutSeconds);
            return 124;
        }
        struct timespec delay = {0, 100000000};
        nanosleep(&delay, NULL);
    }
}
