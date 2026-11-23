# Changelog

## Unreleased — guarded DPI and polling-rate research
- Document GET-side vendor candidates for DPI stages, active profile,
  polling rate and mouse options, with explicit model uncertainty.
- Explain that vendor GET commands may require host-to-device HID writes.
- Preserve the 0xF7/0x28 allowlist and prohibit speculative probes.
- Define capture, readback, source-of-truth and failure-handling gates.


## 0.3.0-beta.51 (2026-11-23)
- Allocate AULA timer only while automatic monitoring is enabled.
- Reject stale replies and serialize AULA requests; prompt resampling on re-enable.
- Unify fresh, cached, expired and manual-only dashboard/API states.
- Twenty-six regression assertions; combined Windows/macOS CI PASS after timer callback compile fix.
- Physical AULA sleep recovery and Windows resource measurement remain pending.
- No changes to HID commands or normal polling cadence.

## 0.3.0-beta.50 (2026-11-23)
- Replace the opt-in ten-second timer with one-shot update deadlines.
- Preserve initial 60-second delay, daily success and hourly failure retry.
- Guard stale timer events and saturate deadline arithmetic.
- Serialize manual and automatic update lookups using a lazy cancellable gate.
- Sixteen new assertions; initial Windows/macOS CI PASS.
- No HID poll cadence, default HA integration or update consent changes.

## 0.3.0-beta.49 (2026-11-23)
- Avoid transient collections in receiver selection and inactive icon paths.
- Compute USB discovery intervals without sorting or LINQ.
- Replace threshold HashSet with a three-bit mask; 8192-sample comparison PASS.
- Reuse immutable absent/unknown readings and saturate missing-poll count.
- Twelve new assertions; initial Windows/macOS CI PASS.
- No polling cadence, HID protocol or default HA behavior changes.
- Windows resource comparison remains outstanding.

## 0.3.0-beta.48 (2026-11-23)
- Reuse visually equivalent primary and secondary tray icons.
- Defer history reads and avoid sorting until a graph is requested.
- Eliminate unchanged history sample allocations; unchanged retention policy.
- Nineteen regression assertions and resource sampler smoke test: initial CI PASS.
- Physical Windows resource comparison remains outstanding.

## 0.3.0-beta.47 (2026-11-23)
- Privacy-filtered immutable battery snapshots with read-time expiration.
- Explicit session-only loopback HTTP API, random bearer token, bounded GET requests.
- 44 snapshot and HTTP assertions; initial Windows and macOS CI PASS.
- No LAN binding, automatic listener, hardware controls or remote HA integration.

## 0.3.0-beta.46 (2026-11-23)
- Portable global preference export, localized preview and explicit restore.
- Strict 8 KiB versioned schema; transactional rollback on settings save failure.
- Exclude device IDs, aliases, history, hardware flags and network consent.
- 22 backup/restore regression assertions; final CI and UI acceptance pending.

## 0.3.0-beta.45 (2026-11-23)
- Explicit opt-in automatic release checks with persisted consent and channel.
- Independent monotonic scheduling, cancellation, session duplicate suppression,
  and exclusion of simultaneous manual and automatic lookups.
- Twenty scheduling and preference assertions; initial Windows/macOS CI PASS.
- No unattended download or installation; real Windows UI acceptance pending.

## 0.3.0-beta.44 (2026-11-23)
- Offline Windows release file verification for the original setup and portable EXE.
- Bounded, cancellable SHA-256 comparison with strict companion manifest handling.
- Twelve local file tests; initial Windows and macOS CI PASS.
- No download, execution, or publisher authentication claim.

## 0.3.0-beta.43 (2026-11-23)
- Manual Windows update checker, stable/experimental channels and EN/RU/UK.
- Fixed GitHub API, bounded response and timeout, locally constructed links.
- 26 pure version/checksum/metadata regression cases; final CI pending.
- No automatic downloads, installation or background network activity.

## 0.3.0-beta.42 (2026-11-23)
- Independent, session-only paired BLE battery monitors, per-device retry,
  alerts, dashboard and tray icons; global conservative USB precedence.
