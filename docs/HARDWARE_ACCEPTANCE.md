# Hardware Acceptance Checklist

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

## Known limitations

- CI passing **does not** prove USB reports, clock writes, notification
  permission, or login item registration work on a particular real Mac.
- AJ159 APEX has not yet been tested on this project's hardware.
- Charging detection, Bluetooth, RGB, GIF uploads and device configuration
  are not enabled.
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
