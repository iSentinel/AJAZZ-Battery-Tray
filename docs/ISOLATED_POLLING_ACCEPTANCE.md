# Isolated routine polling — owner acceptance matrix

Scope: a single development commit containing the Windows, Universal
macOS and High Sierra opt-in routine workers. Published beta.60 and
High Sierra .5 do not implement all these features. Use the exact
development artifacts of one verified commit; record commit SHA,
workflow run, executable checksum, OS build and architecture.
Do not combine results from different commits or different mice.

This procedure does not authorize new HID commands, intentional driver
failures, forced device hangs, firmware changes, or replay of vendor
configuration traffic. Close all other receiver utilities first.
Use natural sleep/wake and ordinary disconnect/reconnect only.

## Launch each edition

Close the previous tray completely before each launch. Use the
unpacked candidate executable in a separate directory; do not replace
the installed stable build. Use normal launch first (no arguments),
then repeat the same scenario with the session-only flag.

Windows PowerShell, from the unpacked candidate directory:

    $exe = (Resolve-Path '.\AJAZZBatteryTray.exe').Path
    $p = Start-Process -FilePath $exe -ArgumentList '--experimental-isolated-polling' -PassThru

Universal macOS, from the unpacked candidate directory:

    "./AJAZZ Battery Tray.app/Contents/MacOS/AJAZZBatteryTray" --experimental-isolated-polling

High Sierra, from the unpacked candidate directory:

    "./AJAZZ Battery Tray High Sierra.app/Contents/MacOS/AJAZZBatteryTrayHighSierra" --experimental-isolated-polling

No persistent preference or login item should enable this flag. Reopen
the ordinary stable application after testing if desired. Do not run
multiple builds against the same hardware concurrently.

## Shared acceptance checks

Repeat independently for each available platform, model and mode.
Use identical interval, notification options, history settings and
power conditions. Record NOT RUN when a device or feature is unavailable,
NOT OBSERVED when a naturally occurring condition did not happen,
FAIL for a reproduced defect, and PASS only for a directly observed
expected result. CI evidence is separate from field evidence.

| ID | Action | Expected observation |
| --- | --- | --- |
| P01 | Launch with awake receiver | Tray responsive; fresh verified percent or explicitly unknown |
| P02 | Compare with vendor application in a separate session | Numeric agreement if both independently supply a fresh reading; unknown is inconclusive, not a battery PASS |
| P03 | Observe three scheduled polls | Same configured poll interval, no duplicate updates or false samples |
| P04 | Leave mouse idle for normal sleep | Unknown if no reply; never fabricate 0% or a fresh sample |
| P05 | Wake by normal movement | Fresh read resumes if the receiver supports it, without app restart |
| P06 | Unplug after a verified reading; allow two completed polls | Confirmed absence; at most one opt-in disconnect notification |
| P07 | Replug same receiver | Discovery recovers; new percent only after successful read |
| P08 | Use Refresh now repeatedly at ordinary UI speed | UI stays responsive; no overlapping vendor requests in instrumented evidence |
| P09 | Quit during an observable active worker | Exit completes; no child remains; no late visible update |
| P10 | Observe naturally occurring timeout if any | No fake charge, false disconnect, or immediate retry burst; subsequent scheduled read can recover |
| P11 | Observe normal and isolated sessions at identical settings | Record CPU/RAM and duration; distinguish parent-only from whole-process-tree measurement |
| P12 | If native RTC supported, request one clock sync | Dock clock visually matches host; do not replay uncertain writes |
| P13 | Restart without experimental flag | Original in-process mode remains default |

For P08/P09/P10, mark NOT OBSERVED if process lifecycle or timeout
cannot be observed reliably. UI behavior alone cannot prove no
overlap or absence of short-lived child processes. Do not force a
hardware hang. CI tests deliberately use synthetic sleeping workers.

## Platform-specific checks

- Windows AJ159 APEX: use the explicit GET-ID comparison after closing
  both tray and vendor utilities. Follow WINDOWS_HID_DIAGNOSTIC_BETA57.md.
  Attach its reviewed diagnostic log. Exit 2 is expected for completed
  experimental comparison, not proof of battery compatibility.
- Windows AJ179 APEX: test confirmed USB absence before optional
  Bluetooth fallback, and USB priority on replug. Unknown or timeout
  must not activate fallback. Manual GATT reading is a separate check.
- Windows AULA L99: repeat A01–A14 from AULA_SLEEP_ACCEPTANCE.md;
  the new AJAZZ worker does not isolate the AULA path.
- Universal macOS: test Intel and Apple Silicon separately if available.
  Verify history gaps and local notification permissions.
- High Sierra: run on actual 10.13 Intel hardware; a 10.13-targeted
  build tested on macOS 15 CI is not physical 10.13 acceptance.
  Existing legacy edition does not implement dock RTC synchronization;
  mark P12 NOT RUN for that edition. Keep the legacy manual BLE test
  separate from USB polling.

## Resource evidence

Use at least 300 seconds per mode, three paired runs where practical.
Keep the same receiver, host, power plan, poll interval, awake/idle
condition, history settings and background workload.

Windows parent process example:

    .\tools\Measure-TrayResources.ps1 -ProcessId $p.Id -DurationSeconds 300 -IntervalSeconds 5 -OutputPath .\isolated-parent.csv

For each normal session select a new file path such as normal-parent.csv.
The existing sampler reports parent cumulative CPU, working set, private
bytes, handles and threads. Its CSV does **not** include short-lived
worker CPU/RAM. It cannot independently establish total resource cost.
For a process-tree comparison use an OS process-lifetime trace that
includes child start/exit and cumulative CPU; report the collection
method, parent and child totals separately. A task-manager snapshot
cannot capture all brief children.

On macOS use Activity Monitor for visual observations and a process
lifetime profiler if available for total child cost; report the method.
For startup-only measurements use tools/measure_apple_worker.py.
Synthetic worker startup CSVs do not establish actual HID or energy use.
No performance PASS threshold is declared until comparable owner data
is collected. Do not enable isolated polling by default from CI alone.

## Evidence template

    commit:
    platform / OS / architecture:
    mouse and connection mode:
    receiver revision (if known, not firmware):
    mode: normal | isolated
    interval / history / notifications:
    test ID:
    result: PASS | FAIL | NOT RUN | NOT OBSERVED
    observed timestamp / status / percent:
    expected vs actual:
    sanitized evidence filename:

Keep raw HAR, full USB captures, serials, private paths and unrelated
process traces local. Share only reviewed redacted excerpts. Preserve
original timestamps and do not mark a field test PASS merely because
the matching synthetic CI self-test passed.

Default activation remains blocked until the applicable field checks
are complete, regressions resolved, and end-to-end resource impact
reviewed. A development build may be distributed for explicit testing
without asserting hardware support or a new public release.


## Regression: unknown Windows receiver observation

An unknown enumeration previously skipped per-receiver history and
disconnect debounce processing. A confirmed missing poll followed by
unknown and another missing poll could be counted as consecutive
absence. The updated monitor explicitly interrupts pending absence
counts for all tracked receivers, preserving already-delivered alerts.
For previously present receivers it records an unavailable history gap,
clears the current measurement, and retains the last verified timestamp.
It never emits a low-battery event or claims a new numeric measurement
from a busy/timeout/unknown result. Already absent devices do not
receive repeated unknown-history rows. The ordinary polling schedule
and BLE fallback rules are unchanged. This correction has synthetic
policy and CSV regression tests; physical acceptance remains separate.