- Serialized feature-independent WinRT battery reads, including timeout isolation.
- Offline GearHub reference analysis and eight regression checks; the live
  AJAZZ HID decoder and existing USB queries are unchanged.
- Hardware validation for multiple BLE devices and affected AJ159 remains pending.

## 0.3.0-beta.41 (2026-11-22)
- Combine HID descriptor inventory, last ordinary monitor state and fresh
  full APEX protocol timing/length matrix in one explicit diagnostic report.
- Continue the bounded diagnostic sweep after successful responses; normal
  polling still stops at first success. No new HID opcodes.
- Four pure matrix checks and a three-mouse comparison procedure.

## 0.3.0-beta.40 (2026-11-22)
- Add observed discharge rate and conditional runtime projection to individual
  Windows receiver and AULA profile history, with localized evidence labels.
- Show observed discharge equivalents over the selected range; distinguish
  insufficient evidence from zero observed discharge.
- Exclude legacy aggregated history from estimates; no physical capacity,
  battery health or cycle-count claims, no additional hardware traffic.
- Add 18 pure analytic checks.

## 0.3.0-beta.39 (2026-11-22)
- Add local per-receiver and AULA profile polling interval overrides
  (15/30/60/120 seconds or inherited global interval).
- Separate AJAZZ discovery from sampling; preserve timestamps on
  scheduled skips and do not replay battery history or alerts.
- Add independent AULA timer, tray and dashboard editor, EN/RU/UK strings,
  settings validation, rollback and diagnostic interval fields.
- Add 24 pure checks. No new HID commands; physical timing validation pending.

## 0.3.0-beta.38 (2026-11-22)
- Configure independent low-battery 50/25/10 threshold preferences for
  each AJAZZ receiver and the AULA profile in Windows tray and dashboard.
- Inherit global settings or use a custom set, including explicit mute.
  Preserve the master switch, low-battery hysteresis and Bluetooth policy.
- Validate persisted preferences, roll back failed saves, and localize
  the editor. Nine pure settings checks cover the new preferences.
- No new HID requests or changes to polling intervals.

## 0.3.0-beta.37 (2026-11-22)
- Add explicitly consented Windows APEX battery protocol capture, including
  full F7/05 feature buffers, timings and parser rejection explanations.
- Test diagnostic-only 30/100/250 ms waits; stop at the first valid reply.
- Preserve ordinary polling, battery parsing, privacy-safe normal reports
  and the existing HID command allowlist. Do not claim incident resolution.
- Add six diagnostic classification checks and official utility comparison
  instructions. Physical target validation remains pending.

## 0.3.0-beta.36 (2026-11-22)
- Add six selectable normal-charge tray colors, independently persisted
  per AJAZZ receiver and AULA monitoring profile.
- Preserve red/amber low-charge and gray cached/unavailable states;
  update primary and additional icons as soon as preferences are saved.
- Add localized palette editor with icon previews, reset via default
  selection, settings validation and eleven pure tests.
- No new HID commands, Windows property writes or threshold changes.

## 0.3.0-beta.35 (2026-11-22)
- Add persistent per-device tray visibility controls in the dashboard and
  receiver/AULA submenus without changing sampling, history or notifications.
- Select a visible primary receiver, show eligible extra icons only, and
  retain a neutral application icon when all active icons are hidden.
- Add privacy-safe preference validation, settings round-trip tests and
  EN/RU/UK controls. No new HID commands or Windows property writes.
- Keep actual Windows icon placement and physical UI validation separate
  from application preference and automated CI.

## 0.3.0-beta.34 (2026-11-22)
- Retain the AULA last-good battery display for prolonged sleep, up to
  24 hours, clearly marked cached with its original measurement time.
- Bind cache continuity to a single local receiver identity; reset on
  unknown presence, ambiguity, receiver replacement, disconnect or opt-out.
- Keep actual poll failures in diagnostics and avoid recording cached
  values as fresh history or evaluating low-battery alerts from them.
