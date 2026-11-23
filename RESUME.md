# Resume — AULA single-flight lifecycle candidate

- beta.49 published, workflow 45087429858 PASS; six assets verified.
- beta.50 PR #64 final Windows 45087837752 / macOS 45087838061 PASS;
  merged 5fd06ca333bd2e47d881446e822ccdb5fd654c20.
  Release workflow 45088588616 in progress, publication unverified.
- PR #65 synchronized with beta.50 main. Lazy AULA timer, disposal on
  disable/shutdown, manual reads without timer; configured cadence unchanged.
- AulaPollLifecycle integrated: one request at a time, stale ticket rejects
  old results; re-enable during read schedules 100 ms replacement after
  completion. Fourteen new assertions; C# CI pending. APEX Python 8/8 PASS.
- Next: verify beta.50 publication and latest PR #65 Windows/macOS CI.
  Prepare beta.51 metadata after PASS; physical AULA sleep/recovery and
  Windows resource comparison remain open. No HID reader/parser changes.
- HA optional and isolated. Both AJ159 reports/HAR, multi-BLE, backup
  restore and actual API acceptance still outstanding.
