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

Initial seventeen mapping assertions: Windows 45092378014 / macOS 45092378033 PASS.

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

## Optional consumer wire format and transport foundation

The optional decoder accepts schema 1 with a valid sessionEpoch, rejects
duplicate JSON properties and source/slot identities, validates UTC timestamps,
integer percentages, supported statuses and their fresh/cached field invariants.
Input is limited to 64 KiB and JSON depth 8. Unknown additive fields may be
ignored; invalid known fields fail closed. Twelve additional wire tests
exercise producer serialization and malformed inputs.

The optional one-shot client only reads HTTP GET /v1/batteries on 127.0.0.1
with a supplied port and session bearer token. No proxy, redirects, cookies,
credential persistence, retry loop or automatic service. A five-second
deadline includes response reading, and the same 64 KiB limit applies.
503 returns no snapshot; other failures must be treated as unavailable by
a future bridge. Six synthetic loopback integration assertions use the
actual local server, including cancellation and restart mapping invalidation.
Combined latest CI remains pending. This is not a deployed or installable
Home Assistant bridge; MQTT, explicit mapping UI and availability policy
still need independent implementation.

## AULA receiver continuity gate
In beta.52 the AULA slot was fixed at 1, which could silently bind a
replacement receiver within the same active API. The next candidate reserves
slot 1 for non-bindable status only, assigns a new ordinal on observed
receiver changes or loss of identity, and never reuses a retired AULA slot.
The same known receiver during no-reply sleep retains its slot. Exhaustion
fails closed; restart the optional API and explicitly map again. Consumers
must not bind AULA slot 1, including beta.52 AULA rows. Ordinals are not
physical keyboard identities: the same receiver path or paired device
replacement without an observed identity change cannot be distinguished.
No persistent mapping or MQTT publication is approved on that basis.
Ten added assertions pending C# CI; no HID requests or default overhead added.

## Offline MQTT 5 availability intent (candidate)

A pure optional component plans exactly two retained QoS1 messages for each
explicitly mapped reading; it opens no connection and requires no broker.
Fresh reads plan battery value (5-minute MQTT 5 message expiry) followed by
availability=online (also expiring). Missing, cached, expired, wrong-epoch,
future or disconnected reads plan availability=offline first, then a retained
empty battery message to clear stale state. Broker implementations MUST check
publish acknowledgments and must not claim availability until both online
messages complete. On reconnect they must first re-read authenticated Local
API and validate the session mapping; never replay cached online plans.
No stable entity ID or topic prefix is inferred from source/slot. MQTT 5
expiry support, HA discovery expire_after, transport authentication, TLS,
credential storage, topic permission scope and actual broker behavior remain
unimplemented/unverified. Tests use synthetic snapshots only.
