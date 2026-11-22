# Resume — automatic update notification candidate

- beta.43 release workflow 45078947181 PASS; six assets verified.
- beta.44 PR #58 merged 8c2b2ed9c0ee227dc1fab14b487c07f788afcd52;
  final Windows 45079329678 and macOS 45079329674 PASS.
  Release workflow 45079507680 in progress; Latest still beta.43 at check.
- PR #59 synced to beta.44 main. One RESUME-only conflict resolved.
  Automatic update consent/channel, independent timer, global notification
  gating, manual exclusion, cancellation and deduplication implemented.
- Review hardened opt-out on save failure (stops current session and
  warns), notification off/on invalidates old request. Twenty pure tests
  now cover scheduling and settings compatibility. Final CI pending.
- Next: verify beta.44 release, latest PR #59 CI, prepare beta.45 metadata,
  verify final CI and publish; real Windows UI/network acceptance pending.
- Remaining hardware gates: working/affected AJ159 beta.41+ full reports
  and GearHub HAR, multiple BLE and prolonged AULA L99 sleep.
  Live HID parser, readers and allowlists are unchanged.
