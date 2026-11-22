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
- [x] Remove obsolete manual Latest action for beta.12; current release
  workflow publishes and verifies the newest six-asset release.
- Every release requires Windows tests, installer install/uninstall smoke test,
  macOS universal build and tests, and checksums in GitHub Releases.
- [x] Preflight Windows, installer and macOS version consistency and
  reject already published release tags before packaging.
- Real-device testing is separate from CI compilation.
- Track confirmed vs unverified behavior in
  [Hardware Validation Matrix](VALIDATION_MATRIX.md).

## Device Manager expansion — approved 2026-11-22

Goal: one lightweight AJAZZ/AULA application for AJ159, AJ179 and L99,
with a shared dashboard and independently managed devices. Keep the tray
workflow, Windows/macOS compatibility and evidence-first hardware policy.

These are feature milestones, not fixed promises of release numbers.
The initial proposed beta.31–44 sequence is retained below. If a hardware
gate blocks a milestone, advance independent software work; the next
available beta number is assigned at release preparation.

| Proposed milestone | Scope | Dependency / status |
| --- | --- | --- |
| beta.30 | AULA battery stability | PR 41 CI PASS, merged and six-asset release verified; owner recovery check pending |
| beta.31 | L99 RTC clock synchronization | BLOCKED: actual 2.4 GHz vendor RTC capture |
| beta.32 | L99 CPU/GPU load, temperatures, GPU selection | BLOCKED on verified RTC/telemetry layout and owner screen test |
| beta.33 | L99 weather | Verified field semantics, explicit location/provider consent |
| beta.34 | Unified Device Manager dashboard | beta.31 released; owner accepted three live dashboard rows in beta.32 |
| beta.35 | Per-device names, Windows PnP friendly names, tray visibility/color, alert and poll settings | beta.32 preview and beta.33 aliases released; beta.35 icon visibility released; beta.36 color selection implemented; PnP apply remains gated |
| beta.36 | Battery analytics | Local fresh history, estimated runtime and charge cycles with uncertainty |
| beta.37 | Multi-device Bluetooth | Paired-only selection, transport identity, independent backoff |
| beta.38 | Update checker | GitHub releases, stable/experimental channel, checksum verification, opt-in |
| beta.39 | Read-only mouse configuration and firmware reporting | Capture/readback verified per model/revision |
| beta.40 | Mouse settings and button control | Verified readback, backup, rollback and explicit apply |
| beta.41 | Lighting and sleep configuration | Readback/recovery and model-specific guarded writes |
| beta.42 | Screen brightness, images/GIF and editor | Verified display transport and capacity, reversible validation |
| beta.43 | Profiles, backup, restore | Safe round trip; import validation and explicit apply |
| beta.44 | Local API and Home Assistant | Local-only by default, authentication, privacy and permissions |
| v1.0.0 | Stable Device Manager | Hardware matrix, CI, release and acceptance gates |

### Cross-cutting feature backlog

- [ ] Battery/transport: wired and Bluetooth support per model, identified
  charging status only when verified, USB/BLE/2.4 GHz handover, no duplicate
  physical devices; separate intervals and device visibility/notifications.
- [ ] Battery analytics: charge/discharge sessions, estimated remaining
  runtime, equivalent cycle estimates, CSV export, timestamps and confidence.
  Never claim battery health or remaining capacity from percentage alone.
- [x] Initial Windows dashboard implementation: device states, battery freshness,
  source, measurement timestamps, history shortcuts, diagnostics, refresh,
  English/Russian/Ukrainian labels; reuse existing polling.
- [x] Dashboard beta.31 Windows/macOS CI and release verified.
- [x] Owner beta.32 screenshot and diagnostics confirm all three live dashboard rows.
- [ ] Keyboard accessibility review, theme options, actual tray icon count
  and future macOS parity.
- [ ] AJ159/AJ179: verified current DPI and stages, polling rates supported by
  revision, sleep, debounce, LOD, motion sync, button mapping, RGB, macros,
  profile import/export and actual firmware version (not USB bcdDevice).
- [ ] L99: RTC, CPU/GPU utilization and temperatures, selected GPU, weather,
  display brightness, media/GIF, RGB, sleep, Fn layer, key remap, macros and
  profiles. Verify wireless/wired transport separately.
- [ ] Windows Dynamic Lighting compatibility investigation; modular per-model
  drivers with capability declarations. macOS feature parity is a separate
  acceptance track, not inferred from Windows.
