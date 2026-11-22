# AJAZZ Battery Tray

A small, independent battery tray utility for **AJAZZ AJ179 APEX** and
**AJ159 APEX** mice connected through compatible **2.4 GHz / 8K docks** (`USB VID_3151 / PID_5007`).

**Version:** v0.3.0-beta.48 (lightweight tray and history candidate).

See [resource optimization and measurement](docs/RESOURCE_OPTIMIZATION.md)
for the controlled Windows comparison procedure.

Use **Diagnostics > Local battery API...** for an explicitly started,
loopback-only authenticated battery snapshot. See [API documentation](docs/LOCAL_API.md).

Use **Settings > Preferences backup** to export, preview or explicitly restore
portable application preferences. No hardware configuration is exported.

Use **Settings > Update preferences** to enable daily GitHub release checks
and select the stable or experimental channel. Automatic checks default off.

Use **Verify downloaded release...** to compare a local Windows EXE with
its companion SHA-256 manifest from the same GitHub release.

Use **Check for updates...** in the Windows tray to select a release channel
and explicitly look up GitHub releases. See [update checker](docs/UPDATE_CHECKER.md).

Windows supports multiple explicitly selected paired LE monitors in one session.
See [limitations and acceptance](docs/MULTI_BLUETOOTH.md) and
[GearHub protocol research](docs/APEX_GEARHUB.md).

For APEX comparison use **Diagnostics → Full APEX comparison report...**.
One local report contains HID descriptor inventory, last ordinary state and
the complete existing query timing/length sweep, even after a valid reply.
Capture working AJ179, working AJ159 and affected AJ159 separately with
the official app closed. Review raw bytes before sharing. The official
utility's USB exchange is not captured by this function.

## Per-device battery analytics (Windows)

Open the individual battery history for a receiver or the AULA profile.
The window shows observed discharge rate, conditional estimated runtime,
observation count and span, and observed discharge equivalents over the
selected range. Insufficient recent observations are explicitly unavailable.
This is a local estimate, not measured physical capacity, health or cycles.
The aggregate legacy history is excluded. See [analytics limitations](docs/BATTERY_ANALYTICS.md).

## Individual polling intervals (Windows)

Select a receiver or the AULA profile in Device Manager or its tray submenu
and choose **Device polling interval...**. Inherit the global interval or
choose 15, 30, 60 or 120 seconds. AJAZZ discovery remains separate from
sampling; scheduled skips preserve the previous timestamp and do not repeat
history or alerts. AULA has its own completion-based timer; its presence is
last-known until the next read. Actual timing depends on HID latency and
Windows scheduling. See [polling integration](docs/PER_DEVICE_POLLING.md).

## Individual low-battery alerts (Windows)

Select an AJAZZ receiver or AULA L99 in Device Manager and choose
**Device battery alerts...**, or open the same editor from its tray submenu.
Inherit the global 50/25/10 thresholds or choose an independent set.
An empty custom set mutes low-battery alerts for that device only.
The global notification switch remains authoritative. Bluetooth fallback
and receiver-disconnect settings are unchanged. Preferences persist locally.

## APEX battery protocol capture (Windows)

Open **Diagnostics → Capture AJAZZ battery protocol...** after closing the
official utility and waking the mouse. Confirm local raw-buffer capture,
review the report, then save if needed. This explicitly invoked diagnostic
uses only the existing battery query and checks 30/100/250 ms delays.
Ordinary monitoring and normal privacy-safe diagnostics are unchanged.
The raw buffers may contain undocumented data; review before sharing.
See [APEX protocol diagnostics](docs/APEX_PROTOCOL_DIAGNOSTICS.md) for
official utility comparison and hardware acceptance.

## Individual tray colors (Windows)

Open **Tray icon color...** from the device submenu or select a device
in Device Manager and open its color editor. Choose from six normal-charge
colors; the editor previews normal, warning, critical and cached icons.
Colors persist locally independently for each AJAZZ receiver and the
single AULA monitoring profile. Default is green. Red at 10% or less,
amber at 20% or less, and gray for unavailable/cached values take priority.
Bluetooth fallback retains the default palette. This changes neither
measurements nor notification thresholds.

