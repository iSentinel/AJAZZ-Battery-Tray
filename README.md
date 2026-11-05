# AJAZZ Battery Tray

A small, independent battery tray utility for **AJAZZ AJ179 APEX** and
**AJ159 APEX** mice connected through compatible **2.4 GHz / 8K docks** (`USB VID_3151 / PID_5007`).

**Version:** v0.2.0-beta.1 development (AJ179 APEX confirmed on Windows; AJ159 APEX and macOS experimental).

## Platforms and hardware status

| Platform | AJ179 APEX | AJ159 APEX |
|---|---|---|
| Windows 10/11 x64 | Battery read confirmed on user's dock | Experimental; shared HID protocol not yet hardware-tested here |
| macOS 13+ (Intel/Apple Silicon) | Experimental; native AppKit + IOKit HID | Experimental; native AppKit + IOKit HID |

**Mac:** see [macOS build and limitations](macos/README.md). This is not a
WinForms port: macOS uses its own Swift menu-bar application. Bluetooth
is not implemented on either platform yet. Only one matching receiver is
reported at a time; if two receivers are attached, the device shown can
be ambiguous.

## Features

- Live battery percentage rendered in the notification area (system tray).
- Receiver presence and unavailable/asleep status (`?` icon, no fabricated 0%).
- Windows low-battery notifications at 20%, 10% and 5%, without repeated alerts.
- Poll every 15, 30 (default), 60 or 120 seconds; double-click to refresh.
- Optional autostart for the current Windows user (no administrator rights).
- Configuration and diagnostic log under `%APPDATA%\AJAZZBatteryTray`.
- No vendor software, external HID driver or background service required.
- No DPI, pairing, firmware, RGB or stored-profile modifications.

## Requirements

- Windows 10/11 x64; .NET 8 SDK **only needed to build**, not to run
  a published self-contained executable.
- AJAZZ AJ179 APEX in 2.4 GHz mode, with the USB/8K receiver attached.

## Build and run

Open PowerShell in the extracted project folder:

```powershell
# Confirm commands and requirements first:
.\build.ps1 -Help

# Run dependency-free tests, then create a portable x64 EXE and ZIP:
.\build.ps1

# Run the application (its icon appears in the Windows notification area):
.\dist\app\AJAZZBatteryTray.exe
```

Or use GitHub Actions > **Build Windows portable app** > Run workflow, then
download the `AJAZZBatteryTray-win-x64` artifact. The workflow builds on a
Windows runner. Download the artifact ZIP and extract it once: the self-contained
`AJAZZBatteryTray.exe` is directly inside, without an additional ZIP.
For local builds, `build.ps1` also produces `dist/AJAZZBatteryTray-win-x64.zip`.

A first launch may display Windows SmartScreen because the app is not signed.
Review the source before allowing it to run.

## Tray menu

Right-click the notification icon to refresh, configure the polling interval,
toggle low-battery alerts, enable or disable autostart, open the diagnostic
folder or exit the app. Double-click to refresh immediately.

## HID protocol and safety

The reader enumerates the currently connected HID device interfaces and
specifically requires all of the following:

- Interface path contains `vid_3151&pid_5007&mi_02`.
- HID usage page is `0xFFFF`; HID usage is `0x02`.
- A zero-payload **status poll** sent as a feature report: `00 F7 00 ...`.
- Around 30 ms later a feature report `0x05` is fetched; Windows returns
  `05 00 00 PP ...`, where `PP` is the reported battery percentage.

Invalid responses, 0%, and percentages above 100% are shown as unknown.
The utility makes **only this documented telemetry poll**. The read protocol
uses a HID SET_FEATURE operation, but it does not issue device-setting,
EEPROM-write, update, or pairing opcodes.

**Important:** A matching VID/PID does not identify the physical mouse model. The Windows
tray therefore shows generic **AJAZZ APEX** rather than claiming a specific
model, and AJ159 APEX is marked experimental until tested. A matching VID/PID
The HID exchange is documented for another AJAZZ APEX model and implemented
for `3151:5007` in Halo Battery. The AJ179 APEX has been observed by the user to return its battery percentage
**in both Halo Battery and AJAZZ Battery Tray** through the original dock.
Extended tests (sleep/wake, charging, disconnect/reconnect and Bluetooth)
are not yet complete.

Do not run Halo Battery, the official configuration app, and AJAZZ Battery
Tray at the same time during initial testing: concurrent reads may compete.

## Limitations / roadmap

- **Bluetooth is not yet implemented on either platform.** It requires testing the Windows BLE
  device's Battery Service or Windows battery property in Bluetooth mode.
  The 2.4 GHz dock is the supported primary transport.
- Charging state is not shown: the documented `0x05` status frame does not
  provide a verified charging bit.
- The notification icon uses a live percent; the tray tooltip and menu provide
  the full status. Windows may suppress balloon notifications in Focus Assist.
- If the receiver remains present while the mouse sleeps, the icon changes to
  `?` rather than showing a stale percentage.
- Prebuilt EXE is produced by the Windows build script or GitHub Actions;
  this source package does not include a precompiled Windows executable.

## Diagnostics

- Settings: `%APPDATA%\AJAZZBatteryTray\settings.json`
- Log: `%APPDATA%\AJAZZBatteryTray\app.log`
- Windows identifiers: `Get-PnpDevice -PresentOnly | Where-Object InstanceId -match 'VID_3151&PID_5007'`

The app does not send telemetry to the Internet or request administrator
privileges. Autostart writes only the current user's `Run` registry entry.

## Attribution

The report format and status-poll sequence were learned from public protocol
notes in [AJAZZ Control Center](https://github.com/Aiacos/ajazz-control-center)
(GPL-3.0) and [Halo Battery](https://github.com/HeyOkay/HaloBattery)
(MIT, protocol documented in `docs/protocols.md` and
`providers/am_infinity.py`). This repository is an independent C# implementation
of the published protocol rather than a distribution of either upstream code.
