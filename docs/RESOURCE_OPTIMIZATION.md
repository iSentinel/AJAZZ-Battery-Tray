# Lightweight runtime acceptance

Keep normal battery polling and threshold behavior unchanged. Optional
Home Assistant / MQTT remains outside the default tray distribution.
API projection and automatic-update timer are allocated only when enabled.

## Icon refresh
Primary and secondary tray icons now compare value-type visual keys before
allocating a bitmap/font/GDI handle. A changed percent, cached marker,
effective palette or neutral state triggers redraw; unchanged output reuses
the owned icon. Menu labels and tooltip writes are skipped when identical.
No unbounded icon cache, no new timer, no hardware polling changes.

## Reproducible Windows comparison
Compare beta.47 and the optimized build on the same Windows PC, power plan,
devices, transports, polling intervals and notification/history settings.
Disable API and automatic updates; close dashboard/history windows. Warm
up for 60 seconds, then run the same five-minute collection for each version.
Do not run two tray instances. Obtain PID using Task Manager or Get-Process.

```powershell
.\tools\Measure-TrayResources.ps1 -ProcessId 1234 -DurationSeconds 300 -OutputPath .\beta47.csv
.\tools\Measure-TrayResources.ps1 -ProcessId 5678 -DurationSeconds 300 -OutputPath .\optimized.csv
```

Use actual PIDs in place of the examples. Record average CPU normalized
to one logical core, private bytes, working set, handles and thread counts.
Repeat at least three runs and compare comparable steady-state intervals.
The sampler itself is a separate process and its CPU is not included.
Measure timer wakeups and GDI/USER object counts separately (e.g., Windows
Performance Recorder and Task Manager); the CSV does not claim to measure
those. Also verify transitions: fresh, cached, disconnected, neutral,
per-device colors, language change, secondary icons and Explorer restart.
No threshold for resource use has yet been owner-approved. No measured
improvement is claimed until the Windows comparison is completed.

## History startup and idle allocation
- Constructor no longer reads or sorts CSV data. First actual Record loads
  only the newest retained valid row using one streaming pass. Explicit
  graph reads still use full retention and chronological ordering.
- Unchanged readings use the existing timestamp/percent/state comparison
  without allocating a BatterySample. Keep five-minute samples, changes,
  disconnect events, 30-day retention and 20,000-row limit unchanged.
- Eight additional assertions cover streaming equivalence, ties, bounds,
  lazy load and actual temporary-file append suppression.
- Windows CI now smoke-tests the PowerShell sampler against its own process
  and verifies CSV shape and no overwrite. This is not a tray CPU benchmark.

## Monitoring hot paths (next candidate)
- Select the preferred present receiver or ordinal minimum in one pass;
  no temporary sorted/distinct array. Visible receiver selection uses direct
  lookup and streaming fallback, preserving hidden-device policy.
- Select the first battery-bearing receiver in original batch order without
  a temporary array. BLE primary selection preserves lowest session number.
- Skip extra-icon collections entirely when multiple icons are disabled;
  skip BLE extra-icon projection with no BLE slots.
- USB discovery interval uses the same minimum and normalization without
  LINQ; excludes AULA overrides. No changes to actual polling cadence.
- Ten added pure selection and interval assertions. Initial CI pending.
  Actual Windows CPU/allocations and rendered behavior still need measurement.

- Low-battery threshold state now uses three bits instead of a HashSet and
  reversed LINQ enumeration on each evaluation. Deterministic reference
  comparison covers 8192 samples with changing thresholds and invalid
  percentages. Preserve urgency, hysteresis and crossed-muted behavior.
- Reuse immutable absent/unknown receiver readings; still run disconnect
  notification and history policies for every known absence. Missing-poll
  counter saturates at two, avoiding overflow after long uptime.
- Two additional regression assertions; combined CI pending.

## Deadline-based opt-in update scheduling
When automatic checks are explicitly enabled, replace the 10-second
repeating timer with a disposable one-shot timer scheduled from the policy's
monotonic deadline. First check after 60 seconds, successful check after
24 hours, failed check after one hour; suspend while manual dialog or an
automatic request is active. Cancel on opt-out/channel change and re-arm
only after the pending request completes. No schedule or timer by default.
Eleven assertions cover initial, due/overdue, success/failure, disabled,
pending and stale-generation deadlines. Windows timer UI lifecycle and
actual wakeup measurements still require acceptance. This does not modify
the HID poll cadence or add HA dependencies.

- Guard callbacks from disposed/replaced update timers. Saturate monotonic
  deadline addition against overflow. Serialize manual and automatic HTTP
  lookups via a lazy shared asynchronous gate, including queue wait in the
  existing 15-second timeout. No worker or timer when unused.
- Five more assertions cover deadline overflow, overlapping callers,
  queued cancellation and gate release on completion/failure. These use
  synthetic operations without a live network. Combined CI pending.

