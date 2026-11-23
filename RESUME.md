# Resume — High Sierra prerelease and stability checkpoints

- PR #78 merged at 2080f302281fc6e0bfe4f05669e20de8cf562410.
  High Sierra Intel CI 45178005476 PASS, modern macOS 45178005491
  PASS and Windows 45178005488 PASS.
- Experimental High Sierra v0.3.0-highsierra.1 release workflow
  45178458346 PASS. Both release assets verified after downloading.
  Main Latest remains v0.3.0-beta.56.
- Next task: guard the manual CoreBluetooth state and per-attempt
  timeout lifecycle; expand HID parser smoke testing; keep hardware
  acceptance explicitly pending.
- Physical High Sierra on iMac Late 2013 not yet tested.
  Do not claim live USB/BLE hardware compatibility.

# Resume — beta.56 publish and physical acceptance checkpoints

- beta.55 release 45150994852 PASS and all six assets verified.
  PR #75 final Windows 45150679762 / macOS 45150679558 PASS.
- PR #76 single-pass opted-in BLE scheduling final Windows
  45151826742 / macOS 45151826820 PASS; merged
  d26780312170a71e5c87a7dccd049bbe5fa36da1.
  beta.56 release workflow 45152156278 PASS; all six assets published.
- PRs #70–#72 offline optional HA MQTT policy, ACK ordering and TLS
  parameters have passed CI and merged. No live broker/credentials.
- Optional Windows resource/GDI/USER CSV comparator merged PR #74.
  Actual same-PC Windows CPU/RAM/GDI/USER observations not available.
- Open physical acceptance: AULA L99 prolonged sleep/recovery, two
  AJ159 (working/affected) redacted reports and HAR, mixed/multiple BLE
  and USB cases, actual Windows resource before/after measurements.
- No claim of measured CPU savings, physical hardware acceptance or
  completed Home Assistant integration; HID protocol remains unchanged.
