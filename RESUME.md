# Resume — resource comparison and beta.51 release preparation

- beta.50 published; workflow 45088588616 PASS, six assets verified.
- PR #65 original Windows failure was EventArgs underscore CS0029;
  588 unit assertions and resource sampler had passed. Fixed callback
  1ec83dc; Windows 45089648620 / macOS 45089648574 PASS.
- beta.51 release metadata prepared (1431938a5a7e8d6033c59867cc1d5c94fa931c30);
  final Windows 45090441648 / macOS 45090441628 running. Verify exact head
  before merge, then check release assets.
- test/resource-comparison: strict CSV structure, 2 MiB bounded reads, UTC
  timestamps, hash-based duplicate rejection, finite calculated metrics.
  Fifteen fixture tests plus eight APEX tests PASS on Gateway.
  Dedicated offline Python tools workflow added, not yet run in GitHub CI.
- Next: finalize beta.51, sync resource-comparison branch to main,
  resolving RESUME conflict explicitly, then open draft PR.
- Actual Windows resource CSVs and physical AULA sleep/wake remain pending;
  do not interpret synthetic CSVs as measurements. HA remains optional.
  Both AJ159 reports/HAR, multi-BLE and actual API acceptance remain open.
