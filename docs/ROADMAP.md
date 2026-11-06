# AJAZZ Battery Tray — Product Roadmap

## Scope and safety contract

- Keep the Windows and macOS applications independent of official AJAZZ software.
- Use 2.4 GHz/8K receiver VID 3151 PID 5007; only vendor HID FFFF:0002.
- Never send unverified write opcodes, especially commands that might
  change the button matrix, persist a profile or enter a bootloader.
- No serial numbers, device paths or user telemetry are uploaded.
- Pull requests run Windows and macOS checks; redundant feature-branch pushes
  should not queue duplicate builds.
- Published release assets must never be silently overwritten.
- [x] Verify future releases appear under GitHub Releases / Latest and
  contain all three distributions and their SHA-256 files.
- Every release requires Windows tests, installer install/uninstall smoke test,
  macOS universal build and tests, and checksums in GitHub Releases.
- Real-device testing is separate from CI compilation.

## Stage 1 — Monitoring and Diagnostics

- [x] Battery percentage in Windows tray and macOS menu bar.
- [x] USB receiver detection and unknown/sleep handling.
- [x] Manual and automatic dock RTC sync (command 0x28).
- [x] Windows battery history (CSV, state transitions, max 30 days).
- [x] Windows battery chart (24h/7d/30d).
- [x] Windows read-only interface diagnostics (VID/PID/HID usage/length).
- [x] Optional Windows receiver-disconnect warning with debounce.
- [ ] Verify mouse reconnection, sleep, charging and clock updates on real dock.
- [x] Document Bluetooth capabilities and standard GATT discovery plan.
- [x] Verify 0x180F / 0x2A19 direct GATT battery read on AJ179 APEX:
  Windows manual read reported 83% (user hardware observation, 2026-11-06).
- [ ] Verify standard Battery Service on actual AJ159 APEX hardware.
- [x] Add bounded manual BLE UI requests and test timeouts on Windows.
- [x] Handle Windows LE/Classic paired endpoints and generic paired names.
- [x] Isolate failed or slow Windows LE/Classic enumeration and show safe
  per-transport counts in the manual Bluetooth dialog.
- [x] Confirm paired AJ179 APEX appears in Windows inspector and returns
  direct GATT Battery Level (83% on 2026-11-06).
- [ ] Verify automatic Bluetooth tray fallback on AJ179 APEX, including
  2.4 GHz receiver unplug/replug and sleep/wake.
- [x] Offer Windows cached battery as a labelled fallback (not necessarily live).
- [ ] Validate Bluetooth battery discovery and Windows cached value on a
  physical AJ179 APEX with 2.4 GHz receiver disconnected.
- [x] Record history state after a backward system-clock adjustment.
- [x] Windows manual, paired-only Bluetooth GATT Battery Level inspector
  (experimental; the user chooses a device and initiates each read).
- [x] macOS manual, already-connected CoreBluetooth Battery Service inspector
  (experimental; no scanning, pairing, device IDs persisted or background reads).
- [x] Confirm AJ179 APEX standard GATT Battery Service on Windows.
- [ ] Confirm AJ159 APEX standard Battery Service on Windows/macOS.
- [x] Windows in-memory, explicit opt-in Bluetooth tray fallback when
  2.4 GHz receiver is physically absent. Direct fresh GATT only; no
  automatic paired-device discovery or persisted device IDs.
- [x] Use typed direct-GATT / Windows-cache / unavailable results for
  Windows automatic Bluetooth trust, independent of displayed wording.
- [x] Distinguish Bluetooth-unavailable from USB-unavailable in the tray.
- [x] Suppress intentional USB-removal notification during BLE fallback.
- [ ] Field-test lost GATT response, USB reconnect and BLE resume on AJ179 APEX.
- [ ] Field-test Windows Bluetooth fallback and source priority on AJ179 APEX.
- [ ] Add model-matched Bluetooth reporting to the tray when verified.
- [ ] Model-matched Bluetooth battery reporting where available.
  See [Bluetooth discovery plan](BLUETOOTH_DISCOVERY.md).
