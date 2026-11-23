# Home Assistant bridge — session mapping foundation

The tray API remains loopback-only. This branch does not open a LAN port,
install an MQTT broker, connect to Home Assistant or publish any state.

## Device mapping
- Add optional sessionEpoch to schema 1; older consumers can ignore it.
  The snapshot store creates a random GUID once per API activation.
  It is not derived from hardware, account, name, address or credential.
- A consumer must explicitly confirm a source and sessionSlot against the
  current epoch. No different row may be substituted for an unavailable row.
- Stopping and restarting the API invalidates all prior bindings. A stable HA entity ID must be
  a separately user-selected identity, never inferred from a session slot.
- Missing or duplicate rows, unsupported schema, stale snapshots, future
  timestamps, expired readings and cached values are unavailable.
- The projection returns availability, fresh percent and machine-readable
  status only; no commands or requests to hardware.

Seventeen regression assertions; compilation and CI pending.

## Transport choices and gates
Prefer a separate opt-in local bridge that reads the existing authenticated
loopback endpoint and publishes only explicitly mapped sensors to an
existing authenticated MQTT broker using TLS with certificate verification.
Do not persist the tray bearer token without a separate credential policy.
No automatically opened firewall port, LAN binding, anonymous MQTT, or
unverified certificate bypass. No deployment or broker credentials assumed.
The bridge must publish unavailable on disconnection and use an appropriate
broker availability/expiry policy; old retained readings must not be presented
as current. Actual HA integration and secure transport are not implemented.

## Distribution isolation

Bridge mapping source lives in integrations/home-assistant, outside the
tray project; it is linked only into the test project at this stage.
The normal tray executable contains no bridge code, MQTT dependency,
network worker or background service. The additive epoch is generated
only when the existing optional API store is instantiated; one-off
clipboard snapshots lack a bindable epoch. API remains disabled by
default. This is a protocol foundation, not an installable HA integration.
