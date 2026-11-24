# Universal Apple worker cancellation prerequisite

The isolated-read prototype now accepts an optional thread-safe
cancellation token. The caller only sets a flag. The supervisor checks
the flag before launch, while waiting for completion (up to 50 ms
between checks under normal scheduling), and before accepting a reply.
It alone stops and reaps the child, and retains the supervisor gate
until process exit. Cancellation is a distinct result and must not
be used as evidence of absence or fresh battery telemetry.

The no-HID self-test verifies cancellation before launch, cancellation
of a deliberately sleeping child, timeout, and successful subsequent
sample. The child alarm still bounds normal abandoned-worker cases.
A kernel-level uninterruptible stall is not guaranteed to terminate
within the requested deadline.

The normal tray and RTC paths are not changed in this PR. Integrating
the opt-in menu mode requires retaining the token for each poll,
cancelling it on quit, suppressing UI updates during shutdown and
waiting for the supervisor's completion before releasing the tray.
Physical macOS behavior, app shutdown and resource use remain open.
