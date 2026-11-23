# High Sierra diagnostic reliability audit — 2026-11-23

## Scope

Reviewed independent Objective-C Intel macOS 10.13 application:
AppKit status-bar UI, synchronous IOKit HID enumeration, F7/05
feature report parser, CLI diagnostics, manual CoreBluetooth, package
and CI/release workflow. Compared to Windows 11 HID reader and
read-only diagnostic design. The user's qmk.top HAR files contain
network traffic rather than HID transactions. Raw HAR is not committed.

## Findings and changes

| Severity | Finding | Mitigation |
| --- | --- | --- |
| High | Redirected stdout was buffered, so a blocked HID call could leave the file empty | Unbuffered parent/worker, immediate output, native private output file |
| High | IOKit Set/GetReport in diagnostics had no deadline | Run worker in a separate process with bounded wall-clock runtime; parent records TIMEOUT and returns 124 |
| High | Background tray read could stall indefinitely without a visible state | Explicit stalled status after 20 seconds; retain single-flight guard to avoid creating further stuck threads |
| Medium | Acceptance helper conflated timeout and generic failure | Treat timeout as inconclusive and never infer 0% battery |
| Medium | All High Sierra releases shared CFBundleVersion 1 | Set package build number from independent release tag |
| Medium | CLI argument validation and output destination were insufficient | Validate modes/timeout, create 0600 file, reject symlink targets |
| Low | Full raw HID reports could disclose device-specific information | Limit to status/length and at most eight bytes of reply prefix |

## Safe protocol boundaries

- Only target USB 3151:5007 HID collection FFFF:0002.
- Only existing read-only-in-purpose F7/05 feature telemetry.
- Do not send vendor configuration, RGB, screen, keymap or firmware
  commands; no speculative HID fallback.
- Battery stays 1–100%; zero/invalid/unknown never becomes charge.
- The Windows reader expects report 05, two zero bytes, level in
  byte 3, but this is not proof of macOS response framing.

## Command in new High Sierra build

    "/Applications/AJAZZ Battery Tray High Sierra.app/Contents/MacOS/AJAZZBatteryTrayHighSierra" --trace-hid --timeout 25 --output "$HOME/Desktop/ajazz-hid-trace.txt"

Also: --diagnose --timeout 20 --output PATH; --self-test; --help.
Timeout range 3..90 seconds. Exit status 0=verified, 2=inconclusive,
124=timeout, 1=failure. Output file is private mode 0600. The parent
writes a BEGIN before IOKit work and records a TIMEOUT if it expires.
The file's existence does not prove valid telemetry.

## Automated checks

- Intel x86_64 binary with macOS 10.13 deployment target, no Swift
- Eight parser cases and four unverified/error-state cases
- Deliberately stuck test worker with 1-second watchdog limit
- Assert BEGIN, worker start and TIMEOUT in saved file
- File permissions 0600; reject symlink output destination
- Reject invalid --timeout; run shell syntax tests
- Preserve modern macOS/Windows CI and separate prerelease

## Still awaiting physical validation

- iMac Late 2013 on 10.13.6 (17G14042) with receiver 3151:5007 /
  FFFF:0002: run --trace-hid and inspect actual IOKit error/response.
- Distinguish open failure, F7 SetFeature failure, 05 GetFeature
  failure, report framing issue and sleeping mouse.
- Verify unplug/replug, extended sleep and wake, notifications.
- Check GATT 180F/2A19 only if connected AJAZZ BLE mouse supports it.
- Confirm ad-hoc Gatekeeper launch and upgrading from .4 to .5.
