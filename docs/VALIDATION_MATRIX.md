# AJAZZ APEX — Implementation and Hardware Validation Matrix

This table separates **implemented code**, **GitHub CI results**, and
**tests actually completed with a physical mouse**. A successful build
is not evidence that a dock clock or wireless handover works on hardware.

## AULA L99 experiment — 2026-11-18

| Capability | Code / CI | Physical validation |
| --- | --- | --- |
| Windows L99 2.4 GHz battery via `05AC:024F MI_03` | Battery-only protocol and UI implemented; CI required | **Confirmed on owner's L99:** FF60:0061, 33-byte input/output, fresh 100% twice on 2026-11-22 |
| Windows L99 history / notifications | Separate file and debouncing implemented | **Pending**: no device test |
| AULA L99 vs S75 Pro identity | Shared receiver IDs; explicitly unverified in UI | **Pending**: vendor ID cannot uniquely identify model |
| macOS L99 | Not implemented | Not tested |

## AJ159 investigation — 2026-11-22

Owner returned two local Save As reports. AJ159 alone: revision 0300,
3151:5007 MI_02 FFFF:0002, feature length 65; F7/05 returned 95%.
Both receivers: revisions 0300 and 0002, one 100% response (model not
distinguished by beta.27). AJ179 revision inferred by receiver removal.
These observations do not establish universal revision-to-model mappings.
Windows beta.28 independent sampling and optional multiple tray icons:
PR Windows/macOS CI and release installer smoke test PASS; simultaneous
hardware acceptance pending.
No new receiver write commands have been enabled.

## Owner evidence — beta.29, 2026-11-22
- At 15:18:18Z, both AJAZZ receivers independently returned F7/05 100%:
  AJ179 rev 0002 and AJ159 rev 0300. Separate tray icons setting true.
  Actual visible icon count, history, disconnect and reconnect remain untested.
- AULA L99 returned 98% at 15:17:48Z; at 15:18:19Z the receiver remained
  present but battery was unavailable. Sleep versus transport failure unknown.
- beta.30 bounded retry and cached display implemented; physical validation
  remains pending. No new HID command.
  
## Device Manager expansion — beta.31 candidate

- beta.30 PR and release CI PASS (workflow 45042853053), published six
  assets; actual recovery and visual tray acceptance pending.
- Windows read-only dashboard implemented: distinct receiver observations,
  AULA cached/manual state, selected Bluetooth fallback and history shortcuts.
  beta.31 CI and release PASS; real desktop acceptance pending. No new HID writes or polling
  triggered merely by opening the window.

## Windows Device Manager friendly names — beta.32 candidate

- Read-only Configuration Manager inventory, parent mapping and proposed
  naming preview: beta.32 CI and release PASS; owner mapping validation pending.
- No Windows property writes. Administrator-only rename, original-property
  backup, readback, exact-instance restore and standard Device Manager
  display acceptance remain pending.

## Local device names — beta.33 candidate

- Local alias editor, persistence, validation, explicit reset, dashboard/tray
  labels and unchanged history identifiers implemented. Pure tests added;
  CI and real UI acceptance pending.
- AULA is a single monitoring profile, not a confirmed physical identity;
  Bluetooth-only aliases and Windows PnP writes are not implemented.

## AULA system telemetry preview — beta.29
- Host-only native CPU load and optional loopback LibreHardwareMonitor
  CPU/GPU data.json parsing implemented; CI PASS, physical sensor test pending.
- Actual radio monitor/RTC wire format remains unconfirmed; no write has
  been implemented. See AULA_L99_SCREEN_SYNC.md.

## Evidence snapshot — 2026-11-06

| Capability | Implementation / CI | Physical validation |
| --- | --- | --- |
| AJ179 APEX battery via 2.4 GHz / 8K receiver | Windows implemented; CI PASS | **Confirmed:** real mouse battery percentage was shown in Windows |
| AJ179 APEX standard BLE Battery Level | Manual Windows GATT reader implemented; CI PASS | **Confirmed:** user read **83% — Fresh GATT Battery Level (2A19) read** |
| Windows automatic Bluetooth tray fallback | Explicit opt-in, session-only, no saved ID | **Pending:** USB unplug/replug, sleep/wake and repeated fresh GATT reads |
| USB vs Bluetooth priority | USB receiver wins while physically attached | **Pending:** verify real mode switching |
| Bluetooth retry delay | 1 / 2 / 5 / 10 minutes after repeated failures | **Pending:** sleeping/waking AJ179 APEX |
| Manual Bluetooth refresh | User initiated, selected paired device only | **Pending:** real sleep recovery |
| Windows low-battery and receiver alerts | Implemented and unit tested | **Pending:** real low-battery and disconnect scenario |
| Temporary Windows HID enumeration error | Unknown state kept separate from confirmed USB absence in code | **Pending:** real transient HID error |

