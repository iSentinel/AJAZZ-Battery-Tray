# Per-device polling integration contract (Windows)

The global 15/30/60/120-second interval remains the inherited default.
A locally stored, validated receiver-key override or AULA profile override
selects one of these same intervals. Bluetooth GATT backoff remains separate.

## Implementation stages

1. Pure monotonic completion-based schedule and persistence (implemented).
2. Separate successful enumeration from actual battery sampling. Return a
   present-but-not-sampled result for a known receiver whose deadline has not
   elapsed. Such a result is not a failed poll, unplug, or new measurement.
3. Preserve each receiver's original timestamp and displayed last measurement
   on scheduled skips; do not append history or rerun alert logic. A fresh
   failed read retains existing unavailable semantics. Never label a cached
   prior measurement as newly sampled. Unknown enumeration remains unknown;
   no release of USB priority or false disconnect. Reset missing receiver
   schedule only after successful discovery, and force first sample after
   unknown presence recovery and actual replug.
4. Run discovery at the smallest active configured interval (including
   inherited default). Use monotonic milliseconds for due checks and UTC
   only for reporting. Use an immutable settings/schedule snapshot on worker
   threads; serialize AJAZZ HID/RTC; manual refresh bypasses due checks,
   without enabling disabled AULA or Bluetooth monitoring. Record completion
   after actual attempts, even failed ones; no catch-up bursts.
5. Integrate AULA separately: its opt-in behavior, independent cache,
   identity and asynchronous busy/generation guards remain authoritative.
   Separate presence discovery from throttled sampling or explicitly show
   last-known status with original timestamps until the next actual read.
6. Add localized tray/dashboard interval editor, inheritance/reset,
   save rollback and diagnostic effective interval. Keep actual local keys
   and paths out of exported reports.
7. Test mixed intervals, repeated skips, force refresh, failure, unplug/replug,
   unknown enumeration, interval changes, disabled AULA, AULA cache and BLE
   handover. No extra HID command, no new protocol format.

## Hardware gate

Use two AJAZZ receivers and AULA, with different configured intervals. Compare
actual query timestamps, verify fresh history only on attempted samples and
disconnects only after confirmed absence. Verify manual refresh, sleep/wake,
restart persistence, and diagnostics. CI is not a hardware acceptance result.

## Integration checkpoint

- AJAZZ enumeration now returns a scheduled-skip result for deferred known
  receivers; actual attempts retain completion tick and UTC. UI-thread
  snapshots determine deferred keys; new/unknown receivers are sampled.
- Receiver state preserves its last measurement on skips and avoids replaying
  history or alerts. Confirmed absence still reaches disconnect policy.
- AULA has a separate completion-based WinForms timer; its presence remains
  last-known until its next actual read. Disabled automatic monitoring stays
  disabled. Manual global refresh requests immediate sampling when available.
- Local interval editor available from tray and Device Manager; effective
  interval and receiver timestamps appear in extended diagnostics.
- Four additional pure presentation tests added. CI and actual mixed-device
  acceptance remain pending. No claim of timing accuracy on physical hardware.
