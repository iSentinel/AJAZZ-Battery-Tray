# Routine HID polling worker cost baseline

The draft audit's isolated full-HID capture has a synthetic sample
worker that starts the published .NET process and transfers a small
known JSON result over stdout, with no HID calls. Before applying
process isolation to routine polling, measure this lower bound.

Use a Windows executable built from draft PR 99 or a descendant:

    powershell -NoProfile -File tools/Measure-PollWorker.ps1 -ExePath .\AJAZZBatteryTray.exe -DryRun
    powershell -NoProfile -File tools/Measure-PollWorker.ps1 -ExePath .\AJAZZBatteryTray.exe -OutputPath .\worker-baseline.csv -Iterations 20

The benchmark starts one worker at a time and verifies its exact
synthetic output. Each worker is bounded by a timeout. CSV rows are
written after successful iterations, and an existing file is never
overwritten. It reports wall-clock p50, p95 and maximum using
nearest-rank quantiles, and the p95 share of the shortest supported
15-second polling interval. The GitHub Windows build runs 20 samples
and publishes the CSV as a separate CI artifact.

This measures process startup, runtime initialization, stdout and
exit on that machine. It does not measure native HID enumeration,
radio latency, CPU usage, real poll energy or memory, or cold-start
behavior under every host condition. CI timing is not a hardware
acceptance result.

Next: record the same benchmark on the owner's Windows PC and
measure steady-state application resources using Measure-TrayResources.ps1.
Compare a supervised process with a persistent worker before changing
default polling. Repeat on macOS separately. No runtime polling
strategy has been changed by this tool.


## Windows CI results, 2026-11-24

PR #101, workflow 45327594576, artifact 14890313646. Independently
recomputed from all 20 CSV rows (nearest-rank p50/p95):

| Metric | Result |
| --- | ---: |
| Completed | 20/20 |
| Minimum | 99.293 ms |
| p50 | 112.419 ms |
| p95 | 148.834 ms |
| Maximum | 304.940 ms |
| Mean | 126.497 ms |
| p95 share of 15 s | 0.992% |

This supports prototyping a supervised subprocess, but does not
establish energy, CPU, HID latency or owner-hardware performance.

## Routine read prototype

The new internal RoutinePollWorker is not connected to the tray timer.
It accepts deferred receiver keys over local stdin and returns a
normal Batch over stdout. The keys are local identifiers, not for
export, logging or public artifacts. No additional feature command
is introduced. The parent rejects a second concurrent invocation,
kills the child at the deadline and awaits process exit before releasing
the gate. An independent child watchdog limits an abandoned child.
A simulated self-test covers valid/unavailable data, scheduled skip,
overlap, timeout, shutdown cancellation and a subsequent fresh worker.
The self-test never accesses HID:

    Start-Process -FilePath .\AJAZZBatteryTray.exe -ArgumentList '--self-test-routine-poll-worker' -Wait -PassThru

The prototype does not include dock clock synchronization, AULA, BLE,
cross-process coordination with other HID tools or UI integration.
Before production activation, define shared device-I/O exclusion,
unknown-presence mapping, orderly shutdown and RTC scheduling; test
actual hardware and resources. The regular tray polling path remains
unchanged.


## Session-local vendor I/O exclusion

The AJAZZ read batch and dock RTC send now share a named mutex within
the Windows logon session. This covers regular polling, bounded full
capture, safe CLI diagnostics and the experimental GET comparison,
because they all call the same AjazzHidReader. A busy gate yields an
unknown-presence batch, not a disconnect or a valid sample. No wait
queue or retry burst is introduced. The gate is held and released
on the native I/O thread; Windows releases ownership on process death,
and the next caller accepts abandoned ownership. No external GearHub
or older app version participates in this mutex; close those separately.
Metadata-only inventory and AULA/BLE use other paths. CI holds the
mutex in a separate process and checks that diagnostic mode performs
no HID enumeration or F7 request. Routine integration remains disabled.


## Opt-in tray integration

In a development build containing this change (not published beta.60),
close all old tray instances and vendor utilities, then launch:

    Start-Process -FilePath .\AJAZZBatteryTray.exe -ArgumentList '--experimental-isolated-polling'

The ordinary invocation still uses the original in-process reader.
The option is session-only, not stored in preferences or autostart.
The experimental path uses sequential children for routine battery
reads and the existing dock RTC command when due. Each has an 8 s
parent deadline and 12 s independent child watchdog. RTC writes are
not automatically retried after an ambiguous timeout; the existing
schedule is recorded before the attempt. Unknown discovery defers
manual RTC requests instead of sending a command or inventing absence.
The same mutex protects vendor I/O in both paths. No new HID opcode,
report framing, poll interval or AULA/BLE implementation is introduced.

