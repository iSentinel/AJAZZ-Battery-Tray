# Local battery API — snapshot foundation

The initial scope is read-only Windows battery monitoring and an eventual
Home Assistant integration. No listener, HTTP endpoint, token, or network
request is implemented or enabled by this foundation.

## Snapshot schema 1
- UTC generation time; bounded list of up to 64 rows.
- Source enum: apex_receiver, aula_receiver, bluetooth.
- Session slot: ordinal only, not a persistent device/entity identity.
  Duplicate source/slot pairs are rejected. Do not treat this as a stable
  Home Assistant entity identifier across restarts or device changes.
- Machine-readable status and measurement time. BatteryPercent is emitted
  only for valid fresh measurements at most five minutes old; scheduled,
  cached or aging fresh data is separated into LastKnownPercent for at most
  24 hours. Missing/future timestamps and invalid values are unavailable.
  Manual-only and disconnected/unknown states never publish numeric values.
- No names, aliases, receiver fingerprints, BLE IDs, filesystem paths,
  history, credentials, or raw HID traffic.

Sixteen pure assertions exercise freshness, privacy, shape and bounds.
Projection is not connected to live tray state yet; CI pending.

## Next
Publish immutable snapshots from existing in-memory monitoring only; never
trigger a HID request from an API read. Then consider a disabled-by-default,
explicitly enabled loopback-only listener with a random per-user bearer
credential, route/method/size/time limits and safe shutdown. Test unauthorized
requests, malformed requests, concurrent reads, port conflicts and revocation.
LAN binding, TLS/proxy configuration, stable entity identities and Home
Assistant connectivity require separate explicit choices and acceptance.
Do not expose device-control endpoints.
