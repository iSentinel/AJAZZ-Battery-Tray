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


## Universal opt-in menu integration

In a development build with the integration, close the older app and
vendor utilities, then launch the executable with the session-only
option:

    "/Applications/AJAZZ Battery Tray.app/Contents/MacOS/AJAZZBatteryTray" --experimental-isolated-polling

The default launch does not enable the worker. In the experimental
mode, the existing battery query and scheduled RTC command run in
sequential bounded children sharing the per-user vendor gate.
On Quit, AppKit defers termination, cancels the active token, and
completes termination after the supervisor returns. No history or
alerts are applied from the cancelled poll. The poll timer is stopped.
A kernel stall can still delay actual child exit.

A battery timeout is displayed explicitly in EN/RU/UK, recorded only
as an unavailable history gap, and resets the disconnect debounce.
Unknown discovery defers a manual RTC request until the next normal
poll, without a retry burst. A clock command that may have reached
the device is treated as an attempt even if its result is unavailable;
no immediate automatic repeat is scheduled. The manual deferral
also corrects the existing in-process path.

Synthetic self-tests include timeout notification policy, valid status
IPC, simulated hang/cancel/recovery, and clock result serialization.
The normal native reader, poll settings, BLE and High Sierra menu
are unchanged. Owner acceptance must cover launch/quit during polling,
sleep/wake, replug, manual refresh, RTC and resource use. No release
or actual hardware PASS is implied.
