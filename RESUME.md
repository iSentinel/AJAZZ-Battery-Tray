# Resume — USB discovery allocation candidate

- beta.53 published; release 45139628072 PASS, all six assets.
- PR #70 optional offline MQTT availability merged
  10be9fde200ffd0b7f775ff62763a768c10c7a63.
- PR #71 acknowledged MQTT sequencing and non-retained state merged
  096778a40bc807d83643273a5a0527baea1d2001.
- PR #72 optional TLS/consent preflight Windows 45141549065,
  macOS 45141549003, preview 45141549165 PASS; merged
  f9498ab953b692cb6d98c72060d38b0c82e06d7d.
- PR #73 runtime optimization synchronized to main; ten pure USB
  reconciliation regression assertions, lazy reused HashSet/List
  scratch to avoid per-known-enumeration allocations. No poll interval,
  HID read or deadline changes. Final Windows/macOS CI pending.
- Next: verify PR #73 exact head CI, prepare beta.54 metadata only
  after PASS; actual Windows resource and AULA sleep acceptance pending.
- MQTT broker, real TLS, HA discovery and credentials still unimplemented.
  AJ159 affected capture and multiple BLE owner acceptance remain open.