## Individual tray visibility (Windows)

Use the device submenu or select its row in Device Manager and choose
**Hide device in tray** / **Show device in tray**. The preference is local
and persists across restarts. Hidden devices continue sampling battery,
recording history and evaluating notification thresholds. The global
Separate tray icons setting still controls whether extra icons appear;
the dashboard indicates permission to display an icon, not whether Windows
has placed it in the notification-area overflow. When every active device
icon is hidden, retain a neutral application icon for access to menus.
AJAZZ preferences use the existing local receiver identity; AULA uses its
single monitoring profile. Bluetooth fallback remains unchanged.

## Local device names (Windows)

Select a known device in Device Manager and choose **Edit local name...**,
or use its tray submenu. Enter up to 40 characters; clear the field to
restore the detected name. The application keeps the model label alongside
the alias in the dashboard, tray and history window. Aliases persist locally
in settings; AJAZZ aliases use the same local hashed receiver identity as
history, so changing a name does not change or migrate history. AULA has
one alias for its monitoring profile, not a confirmed physical identity.
A different USB instance may obtain a different AJAZZ identity.
Bluetooth-only aliases and actual Windows property changes are not included.
No elevation or new HID commands are required.

## Windows Device Manager names preview

Open **Settings → Windows device names preview...** from the Windows tray.
The local read-only preview lists supported present USB receiver nodes
and candidate primary HID mouse/keyboard nodes by their actual parent
ancestry, with receiver group, VID/PID, USB revision, current and suggested
display names. Suggestions based on the owner's observed revisions are
provisional, not proof of model identity. Instance paths and serials are
not displayed or logged by this feature. The window does not rename devices,
install drivers, elevate privileges, or issue HID commands.

The next stage is explicitly confirmed, reversible, per-instance changes
to Windows' DEVPKEY_Device_FriendlyName after validating the target mapping
on physical hardware. See [the Windows naming plan](docs/WINDOWS_DEVICE_NAMES.md).

## Device Manager dashboard (Windows)

Open **Device Manager** from any tray icon to view all known AJAZZ
receivers, AULA L99, and the explicitly enabled Bluetooth fallback.
The table distinguishes fresh, cached, manual, unavailable, unknown,
disabled, standby and disconnected states, with battery percentages
and local measurement timestamps. Select a supported device to open
its independent battery history. Refresh, extended diagnostics and
host telemetry preview reuse the existing application commands.
Opening or closing the dashboard does not start new HID polling.
The window refreshes when the normal monitor updates; closing it
leaves tray operation unchanged. No device configuration writes are
implemented by this dashboard. macOS dashboard parity remains planned.

## Windows multiple devices

Each supported AJAZZ receiver is polled independently, even if another
receiver already returned a valid battery level. **Settings → Separate tray
icons** (enabled by default) displays an icon for each present receiver and
the opted-in AULA battery monitor. Windows may place extra icons in the
notification-area overflow; pin them using Windows taskbar settings.
All icons share the application menu; the **AJAZZ receivers** submenu shows
individual battery levels and charts, including unavailable receivers.
Double-click an icon to request a refresh.

The owner's AJ159 reported USB revision 0300 and AJ179 is inferred as 0002
from removal comparison; these are provisional model labels, not universal
model identifiers. Repeated or unknown revisions get distinct labels.
Receiver histories are stored locally using a hash of the Windows HID path;
moving a receiver to a different USB port may create a new history. The
previous combined CSV remains available under Legacy battery history and
is no longer modified. Bluetooth fallback remains a single manually selected
device, only active when no matching USB receiver is present. Existing dock
clock synchronization still targets the first accepting collection.

## Experimental AULA L99 2.4 GHz battery monitor (Windows only)

AULA L99 monitoring is **disabled by default**. In the Windows tray open
**AULA L99 (experimental) → Read AULA battery once** to query the connected
2.4 GHz dongle manually, or explicitly enable **Monitor AULA automatically**
to poll it with the normal refresh interval. The keyboard has its own status,
local history file (`aula-l99-history.csv`) and independent low-battery
notification debounce. Global notification thresholds (below 50, 25, 10%)
and the Record battery history toggle apply to both devices. Use
**Copy AULA diagnostic summary** to share a privacy-safe result.

