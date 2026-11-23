# Resume — separate HA preview candidate

- beta.51 published; release 45091032358 PASS, six assets verified.
- PR #67 combined Windows 45092724526 / macOS 45092724453 PASS;
  35 assertions. beta.52 metadata commit 0617547f587f6727a76a899734aef15bd99d078d;
  final CI and publication pending.
- feat/optional-ha-cli adds separately runnable .NET 8 AjazzHaPreview,
  hidden in-memory token, explicit session row confirmation and fresh-only
  preview. No polling worker, MQTT, installation or tray reference.
  Python regression 23/23 PASS; Gateway has no dotnet SDK.
- Added dedicated optional preview CI for build, CLI help, invalid port,
  redirected input and project isolation. Not yet run.
- Next: verify beta.52 final CI, merge PR #67 and verify publication.
  Sync preview branch to main and open draft PR; audit interactive token
  cancellation and build/test results before any separate packaging.
- Actual HA/MQTT transport, Windows hardware acceptance and measured
  resource comparison remain outstanding.
