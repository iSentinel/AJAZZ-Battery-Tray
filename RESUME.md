# Resume — optional MQTT availability policy candidate

- beta.53 PR #69 final Windows 45139329299 / macOS 45139329460 /
  preview 45139329257 PASS, merged
  1a053ddd611dd50b058bd95d1d187bb5698932da.
  Release publication not yet verified.
- feat/ha-mqtt-availability synchronized with beta.53 main; conflicts
  resolved by preserving complete main AULA tests and appending MQTT tests.
  Optional pure message-intent policy only, no network/broker dependency.
- Fresh session-bound reading: retained QoS1 battery followed by online;
  both have proposed 300s MQTT5 message expiry. Missing/stale: offline
  first, then empty retained battery message to clear a previous value.
- Twenty pure policy assertions pending C# CI, including remaining
  expiry floor and 5-minute boundary. Python tools 23/23 PASS.
- Next: verify beta.53 release, open PR for policy and run Windows/macOS/
  HA preview CI. Do not publish MQTT until authenticated TLS transport,
  acknowledgments, HA discovery/expiry and explicit stable mapping tested.
- Actual Windows resource baselines, AULA sleep/wake, AJ159 affected
  captures and multi-BLE remain pending.
