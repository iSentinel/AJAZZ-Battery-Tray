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
Preview uses localized labels and never modifies the active settings.

Fifteen regression assertions cover the round trip, privacy exclusions,
malformed and incompatible data, file size, no overwrite and read-only
preview. CI and physical UI checks are outstanding.

## Next
Add explicit confirmation and a validated global-preferences application
path with rollback on failed persistence and correct live UI propagation.
Never import network consent or hardware-control settings. Do not claim
that this is a backup of the mouse, keyboard, dock or their firmware.
