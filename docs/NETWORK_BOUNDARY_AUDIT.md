# Network boundary audit (ENG-15) — 2026-11-25

Scope: source review of actual Windows/HA HTTP paths and the offline
MQTT preflight, based on the ENG-05 candidate tree a57db6c. This does
not exercise a live network, TLS handshake, real broker or hardware.

| Path | Observed source contract | Status |
| --- | --- | --- |
| UpdateClient | Fixed HTTPS GitHub API; default platform certificate validation; redirects/cookies disabled; no authentication/device data; 15 s and 2 MiB bounds; links constructed locally | Source reviewed; duplicate metadata fix in candidate |
| HostMetricsReader | User-initiated fixed http://127.0.0.1:8085/data.json read; proxy/redirects/cookies disabled; 3 s and 2 MiB bounds; no credentials sent | Intentional loopback-only exception; provider data untrusted; live acceptance pending |
| LocalApiServer / LocalApiRequest | IPv4 loopback, session token, exact Host, GET-only, no Origin/body, no-store, bounded header/deadline | Source reviewed; existing integration tests; actual live product acceptance pending |
| HaLocalClient / AjazzHaPreview | Explicit interactive local API token; fixed 127.0.0.1, no proxy/redirect/cookies, 5 s/64 KiB; masked input | Source reviewed; no credential persisted by preview |
| HaMqttBrokerPreflight | Offline validation only: opt-in, TLS, certificate verification, MQTT5, scoped topic and credential-present flag required | No network connector or broker credentials implemented; real MQTT transport NOT_RUN |

Earlier audit suspected plaintext MQTT risk. There is no actual MQTT
client/dependency in the preview, and the preflight rejects plaintext.
Do not treat a successful preflight as authenticated TLS. Future
connector must implement and qualify certificate validation and
acknowledgment/recovery before deployment. External GitHub HTTPS
currently follows the platform trust store and proxy policy; no
certificate bypass is present in reviewed code. Do not change proxies
or trust configuration without separate scope.

## Metadata ambiguity

JsonElement.TryGetProperty can select the final value of duplicate
properties. Reject duplicate names in each top-level release object
(including escaped-equivalent names) and duplicate supported tag names
before selecting a release. Unique additive fields remain compatible;
remote URL fields still ignored. Synthetic tests cover conflicting
draft/tag/prerelease fields, additive duplicate fields, escaped names,
repeated tags and ordinary additive metadata. No actual HTTP request,
software download, execution, automatic update or broker connection
introduced. Native CI required. Wider input schema, source audit and
live TLS/transport acceptance remain open.