The reader accepts only the documented battery query (`0x20`) on the
`05AC:024F / MI_03` vendor interface and validates 1–100% responses.
The receiver identifier is shared with AULA S75 Pro: a response is **not**
proof of L99 identity. The owner's connected L99 returned a fresh 100% battery reply twice;
sleep/wake and other hardware behavior remain unverified. A sleeping keyboard, mismatched dongle revision or missing response
will show unavailable rather than an invented percentage. No keyboard
settings/firmware/RGB command is implemented. **macOS L99 is not supported**.

For an intermittent AULA reply failure, beta.30 retries the existing battery
query once. A recent last-good percentage can appear in grey with an asterisk
for up to 24 hours (expiry applied during refresh), with a cached label
and timestamp in the menu. Unknown presence, receiver identity change, ambiguous multiple candidates,
confirmed removal or opt-out clear cached values. The cache is session-only;
a new application session needs a successful reply before displaying it. History and warnings never use cached battery data.
This does not prove that every sleeping keyboard wakes or responds.

## AULA system telemetry preview (Windows)

Open **AULA L99 → System telemetry preview...** to sample Windows CPU load.
GPU utilization and CPU/GPU temperatures are read from a user-started
LibreHardwareMonitor local web server at 127.0.0.1:8085 if available.
Keep that server restricted to loopback, never expose it to the network.
Each GPU/package is shown separately; missing sensors remain unavailable.
No driver is installed or bundled; the preview does not send keyboard
data, start a remote service or enable automatic screen synchronization.
See [the screen synchronization evidence and gates](docs/AULA_L99_SCREEN_SYNC.md).

## Extended Windows diagnostics

Open **Diagnostics → Extended device diagnostics...**. After collecting the
report, the application automatically opens a Save As dialog for a dated
TXT file. Canceling the dialog opens a selectable report with Copy and Save
buttons. Reports stay local unless you choose to share them.

The inventory covers all present HID collections for AJAZZ VID 3151
(including 4026/4027 and 5007), plus known AULA candidate USB IDs. It
reports VID/PID, MI/collection, bcdDevice, usage and report lengths, descriptor
errors, the last ordinary AJAZZ battery polling trace and timestamp, and
cached AULA/Bluetooth status. It does not send new HID commands, collect
serial numbers or private device paths, scan Bluetooth, or upload files.
For current poll results, wake the target device, select Refresh now and
allow an ordinary polling cycle to finish before collecting the report.
Unknown receivers are inventoried but not automatically polled.

## Platforms and hardware status

| Platform | AJ179 APEX | AJ159 APEX |
|---|---|---|
| Windows 10/11 x64 | Battery read confirmed on user's dock | Battery read confirmed at 95% on owner's receiver |
| macOS 13+ (Intel/Apple Silicon) | Experimental; native AppKit + IOKit HID | Experimental; native AppKit + IOKit HID |

**Mac:** see [macOS build and limitations](macos/README.md). AJ159 APEX has
multiple USB identities; only the 8K dock `3151:5007` is targeted here,
not alternate `3151:4026` or `3151:4027` receivers. This is not a
WinForms port: macOS uses its own Swift menu-bar application. Bluetooth
has experimental manual battery inspectors on both platforms; automatic
Bluetooth monitoring is not yet enabled. On macOS only one matching receiver is reported at a time;
Windows now exposes independent receiver readings.

## Features

- Live battery percentage rendered in the notification area (system tray).
- Receiver presence and unavailable/asleep status (`?` icon, no fabricated 0%).
- **Compact Settings menu** on Windows and macOS with notifications,
  thresholds, refresh interval, history recording, dock clock, startup
  and **Language → English / Русский / Українська**.
  Switch language immediately, without restarting or changing device state.
- Selectable battery alerts strictly below 50%, 25% and 10% on Windows and
  macOS, with per-level toggles and duplicate suppression. Windows also alerts
  on a fresh opted-in Bluetooth GATT reading while USB is absent.
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

