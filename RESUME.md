# Resume — optional offline MQTT availability intent

- beta.52 published, PR #68 optional preview merged
  a1f280379e68504a1d39fc55daf5f3ff3f51e534.
- PR #69 AULA continuity beta.53 metadata 5fb9051 pending full CI.
- feat/ha-mqtt-availability based on beta.52 main, independent of PR #69:
  pure message-intent policy only, no network code or MQTT dependency.
  Fresh session-bound data: retained QoS1 battery then online with MQTT5
  300s expiry. Otherwise offline then clear retained battery. Twelve pure
  checks added; C# CI pending; Python tests PASS.
- Next: verify CI for PR #69, publish beta.53 only on final PASS.
  Sync optional policy branch to latest main after release and verify CI.
  Broker, credentials, TLS, discovery and HA installation remain blocked
  until explicit separate opt-in and physical acceptance.
- AULA sleep/wake, AJ159 affected captures, multi-BLE, API UI and
  resource measurements remain open.
