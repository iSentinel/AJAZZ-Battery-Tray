# Changelog

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
