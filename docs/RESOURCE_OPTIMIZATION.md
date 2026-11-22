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
