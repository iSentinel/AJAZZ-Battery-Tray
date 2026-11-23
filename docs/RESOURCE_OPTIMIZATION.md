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
