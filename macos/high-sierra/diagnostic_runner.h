#import <Foundation/Foundation.h>

/// 0600 output file; no symlink following. Returns 0 on success.
int LegacyPrepareOutput(NSString *path);

/// Spawn a diagnostic worker and enforce a wall-clock timeout.
/// Exit status: 0=verified, 2=inconclusive, 124=timeout, 1=error.
int LegacyRunBoundedWorker(const char *worker, int timeoutSeconds);
