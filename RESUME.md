# Resume — optional MQTT delivery acknowledgment gate

- beta.53 released; workflow 45139628072 PASS; six assets.
- PR #70 availability policy Windows 45140136771 / macOS 45140136699 /
  optional HA preview 45140136710 PASS; merged
  10be9fde200ffd0b7f775ff62763a768c10c7a63.
- feat/ha-mqtt-delivery-gate now synchronized with main. All MQTT code
  remains optional in integrations/home-assistant; no broker, credentials,
  service or tray distribution changes.
- Separate pure delivery gate validates the two-message retained QoS1
  sequence, cannot advance after failed acknowledgment or cancellation.
  Eight additional assertions pending CI; Python regressions 23/23 PASS.
- Next: open draft PR and verify Windows/macOS/preview CI; avoid release
  version increment for this isolated optional pure-policy change.
- Actual TLS/MQTT broker, HA discovery, live delivery receipts, stable
  entity mapping and operator-approved credentials still unimplemented.
  AULA sleep, affected AJ159, mixed BLE and measured Windows resources
  remain open.
