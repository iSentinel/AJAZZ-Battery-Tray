# Local battery API — snapshot foundation

The initial scope is read-only Windows battery monitoring and an eventual
Home Assistant integration. The optional HTTP listener is session-only and never starts automatically.

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
generation timestamps. Initial snapshot Windows 45082634886 / macOS 45082634877 PASS.
Combined HTTP regression and physical UI acceptance pending.

## Experimental loopback endpoint

- Diagnostics > Local battery API... > Start local API. Keep the window
  open (minimizing is allowed); Stop or closing the window stops the
  listener. App exit also closes it. No automatic startup or saved token.
- IPv4 127.0.0.1:18789 only, exact Host header, GET /v1/batteries, no
  query string, request body, device controls, external requests or CORS.
- Copy API token explicitly; the 32 random bytes are represented in hex.
  Token is regenerated on each start; don't paste it into public reports.
- Use Authorization: Bearer <token>. HTTP 401 without a valid token,
  503 if no snapshot, 200 with JSON only for authorized valid requests.
- Single-request connections and sequential processing; backlog 8,
  8 KiB headers, three-second total processing deadline per connection.
  A stalled local client may delay other clients. No TLS: loopback only.
- Example (PowerShell, replace placeholder locally):

```powershell
$headers = @{ Authorization = 'Bearer <token>' }
Invoke-RestMethod -Uri 'http://127.0.0.1:18789/v1/batteries' -Headers $headers
```

The 12 request-policy and 7 actual loopback assertions cover authorization,
route/method, unsafe Host, browser Origin, malformed headers, unavailable
snapshot, port conflicts and listener shutdown. Combined CI pending.

## Next
Complete CI and owner Windows acceptance. Test token rotation, stalled
client cancellation and actual interactions while HID monitoring runs.
LAN binding, TLS/proxy configuration, stable entity identities and Home
Assistant connectivity require separate explicit choices and acceptance.
Never expose device-control endpoints.
