# AJAZZ Battery Tray for macOS (experimental)

A native AppKit **menu bar** application for macOS 13 or later, built from
`macos/main.swift` using Apple's IOKit HID framework. The build is universal:
Intel (x86_64) and Apple Silicon (arm64).

## Compatibility and limitations

- Read-only Device diagnostics in the menu shows the HID product string
  and matching collection count, never a serial number.
- Tries the vendor-defined HID status interface on USB receiver
  `VID_3151:PID_5007`, usage page `0xFFFF`, usage `0x02`.
- The receiver/protocol is documented for AJ159 APEX and has been confirmed
  under **Windows** on AJ179 APEX. The **macOS HID report behaviour has not yet
  been tested on physical hardware**. A successful macOS CI build verifies
  compilation only, not device compatibility.
- This version handles **one receiver at a time**. When AJ159 APEX and AJ179
  APEX are both connected simultaneously, which model is shown is undefined.
- A HID `SetFeature` request transmits the same poll as the Windows version:
  ID 0, zero-filled payload with `0xF7` in the second byte. No other device
  commands are sent. A `GetFeature` report ID `0x05` returns the battery
  value, if the device and macOS expose the same protocol. The parser handles
  reports with or without an included report-ID byte.
- For AJ159 APEX, only the **8K dock** with `3151:5007` is targeted;
  alternative `3151:4026` and `3151:4027` receivers are not supported.
- A runtime allowlist permits only the documented telemetry/RTC frames.
  Screen/GIF, mouse button mapping and firmware packets are rejected.
- Dock Clock Sync uses the documented 0x28 feature report, manually or every
  five minutes. It follows the HID framing used by the macOS open-source
  Ajazz clock-sync daemon and is still unverified on our real hardware.
- Only 2.4 GHz USB is implemented. Bluetooth and charging detection are not implemented.
  macOS 13+ supports optional Start at Login from the menu.
- Optional **Low battery notifications** (20%, 10%, 5%) and **Notify on
  receiver disconnect** are available in the menu bar. Both are off by
  default. Enabling either requests macOS notification permission. A sleeping
  mouse with its receiver still present does not trigger a disconnect alert.
  Check System Settings → Notifications if alerts are not displayed.
- The app is **ad-hoc signed, not Apple-notarized**. macOS Gatekeeper can show a
  warning. Do not disable Gatekeeper globally; use the standard System
  Settings → Privacy & Security → Open Anyway flow after inspecting the source.

## Download and install

Get the macOS Universal ZIP from
[GitHub Releases](https://github.com/iSentinel/AJAZZ-Battery-Tray/releases).
Extract once and move `AJAZZ Battery Tray.app` to `/Applications`.
The app runs in the menu bar, not the Dock.

## Start at Login

Select **Start at login** from the menu bar to register this app using the
macOS Service Management API. The application must reside in `/Applications`
for reliable login registration. Registration is optional and uses no
administrator privileges. If macOS reports **approval needed**, open
**Open Login Items settings...** and approve the app under
System Settings → General → Login Items.

The menu reads the current system registration state rather than assuming
success. Ad-hoc-signed builds are not notarized, and the login item flow still
requires a real Mac validation.

## Battery history

The menu-bar app writes only battery percent and connection states to
`~/Library/Application Support/AJAZZBatteryTray/battery-history.csv`
while **Record battery history** is enabled. It captures changes and a
five-minute observation if the state remains unchanged, keeps at most 30 days,
and never includes USB serial numbers. **Open battery history folder...**
opens Finder to the directory containing the CSV. Choose **Battery history
chart...** for a native graph with 24-hour, 7-day and 30-day views.
Unavailable and disconnected readings are gaps rather than 0%.

## Sharing a diagnostic report

Choose **Copy diagnostic report** from the menu bar to copy the app version,
macOS version and receiver metadata. The app does not query device serials
or private USB paths. Inspect the clipboard before posting an issue.

Follow [hardware acceptance tests](../docs/HARDWARE_ACCEPTANCE.md) to verify
receiver detection, dock clock and login-item behavior on your Mac.

## Troubleshooting

Run the executable from a terminal to check HID discovery:

```bash
"/Applications/AJAZZ Battery Tray.app/Contents/MacOS/AJAZZBatteryTray" --diagnose
```

Expected: `PASS: battery XX%` if the compatible receiver can be queried.
`UNKNOWN` means no valid report was read; it does not indicate 0% charge.

If the Mac sees the receiver but cannot read status, please submit a GitHub
issue containing your macOS version, model, connection method, and the exact
`--diagnose` output. Never post serial numbers or private device identifiers.
