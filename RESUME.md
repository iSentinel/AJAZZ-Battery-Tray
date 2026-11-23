# Resume — beta.56 opt-in Bluetooth scheduling candidate

- beta.55 published: release workflow 45150994852 PASS, six assets.
- PR #76 single-pass BluetoothMultiSession.TryBegin initial Windows
  45151372157 and macOS 45151372393 PASS.
- beta.56 release metadata prepared. Require final exact-head CI before
  merging or publishing. HID readers and poll intervals unchanged.
- No automatic BLE opt-in, no additional GATT request, service or HA broker.
- Actual Windows CPU/GDI/USER measurements, AULA sleep/wake, paired
  AJ159 evidence and multi-device BLE owner acceptance remain pending.
