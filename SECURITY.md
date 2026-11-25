# Security and trust boundaries

Report potential vulnerabilities privately to the repository owner; do not
post secrets or raw private diagnostics in public issues. No security contact
or vulnerability disclosure service is assumed configured.

AJAZZ 3151:5007 vendor FFFF:0002 only; shared revision is not model identity.
Approved zero-payload F7 query and narrowly validated 0x28 RTC frame only;
AULA uses existing independently scoped battery-only protocol. Preserve
HidFeaturePolicy and Apple equivalents. No speculative writes, automatic
power cycles, firmware/configuration writes, new hardware opcodes or
destructive tests without reviewed scope and separate approval. Explicit
full capture has deadline and user consent; raw buffers local, review
before sharing. Timeout/unknown is not proof of absence or successful write.

BLE opted-in paired devices only; API session-only exact IPv4 loopback,
Bearer token, read-only, no external bind/CORS, no TLS on loopback only.
External update/MQTT traffic must use verified TLS where applicable;
any existing plaintext MQTT preview limitation requires explicit review
before broader exposure. Do not log credentials, private device IDs,
aliases, paths or raw exceptions. Windows FileLog candidate uses closed structured events; see
[operational journal](docs/WINDOWS_OPERATIONAL_LOG.md). Existing legacy
app.log can contain private data and is left untouched; never upload it. Do not upload raw logs or histories.
No unverified or stale AJAZZ field as fresh telemetry, alerts or estimates.

Use minimal CI permissions, no release write token during routine tests.
Current release workflows intentionally fail closed pending explicit
candidate-bound admission. No production deployment, visibility changes,
external publication or existing asset replacement authorized by adoption.