- Record beta.32 owner evidence: all three dashboard rows displayed fresh
  battery readings (AJ179 100%, AJ159 100%, L99 93%). Owner reports that
  prolonged L99 sleep can hide the reading; sleep fix remains unverified.

## 0.3.0-beta.33 (2026-11-22)
- Add persistent local per-receiver AJAZZ aliases and a single AULA profile alias.
- Edit or reset names from Device Manager or tray menus; retain detected model
  labels, independent history keys and selection during refresh.
- Validate alias length, control/format characters and local identity keys;
  roll back the in-memory edit if settings cannot be saved.
- Localize controls in EN/RU/UK. No Windows PnP writes, elevation or new HID I/O.
- Record verified beta.32 release; hardware mapping and actual Windows
  Device Manager rename remain pending.

## 0.3.0-beta.32 (2026-11-22)
- Add a read-only Windows PnP names preview from Settings.
- Group exact supported USB receiver families and candidate primary HID
  nodes by live parent ancestry; read the original Windows friendly name
  or description and suggest a provisional revision-based model label.
- Add strict candidate/revision tests and localized preview. No instance
  paths exported, administrator elevation, property changes or HID writes.
- Add the approved Windows naming milestone and restore/acceptance gates.
  Physical mapping validation remains pending.

## 0.3.0-beta.31 (2026-11-22)
- Add unified Windows Device Manager dashboard displaying independent
  AJAZZ/AULA observations and the selected Bluetooth fallback.
- Mark fresh, cached, manual, unavailable, disconnected, unknown,
  disabled and standby states; show the original measurement timestamp.
- Add per-device history shortcuts, existing refresh, diagnostic and
  host-telemetry commands, English/Russian/Ukrainian localization.
- Preserve tray polling and HID command allowlists: no extra automatic
  hardware requests for an open dashboard.
- Save the approved expansion roadmap through v1.0.0. Advance independent
  dashboard work while L99 wireless screen synchronization awaits evidence.
- Physical desktop acceptance remains pending.

## 0.3.0-beta.30 (2026-11-22)
- Retry the approved AULA battery request once after a missed response.
- Mark a recent last-good percentage as cached (grey icon, asterisk and
  timestamp), expire it at the next refresh after two minutes and clear it
  on confirmed removal or opt-out. Preserve fresh-only warnings and history.
- Add cache/recovery tests and last-good diagnostic fields; discard obsolete
  results after monitoring changes.
- Record beta.29 owner evidence: independent simultaneous AJ159/AJ179 reads
  both returned 100%; AULA returned 98% then no valid reply 31 seconds later.
- No additional keyboard opcode or screen write; physical recovery pending.

## 0.3.0-beta.29 (2026-11-22)
- Add manual, host-only AULA system telemetry preview: native Windows CPU
  load and optional local LibreHardwareMonitor CPU/GPU load/temperature.
- Parse hardware sensor trees without mixing adapters; preserve missing
  values, bound local HTTP and reject invalid sensor types/units/ranges.
- Document contradictory wireless RTC layouts and the capture gate before
  enabling any screen command. No driver install or new HID write.
- Keep existing multi-device monitoring and macOS behavior.

## 0.3.0-beta.28 (2026-11-22)
- Poll each supported Windows AJAZZ receiver independently instead of
  returning after the first successful response.
- Add optional multiple tray icons (on by default), per-receiver status,
  history and notification debounce, and per-receiver extended diagnostics.
- Label the owner's AJ159/AJ179 USB revisions provisionally; maintain
  separate local identifiers even for receivers with the same revision.
- Expose previous mixed history read-only; retain AULA opt-in, BLE fallback
  and the existing HID allowlist. macOS behavior unchanged.
- Owner diagnostics confirmed AJ159 battery 95% and L99 battery 100%;
  simultaneous multi-device UI acceptance remains pending.

## 0.3.0-beta.27 (2026-11-22)
- Add extended Windows HID diagnostics with automatic local TXT Save As dialog
  and a copy/save fallback after cancellation.