- [ ] Update notification, signed/checksummed distribution, settings backup,
  connection event log, optional local read-only REST API and Home Assistant.
- [ ] Recovery: maintain RESUME.md with verified baseline, current branch,
  completed code checkpoints, test/release evidence, blocking dependencies
  and next actionable stage. Never repeat completed work after interruption.

### Windows Device Manager friendly names (owner approved)

- [x] Implement present PnP inventory and read current FriendlyName/DeviceDesc,
  root hardware IDs and actual parent ancestry for primary HID candidates.
- [x] Implement proposed names preview for AJ159, AJ179 and AULA L99,
  including root and candidate primary HID nodes; shared IDs and revision
  mappings remain provisional.
- [ ] Validate actual root/child mapping in owner preview and require
  explicit model confirmation before any property change.
- [x] Implement local manual aliases independent of Windows PnP metadata
  (beta.33 released); per-AJAZZ receiver and single AULA monitoring profile.
- [ ] Confirm alias persistence, reset and independent histories in real UI.
- [ ] Add an explicit local mapping confirmation workflow and a narrowly
  scoped elevated helper only after owner preview validation.
- [ ] Implement explicit per-node administrative apply using only
  DEVPKEY_Device_FriendlyName (documented Configuration Manager/SetupAPI).
  No driver installation, device restart, registry permission changes,
  class-wide rename or HID writes.
- [ ] Save original property presence/value before applying; read back
  changes; exact-instance restore including deleting an originally absent
  property. Refuse unexpected changes and stale/ambiguous target mappings.
- [ ] Verify display in standard Windows Device Manager, independent
  receivers with identical IDs, unplug/replug and restore on owner hardware.
  No automatic rename on connection or reinstall until separately approved.
- [ ] Keep actual instance IDs strictly local; do not include them in
  diagnostics, release evidence or logs. Keep the tray unelevated.

Implementation: beta.32 preview released, beta.33 local aliases implemented;
explicitly confirmed, reversible system name changes require physical mapping
validation. No automatic reapply.

### Acceptance gates

Read-only features may proceed independently of unverified writes.
For configuration/display changes, first identify the model and transport,
document the exact approved packet from real evidence, test the encoder
and allowlist, capture original settings and recovery path when applicable,
serialize I/O, require explicit apply and physical owner readback. No
speculative writes, generic raw command UI, firmware flashing or bootloader
operations. Shared receiver IDs are not sufficient proof of model identity.
Missing metrics stay unknown, not invented values. Release checks and
hardware acceptance remain separate.

## AULA L99 keyboard support (Windows, experimental)

- [x] Add separate opt-in 2.4 GHz battery monitor, manual check and status.
- [x] Accept only the exact AULA battery request and constrained HID path;
  model shares dongle IDs with S75 Pro, so identity remains unverified.
- [x] Add separate history CSV/chart and independent 50/25/10% alert state.
- [x] Localize AULA controls and add privacy-safe diagnostic summary.
- [x] Owner's L99 showed `05AC:024F MI_03`, FF60:0061, reports 33 bytes
  and two fresh 100% replies on 2026-11-22. Shared model ID caveat remains.
- [ ] Check sleep/wake, Bluetooth-vs-dongle handover, charging behavior,
  low-battery notifications and real desktop UI on user's keyboard.
- [ ] Research macOS implementation after Windows hardware validation.

## P0 — APEX battery protocol compatibility (2026-11-22)