The macOS version records battery and connection history to
`~/Library/Application Support/AJAZZBatteryTray/battery-history.csv`.
The new **Battery history chart...** window provides 24-hour, 7-day and
30-day views; missing readings are displayed as gaps.
Use **Open battery history folder...** in the menu bar to view/export data,
or **Record battery history** to disable it. Collection records status changes
and one sample at most every five minutes, retaining up to 30 days.
The native **Battery history chart...** window offers 24-hour, 7-day
and 30-day views. Low-battery and disconnect notifications are optional
and disabled by default; enabling them requests macOS notification permission.
The menu also offers **Start at login** through macOS Service Management,
with a shortcut to Login Items settings if approval is needed.


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

Right-click the notification icon for **Refresh now**, **Battery history**,
**Bluetooth**, **Sync dock time now**, **Settings**, **Diagnostics** and **Exit**.
Under **Settings** choose **Notifications** (including each 50/25/10% threshold),
**Update interval**, **Auto-sync dock clock**, **Record battery history**,
**Start with Windows**, or **Language**. Diagnostics contains diagnostic report
and log-folder actions. Double-click the tray icon to refresh immediately.
Language choice is stored in the user settings JSON and does not alter HID commands.

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

A [safe dock protocol capture guide](docs/DOCK_CAPTURE_GUIDE.md) is available
for collecting reversible RGB/display evidence from the official software.
No unverified configuration opcode is enabled in this app.

A [read-only DPI and polling-rate research plan](docs/DPI_POLLING_READBACK.md)
identifies vendor command candidates and lists hardware verification gates.
It deliberately does **not** enable any untested HID requests or mouse
configuration changes.

For a clear distinction between successful CI builds and real mouse tests,
see the [Hardware Validation Matrix](docs/VALIDATION_MATRIX.md). It includes
AJ179 Bluetooth GATT confirmation (83%), remaining USB/BLE handover tests,
and dock clock acceptance steps.

See [ROADMAP.md](docs/ROADMAP.md) for the safety gates, validation plan and
next staged work. Battery monitoring and clock sync are implemented;
RGB, display uploads and mouse configuration are **not** exposed until
verified read-back and a reliable recovery path exist.

## Limitations / roadmap

- **Windows Bluetooth tray fallback:** optional per-session automatic
  monitoring is available after a successful **fresh** manual GATT read on
  a selected paired device. It runs only while the 2.4 GHz receiver is
  physically absent and never stores Bluetooth identifiers on disk.
  AJ179 APEX directly returned 83% via GATT on Windows in a real
  hardware test (2026-11-06). Automatic switching and reconnect behavior
  still require field validation. AJ159 APEX BLE remains unverified.
- The tray prioritizes USB 2.4 GHz even if the attached mouse sleeps.
  If Windows **cannot determine whether the receiver is present**, the app
  treats that as **unknown**, not an unplug event: no false disconnect alert
  and no switch to Bluetooth during that temporary HID enumeration failure.
  Bluetooth fallback resumes only after USB absence is confirmed.
  Windows-cached Bluetooth values are displayed in the manual inspector
  but are **not** used for automatic battery monitoring.
- macOS Bluetooth remains manual and experimental.
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
The Windows history reader validates each CSV observation: an `online`
row requires a battery percentage, while disconnected/unavailable rows must
have an empty value. Corrupt rows are skipped without discarding other data.
The on-disk schema remains unchanged, and a valid `0%` record is preserved
if supplied by a future supported source. This does **not** change the USB
receiver rule: its zero-valued HID status remains unknown, never 0%.

The chart intentionally **does not predict remaining runtime**: voltage-based
battery percentages, charging state and awake/idle time are not sufficiently
validated to make that prediction trustworthy.

## Manual Bluetooth battery check (Windows, experimental)

Switch an AJAZZ mouse into Bluetooth mode and pair it through Windows
Settings. Right-click the battery tray icon, select **Check paired Bluetooth
battery...**, click **Find paired Bluetooth devices**, choose your mouse,
then click **Read selected battery**. If the mouse is missing, enable
**Show all paired Bluetooth devices** and click Find again; Windows may
advertise it with a generic name or as Bluetooth Classic. The dialog
tries standard BLE GATT Battery Level first and can show Windows's cached
battery percentage if GATT is unavailable. The result identifies its source,
and a cached value may not reflect the latest charge.