- Inventory all AJAZZ vendor PIDs and known AULA HID identifiers without
  opening them for input or output; include report lengths and usage.
- Record the last ordinary supported AJAZZ battery poll stages and errors,
  bounded status header, timestamps and cached AULA/Bluetooth status.
- Do not add commands for alternate AJ159 receiver revisions; real-device
  diagnostics are required before extending monitoring. macOS unchanged.

## 0.3.0-beta.26 (2026-11-18)
- Add experimental Windows-only AULA L99 2.4 GHz battery monitor, off by
  default; manual one-shot read and explicit automatic-monitoring toggle.
- Validate dongle identity and report caps before the sole battery command;
  reject malformed, stale, invalid, or absent battery reports.
- Add separate AULA battery history/graph and independent threshold state,
  using the existing user-configured 50/25/10% alert preferences.
- Add privacy-safe copyable AULA status for physical acceptance.
- Track unresolved shared AULA S75 Pro/L99 receiver ID and hardware test
  requirement. macOS remains unchanged for keyboard monitoring.

## 0.3.0-beta.25 (2026-11-16)
- Group Windows and macOS tray/menu-bar settings into a dedicated Settings
  submenu; keep status, refresh and dock clock sync easily accessible.
- Move diagnostic tools into Diagnostics and group Bluetooth controls.
- Add English, Russian and Ukrainian UI language choice, remembered across
  restarts, with immediate menu translation and open-window caption updates.
- Translate battery notifications and history/Bluetooth UI without changing
  protocol-level diagnostics or hardware access.
- Fix macOS refresh-interval updates clearing unrelated threshold checks.
- Add pure Windows language tests and macOS localization self-tests.
- Keep the verified HID write allowlist and Bluetooth consent unchanged.

## 0.3.0-beta.24 (2026-11-16)
- Add individually selectable low-battery alert thresholds strictly below
  50%, 25% and 10% on Windows and macOS.
- Persist Windows alert levels in per-user JSON settings and macOS choices
  in UserDefaults. Keep existing global notification toggles.
- Suppress repeated alerts, use 5-point recharge hysteresis and emit only
  the most urgent warning when a reading crosses several levels at once.
- Allow fresh, session-opted-in Windows Bluetooth GATT readings to trigger
  low-battery alerts when the USB receiver is confirmed absent.
- Extend Windows unit tests and macOS self-tests; preserve HID write safety.

## 0.3.0-beta.23 (2026-11-07)
- Validate both SetupAPI interface-detail calls instead of silently ignoring
  failed size queries, failed detail reads or invalid interface paths.
- Classify such errors as unknown USB presence, preserving safe BLE priority.
- Add seven pure tests for expected Win32 buffer errors and valid sizes.
- Preserve the existing HID write allowlist and paired-only Bluetooth policy.

## 0.3.0-beta.22 (2026-11-07)
- Distinguish SetupAPI ERROR_NO_MORE_ITEMS from unexpected Windows HID
  enumeration failures, which must not imply that the USB receiver is absent.
- Surface unexpected scan errors through the existing unknown USB state,
  preventing false disconnect events and automatic Bluetooth fallback.
- Add four pure tests of SetupAPI completion/error classification.
- Keep all existing HID and Bluetooth write restrictions unchanged.
- Bump release metadata consistently across Windows, macOS and installer.

## 0.3.0-beta.21 (2026-11-07)
- Treat Windows USB/HID enumeration failures as unknown rather than unplugged.
- Prevent false USB disconnect history, notifications and Bluetooth handover.
- Block automatic/manual BLE polling until receiver absence is confirmed.
- Restore USB-first status after the next successful HID enumeration.
- Test present, absent and unknown receiver state with 11 regression checks.
- Keep approved HID commands unchanged; no new wireless writes.


## 0.3.0-beta.20 (2026-11-07)
- Recover Windows automatic dock RTC synchronization after the system clock
  moves backward instead of delaying updates until the old clock is reached.
- Test immediate recovery, no rapid repeat and the normal five-minute interval.
- Keep verified HID command restrictions unchanged; real dock confirmation
  is still required.
