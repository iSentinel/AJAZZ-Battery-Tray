# Resume — isolated optional HA mapping candidate

- beta.51 publication 45091032358 PASS; all six assets verified.
- PR #66 Windows 45091148941 / macOS 45091148912 / Python 45091148907 PASS;
  merged dca6bee7e2ef79e28e7e093e65e34dc4940660cc, main Python
  45092260378 PASS. No runtime version bump for developer tools.
- feat/optional-ha-session-binding transplants the older HA mapping
  into integrations/home-assistant, outside the tray project, test-only
  link. Optional API store adds random per-activation epoch; clipboard
  snapshot without active API omits it. Seventeen regression checks
  await C# CI; 23 offline Python tests PASS, HID readers unchanged.
- Next: open draft PR and verify CI; audit mapping against actual
  exported JSON, distinguish API activation from process identity,
  then plan independent opt-in bridge transport. No MQTT dependency,
  automatic service, LAN binding or HA installation introduced.
- Physical AULA sleep/wake, paired AJ159 evidence, multi-BLE, API and
  Windows resource measurements remain open.