- [x] macOS battery history CSV with private local storage and retention.
- [x] macOS battery history chart (24h, 7d, 30d).
- [x] macOS opt-in low-battery and receiver-disconnect notifications.
- [x] macOS Start at Login via SMAppService (requires real Mac validation).
- [ ] Verify macOS notification delivery and permission prompts on a real Mac.

## Stage 2 — Dock customization

- [x] Read-only dock product string and USB revision (Windows); product name on macOS.
- [ ] Display capability identification and screen-controller version (unverified).
- [x] Document safe USB capture of official dock commands and rollback.
- [ ] Collect real AJ179 APEX before/after/readback traces for RGB/display.
- [ ] Validate reversible RGB brightness / effect protocol on AJ179 APEX.
- [ ] Capture known-good original settings and demonstrate read-back.
- [ ] Only after validation: RGB UI with explicit apply/reset controls.
- [ ] Determine image/GIF upload framing, chunk ordering and rollback.
- [ ] Only after full hardware test: display media editor with preview.

### Safety note — display payloads

The public AJ-series reverse engineering lists OLED/TFT commands
0x25/0x29 and USERGIF 0x18/0x19, but those commands are not verified
for our particular physical dock. Earlier host-rendered clock attempts
failed. Do not expose, guess or send these commands until a device-specific
read-back/round-trip and recovery test is recorded.

## Stage 3 — Mouse configuration

- [x] Add strict HID write-command allowlists for Windows and macOS.
- [x] Unit-test blocking of screen/GIF, key-matrix and firmware opcodes.

- [ ] Validate safe GET-only read-back of DPI levels and polling rate.
- [ ] Add explicit read-only reporting if a matching verified response exists.
- [ ] Document actual DPI stage count and receiver limits per model.
- [ ] Back up and restore all affected settings on physical hardware.
- [ ] Only then expose set-DPI, polling-rate, LOD and button mapping.
- [ ] Keep firmware updates and bootloader writes out of scope.

### Safety note — button configuration

A public AJ-series analysis found a mistaken commit opcode 0x50 actually
targets the mouse key matrix. Do not introduce generic "commit" or
write commands from speculative opcode tables. Use only confirmed packets
with device-model-specific guards and recovery instructions.

## Hardware acceptance preparation

- [x] Copy diagnostic report on Windows and macOS without serial number queries.
- [x] Publish physical hardware acceptance checklist for AJ179 and AJ159.
- [ ] Gather real Windows sleep/reconnect/RTC observations and Mac compatibility results.
- [ ] Confirm AJ159 APEX with its particular 8K receiver on hardware.

## Evidence and release rules

Before promoting any experimental feature to supported:
1. Capture receiver VID/PID, HID usage, model and firmware without publishing
   serial numbers.
2. Test on hardware, record before/after/read-back and recoverability.
3. Validate sleep/wake, unplug/replug, reconnect and simultaneous vendor app.
4. Pass Windows/macOS CI, app packaging and release checksums.

## Current Stage 2 evidence

Safe Windows HID calls: `HidD_GetProductString` and `HidD_GetAttributes`
from Microsoft's documented APIs. They return metadata without vendor
configuration commands. USB `VersionNumber` is a device revision,
**not** firmware version.

- https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidsdi/nf-hidsdi-hidd_getproductstring
- https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidsdi/nf-hidsdi-hidd_getattributes

## Protocol references

- https://github.com/Aiacos/ajazz-control-center
- https://github.com/Aiacos/ajazz-control-center/blob/develop/docs/protocols/mouse/aj_series_opcode_table.md
- https://github.com/Aiacos/ajazz-control-center/blob/develop/docs/protocols/mouse/aj_series_vendor.md
