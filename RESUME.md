# Resume — beta.47 experimental local API candidate

- beta.46 release 45082464200 PASS, all six assets verified.
- PR #61 initial full API Windows 45083205204 / macOS 45083205268 PASS.
  44 snapshot and HTTP assertions; loopback only, ephemeral bearer,
  request limits, explicit start/stop, no additional HID polls.
- beta.47 metadata prepared; final CI and publication pending.
- Next: verify final PR #61 CI and beta.47 assets. Design a secure HA
  bridge separately; do not bind the tray API to LAN or imply durable
  entity identity from session slots.
- Physical acceptance: both AJ159 reports/HAR, multi-BLE, prolonged
  AULA sleep, backup restore and actual Windows HTTP UI pending.