- Bump Windows, installer, macOS build and release metadata for beta.20.

## 0.3.0-beta.19 (2026-11-07)
- Share a strict, hardware-independent Windows battery history CSV codec.
- Preserve valid 0% history rows and reject incomplete or contradictory
  online/disconnected/unavailable rows, bad dates and out-of-range values.
- Keep the existing CSV schema and recover readable rows from headerless files.
- Align the macOS history parser with the same CSV validation rules.
- Retry macOS history writes after disk errors and pruning failures.
- Record a new macOS sample after a backward system-clock correction.
- Add Windows CSV round-trip tests and macOS history self-test checks.
- The USB HID zero-value report still means unknown; no new device commands.

# Changelog

## Unreleased — hardware evidence clarification
- Add a capability-by-capability validation matrix separating CI and
  actual AJ179 APEX observations.
- Document the direct Bluetooth GATT 83% hardware result and remaining
  sleep/wake, USB handover, RTC and AJ159 acceptance steps.
- Consolidate duplicate pending Bluetooth roadmap items without claiming
  unverified hardware support.


## 0.3.0-beta.18 (2026-11-06)
- Back off failed automatic Bluetooth GATT reads from one minute to two,
  five, then a maximum of ten minutes while the mouse is unavailable.
- Reset the retry interval after a fresh successful GATT Battery Level read.
- Add Refresh Bluetooth battery now for the selected, opted-in mouse.
- Disable manual BLE polling while USB receiver is present or a read runs.
- Add fifteen scheduling and user-consent tests, with sleep/wake guide.
- No additional Bluetooth scans, pairing, firmware or HID/GATT writes.


## 0.3.0-beta.17 (2026-11-06)
- Show Bluetooth fallback state, recent GATT percentage and repeated failures
  in the Windows tray menu.
- Track last attempted and last successful automatic GATT read timestamps.
- Add Copy Bluetooth monitor status with no device IDs, MACs or serial numbers.
- Clear diagnostic counters on disable; reject monitoring results when off.
- Test status labels, failed-read counters, timestamp preservation and reset.
- Add a hardware validation issue field for the redacted monitor status.


## 0.3.0-beta.16 (2026-11-06)
- Make Windows USB battery updates independent of slow Bluetooth polling.
- Avoid overlapping automatic Bluetooth GATT requests in the same session.
- Reject late GATT responses after Bluetooth selection/disable changes.
- Refresh the tray on BLE completion without duplicating USB history or alerts.
- Test session-generation invalidation and document unplug/replug acceptance.
- No new HID/GATT writes, automatic pairing or unpaired Bluetooth scanning.


## 0.3.0-beta.15 (2026-11-06)
- Replace fragile Bluetooth source detection by display text with typed
  DirectGatt, WindowsCached and Unavailable states.
- Use only validated fresh direct-GATT values for automatic Bluetooth tray.
- Label a selected but currently unavailable Bluetooth source explicitly.
- Suppress misleading USB receiver-disconnect warnings during intentional
  Bluetooth fallback; preserve USB warnings when fallback is disabled.
- Add regression tests for stale values, cached source, asleep USB receiver,
  source priority and disabling fallback.
- No new HID write commands, Bluetooth scanning or automatic pairing.


## 0.3.0-beta.14 (2026-11-06)
- Record field-confirmed AJ179 APEX Bluetooth GATT Battery Level: 83%.
- Add explicit opt-in automatic Bluetooth tray fallback on Windows after
  successfully reading a selected mouse's standard GATT Battery Level.
- Keep selected device in memory only, cleared on disable and app restart.
- USB receiver takes priority; BLE is queried only when USB is absent.
- Enforce 60-second minimum BLE polling and 120-second reading freshness.
- Reject Windows-cached values for automatic display; unavailable stays unknown.
- Add a tray disable option and scheduling/source-priority unit tests.
- No auto-pairing, BLE scans, GATT writes or new vendor HID commands.


