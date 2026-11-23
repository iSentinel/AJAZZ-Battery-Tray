# Resume — beta.51 release candidate

- beta.50 published; workflow 45088588616 PASS, six assets.
- PR #65 adds lazy AULA timer, single-flight lifecycle, consistent
  fresh/cached UI and API state. Twenty-six new assertions.
- Windows 45088980556: 588 unit assertions and resource sampler PASS;
  publish failed CS0029 on event parameter named underscore.
- Fixed in 1ec83dcbfebd2a97362beb2e26e19034af8cd6e8;
  Windows 45089648620 / macOS 45089648574 PASS.
- beta.51 release metadata prepared. Final CI and publication pending.
- Separate test/resource-comparison branch has ten new Python tests,
  eight APEX tests PASS. Integrate after beta.51 release.
- Hardware sleep/wake, both AJ159 reports/HAR, multi-BLE and actual
  Windows resource measurements remain open. No HID reader changes.
  HA stays optional and isolated.
