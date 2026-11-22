# Home Assistant bridge — session mapping foundation

The tray API remains loopback-only. This branch does not open a LAN port,
install an MQTT broker, connect to Home Assistant or publish any state.

## Device mapping
- Add optional sessionEpoch to schema 1; older consumers can ignore it.
  The snapshot store creates a random GUID once per application lifetime.
  It is not derived from hardware, account, name, address or credential.
- A consumer must explicitly confirm a source and sessionSlot against the
  current epoch. No different row may be substituted for an unavailable row.
- A restart invalidates all prior bindings. A stable HA entity ID must be
  a separately user-selected identity, never inferred from a session slot.
- Missing or duplicate rows, unsupported schema, stale snapshots, future
  timestamps, expired readings and cached values are unavailable.
- The projection returns availability, fresh percent and machine-readable
  status only; no commands or requests to hardware.

Twelve regression assertions added; compilation and CI pending.

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
