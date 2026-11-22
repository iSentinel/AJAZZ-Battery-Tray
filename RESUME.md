# Resume — monitoring hot path optimization

- beta.47 release 45084000358 PASS, six assets verified.
- PR #62 initial combined Windows 45084378739 / macOS 45084378734 PASS,
  including 19 icon/history assertions and PowerShell sampler smoke test.
  beta.48 final candidate 5462e482c1d26d581cc06f58857181de4215df9e;
  Windows 45085165165 / macOS 45085165171 PASS.
  Merged ed8d8388a46ec0977457a47768edf2b0241237d4; publication pending.
- perf/monitor-hot-path based on beta.48 candidate; replaces sorted
  receiver selection and temporary summary arrays with streaming selection,
  skips inactive extra tray icon and BLE collections, uses direct USB
  discovery interval minimum. Ten new assertions; C# CI not yet run.
  Gateway Python APEX regression 8/8 PASS, git diff --check PASS.
- Next: verify beta.48 release assets; hot-path branch synced with main;
  open draft PR and run CI. Compare real
  Windows CPU, memory, handles, GDI and wakeups before claiming improvement.
- HA optional and isolated. Hardware gates unchanged: two AJ159 reports/HAR,
  multi-BLE, AULA sleep, backup restore and real API acceptance.