| USB receiver disconnect and reconnect | State-handling code and unit tests | **Pending:** real sleep/replug matrix |
| Dock time and date sync | Documented 0x28 report implemented and tested | **Pending:** visibly confirm clock update on dock screen |
| AJ159 APEX via 8K receiver | Experimental shared-receiver implementation | **Confirmed:** owner's AJ159 returned 95% via F7/05 on Windows |
| AJ159 APEX via Bluetooth | Standard Battery Service inspector available | **Pending:** actual AJ159 hardware |
| macOS battery / dock RTC | Swift universal build and self-tests PASS | **Pending:** real AJ179/AJ159 on a Mac |
| macOS Bluetooth and notifications | Manual CoreBluetooth and notification code build PASS | **Pending:** actual device and OS permission prompts |
| Windows installer | Inno Setup x64; GitHub smoke-test PASS | **Pending:** end-user upgrade/uninstall on own PC |
| RGB, GIF, DPI, polling-rate writes | Blocked by HID safety allowlist | **Not enabled:** requires confirmed read-back and recovery |
| Bluetooth charging status | Not implemented | **No validated charging report** |

The observed **83%** is one historical reading, not a permanent battery
level, and does not prove compatibility of all firmware variants or AJ159.

## Highest-value Windows hardware acceptance sequence

