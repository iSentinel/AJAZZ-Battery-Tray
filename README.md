# AJAZZ Battery Tray

A small, independent battery tray utility for **AJAZZ AJ179 APEX** and
**AJ159 APEX** mice connected through compatible **2.4 GHz / 8K docks** (`USB VID_3151 / PID_5007`).

**Version:** v0.3.0-beta.3 (AJ179 APEX confirmed on Windows; AJ159 APEX and macOS experimental).

## Platforms and hardware status

| Platform | AJ179 APEX | AJ159 APEX |
|---|---|---|
| Windows 10/11 x64 | Battery read confirmed on user's dock | Experimental; shared HID protocol not yet hardware-tested here |
| macOS 13+ (Intel/Apple Silicon) | Experimental; native AppKit + IOKit HID | Experimental; native AppKit + IOKit HID |

**Mac:** see [macOS build and limitations](macos/README.md). AJ159 APEX has
multiple USB identities; only the 8K dock `3151:5007` is targeted here,
not alternate `3151:4026` or `3151:4027` receivers. This is not a
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
- **HID command guard:** only documented battery poll and dock RTC packets are
  permitted to reach the device; all other vendor SET_FEATURE opcodes are
  rejected before transmission.
- **Dock Clock Sync:** set the 8K dock's screen clock to the computer's local time.
  Automatically on connection and every five minutes, or manually from the tray.
- **Windows Battery History:** local 30-day CSV history with a 24-hour,
  7-day or 30-day chart showing charge and connection interruptions.
- **Device Diagnostics:** receiver product name on Windows and macOS, USB
  VID/PID and vendor HID usage; Windows also shows the USB device revision and
  feature report size, without querying or exposing private serial numbers.
- Optional Windows notification when the receiver disconnects for two polls;
  disabled by default to prevent noise.
- Configuration and diagnostic log under `%APPDATA%\AJAZZBatteryTray`.
- No vendor software, external HID driver or background service required.
- No DPI, pairing, firmware, RGB or stored-profile modifications.

## Requirements

- Windows 10/11 x64; no separate .NET installation needed for released builds.
- AJAZZ AJ179 APEX in 2.4 GHz mode, with the USB/8K receiver attached.

## Download and install