## Unreleased — release verification and field evidence
- Check that each published release is GitHub's Latest, not a hidden pre-release.
- Check all three distributions and their SHA-256 files after publishing.
- Add a structured AJ179/AJ159 hardware test report with privacy checks.
- No application code or HID commands changed.


## 0.3.0-beta.13 (2026-11-06)
- Isolate Windows paired BLE and Classic enumeration failures.
- Limit each transport's lookup time to eight seconds, retaining partial results.
- Show per-transport paired-device counts and sanitized error names.
- Add Copy lookup summary without device IDs, addresses or serial numbers.
- Test manual Show all paired-device name filtering and update diagnostics docs.
- Do not add auto-pairing, Bluetooth background polling or device writes.


## 0.3.0-beta.12 (2026-11-06)
- Fix Windows Bluetooth device list hiding paired AJAZZ mice.
- Enumerate paired-only LE and Classic devices; allow all paired device names.
- Remove unreliable second pairing-state filter on Windows endpoints.
- Read Windows's cached numeric device battery property if GATT is absent.
- Label cached values and reject unknown sentinel 101 or invalid percentages.
- Keep Bluetooth data manual and separate from USB receiver monitoring.
- Add cached-battery parser tests; no pairing, GATT writes or HID settings.


## Unreleased — dock protocol evidence guide
- Document Windows USBPcap/Wireshark capture of one reversible vendor setting.
- Require before/after/readback/restore and redaction before publishing.
- Keep all unverified RGB, GIF, DPI and profile writes blocked.


## 0.3.0-beta.11 (2026-11-06)
- Add 12-second timeout to the Windows paired BLE lookup and a 15-second
  timeout to the manually triggered Battery Service read.
- Report timeouts without inventing a percentage or changing 2.4 GHz status.
- Resume battery-history observations if Windows system time moves backward.
- Add deterministic tests for timeout completion, expiration and clock jumps.
- No new HID or GATT commands and no automatic Bluetooth polling.


## 0.3.0-beta.10 (2026-11-06)
- Add an experimental macOS manual read of the standard GATT Battery Level.
- Enumerate only CoreBluetooth already-connected peripherals with Battery
  Service, filter plausible AJAZZ names and require user selection.
- Never scan, pair, write GATT characteristics, or poll in background.
- Add a 10-second read timeout and explicit unavailable results.
- Add parser self-tests and Bluetooth permission description.
- Real AJ179/AJ159 BLE compatibility still requires a Mac hardware test.


## 0.3.0-beta.9 (2026-11-06)
- Add an explicit Windows manual Bluetooth Battery Service (GATT 180F) probe.
- Enumerate only already paired BLE candidates and require user selection.
- Read Battery Level (2A19) without GATT writes, pairing or background scanning.
- Validate standard one-byte 0..100 responses; unavailable remains unknown.
- Keep BLE results separate from 2.4 GHz tray status and history.
- Move Windows targeting to Windows SDK 19041 for .NET 8 WinRT interop.
- Hardware Bluetooth percentage support remains experimental until tested.


## Unreleased (Bluetooth research)
- Confirmed Bluetooth connectivity of AJ179 APEX and AJ159 APEX from product specs.
- Documented standard read-only Battery Service discovery and privacy gates.
- Runtime BLE support remains disabled until paired-device hardware validation.

## Unreleased (CI improvements)
- Avoid duplicate Windows and macOS builds for every feature-branch push.
- Keep mandatory pull-request checks and main-branch builds.
- Cancel superseded pull-request CI runs when new commits arrive.
- Serialize beta release publishing and reject overwriting existing assets.


## 0.3.0-beta.8 (2026-11-06)
- Add Copy diagnostic report to Windows tray and macOS menu bar.
- Include app and OS version with read-only receiver metadata.
- Do not query USB serial numbers or private device paths.
- Add hardware acceptance checklist for AJ179/AJ159 and both OSes.
- Keep vendor mouse and display configuration opcodes blocked.


## 0.3.0-beta.7 (2026-11-06)
- Add optional macOS Start at Login using SMAppService.mainApp.
- Read the system registration state and show when approval is needed.
- Add shortcut to macOS Login Items settings.
- No administrator privileges or custom launch agents required.
- Hardware/Mac startup behavior remains experimental until field validation.


