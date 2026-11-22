# Resume — portable preferences backup candidate

- beta.44 release workflow 45079507680 PASS, six assets verified.
- beta.45 PR #59 final Windows 45081400123 / macOS 45081400087 PASS;
  merged e071032fe06a9fcfe222813209c0815ea1d90408; publication pending.
- Global preference backup schema 1, strict fields and 8 KiB limit,
  local export and read-only localized preview. Fifteen tests added.
- Does not transfer device keys, history, network consent/channel,
  dock RTC preferences, AULA or BLE opt-ins or hardware settings.
  Existing export files are not overwritten.
- Next: verify beta.45 release assets, initial backup CI, implement
  explicit restore confirmation with transactional settings persistence
  and correct live-state/restart behavior. No restore yet.
- Hardware gates: working and affected AJ159 reports/HAR, multi-BLE,
  prolonged AULA L99 sleep; no change to live HID parser.
