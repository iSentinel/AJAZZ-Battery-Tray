# Changelog

## 0.3.0-beta.13 (2026-11-06)
- Isolate Windows paired BLE and Classic enumeration failures.
- Limit each transport's lookup time to eight seconds, retaining partial results.
- Show per-transport paired-device counts and sanitized error names.
- Add Copy lookup summary without device IDs, addresses or serial numbers.
- Test manual Show all paired-device name filtering and update diagnostics docs.
- Do not add auto-pairing, Bluetooth background polling or device writes.


## 0.3.0-beta.12 (2026-11-06)
- Fix Windows Bluetooth device list hiding paired AJAZZ mice.
- Enumerate paired-only LE and Classic devices; allow all paired device names.
- Remove unreliable second pairing-state filter on Windows endpoints.
- Read Windows's cached numeric device battery property if GATT is absent.
- Label cached values and reject unknown sentinel 101 or invalid percentages.
- Keep Bluetooth data manual and separate from USB receiver monitoring.
- Add cached-battery parser tests; no pairing, GATT writes or HID settings.


## Unreleased — dock protocol evidence guide
- Document Windows USBPcap/Wireshark capture of one reversible vendor setting.
- Require before/after/readback/restore and redaction before publishing.
- Keep all unverified RGB, GIF, DPI and profile writes blocked.


## 0.3.0-beta.11 (2026-11-06)
- Add 12-second timeout to the Windows paired BLE lookup and a 15-second
  timeout to the manually triggered Battery Service read.
- Report timeouts without inventing a percentage or changing 2.4 GHz status.
- Resume battery-history observations if Windows system time moves backward.
- Add deterministic tests for timeout completion, expiration and clock jumps.
- No new HID or GATT commands and no automatic Bluetooth polling.


## 0.3.0-beta.10 (2026-11-06)
- Add an experimental macOS manual read of the standard GATT Battery Level.
- Enumerate only CoreBluetooth already-connected peripherals with Battery
  Service, filter plausible AJAZZ names and require user selection.
- Never scan, pair, write GATT characteristics, or poll in background.
- Add a 10-second read timeout and explicit unavailable results.
- Add parser self-tests and Bluetooth permission description.
- Real AJ179/AJ159 BLE compatibility still requires a Mac hardware test.


## 0.3.0-beta.9 (2026-11-06)
- Add an explicit Windows manual Bluetooth Battery Service (GATT 180F) probe.
- Enumerate only already paired BLE candidates and require user selection.
- Read Battery Level (2A19) without GATT writes, pairing or background scanning.
- Validate standard one-byte 0..100 responses; unavailable remains unknown.
- Keep BLE results separate from 2.4 GHz tray status and history.
- Move Windows targeting to Windows SDK 19041 for .NET 8 WinRT interop.
- Hardware Bluetooth percentage support remains experimental until tested.


## Unreleased (Bluetooth research)
- Confirmed Bluetooth connectivity of AJ179 APEX and AJ159 APEX from product specs.
- Documented standard read-only Battery Service discovery and privacy gates.
- Runtime BLE support remains disabled until paired-device hardware validation.

## Unreleased (CI improvements)
- Avoid duplicate Windows and macOS builds for every feature-branch push.
- Keep mandatory pull-request checks and main-branch builds.
- Cancel superseded pull-request CI runs when new commits arrive.
- Serialize beta release publishing and reject overwriting existing assets.


## 0.3.0-beta.8 (2026-11-06)
- Add Copy diagnostic report to Windows tray and macOS menu bar.
- Include app and OS version with read-only receiver metadata.
- Do not query USB serial numbers or private device paths.
- Add hardware acceptance checklist for AJ179/AJ159 and both OSes.
- Keep vendor mouse and display configuration opcodes blocked.


## 0.3.0-beta.7 (2026-11-06)
- Add optional macOS Start at Login using SMAppService.mainApp.
- Read the system registration state and show when approval is needed.
- Add shortcut to macOS Login Items settings.
- No administrator privileges or custom launch agents required.
- Hardware/Mac startup behavior remains experimental until field validation.


