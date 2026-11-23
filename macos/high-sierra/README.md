# AJAZZ Battery Tray — High Sierra Intel Edition

An independent, experimental native status-bar app for macOS High Sierra 10.13.x
on Intel x86_64 Macs, including iMac Late 2013. Separate bundle ID avoids
overwriting the existing macOS 13+ application.

## Features

- Battery percentage, unknown state, or disconnected state in the menu bar.
- 3151:5007 / HID vendor FFFF:0002 F7/05 receiver telemetry protocol.
- Conservative 1–100% parser; invalid or zero values display as unknown.
- Distinguishes absent receiver, unsupported HID usage and HID access errors;
  failed reads and sleeping devices never become false 0% battery values.
- Poll every 15, 30, 60, or 120 seconds (default 30).
- Opt-in low battery notifications below 50%, 25%, 10%, and receiver removal.
- Manual selection of already-connected AJAZZ Bluetooth mice exposing GATT
  Battery Service 180F / Battery Level 2A19; no automatic scanning or pairing.
  Requests wait for Bluetooth initialization with a bounded timeout;
  unsolicited radio changes never open dialogs. Stale timeouts cannot
  cancel a newer request; failed service discovery and disconnect are
  reported without inventing a battery value.
- English, Russian and Ukrainian menu translations, diagnostic copy action.
- --help, --self-test, and --diagnose command-line options.

## Install

Download AJAZZBatteryTray-macOS-HighSierra-Intel.zip and the matching
AJAZZBatteryTray-macOS-HighSierra-Intel.sha256 from the dedicated prerelease.
Extract once and move AJAZZ Battery Tray High Sierra.app into /Applications.
It appears in the top menu bar, not the Dock. App is ad-hoc signed and is
not Apple notarized. If Gatekeeper warns, use Finder right-click -> Open after
verifying SHA-256; never disable Gatekeeper system-wide.

Verify ZIP in the download directory:
    shasum -a 256 -c AJAZZBatteryTray-macOS-HighSierra-Intel.sha256

Diagnostics:
    "/Applications/AJAZZ Battery Tray High Sierra.app/Contents/MacOS/AJAZZBatteryTrayHighSierra" --self-test
    "/Applications/AJAZZ Battery Tray High Sierra.app/Contents/MacOS/AJAZZBatteryTrayHighSierra" --diagnose

On the CLI, an access failure is reported as a distinct UNKNOWN message.
A receiver with VID:PID 3151:5007 but without the expected FFFF:0002 HID
collection is reported as an unsupported interface, not a battery result.
No hardware settings are changed.

If the compatible USB receiver is absent or does not supply a verified
response, --diagnose prints UNKNOWN and exits 2, not a zero-percent reading.

## Build

Run on macOS with Xcode command-line tools:
    bash macos/high-sierra/build.sh --help
    bash macos/high-sierra/build.sh

Generated ZIP and SHA-256 are under dist/. The build targets
x86_64-apple-macosx10.13 and has no Swift runtime dependency.

## Scope and acceptance

This is an experimental port. Compiling on a modern Intel macOS runner
does not demonstrate that HID or Bluetooth calls succeed on an actual
High Sierra machine. AJ179/AJ159 physical acceptance remains pending.
The 3151:5007 receiver target was confirmed on Windows, not on this iMac.

No AULA L99 support, no dock clock synchronization, no multiple USB
receiver selection, no battery history, no auto-start integration.
No firmware, screen, button mapping, or configuration commands are sent.
Battery Service access may not be exposed by a connected mouse.

Hardware test: launch the app, inspect permissions and menu,
connect receiver, run --diagnose, sleep/wake, unplug/replug,
try opt-in alerts, and optionally test GATT read. Report system version,
mouse model and sanitized diagnostics; do not publish serial numbers.

Publish this edition separately under a v*-highsierra.* prerelease tag,
without changing the Latest Windows/macOS universal release.
