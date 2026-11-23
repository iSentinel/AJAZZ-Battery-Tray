# Resume — beta.55 receiver/icon scratch release candidate

- beta.54 published; release 45142789278 PASS, six assets.
- PR #74 optional GDI/USER sampler Windows 45143788162,
  macOS 45143788089, Python 45143788173 PASS; merged
  db331116f469da417539acec63959275ef659da9.
- PR #75 initial Windows 45150093604 and macOS 45150093633 PASS.
  ReceiverMonitor uses lazy, separate reusable scratch sets and
  missing-key lists for USB and extra-icons; finally clears keys.
  Ten frame assertions plus two exception/recovery checks.
- beta.55 metadata prepared. MUST verify exact final CI head before
  merge and publication. No HID reader/protocol or poll timer changes.
- Do not claim Windows resource improvement without actual same-PC runs.
  AULA sleep/recovery, affected AJ159 evidence, multi-BLE and interactive
  HA preview acceptance remain open. Optional MQTT broker is not deployed.
