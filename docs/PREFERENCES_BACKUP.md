# Portable preferences backup

Windows Settings > Preferences backup... exports a versioned JSON file
containing only global polling interval, language, notification preferences,
battery-history recording preference and separate tray icon mode.
The file is local, not uploaded, and must be saved under a new name.

## Deliberate exclusions
- Device keys, aliases, per-device overrides, battery readings or history.
- Automatic update consent/channel, BLE sessions, AULA opt-in, dock RTC policy.
- Startup registration, Windows properties, DPI, RGB, firmware, button mapping.

The parser accepts schema 1 only, requires every allowlisted field exactly
once, rejects unknown keys and invalid types/values, and caps input at 8 KiB.
Preview uses localized labels and never modifies the active settings until
an explicit Restore action and a separate default-No confirmation.

Twenty-two regression assertions cover the round trip, privacy exclusions,
malformed and incompatible data, file size, no overwrite, read-only preview,
transactional restore and preservation of excluded settings. Initial export
CI passed; final restore CI and actual Windows UI checks are outstanding.

## Next
Restore only the already validated preview, persist synchronously using the
existing settings save path, roll back in-memory values on failure, and
refresh the localized tray/dashboard after successful save. No forced HID
poll or configuration command. Existing automatic-update consent is not
imported, but restoring enabled notifications may resume an already
consented automatic schedule (explicitly disclosed in confirmation).
Validate real dialog behavior, save errors, menu refresh, and changed poll
intervals on Windows.
Never import network consent or hardware-control settings. Do not claim
that this is a backup of the mouse, keyboard, dock or their firmware.