## Optional AULA timer lifecycle
The prior AULA timer already stopped during each poll and used the configured
interval after completion. Do not claim a reduction in periodic wakeups from
this change. Allocate the timer only when automatic AULA monitoring is enabled,
dispose it on opt-out or shutdown, and ignore callbacks from replaced timers.
Manual battery reads remain possible with monitoring off without allocating a
timer. Preserve the first startup delay (1 second), 100 ms interval-change
refresh, configured completion-based cadence, and existing generation guard.
Acceptance: disabled startup; manual read while disabled; enable; change
interval; disable during a pending read; re-enable before completion; exit
with a pending read. Verify no stale result or automatic polling after opt-out,
no duplicate workers, unchanged cached readings and normal sleep recovery.
C# compilation, actual Windows timer lifecycle and hardware acceptance pending.

### AULA single-flight lifecycle
The UI uses a testable ticket-based lifecycle. A late reply from a disabled
or replaced session cannot update readings. Re-enable during an existing
read waits for that read to finish, then schedules a replacement after
100 ms instead of waiting a complete configured interval. No parallel
worker or new HID command is introduced. Fourteen assertions exercise
manual/automatic reads, disabled/idle states, repeated completion, stale
reply, fast re-enable and shutdown. C# CI and physical acceptance pending.

### AULA sleep and recovery state consistency
AULA dashboard and active API projection share one observation classifier.
A successful automatic reading is fresh, never a scheduled-skip state.
Explicit manual reads remain manual-only and are excluded from API output
when automatic monitoring is disabled. Cached replies retain the original
observation timestamp; unknown presence, unplug, invalid samples and
expired cache never become fresh. Unexpected read failures clear the cache.
Twelve new assertions include a simulated eight-hour sleep (960 no-reply
observations), 24-hour expiration, and successful recovery. These are
synthetic state tests, not real hardware or wall-clock endurance evidence.

## Offline comparison of measured runs
After collecting comparable CSVs on the same Windows PC, run the standalone
standard-library Python analyzer (no dependency added to the tray):

```powershell
python tools/compare_tray_resources.py --baseline baseline1.csv baseline2.csv baseline3.csv --candidate candidate1.csv candidate2.csv candidate3.csv
```

CPU is calculated from total CPU-time delta divided by elapsed duration,
normalized to one logical core. Each run contributes a median for RAM,
handles and threads; the report compares medians across runs. A zero
baseline reports N/A for relative change. Durations must be within 10%;
versions must be consistent within each group. Fewer than three runs raises
a warning. PASS means validated inputs, not a performance acceptance gate.
The analyzer cannot independently verify identical hardware, workload or
settings, and does not measure GDI objects or wakeups. No measured tray
improvement is claimed. Fifteen fixture tests and eight APEX tests PASS on
Gateway. Actual owner Windows CSVs remain outstanding.

The analyzer now validates exact CSV row shape, bounded UTF-8 input, UTC
measurement timestamps and finite calculated metrics. Duplicate paths and
byte-identical CSVs (SHA-256) are rejected to avoid counting the same run
twice. A dedicated offline developer-tools workflow runs on tool changes;
no runtime dependency or additional tray process is introduced.

## USB reconciliation scratch reuse (candidate)

The prior DevicePollSchedule.Reconcile allocated a HashSet plus a filtered
array after each known USB inventory. The candidate lazily allocates two
small scratch collections and reuses them across reconciliations, clearing
all contents after each pass. Unknown discovery still preserves deadlines,
a known empty inventory removes expired identities, and no poll interval or
hardware request changes. Ten pure regression assertions cover large
inventories, repeated discovery, unplug, empty/unknown results and single
input enumeration. This is an allocation strategy, not a measured reduction
of Windows CPU/working set or timer wakeups; actual side-by-side Windows
benchmarks remain required.

## Optional GDI/USER object sampling

Use the explicit Windows-only -IncludeGuiResources switch:
```powershell
.\tools\Measure-TrayResources.ps1 -ProcessId 1234 -DurationSeconds 300 -IncludeGuiResources -OutputPath .\gui.csv
python tools/compare_tray_resources.py --baseline old1.csv old2.csv old3.csv --candidate new1.csv new2.csv new3.csv
```
Default CSV remains compatible. With the switch, the sampler appends
gdi_objects and user_objects from Windows GetGuiResources. The offline
comparator accepts either exact schema and refuses mixed-schema data.
These counts are not CPU wakeup metrics. A Windows CI smoke checks the
extended sampler; four Python fixtures cover GUI comparison and rejection.
Actual Windows CPU/RAM/GDI/USER improvements are not claimed until the
owner provides same-PC, comparable measurement runs.

## Receiver/icon reconciliation scratch candidate

ReceiverMonitor.Apply and RefreshIcons previously constructed a fresh
HashSet for each pass and icon cleanup created an additional ToArray.
The candidate reuses separate lazy scratch sets and missing-key lists
for USB receiver and tray icon inventories. The identity buffers are cleared
in finally after each pass, including when notifications fail. Unknown USB
enumeration still preserves the prior state, missing keys are captured
before icon dictionary removals, and primary receiver selection remains
ordinal/sticky. No HID commands or poll intervals change. Ten pure checks
and combined CI are required before release; no CPU/RAM improvement is
claimed absent repeatable Windows measurements.
