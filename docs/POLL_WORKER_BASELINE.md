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