## 0.3.0-beta.6 (2026-11-06)
- Add opt-in macOS local notifications for battery thresholds 20/10/5%.
- Add optional receiver-disconnect alert after two missing USB polls.
- Request notification permission only when the user enables a menu option.
- Prevent duplicate alerts and ignore sleeping mice when the receiver remains.
- Add hardware-independent alert-policy checks to macOS self-test.


## 0.3.0-beta.5 (2026-11-06)
- Add a native AppKit battery history graph for macOS.
- Select 24 hours, 7 days or 30 days and refresh on demand.
- Preserve gaps for missing battery readings instead of showing 0%.
- Test CSV parser with malformed rows and invalid percentages.
- Document ready-made GitHub release downloads for macOS users.


## 0.3.0-beta.4 (2026-11-06)
- Add private macOS battery history CSV under Application Support.
- Record charge changes and receiver status; sample unchanged state every 5 min.
- Auto-prune history after 30 days and cap rows at 20,000.
- Add macOS menu options to open history folder and disable recording.
- Add macOS self-tests for recording frequency and state changes.
- Windows features remain unchanged from v0.3.0-beta.3.


## 0.3.0-beta.3 (2026-11-06)
- Add an explicit allowlist for every Windows HID feature write.
- Permit only correctly framed 0xF7 telemetry and 0x28 dock clock packets.
- Reject malformed timestamps, unexpected payloads, display, mapping and
  bootloader commands before they reach the receiver.
- Add equivalent macOS guards and unit/self-tests for dangerous opcodes.
- No new mouse configuration write commands have been enabled.


## 0.3.0-beta.2 (2026-11-06)
- Stage 2 start: read-only AJAZZ 8K dock product identification.
- Windows: read HID product string and bcdDevice revision (not firmware).
- macOS: read HID product string in the menu-bar diagnostics dialog.
- No unverified RGB, image, GIF, DPI or profile commands were added.


## 0.3.0-beta.1 (2026-11-06)
- Add Windows battery history with a built-in 24h/7d/30d chart.
- Store state transitions in local CSV with a 30-day retention limit.
- Add receiver/interface diagnostics without unverified HID commands.
- Add opt-in notification for repeated receiver disappearance.
- Add history and disconnect policies with hardware-independent tests.
- Keep firmware, DPI, RGB, GIF and polling-rate configuration gated.


## 0.2.0-beta.3 (2026-11-06)
- Add manual and automatic 8K dock clock synchronization (Windows/macOS).
- Send documented clock opcode 0x28 and fixed 0xD7 marker with local time.
- Resynchronize on receiver connection and every five minutes.
- Add optional setting and status in tray/menu-bar menus.
- Add packet and scheduling tests; hardware clock verification pending.


## 0.2.0-beta.2 (2026-11-05)
- Add a separate Windows x64 installer using Inno Setup.
- Install to Program Files, add Start menu and optional desktop shortcuts.
- Register standard Windows uninstaller; preserve user settings by default.
- Publish both a portable executable and an installer in GitHub Releases.
- Add CI installation/uninstallation smoke test and SHA256 checksums.
- Simplify README to direct users to GitHub Releases.

## 0.2.0-beta.1 (development)
- Native macOS Intel/Apple Silicon menu-bar prototype via AppKit and IOKit.
- Mark AJ159 APEX compatibility as experimental; shared receiver protocol.
- Use generic AJAZZ APEX label in Windows to avoid incorrectly naming model.
- macOS HID read and AJ159 compatibility require real-device validation.


## 0.1.0 (2026-11-05)
- Initial Windows 10/11 .NET 8 notification-area application.
- 2.4 GHz/8K receiver: VID 3151 PID 5007 MI_02, usage FFFF:0002.
- Read-only battery telemetry, invalid frame rejection, low-charge alerts.
- Per-user JSON settings, autostart toggle, local log, CI release build.
- Bluetooth and charging detection deferred pending protocol validation.
