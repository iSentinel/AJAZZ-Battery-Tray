# Resume — monitoring hot-path candidate

- beta.47 release 45084000358 PASS, six assets verified.
- beta.48 PR #62 final Windows 45085165165 / macOS 45085165171 PASS;
  merged ed8d8388a46ec0977457a47768edf2b0241237d4.
  Release workflow 45086004496 started; publication not yet verified.
- PR #63 synced with main, streaming receiver and BLE selection, fewer
  temporary collections, same USB discovery interval. Ten assertions.
- Added bitmask low-battery threshold policy with old-policy comparison
  over 8192 deterministic samples; reusable absent/unknown readings and
  saturated disconnect counter, preserving history and notification timing.
  Twelve new assertions total. Gateway Python APEX 8/8 PASS.
- Next: verify beta.48 publication and latest PR #63 CI; prepare beta.49
  metadata only after PASS. Windows resource comparison still outstanding.
- HA optional and isolated. Both AJ159 reports/HAR, multi-BLE, long AULA
  sleep and physical UI acceptance pending. Live HID readers unchanged.