Get the latest builds from [GitHub Releases](https://github.com/iSentinel/AJAZZ-Battery-Tray/releases).
Use the **Releases** section rather than GitHub Actions artifacts.

**Windows 10/11 x64**

- **Installer (recommended):** `AJAZZBatteryTray-Setup-win-x64.exe`.
  Run it, approve the Windows administrator prompt, and the application is
  installed in `C:\Program Files\AJAZZ Battery Tray\` with a Start menu
  shortcut and an entry in Windows Settings → Installed apps.
  An optional desktop shortcut is available in the wizard.
- **Portable:** `AJAZZBatteryTray-win-x64.exe`.
  Run it from any folder without installation or administrator rights.
- Choose **Start with Windows** in the tray menu after installing if you want
  autostart. If you previously enabled autostart from the portable version,
  disable and re-enable it from the installed application so Windows uses the
  new path.

**macOS 13+ (Intel / Apple Silicon, experimental)**

Download `AJAZZBatteryTray-macOS-universal.zip`, extract it once, and move
`AJAZZ Battery Tray.app` to Applications. See
[macOS installation and limitations](macos/README.md). macOS is not yet tested
with physical AJAZZ hardware.

Windows installer installation and removal require administrator permissions.
The application itself runs as the current user without elevation. Uninstall
from Windows Settings → Installed apps; personal settings and diagnostic logs
are intentionally preserved in `%APPDATA%\AJAZZBatteryTray`.

Releases are unsigned; Windows SmartScreen and macOS Gatekeeper may warn. Review
the project source and checksums before deciding to run the software.

## Tray menu

Right-click the notification icon to refresh, configure the polling interval,
toggle low-battery alerts, synchronize the dock clock or disable automatic clock
synchronization, enable or disable autostart, open the diagnostic folder or exit. Double-click to refresh immediately.

## HID protocol and safety

The reader enumerates the currently connected HID device interfaces and
specifically requires all of the following:

- Interface path contains `vid_3151&pid_5007&mi_02`.
- HID usage page is `0xFFFF`; HID usage is `0x02`.
- A zero-payload **status poll** sent as a feature report: `00 F7 00 ...`.
- Around 30 ms later a feature report `0x05` is fetched; Windows returns
  `05 00 00 PP ...`, where `PP` is the reported battery percentage.

Invalid responses, 0%, and percentages above 100% are shown as unknown.
The battery reader sends the documented telemetry poll. Clock sync (enabled by
default, with a tray toggle) sends **only** documented firmware RTC opcode
`0x28`, with marker `0xD7`, a big-endian year and local date/time, on the
same restricted vendor HID collection. It does not change DPI, firmware,
pairing, display images, or stored device profiles. HID transfer success does
not confirm that the dock screen accepted the new time.

**Important:** A matching VID/PID does not identify the physical mouse model. The Windows
tray therefore shows generic **AJAZZ APEX** rather than claiming a specific
model, and AJ159 APEX is marked experimental until tested. The HID exchange
is documented for another AJAZZ APEX model and implemented
for `3151:5007` in Halo Battery. The AJ179 APEX has been observed by the user to return its battery percentage
**in both Halo Battery and AJAZZ Battery Tray** through the original dock.
Extended tests (sleep/wake, charging, disconnect/reconnect and Bluetooth)
are not yet complete.

Do not run Halo Battery, the official configuration app, and AJAZZ Battery
Tray at the same time during initial testing: concurrent reads may compete.

## Roadmap

See [ROADMAP.md](docs/ROADMAP.md) for the safety gates, validation plan and
next staged work. Battery monitoring and clock sync are implemented;
RGB, display uploads and mouse configuration are **not** exposed until
verified read-back and a reliable recovery path exist.

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
- Prebuilt Windows portable and installer EXEs and the macOS ZIP are published
  under GitHub Releases; local compilation is not necessary for users.

## Dock clock sync

Right-click the tray icon and choose **Sync dock time now**, or toggle
**Auto-sync dock clock (5 min)**. Automatic syncing runs when the receiver
becomes available and every five minutes, including after the next poll when
Windows wakes from sleep. It uses the computer's **local time**, not UTC.
The application reports whether the HID transfer was accepted by Windows;
visually confirm the clock on your dock. Because clock sync is a write,
close the official AJAZZ application before testing to avoid conflicting
commands. The feature is based on documented 8K receiver behaviour but
has not yet been tested on this application's AJ179 APEX hardware.

## Battery history (Windows)

Right-click the tray icon and choose **Battery history...**. The chart shows
observed charge values; gaps indicate missing data, not zero battery.
The history is written locally to
`%APPDATA%\AJAZZBatteryTray\battery-history.csv`, at most once every
five minutes unless the charge or connection state changes. Data older than 30
days is automatically pruned and storage is capped at 20,000 observations.
Use the **Record battery history** menu option to disable collection.

The chart intentionally **does not predict remaining runtime**: voltage-based
battery percentages, charging state and awake/idle time are not sufficiently
validated to make that prediction trustworthy.

## Safe HID operations

A strict command policy blocks unknown or malformed feature-report writes.
On Windows it explicitly permits the zero-payload battery poll `0xF7`
and the correctly encoded clock packet `0x28`, and rejects
button-map, display/GIF and bootloader commands. A matching guard is included
in the macOS app. There is no UI to bypass this safety check.

## Safe device diagnostics

The Windows tray menu's **Device diagnostics...** reports HID usage,
feature-report length, product name, USB revision and matching interfaces.
The macOS menu contains a read-only **Device diagnostics...** dialog too. USB revision is **not firmware version**. Firmware
version, DPI and polling rate are explicitly shown as not yet queried:
the corresponding read protocol has not been verified on AJ179 hardware.
It does not enumerate private USB identifiers or send configuration commands.

## Diagnostics

- Settings: `%APPDATA%\AJAZZBatteryTray\settings.json`
- Battery history: `%APPDATA%\AJAZZBatteryTray\battery-history.csv`
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