AJ179 APEX has now returned a direct GATT reading on Windows; AJ159 remains
unverified. The mouse
name is only a candidate hint, not a trustworthy identity. No pairing or
automatic background Bluetooth polling is performed. The original 2.4 GHz
monitor and safety guards are unchanged.

### Enable automatic Bluetooth tray fallback (Windows)

1. Pair AJ179 APEX through Windows Bluetooth settings.
2. Open **Check paired Bluetooth battery...**, select the mouse and choose
   **Read selected battery**.
3. After **Fresh GATT Battery Level (2A19) read**, enable **Use this mouse
   in tray when 2.4 GHz receiver is absent (this session)**.
4. Remove the 2.4 GHz receiver. The tray shows **Bluetooth: NN%** and reads
   again at most once every 60 seconds. USB receiver presence always wins.
5. To stop, choose **Disable Bluetooth tray fallback** from the tray menu.
   Restarting AJAZZ Battery Tray also disables it.

When Bluetooth fallback is enabled but the GATT value is unavailable,
the tray explicitly shows **Bluetooth: unavailable**. The Windows cached
battery property is never treated as a live reading, even if a future UI
label changes. If you intentionally remove the USB receiver to use
Bluetooth, the optional USB-disconnect warning is suppressed for the
duration of that session's Bluetooth fallback.

Only a successful direct GATT value enables this option. Cached Windows
BatteryLife does not qualify. USB battery polling is no longer delayed by the Bluetooth read timeout.
A new USB reading updates the tray immediately; the Bluetooth request runs
independently and updates the tray when it completes. Only one automatic
Bluetooth request can be in progress at a time. Switching the selected mouse,
disabling fallback or exiting invalidates any older pending result.

When Bluetooth cannot be read, automatic retries back off: **1 minute**
normally, then **2, 5, and up to 10 minutes** after consecutive errors.
This reduces repeated requests while the mouse sleeps. Use
**Refresh Bluetooth battery now** to read immediately from the
already-selected paired mouse without waiting for the backoff. This is
available only while fallback is enabled, no USB receiver is present, and
no other Bluetooth read is pending. No scan or pairing occurs.

The tray menu also shows **Bluetooth fallback** status: off, standby while
USB is primary, checking, fresh GATT percentage or unavailable with a
failed-read count. **Copy Bluetooth monitor status** copies the displayed
source, last attempt and last successful GATT timestamp for troubleshooting.
The report intentionally excludes Bluetooth addresses, device IDs and
serial numbers. Disabling fallback clears in-memory diagnostics.

Bluetooth values older than 120 seconds
or failed reads are treated as unknown. The fallback does not currently
feed the USB-only history chart or receiver-disconnect notifications;
  a fresh opted-in Bluetooth reading can trigger a selected low-battery alert.

### Troubleshooting Windows Bluetooth discovery

In **Check paired Bluetooth battery...**, choose **Show all paired Bluetooth
devices**, then **Find paired Bluetooth devices**. Windows Classic and BLE
enumeration now return independently: if one transport fails, the other can
still list paired devices. The dialog shows paired counts and error types, with
**Copy lookup summary** for sharing a short diagnostic report. It does not
include addresses or device IDs. A device displayed in this list is not proof
that its GATT Battery Service is available. Cached Windows battery readings are
labelled as potentially stale.

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

## Hardware acceptance

Choose **Copy diagnostic report** in the Windows tray or macOS menu bar.
It copies the app version, operating system and read-only receiver details
without requesting serial numbers or private device paths.
Review the clipboard text before sharing it.

For real-device findings, use the
[hardware validation issue form](https://github.com/iSentinel/AJAZZ-Battery-Tray/issues/new?template=hardware-validation.yml).

See [Hardware Acceptance Checklist](docs/HARDWARE_ACCEPTANCE.md) for safe
real-device tests covering AJ179/AJ159, disconnect/reconnect, sleep/wake,
dock clock, history and the experimental macOS features.

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