Use the newest package from
[GitHub Latest](https://github.com/iSentinel/AJAZZ-Battery-Tray/releases/latest).

1. Close the vendor AJAZZ utility to avoid HID conflicts, then run Battery
   Tray. Verify battery percentage over 2.4 GHz. Note the displayed source.
2. Switch AJ179 APEX to Bluetooth. Open **Check paired Bluetooth battery...**,
   select **AJ179 APEX**, click **Read selected battery** and confirm the
   message says **Fresh GATT Battery Level (2A19) read**.
3. Explicitly enable **Use this mouse in tray when 2.4 GHz receiver is
   absent (this session)**. The Bluetooth device ID stays in memory only.
4. **Physically unplug the 2.4 GHz USB receiver.** Confirm the tray switches
   to **Bluetooth** and shows a fresh percent, or clearly says unavailable.
5. Check another automatic GATT reading after 60 seconds. It must not be a
   Windows cached BatteryLife value. If the mouse sleeps, the indicator
   should become unavailable rather than remain at an obsolete percentage.
6. Wake the mouse. Use **Refresh Bluetooth battery now** to bypass the
   automatic retry delay. The success state should reset failure count.
7. Reinsert the USB receiver. Verify the tray now prioritizes USB.
   **If the USB receiver is present but the mouse is still in Bluetooth mode,
   the expected USB display may be unavailable**; Bluetooth is intentionally
   not substituted while USB is present.
8. Disable Bluetooth fallback, confirm the UI and diagnostics report it off,
   restart the application, and verify it has not silently re-enabled.
9. Copy **Bluetooth monitor status** and record the result. The copied report
   contains timestamps, counts and transport labels, **not MAC/USB IDs**.

## Dock clock acceptance

With the physical 8K receiver connected, run **Sync dock time now**. Compare
the displayed date/time on the dock against the Windows local date/time.
The application's "command sent" status confirms only that Windows accepted
the HID transfer, **not** that the dock applied it. Repeat after unplug,
resume from Windows sleep, and automatic five-minute synchronization.
Capture a screenshot of the dock only if needed, excluding personal data.

## Reporting

Use the [hardware validation issue form](https://github.com/iSentinel/AJAZZ-Battery-Tray/issues/new?template=hardware-validation.yml)
or paste the privacy-safe **Copy Bluetooth monitor status** text into this
conversation. Report PASS/FAIL and observed source/percentage, not device
instance IDs, serial numbers, addresses, raw packet dumps or unrelated
USB captures.

Do not enable unverified RGB/GIF/DPI/firmware operations to try to fix a
battery or clock problem.

## Owner beta.32 dashboard acceptance and prolonged AULA sleep

- 2026-11-22 16:52:40Z: AJ179 rev 0002 and AJ159 rev 0300 both
  independently returned 100%, AULA L99 returned 93% on 2.4 GHz.
- Screenshot confirms all three dashboard rows with fresh state, Russian
  UI and measurement time. Actual individual tray icons not shown.
- Owner reports periodic L99 sleep hides the charge. Provided report
  is a fresh success, not a capture of the sleeping state.
- beta.34 candidate extends explicitly stale display to 24 hours,
  invalidates cache on uncertain/changed identity and does not add writes.
  CI and prolonged sleep/recovery physical acceptance pending.

## Independent tray visibility — beta.35 candidate

- beta.33 six-asset release verified; beta.34 PR and main builds PASS,
  release publication in progress at checkpoint.
- beta.35 local per-device visibility, visible primary selection and neutral
  app icon implemented. Seven pure preference/selection tests added.
- CI and actual Windows tray behavior pending, including hide all, restore,
  global single-icon mode, persisted settings and unaffected history/alerts.

## Individual tray colors — beta.36 candidate

- beta.35 PR #46 and release workflow 45049517485 PASS; six release assets
  verified. Physical hide/show/persistence validation remains pending.
- beta.36 six normal-charge palettes, warning/cache precedence, editor,
  main and extra icon refresh, local settings persistence and eleven pure
  tests implemented. Windows/macOS CI and owner visual acceptance pending.
- No change to hardware writes, polling, history or alert policy.

## APEX protocol compatibility — beta.37 candidate

- Initial PR #49 head 9dfcfef: Windows CI 45062122792 and macOS CI
  45062122761 completed successfully. Final release metadata CI pending.
- Capture is explicit, local and Windows-only, with existing F7/05 requests
  and diagnostic-only timing sweep; ordinary monitoring is unchanged.
- Owner reports an additional APEX mouse whose original software reads
  battery correctly. Exact physical model and reference traffic pending.
- Hardware acceptance: collect redacted target transactions and compare
  official app against our capture; regress prior APEX receivers and sleep/wake.
- No claim that the battery compatibility defect is fixed.

## Individual device alerts — beta.38 candidate

- beta.37 merged as aaf165abab7addf3a537641f126fde1b6eff9d4c; release
  workflow 45064435127 PASS, Latest and six release assets confirmed.
- PR #50 initial Windows CI 45064447976 and macOS CI 45064448135 PASS.
- Final beta.38 metadata CI and actual UI/notification acceptance pending.
- Test global inheritance, distinct receiver overrides, AULA mute/reset,
  global master switch, persistence, charging hysteresis and unchanged
  Bluetooth/disconnect behavior. Diagnostic APEX hardware work remains open.

## Individual polling intervals — beta.39 candidate

- beta.38 release workflow 45066102066 PASS, Latest and six assets verified.
- Initial PR #51 Windows 45066661421 and macOS 45066661426 CI PASS.
- 24 pure checks cover deadline rules, settings and presentation; actual
  Windows mixed-device timing, sleep and disconnect handling remain unverified.
- Verify 15/30/60/120-second profiles, manual refresh, original timestamps,
  no duplicated history/alerts, AULA last-known presence and Bluetooth priority.

## Battery analytics — beta.40 candidate

- beta.39 release workflow 45067421661 PASS; Latest and all six assets verified.
- Initial PR #52 Windows 45067489196 and macOS 45067489222 CI PASS.
- Eighteen pure checks exercise stale/insufficient data, charging, gaps,
  endpoint rates and valid observed discharge pairs.
- Physical history review and localized layout acceptance remain pending;
  estimates are conditional and not battery health or physical cycles.

## beta.42 — multiple BLE and APEX research

- beta.41 release workflow 45074067608 PASS, six assets verified.
- AJ179 owner beta.41 report: 6/6 F7/05 attempts, 100%; local GearHub HAR
  independently reports 100% in all 266 matched F7 pairs.
- PR #54 post-beta.41 CI Windows 45074388934 / macOS 45074388910 PASS.
- Final combined candidate CI and physical two-device BLE acceptance pending.
- Affected AJ159 and working AJ159 full captures and HAR remain outstanding.
  No change to live AJAZZ HID parser.


## November 24 audit candidate — current evidence, not new hardware results

Historical readings above remain unchanged. The current candidate is
not a public release. The affected AJ159 owner report uses 3151:5007
MI_02 FFFF:0002, rev 0002, and has six successful HID transactions with
zero validated battery samples. This is a distinct observation from
historical AJ159 rev 0300 readings. The AJ179 reference includes a 100
field with the readiness flag clear; the conservative current shared
decoder rejects that field as fresh. Do not identify either mouse from
receiver revision, and do not infer physical compatibility from CI.

| Candidate capability | Software evidence | Outstanding field evidence |
| --- | --- | --- |
| Shared F7 decoder and downstream history/alerts | PR #119 Windows 45372850872, Universal 45372851026, High Sierra 45372850906 PASS (20 fixture rows) | Two actual charge levels per mouse, wake/sleep/replug |
| Isolated routine polling on three platforms | Session-only flag, synthetic watchdog/cancellation and exclusion tests | Normal vs isolated P01–P13, resource cost including children |
| AULA sleep continuity and presentation | Cached/unknown states, 24-hour display-only cache, policy tests | Awake/sleep/recovered A01–A14 evidence |
| AJ179 BLE and USB priority | Historical manual fresh 83% GATT read; automatic policy tests | Actual automatic handover, expiry, recovery |
| Windows Device Manager | Localized minimum-size smoke tests | Keyboard and interactive DPI 125/150/200% |
| High Sierra | Intel 10.13-targeted build exercised on macOS 15 Intel CI | Actual 10.13 iMac acceptance |

See ISOLATED_POLLING_ACCEPTANCE.md and
AJ159_APEX_F7_HAR_FORENSICS_20261123.md. All field items are pending
for the current candidate unless a separately labeled observation exists.
