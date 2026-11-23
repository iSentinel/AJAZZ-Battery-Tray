# Resume — beta.54 USB discovery allocation release candidate

- beta.53 published; workflow 45139628072 PASS, all six release assets.
- PR #70 offline optional HA availability merged 10be9fde200ffd0b7f775ff62763a768c10c7a63.
- PR #71 acknowledged ordering/non-retained state merged
  096778a40bc807d83643273a5a0527baea1d2001.
- PR #72 optional TLS parameter preflight final Windows 45141549065,
  macOS 45141549003, preview 45141549165 PASS; merged
  f9498ab953b692cb6d98c72060d38b0c82e06d7d.
- PR #73 lazy USB reconcile scratch reuse Windows 45142142430 /
  macOS 45142142117 PASS after main sync. Ten C# assertions.
- beta.54 version and release metadata prepared. Final exact HEAD CI
  must PASS before merge and release. HID commands and polling unchanged.
- No actual Windows resource improvement is claimed; owner measurements
  and AULA long sleep/wake, affected AJ159 and multi-BLE remain pending.
- MQTT actual broker TLS, credentials, HA entity mapping and deployment
  unimplemented. Optional-only policy code is isolated.
