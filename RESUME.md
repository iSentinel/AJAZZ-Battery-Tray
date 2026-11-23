# Resume — optional MQTT broker parameter preflight

- beta.53 published; workflow 45139628072 PASS; six assets.
- PR #70 availability policy merged 10be9fde200ffd0b7f775ff62763a768c10c7a63.
- PR #71 non-retained fresh battery / retained availability, ack gate;
  final Windows 45140932515, macOS 45140932548 and preview
  45140932525 PASS; merged 096778a40bc807d83643273a5a0527baea1d2001.
- feat/ha-mqtt-tls-preflight adds optional offline config validation:
  explicitly enabled, MQTT5, TLS, certificate verification, manual topic
  prefix and session credentials presence. Fifteen pure checks await CI, including null/whitespace rejection.
  No MQTT package, network calls, service, credentials on disk or tray code.
- Next: open draft PR and verify Windows/macOS/preview CI. Real broker TLS
  identity validation, scoped credentials, HA discovery/expire_after and
  reconnect behavior require explicit operator opt-in and hardware tests.
- Owner Windows idle resource measurement, AULA physical sleep/wake,
  affected AJ159 capture and multi-BLE remain pending.