The parent's normal state handling consumes the returned batch. Read
timeout and busy state produce no battery sample, no confirmed
disconnect and no Bluetooth fallback. The tray timer resumes after
the worker has exited. Closing the application cancels an active child.
Synthetic tests cover IPC, schedule skips, child timeout, overlap,
cancellation, recovery, clock-result serialization and localized
status rules. Physical behavior and resource cost remain unverified.

Field acceptance: compare normal and opt-in sessions on the same PC
with automatic update checks disabled; use identical poll settings,
one receiver first, then multiple if available. Record startup,
several polls, sleep/wake, unplug/replug, manual refresh, a manually
requested RTC sync when applicable, and app exit. Confirm no parallel
vendor I/O, no false battery sample or disconnect after timeout,
no orphan child, and comparable idle CPU/RAM. Use the existing
Measure-TrayResources.ps1 for resource evidence. Do not deliberately
force a native hardware hang; the CI synthetic hang covers that case.


## Apple synthetic startup baseline

The universal Swift app and the separate High Sierra Objective-C app
expose the same internal synthetic sample. It returns a fixed JSON
response with unknown presence and null battery, without accessing
IOKit, modifying device settings, or starting the menu-bar application.

    python3 tools/measure_apple_worker.py --dry-run
    python3 tools/measure_apple_worker.py --exe "/Applications/AJAZZ Battery Tray.app/Contents/MacOS/AJAZZBatteryTray" --output apple-worker.csv

For High Sierra use the corresponding High Sierra development
executable and a new CSV path. Python 3.7+ is required for the
measurement helper, not for the application. This mode is not present
in the published beta.60 or High Sierra .5 binaries.

The helper runs 20 sequential samples by default, checks exact synthetic
response content, limits each process to five seconds by default, and
preserves completed CSV rows if a later sample fails. It reports
nearest-rank p50/p95 and maximum wall latency. CI uploads separate CSVs
for both Apple editions using the macOS 15 Intel runner. A successful
Intel runner measurement of the 10.13-targeted executable is not an
actual High Sierra test, nor does a universal build establish arm64
runtime latency. This is a startup lower bound, not HID/CPU/energy
performance. No regular Apple polling or RTC behavior changes.


## Apple CI results, 2026-11-24

PR #106 passed Windows, Python, macOS Universal and High Sierra CI.
The two 20-row CSV artifacts were downloaded and independently checked.

| Target on macOS 15 Intel | Min ms | p50 ms | p95 ms | Max ms |
| --- | ---: | ---: | ---: | ---: |
| Universal Swift | 11.856 | 14.716 | 20.310 | 33.708 |
| High Sierra Objective-C | 7.306 | 9.669 | 12.959 | 13.837 |

Universal: workflow 45329966717, artifact 14891985387.
High Sierra: workflow 45329966716, artifact 14891970336.
These are not physical macOS 10.13 or Apple Silicon results.

## Universal bounded-read prototype

ApexBoundedWorker.swift supervises a separate instance of the same
binary with an eight-second parent deadline and a 12-second child
alarm. It keeps the local gate until process exit, and distinguishes
timeout, busy and failed IPC from actual absence. The small JSON
reply carries only the existing receiver status and a 1..100 battery
value if verified. It contains no HID paths, raw frames or serials.
The regular menu timer, RTC, history and BLE remain unchanged.
The synthetic self-test covers all existing statuses, invalid frames,
overlap rejection, a simulated hang and recovery without HID:

    "/Applications/AJAZZ Battery Tray.app/Contents/MacOS/AJAZZBatteryTray" --self-test-bounded-poll

Use a development build containing the prototype, not beta.60.
CI must run this test after building. Before integrating the supervisor
into the menu timer, implement shared I/O exclusion, cancellation on
quit, and preserve uncertain USB presence and RTC scheduling. A
separate High Sierra implementation and physical validation remain
open. No public release is implied.

## High Sierra diagnostic worker lifecycle prerequisite

The legacy diagnostic watchdog previously returned 124 after SIGKILL
and a non-blocking waitpid. That did not establish child exit. Before
reusing the mechanism for regular polling, the supervisor now waits
for child termination/reaping (retrying EINTR), and reports failure
if it cannot stop/reap the worker. ECHILD is not followed by a kill
of a potentially reused PID. The real diagnostic child has its own
92-second alarm, just beyond the maximum supported 90-second deadline.
The CI synthetic sleep fixture checks the PID no longer exists after
the watchdog returns. This is a lifecycle fix to existing explicit
diagnostics; the menu timer still uses its original in-process reader.
As with any native worker, an OS-level uninterruptible kernel stall
cannot be guaranteed to terminate within the requested timeout.