## 0.3.0-beta.6 (2026-11-06)
- Add opt-in macOS local notifications for battery thresholds 20/10/5%.
- Add optional receiver-disconnect alert after two missing USB polls.
- Request notification permission only when the user enables a menu option.
- Prevent duplicate alerts and ignore sleeping mice when the receiver remains.
- Add hardware-independent alert-policy checks to macOS self-test.


## 0.3.0-beta.5 (2026-11-06)
- Add a native AppKit battery history graph for macOS.
- Select 24 hours, 7 days or 30 days and refresh on demand.
- Preserve gaps for missing battery readings instead of showing 0%.
- Test CSV parser with malformed rows and invalid percentages.
- Document ready-made GitHub release downloads for macOS users.


## 0.3.0-beta.4 (2026-11-06)
- Add private macOS battery history CSV under Application Support.
- Record charge changes and receiver status; sample unchanged state every 5 min.
- Auto-prune history after 30 days and cap rows at 20,000.
- Add macOS menu options to open history folder and disable recording.
- Add macOS self-tests for recording frequency and state changes.
- Windows features remain unchanged from v0.3.0-beta.3.


## 0.3.0-beta.3 (2026-11-06)
- Add an explicit allowlist for every Windows HID feature write.
- Permit only correctly framed 0xF7 telemetry and 0x28 dock clock packets.
- Reject malformed timestamps, unexpected payloads, display, mapping and
  bootloader commands before they reach the receiver.
- Add equivalent macOS guards and unit/self-tests for dangerous opcodes.
- No new mouse configuration write commands have been enabled.


## 0.3.0-beta.2 (2026-11-06)
- Stage 2 start: read-only AJAZZ 8K dock product identification.
- Windows: read HID product string and bcdDevice revision (not firmware).
- macOS: read HID product string in the menu-bar diagnostics dialog.
- No unverified RGB, image, GIF, DPI or profile commands were added.


## 0.3.0-beta.1 (2026-11-06)
- Add Windows battery history with a built-in 24h/7d/30d chart.
- Store state transitions in local CSV with a 30-day retention limit.
- Add receiver/interface diagnostics without unverified HID commands.
- Add opt-in notification for repeated receiver disappearance.
- Add history and disconnect policies with hardware-independent tests.
- Keep firmware, DPI, RGB, GIF and polling-rate configuration gated.


## 0.2.0-beta.3 (2026-11-06)
- Add manual and automatic 8K dock clock synchronization (Windows/macOS).
- Send documented clock opcode 0x28 and fixed 0xD7 marker with local time.
- Resynchronize on receiver connection and every five minutes.
- Add optional setting and status in tray/menu-bar menus.
- Add packet and scheduling tests; hardware clock verification pending.


## 0.2.0-beta.2 (2026-11-05)
- Add a separate Windows x64 installer using Inno Setup.
- Install to Program Files, add Start menu and optional desktop shortcuts.
- Register standard Windows uninstaller; preserve user settings by default.
- Publish both a portable executable and an installer in GitHub Releases.
- Add CI installation/uninstallation smoke test and SHA256 checksums.
- Simplify README to direct users to GitHub Releases.

## 0.2.0-beta.1 (development)
- Native macOS Intel/Apple Silicon menu-bar prototype via AppKit and IOKit.
- Mark AJ159 APEX compatibility as experimental; shared receiver protocol.
- Use generic AJAZZ APEX label in Windows to avoid incorrectly naming model.
- macOS HID read and AJ159 compatibility require real-device validation.


## 0.1.0 (2026-11-05)
- Initial Windows 10/11 .NET 8 notification-area application.
- 2.4 GHz/8K receiver: VID 3151 PID 5007 MI_02, usage FFFF:0002.
- Read-only battery telemetry, invalid frame rejection, low-charge alerts.
- Per-user JSON settings, autostart toggle, local log, CI release build.
- Bluetooth and charging detection deferred pending protocol validation.
