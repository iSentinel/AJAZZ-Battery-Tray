# Hardware Acceptance Checklist

The [Hardware Validation Matrix](VALIDATION_MATRIX.md) distinguishes
features verified on real hardware from CI-only implementation. Start there
before marking a scenario as physically validated.

For the development-only isolated polling modes, use the separate
[Isolated Polling Acceptance](ISOLATED_POLLING_ACCEPTANCE.md) matrix.

This checklist records tests of **physical AJAZZ APEX hardware** separately
from the GitHub Actions compile, packaging, and unit-test results.

The targeted AJAZZ USB receiver is **VID 3151, PID 5007**. A single
AJ179 direct BLE reading was historically verified; current candidate
continuous monitoring, other variants and transport handover remain pending.

## Before testing

1. Use the exact reviewed CI candidate specified in [candidate acceptance](CANDIDATE_ACCEPTANCE.md). Public beta.60 does not include the new features.
2. Close the official AJAZZ utility and Halo Battery to avoid competing
   HID feature requests.
3. In the tray/menu bar, click **Copy diagnostic report**.
4. Save that report in the test notes. It has app version, OS, receiver product
   name and safe HID data, **not serial numbers or device paths**.
5. Record model (AJ179 APEX or AJ159 APEX), connection mode, dock type,
   approximate charge and any relevant firmware version from the vendor app.
   Do not infer firmware from USB `bcdDevice`.

## Windows test matrix

| Test | Procedure | Expected result |
|---|---|---|
| Receiver connected | Start app with 8K receiver | Percentage appears, not fake 0% |
| Battery comparison | Compare with vendor utility, one app at a time | Same reported percent |
| Mouse sleep | Leave mouse idle until it sleeps | Unknown state is acceptable; no false 0% |
| Mouse wake | Move mouse after sleep | Reading resumes without app restart |
| Receiver unplug | Unplug receiver twice over polling interval | Disconnected, opt-in warning once |
| Receiver replug | Reconnect receiver | Charge reading resumes |
| Dock RTC | Click Sync dock time now | Date and time visually match PC |
| History | Open Battery history, choose 24h/7d/30d | Chart and CSV record state transitions |
| Low charge | Wait for natural 50/25/10% thresholds | At most one alert per threshold |
| Installer | Install to Program Files, then uninstall | Start menu and uninstall entry work |

## macOS test matrix (experimental)

| Test | Procedure | Expected result |
|---|---|---|
| Universal app | Open on Intel or Apple Silicon | Menu bar icon appears |
| HID read | Connect 8K receiver | Percent or explicitly unavailable |
| History | Open Battery history chart | 24h/7d/30d chart; missing readings are gaps |
| Local alerts | Enable notification menu options | macOS asks permission only on opt-in |
| Receiver disconnect | Unplug receiver after a valid reading | One opt-in warning after two missing polls |
| Start at login | Enable via menu; review Login Items | OS status enabled or requires approval |
| Dock RTC | Trigger Sync dock time now | Clock on physical dock changes correctly |
| Diagnostics | Copy diagnostic report | Report contains no serial number or HID path |

## Verified field evidence

- **2026-11-06, Windows, AJ179 APEX, Bluetooth:** device appeared in
  **Check paired Bluetooth battery...** and returned
  **83% — Fresh GATT Battery Level (2A19) read**. This confirms one direct
  GATT reading on real AJ179 APEX hardware; it does not prove periodic
  polling or receiver handover. No identifying device data was recorded.

## Independent Bluetooth monitoring (Windows)

Use the current [candidate acceptance matrix](CANDIDATE_ACCEPTANCE.md)
for persistent consent, restart, independently scheduled reads, cached
display, explicit linking, opt-out and multiple devices. This supersedes
the historical session-only fallback behavior.

A USB enumeration error must remain unknown, not confirmed absence,
and must not generate a false USB disconnect alert. It does not inhibit
an independently opted-in BLE monitor. A cached BLE value must be
marked stale, never trigger a new alert or become fresh API telemetry.
Do not disable USB controllers or remove drivers to induce an error.

## Known limitations

- CI passing **does not** prove USB reports, clock writes, notification
  permission, or login item registration work on a particular real Mac.
- Historical AJ159 Windows readings exist (including rev 0300), but
  the affected AJ159 rev 0002 returned 0/6 validated battery replies in
  the November 23 evidence. Current candidate compatibility is not
  established; do not infer model identity from receiver revision.
- Charging detection, automatic USB/BLE identity matching, RGB, GIF uploads
  and device configuration are not enabled. Explicit local BLE consent
  is persistent; it is not automatic opt-in.
- If the receiver is present while the mouse sleeps, that is not counted
  as a disconnect alert.
- Do not send speculative HID configuration or firmware opcodes.

## Reporting a result

Open the [hardware validation issue form](https://github.com/iSentinel/AJAZZ-Battery-Tray/issues/new?template=hardware-validation.yml) with:

- Version, OS, mouse model and connection type.
- The **Copy diagnostic report** output (inspect before sharing).
- Which test passed or failed, with reproducible steps and any visible error.
- Whether app log or battery-history CSV shows the expected state transitions.
- A cropped photo of dock time only if needed; remove personal information.

Keep raw USB captures and serial numbers private until they have been redacted.
