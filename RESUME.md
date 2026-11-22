# Resume — portable preferences backup candidate

- beta.44 release workflow 45079507680 PASS, six assets verified.
- beta.45 PR #59 final Windows 45081400123 / macOS 45081400087 PASS;
  merged e071032fe06a9fcfe222813209c0815ea1d90408;
  release workflow 45081549658 PASS, six assets verified.
- Global preference backup schema 1, strict fields and 8 KiB limit,
  local export and localized preview; initial Windows 45081604762 and
  macOS 45081604695 PASS. Explicit restore with rollback, UI refresh and
  preservation of excluded settings added; 22 total backup/restore checks.
- Does not transfer device keys, history, network consent/channel,
  dock RTC preferences, AULA or BLE opt-ins or hardware settings.
  Existing export files are not overwritten.
- Next: prepare beta.46 metadata and final CI; publish only after CI passes.
  Windows UI/restore acceptance remains pending. Continue local API design
  using a privacy-safe read-only snapshot and no network listener by default.
- Hardware gates: working and affected AJ159 reports/HAR, multi-BLE,
  prolonged AULA L99 sleep; no change to live HID parser.
