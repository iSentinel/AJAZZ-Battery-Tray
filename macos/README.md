# AJAZZ Battery Tray for macOS (experimental)

A native AppKit **menu bar** application for macOS 13 or later, built from
`macos/main.swift` using Apple's IOKit HID framework. The build is universal:
Intel (x86_64) and Apple Silicon (arm64).

## Compatibility and limitations

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
- Only 2.4 GHz USB is implemented. No Bluetooth, battery charging detection,
  macOS notifications, or automatic start at login yet.
- The app is **ad-hoc signed, not Apple-notarized**. macOS Gatekeeper can show a
  warning. Do not disable Gatekeeper globally; use the standard System
  Settings → Privacy & Security → Open Anyway flow after inspecting the source.

## Build

On a Mac with Xcode command line tools:

```bash
bash macos/build-macos.sh --help
bash macos/build-macos.sh
```

The resulting ZIP is `dist/AJAZZBatteryTray-macOS-universal.zip`. Extract
once and move `AJAZZ Battery Tray.app` to `/Applications`, then open it.
The app runs in the menu bar, not the Dock.

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
