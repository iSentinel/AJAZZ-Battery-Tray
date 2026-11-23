# Resume — isolated portable HA preview candidate

- beta.52 PR #67 final Windows 45092998151 / macOS 45092998102 PASS;
  merged ec66c667433f818e6c440595250baf8e217f4f90. Release workflow
  45093197963 started; confirm all six assets before claiming publication.
- PR #68 feat/optional-ha-cli synced with beta.52 main without conflict.
  No source/installer/macOS/release workflow differences.
- Native Ctrl+C terminates blocking input; Escape cancels token entry.
  Mutable 64-character token buffer cleared in finally; managed token
  string remains in process memory until GC/exit, not persisted.
- Dedicated CI builds, smoke-tests and publishes a separate self-contained
  win-x64 preview EXE and SHA256 manifest as Actions artifacts only.
  Latest C# preview CI pending. Gateway Python 23/23 PASS and diff checks PASS.
- Next: verify beta.52 publication and exact PR #68 head Windows/macOS/
  optional preview CI; verify portable artifact and merge if all PASS.
  Then audit session-bound mapping identity and design explicit MQTT opt-in
  with TLS/credentials/availability before transport implementation.
- No Home Assistant connection, broker, service, auto-start or tray bundle.
  Physical AULA, AJ159, multi-BLE and resource measurements remain open.