- Owner reports an additional APEX mouse whose battery is unavailable in our
  app but available in the original utility; owner confirmed AJ159 APEX (#53).
- [x] Implement one-action inventory + full existing HID timing/length matrix.
- [ ] CI and comparison captures from working AJ179, working AJ159 and affected AJ159.
- [x] Implement explicit local full-buffer battery capture and parser reasons
  without changing normal sampling, allowlist or model mappings.
- [x] Add diagnostic-only bounded timing sweep and instructions for official
  utility comparison: [APEX protocol diagnostics](APEX_PROTOCOL_DIAGNOSTICS.md).
- [x] Initial PR #49 Windows/macOS CI passed (45062122792 / 45062122761).
- [x] Final beta.37 CI, PR #49 merged, six-asset Latest published (45064435127).
- [ ] Capture dialog smoke test on target hardware.
- [ ] Obtain reference captures and physically confirm model.
- [ ] Compare actual interface, report IDs, sequence, lengths, data and delays.
- [ ] Evidence-backed protocol correction and regression on previous APEX models.

## AJ159 receiver compatibility investigation

- [x] Add Windows extended diagnostics for all AJAZZ VID 3151 HID
  interfaces and known AULA receiver IDs, including ordinary polling trace.
- [x] Automatically open local TXT Save As after report collection.
- [x] Owner completed diagnostic Save As twice on Windows.
- [x] AJ159 isolated: 3151:5007 MI_02 FFFF:0002, bcdDevice 0300,
  Feature 65, F7/05 returned 95%. With both receivers attached, the prior
  version returned only one valid response; AJ179 inferred as bcdDevice 0002.
- [x] Independent per-receiver sampling, history, notification state,
  diagnostic trace and optional extra tray icons (Windows beta.28 code).
- [x] beta.28 PR CI, release workflow and six-asset Latest verified.
- [x] beta.29 owner diagnostics: both AJ159 and AJ179 independently returned
  100% with separate icons enabled; AULA returned 98% on preceding poll.
- [ ] Visual acceptance with all three icons, sleep/replug and persistence.
- [x] beta.30 implement bounded AULA retry and labelled last-good cache.
- [x] beta.30 PR #41 Windows and macOS CI PASS; merged.
- [x] beta.30 six-asset Latest publication verified (release workflow 45042853053).
- [x] Owner beta.32 report: fresh L99 battery 93%; prolonged sleep can still hide battery.
- [x] beta.34 implement 24-hour session-only stale display and receiver continuity.
- [x] beta.34 PR #45 Windows/macOS CI PASS; merged.
- [x] beta.34 six-asset release publication verified.
- [ ] Physical prolonged-sleep recovery.
- [x] beta.35 implement independent showing/hiding of AJAZZ/AULA icons,
  persistent preferences and neutral menu access without disabling monitoring.
- [x] beta.35 Windows/macOS CI and six-asset release verified.
- [ ] Owner acceptance of hide/show and persistence.
- [x] beta.36 implement individual normal-charge palette with fixed warning/cached colors.
- [ ] beta.36 CI, release and real tray visual acceptance.
- [x] Per-device low-battery alert preferences implemented in beta.38 candidate; initial PR #50 CI PASS.
- [x] beta.38 final CI, PR #50 merged and six-asset release verified (45066102066).
- [ ] Physical notification acceptance.
- [x] Per-device polling intervals implemented; initial PR #51 Windows/macOS CI PASS.
- [x] beta.39 final CI, PR #51 merged, six-asset Latest release verified (45067421661).
- [ ] Mixed-device physical timing acceptance.
- [x] Local per-device analytics and observed runtime/discharge equivalents implemented; initial PR #52 CI PASS.
- [x] Final beta.40 CI and PR #52 merge; six release assets visible.
- [ ] Real-history UI acceptance; final release workflow conclusion.
- [ ] Add manual model aliases if needed for identical/unknown revisions.
- [x] beta.29 host-only CPU/GPU preview implementation and parser tests.
- [x] beta.29 CI and six-asset Latest release verified.
- [ ] Real Windows sensor preview acceptance.
- [ ] Resolve radio RTC packet layout from actual L99 2.4 GHz vendor traffic
  before enabling any additional approved write command.
  See [AULA screen sync evidence and gates](AULA_L99_SCREEN_SYNC.md).
- [ ] Confirm manual L99 time/telemetry transfer on hardware before automatic
  sync; weather is a later, separately validated stage.

## Stage 1 — Monitoring and Diagnostics

- [x] Battery percentage in Windows tray and macOS menu bar.
- [x] USB receiver detection and unknown/sleep handling.
- [x] Manual and automatic dock RTC sync (command 0x28).
- [x] Recover automatic RTC sync after a backward Windows clock correction;
  regression tests confirm no rapid repeat (hardware display unverified).
- [x] Windows battery history (CSV, state transitions, max 30 days).
- [x] Validate existing Windows/macOS history CSV rows consistently,
  including 0%, missing values, invalid states and headerless recovery.
- [x] Retry failed macOS history writes and recover after system time moves
  backward without changing the CSV file format.
- [x] Windows battery chart (24h/7d/30d).
- [x] Windows read-only interface diagnostics (VID/PID/HID usage/length).
- [x] Optional Windows receiver-disconnect warning with debounce.
- [x] Compact Settings and Diagnostics menus for Windows and macOS,
  grouping notifications, refresh interval, history, clock and startup.
- [x] Russian and Ukrainian UI language selection on both platforms,
  preserved across restarts, with English fallback and CI string checks.
- [ ] Validate localized menus, notifications and open windows on physical
  Windows/macOS desktops (code tested; visual acceptance pending).
- [x] Select independent battery notification thresholds below 50%, 25%,
  10% on Windows and macOS; persist choices and suppress repeat alerts.
- [x] Include fresh, opted-in Bluetooth GATT battery readings in Windows
  low-battery alerts while the receiver is confirmed absent.
- [x] Treat Windows HID enumeration failures as unknown, not confirmed USB
  removal, to avoid incorrect BLE fallback and false disconnect alerts.
- [x] Check SetupAPI enumeration completion status: only Win32 259 ends
  the scan; unexpected errors preserve unknown receiver presence.
- [x] Validate SetupAPI interface-detail size probes (Win32 122), size bounds
  and final reads; propagate failed reads as unknown USB presence.
- [ ] Validate recovery from temporary Windows HID enumeration errors on
  physical AJ179 hardware.
- [ ] Verify mouse reconnection, sleep, charging and clock updates on real dock.
- [x] Document Bluetooth capabilities and standard GATT discovery plan.
- [x] Verify 0x180F / 0x2A19 direct GATT battery read on AJ179 APEX:
  Windows manual read reported 83% (user hardware observation, 2026-11-06).
- [x] Add bounded manual BLE UI requests and test timeouts on Windows.
- [x] Handle Windows LE/Classic paired endpoints and generic paired names.
- [x] Isolate failed or slow Windows LE/Classic enumeration and show safe
  per-transport counts in the manual Bluetooth dialog.
- [x] Confirm paired AJ179 APEX appears in Windows inspector and returns
  direct GATT Battery Level (83% on 2026-11-06).
- [ ] Verify automatic Bluetooth tray fallback on AJ179 APEX, including
  2.4 GHz receiver unplug/replug and sleep/wake.
- [x] Offer Windows cached battery as a labelled fallback (not necessarily live).
- [ ] Validate real Bluetooth tray fallback with the 2.4 GHz receiver
  physically absent; direct GATT has already been confirmed.
- [x] Record history state after a backward system-clock adjustment.
- [x] Windows manual, paired-only Bluetooth GATT Battery Level inspector
  (experimental; the user chooses a device and initiates each read).
- [x] macOS manual, already-connected CoreBluetooth Battery Service inspector
  (experimental; no scanning, pairing, device IDs persisted or background reads).
- [x] Confirm AJ179 APEX standard GATT Battery Service on Windows.
- [ ] Confirm AJ159 APEX standard Battery Service on real Windows/macOS hardware.
- [x] Windows in-memory, explicit opt-in Bluetooth tray fallback when
  2.4 GHz receiver is physically absent. Direct fresh GATT only; no
  automatic paired-device discovery or persisted device IDs.
- [x] Use typed direct-GATT / Windows-cache / unavailable results for
  Windows automatic Bluetooth trust, independent of displayed wording.
- [x] Distinguish Bluetooth-unavailable from USB-unavailable in the tray.
- [x] Suppress intentional USB-removal notification during BLE fallback.
- [x] Keep USB tray updates independent of slow Bluetooth GATT reads.
- [x] Back off failed Windows Bluetooth reads to 2/5/10 minutes to avoid
  repeated requests to a sleeping mouse.
- [x] Add explicit Refresh Bluetooth battery now for the selected paired
  mouse, disabled while the USB receiver has priority.
- [ ] Field-verify failure recovery, wake responsiveness and the new
  retry schedule on AJ179 APEX Bluetooth.
- [x] Show Bluetooth polling state, consecutive failures and last success in
  Windows tray; copy redacted status for field testing.
- [x] Avoid overlapping background GATT requests and invalidate replies
  from previously selected or disabled Bluetooth sessions.
- [ ] Hardware-test USB polling responsiveness during slow or sleeping
  Bluetooth GATT responses, and selection changes mid-request.
- [ ] Field-test lost GATT response, USB reconnect and BLE resume on AJ179 APEX.
- [ ] Field-test Windows Bluetooth fallback and source priority on AJ179 APEX.
- [ ] Establish safe persistent, model-matched Bluetooth identity only if
  real hardware evidence justifies it; avoid storing Bluetooth addresses.
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

- [x] Document vendor GET-side DPI, profile and polling opcode
  candidates and the host-to-device transport safety warning.
  See [Read-only research](DPI_POLLING_READBACK.md).
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
