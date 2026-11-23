# Resume — resource comparison and beta.51 compile recovery

- beta.50 published; workflow 45088588616 PASS, six assets verified.
- PR #65 head 6a6d187 Windows 45088980556: all 588 unit tests PASS,
  resource sampler smoke PASS, Windows publish FAIL CS0029 (EventArgs
  parameter named underscore). macOS 45088980635 PASS.
- Fixed the timer callback in commit 1ec83dcbfebd2a97362beb2e26e19034af8cd6e8.
  Windows 45089648620 running; macOS 45089648574 PASS. Do not merge before
  successful full CI. Prepare beta.51 version metadata after PASS.
- Separate branch test/resource-comparison implements offline CSV comparison
  with CPU delta/elapsed and medians across runs, duration/version validation,
  and zero-baseline handling. Ten fixture tests + eight APEX tests PASS
  on Gateway; no tray dependency. Actual comparable Windows CSVs absent.
- Next: finish PR #65 beta.51 CI and release, sync comparison branch with
  main; add CI coverage for Python tools and review CSV validation.
- Physical AULA sleep/wake, paired AJ159 evidence, multi-BLE, API and
  Windows resource acceptance remain pending. No HID reader changes.
