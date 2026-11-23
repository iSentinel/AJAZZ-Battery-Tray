# Resume — resource comparison acceptance candidate

- beta.51 PR #65 final Windows 45090441648 / macOS 45090441628 PASS;
  merged a1d9a06e61e11248e69d9746b29bc8699314e2c3.
  Publication verification pending.
- test/resource-comparison synchronized with beta.51 main. Offline bounded
  CSV comparison validates schema, UTC timestamps, finite values and
  duplicate content. Fifteen synthetic tests plus eight APEX tests.
- New separate Python tools workflow. No application runtime changes or
  dependencies. Actual Windows measurements remain absent.
- Next: open draft PR; verify CI and publication, then merge tools after PASS.
- Hardware AULA sleep/wake, both AJ159 reports/HAR, multi-BLE and actual
  Windows resource comparison remain open. HA remains optional.
