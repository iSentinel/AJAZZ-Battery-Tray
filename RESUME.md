# Resume — offline MQTT acknowledgment candidate

- beta.53 merged 1a053ddd611dd50b058bd95d1d187bb5698932da;
  publication check pending at branch creation.
- PR #70 availability policy head 264aab562f040d22949c59f05721fd3db11aa970.
- feat/ha-mqtt-delivery-gate branches from PR #70, not from main:
  pure in-memory QoS1 message sequence validation and acknowledged
  progression only, with explicit cancellation. Eight assertions added.
  Python offline tests PASS. No broker, credentials, MQTT library, service
  or runtime tray dependency.
- Next: verify PR #70 exact CI and merge; sync this branch with main,
  review C# CI and publish no app release without a functional tray change.
  Actual TLS transport, MQTT5 broker and Home Assistant tests remain
  blocked on explicit opt-in/credentials and real acceptance environment.
- AULA long sleep, AJ159 affected capture, multiple BLE and Windows idle
  resource measurements remain unverified.
