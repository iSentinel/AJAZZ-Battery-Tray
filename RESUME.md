# Resume — optional GDI/USER resource sampler candidate

- beta.54 published; release 45142789278 PASS, six assets.
  Main merge 5d99d10189f6627d918b8c39deb39575849233f1.
- USB Reconcile scratch allocation optimization shipped in beta.54;
  real CPU and memory improvement is not yet measured.
- perf/gui-resource-sampler adds opt-in Windows GDI/USER object counts.
  Default sampler CSV unchanged, offline comparator accepts base/GUI
  formats and refuses mixed input. Four fixture tests; CI pending.
- Only developer tools and docs/workflow modified, no tray, installer
  or HID changes. No runtime GUI metrics collector added.
- Next: verify Python and Windows CI, merge after PASS without new app
  version. Actual device sleep, affected AJ159, multi-BLE and owner
  Windows benchmarking remain outstanding; no live HA/MQTT broker.
