# Hardware Acceptance Checklist

The [Hardware Validation Matrix](VALIDATION_MATRIX.md) distinguishes
features verified on real hardware from CI-only implementation. Start there
before marking a scenario as physically validated.

This checklist records tests of **physical AJAZZ APEX hardware** separately
from the GitHub Actions compile, packaging, and unit-test results.

Only the compatible **2.4 GHz / 8K receiver (VID 3151, PID 5007)** is
targeted. Other receiver variants and Bluetooth are not yet validated.

## Before testing

1. Download the current installer or macOS ZIP from
   [GitHub Releases](https://github.com/iSentinel/AJAZZ-Battery-Tray/releases).
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
| Low charge | Wait for natural 20/10/5% thresholds | At most one alert per threshold |
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

## Automatic Bluetooth fallback test (Windows)

1. Switch AJ179 APEX to Bluetooth and use Windows to pair it.
2. Select the paired mouse in the tray Bluetooth inspector, then click
   **Read selected battery**. Confirm **Fresh GATT Battery Level**.
3. Explicitly enable **Use this mouse in tray when 2.4 GHz receiver is
   absent (this session)**. Close the inspector if desired.
4. With the USB/2.4 GHz receiver removed, verify the tray label shows
   **Bluetooth** and a plausible percent; wait more than 60 seconds.
5. Plug the USB receiver back in: the tray must prioritize **2.4 GHz**,
   never silently merge both sources. If USB mouse sleeps, show unknown,
   not a stale Bluetooth percentage.
6. Unplug receiver and allow Bluetooth to disconnect/sleep. The app must
   show unavailable after a failed/expired read (maximum 120 seconds).
7. Select **Disable Bluetooth tray fallback** and confirm there are no
   further automatic GATT requests. Restart the app; fallback must be off.

## Asynchronous Bluetooth response test (Windows)

1. Enable Bluetooth fallback after a fresh manually verified 2A19 read.
2. While GATT polling is delayed by a sleeping mouse, reconnect the USB
   receiver. USB battery reporting should update on its regular interval,
   without waiting for the 12-second Bluetooth timeout.
3. Disconnect the USB receiver and allow an automatic BLE read to begin.
4. Disable Bluetooth fallback before the BLE response arrives. The late
   response must not update the tray or re-enable fallback.
5. Select and verify the mouse again. Pending results from the previous
   Bluetooth session must not update the new session.
6. Confirm no duplicate USB history rows or low-battery notifications are
   produced by completion of the asynchronous Bluetooth request.

## Bluetooth sleep/wake and retry backoff (Windows)

1. Enable Bluetooth tray fallback after a direct manual GATT Battery Level
   read from AJ179 APEX. Remove the 2.4 GHz receiver.
2. Leave the mouse idle until sleeping. Verify the tray shows unavailable
   after failed/expired GATT results rather than a stale percentage.
3. Verify the retry schedule increases after consecutive failures:
   two minutes, five minutes, then a maximum of ten minutes.
4. Wake the mouse and choose **Refresh Bluetooth battery now**. A successful
   fresh GATT read should restore the percent and reset failure counters.
5. Reinsert the 2.4 GHz receiver: the manual Bluetooth refresh menu item
   must become disabled and the tray must prioritize USB status.
6. Disable Bluetooth fallback: neither scheduled nor manual BLE reads
   should run until a newly verified, opted-in session starts.

## Bluetooth diagnostic report

With the opt-in Bluetooth fallback enabled on Windows, use **Copy Bluetooth
monitor status** in the tray menu after (1) a fresh 2A19 reading,
(2) mouse sleep or Bluetooth outage, and (3) recovery. Record whether
consecutive failures reset to zero and last-success timestamp advances.
The report contains no Bluetooth address or device instance ID.
Review all copied data before attaching to a public GitHub issue.

## HID enumeration error versus unplug (Windows)

The 2.4 GHz receiver status can be **present**, **absent**, or **unknown**
when Windows reports a HID enumeration error. An unknown result should
keep the battery unavailable; it must **not** be recorded as unplugged,
trigger a disconnect notification, or activate Bluetooth fallback.
Only a confirmed absent USB receiver may activate the opted-in BLE path.
Recheck after a successful enumeration; USB receiver priority must recover.

This behavior has pure unit tests but is **not yet verified under an actual
Windows USB/HID error**. Do not disable USB controllers or remove device
drivers just to reproduce the scenario.

## Known limitations

- CI passing **does not** prove USB reports, clock writes, notification
  permission, or login item registration work on a particular real Mac.
- AJ159 APEX has not yet been tested on this project's hardware.
- Charging detection, automatic persistent Bluetooth device selection,
  RGB, GIF uploads and device configuration are not enabled.
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
