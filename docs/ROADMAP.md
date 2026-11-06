# AJAZZ Battery Tray — Product Roadmap

## Scope and safety contract

- Keep the Windows and macOS applications independent of official AJAZZ software.
- Use 2.4 GHz/8K receiver VID 3151 PID 5007; only vendor HID FFFF:0002.
- Never send unverified write opcodes, especially commands that might
  change the button matrix, persist a profile or enter a bootloader.
- No serial numbers, device paths or user telemetry are uploaded.
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
- [ ] Model-matched Bluetooth battery reporting where available.
- [ ] macOS battery history chart and notifications.

## Stage 2 — Dock customization

- [x] Read-only dock product string and USB revision (Windows); product name on macOS.
- [ ] Display capability identification and screen-controller version (unverified).
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
