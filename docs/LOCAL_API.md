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

Twenty-five pure assertions exercise freshness, privacy, shape, bounds,
immutable publication and read-time expiration. The existing monitoring
refresh path publishes a sanitized snapshot independently of the dashboard.
Receiver ordinals are assigned once per process; BLE uses its existing
session number. Overflow or projection errors clear the snapshot rather
than returning partial data. The AULA row excludes manual-only readings
when monitoring is disabled. Diagnostics > Copy local battery snapshot
explicitly copies the current projection without polling hardware.
The store re-ages values at read time without changing measurement or
generation timestamps. CI and hardware/UI acceptance pending.

## Next
The immutable snapshot uses existing monitoring only; API reads must never
trigger a HID request. Next, consider a disabled-by-default,
explicitly enabled loopback-only listener with a random per-user bearer
credential, route/method/size/time limits and safe shutdown. Test unauthorized
requests, malformed requests, concurrent reads, port conflicts and revocation.
LAN binding, TLS/proxy configuration, stable entity identities and Home
Assistant connectivity require separate explicit choices and acceptance.
Do not expose device-control endpoints.
