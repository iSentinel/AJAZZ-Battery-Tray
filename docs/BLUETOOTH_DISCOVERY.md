# Bluetooth Battery Support — Research and Acceptance Plan

## Confirmed hardware capability

AJ179 APEX and AJ159 APEX are tri-mode mice: 2.4 GHz, USB-C wired
and Bluetooth. However, support for Bluetooth pairing **does not prove**
the mouse exposes a standard GATT battery-level characteristic.

References:
- AJ179 series official product:
  https://ajazzbrand.com/products/ajazz-aj179-series-mouse
- AJ159 series:
  https://ajazzstore.com/products/ajazz-aj159-series
- Bluetooth SIG assigned numbers:
  https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Assigned_Numbers/out/en/index-en.html

## Windows Bluetooth retry backoff (v0.3.0-beta.18)

Automatic direct-GATT reads have a normal interval of one minute.
After one consecutive failed read the interval is two minutes; after two
failures it becomes five minutes, and after three or more failures it is
limited to ten minutes. Successful fresh direct-GATT reads reset the
schedule to one minute. Unavailable readings remain unavailable rather
than showing a stale battery percentage.

The Windows tray offers **Refresh Bluetooth battery now** for a manually
selected paired mouse. This bypasses the retry delay but does not
enumerate, scan, pair, or write any Bluetooth characteristics.
It remains disabled when the USB/2.4 GHz receiver is present, the fallback
was not explicitly enabled, or another GATT read is in progress.
The manual action is intended to check the mouse after wake/reconnect.

The backoff policy has hardware-independent scheduling tests. Actual
battery and sleep/wake responsiveness must still be checked on the
physical AJ179 APEX.

## Windows monitoring diagnostics (v0.3.0-beta.17)

The tray shows whether the opt-in Bluetooth fallback is **off**, waiting
behind a connected USB receiver, actively checking a GATT battery reading,
showing a fresh percentage or currently unavailable. Unavailable status
includes the number of failed consecutive reads and the local time of the
last successful GATT reading.

**Copy Bluetooth monitor status** writes a short, human-readable report to
the clipboard with the app version, USB receiver state, displayed transport,
last displayed percent, pending request state, consecutive failures, and
UTC times for the last attempted and last successful GATT reads.

It never copies the mouse's Bluetooth address, Windows device instance ID,
serial number or raw Bluetooth payloads. The in-memory counters and times
are reset when fallback is disabled or a new session starts. The report
supports hardware acceptance without background data upload.

## Nonblocking Windows monitoring (v0.3.0-beta.16)

The USB/2.4 GHz receiver poll now updates the tray **before** starting any
automatic Bluetooth request. A slow or timed-out GATT operation no longer
holds the USB poll timer or delays its screen/icon update.

Bluetooth requests are still opt-in and limited to a single active request
at a time. Enabling, disabling or changing the selected Bluetooth mouse
increments a session generation. A result from an older generation is
ignored instead of changing the new session's battery indicator.

A completed GATT read updates the tray **without** re-recording an extra
USB history sample or triggering duplicate USB connection/low-battery alerts.
The Windows UI remains responsive while Bluetooth is pending. Physical
handover, sleep/wake and delayed-response tests are still necessary.

## Windows source and reconnect hardening (v0.3.0-beta.15)

Automatic Bluetooth fallback now relies on a **typed battery source**:
`DirectGatt`, `WindowsCached` or `Unavailable`. No UI string or label
determines whether a reading is eligible for automatic display.
Only a valid direct GATT response is accepted.

When the receiver is absent and Bluetooth fallback is enabled, the tray
labels the source **Bluetooth**, even if the last reading has expired.
The source shows **unavailable** instead of falling back to a misleading
2.4 GHz unavailable status. Reconnecting a USB receiver prioritizes its
reading; a sleeping USB mouse does not show a Bluetooth percentage.
Intentional USB removal does not cause an unrelated disconnect warning
while the Bluetooth fallback session is active.

Tests cover typed result trust, cached values, unknown/stale readings, source
priority, and disconnect notification behavior. Real hardware switching and
sleep/wake still need field validation.

## Confirmed AJ179 APEX hardware observation (2026-11-06)

On a physically paired AJ179 APEX in Windows, the user selected the mouse
inside **Check paired Bluetooth battery...** and observed
**AJ179 APEX 83% — Fresh GATT Battery Level (2A19) read**.
This establishes that at least this AJ179 APEX configuration exposes the
standard GATT Battery Service, rather than only Windows's cached battery.

It does **not** validate AJ159 APEX, another firmware revision, Mac BLE
access, Bluetooth sleep/wake or source handover.

## Opt-in Windows tray fallback (v0.3.0-beta.14)

After selecting the mouse and successfully reading a **fresh** standard
GATT Battery Level (0x2A19), the dialog enables **Use this mouse in tray when
2.4 GHz receiver is absent (this session)**. User consent is explicit;
it is disabled by default and reset at program restart.

- The exact selected paired device ID is held **in memory only**.
- No automatic Bluetooth discovery, pairing, GATT writes or device scanning.
- The USB receiver takes priority, including when the USB-connected mouse
  is asleep; BLE is queried only if the USB receiver itself is absent.
- The minimum automatic Bluetooth polling interval is 60 seconds.
- Each Bluetooth read has a 12-second UI timeout. Unavailable or stale
  values are replaced by **unknown**, never by a fabricated percentage.
- Windows cached BatteryLife values are *not* accepted as automatic fallback.
- History and low-battery alerts still cover the 2.4 GHz path only.
- A tray menu item disables fallback without restarting; disabling clears
  the selected identifier and latest value from memory.
- Actual unplug/replug and sleep/wake behavior still needs hardware tests.

## Windows discovery diagnostics (v0.3.0-beta.13)

The manual Windows inspector independently queries the paired-only BLE and
Classic endpoints, with an eight-second bound on each transport. If one query
fails, the other can still return devices. The UI shows counts for each
transport and a short, sanitized error type. **Copy lookup summary** copies
only counts, the selected filter mode and error names; it does not copy
Bluetooth addresses, serial numbers, or system device instance IDs.

This is a diagnostic improvement, not confirmation that a specific AJAZZ
Bluetooth device exposes GATT Battery Service. The user still selects the
paired device and manually requests Battery Level. A Windows-cached value
is labelled as potentially stale.

## Windows discovery fix (v0.3.0-beta.12)

Some Bluetooth mice are reported by Windows as Classic rather than LE, or
appear under an unexpected device name. Other Windows paired endpoints can
have inconsistent `Pairing.IsPaired` metadata despite the paired-only AQS
selector. An extra LE-only and name-only filter incorrectly hid the mouse.

The Windows dialog now:
- Queries **paired-only Bluetooth LE and Bluetooth Classic** association
  endpoints; no unpaired discovery or pairing operation takes place.
- Defaults to names containing AJAZZ/AJ159/AJ179, and offers an explicit
  **Show all paired Bluetooth devices** option when the mouse has a
  different Windows name.
- Does not apply an additional unreliable `Pairing.IsPaired` check.
- Tries an uncached GATT read only for LE endpoints. If it is unavailable,
  uses Windows's numeric `System.Devices.BatteryLife` property when present.
- Labels Windows-reported battery as cached, which may be stale, and rejects
  its special unknown value 101 and all values outside 0–100%.
- Keeps Bluetooth reads manual and separate from the 2.4 GHz tray status,
  battery history and notifications; no device identifiers are persisted.
- Still requires field testing on the physical mouse and Windows version.

## Experimental Windows manual inspector (v0.3.0-beta.9)

The tray option **Check paired Bluetooth battery...** now offers explicit
read-only inspection of an already paired BLE device. It enumerates paired
Bluetooth LE devices only, filters plausible AJAZZ names, requires the user to
select the entry and press **Read selected battery**, then reads standard
GATT Battery Service (0x180F) / Battery Level (0x2A19) uncached.

- A value is accepted only if it is one byte in the range 0..100.
- Absent service, sleeping device, access denial or invalid payload produces
  a clear unavailable status, **not an invented percentage**.
- Device instance IDs are held in memory only; no address or UUID is logged.
- Nothing scans unpaired peripherals, pairs devices, or writes a GATT value.
- A BLE value does not overwrite the 2.4 GHz tray icon or battery history.
- **Hardware support is not confirmed** until the actual AJ179/AJ159 is tested.
- The chosen entry is not stored across sessions.
- Windows BLE lookup and read dialogs have bounded UI waits (12s and 15s).
  A timeout means unknown, not 0%. The underlying OS request may still finish
  after the UI stops waiting; no GATT write operation is involved.

## Experimental macOS connected-device inspector (v0.3.0-beta.10)

The macOS menu exposes **Check connected Bluetooth battery...**. On the
user's explicit request, CoreBluetooth checks only peripherals the macOS
Bluetooth stack already reports connected **with Battery Service 0x180F**.
The user selects a likely AJAZZ-named device and requests one read of
Battery Level 0x2A19. It connects to that selected peripheral for the read,
then disconnects its CoreBluetooth session; there is a ten-second timeout.

- No scan API, automatic pairing or periodic reads are used.
- macOS prompts for Bluetooth permission only when the user opens the feature.
- Bluetooth identifiers are kept in memory only and never logged or exported.
- The selected peripheral is not stored or merged with 2.4 GHz status.
- If CoreBluetooth doesn't expose the HID mouse or Battery Service, the
  result is explicitly unknown; **absence does not imply 0%**.
- This implementation compiles in CI but needs a physical Mac acceptance test.

## Standard read-only discovery path

Bluetooth SIG Battery Service is `0x180F`; the classic Battery Level
characteristic is `0x2A19`. Modern Battery Service versions may expose
additional characteristics: do not interpret arbitrary bytes as a percent.

A read-only Battery Level response should have the documented encoding and
a percent between 0 and 100. Do not assume device-specific firmware uses
this standard until a real bonded mouse is inspected.

Expected implementation choices:

- **Windows:** use the Windows Bluetooth LE device enumeration and GATT APIs.
  The application must use only a user-approved, already-paired AJAZZ mouse.
- **macOS:** CoreBluetooth device discovery and read-only GATT characteristic
  lookup; ask for OS Bluetooth permission only on explicit opt-in.
- Do not automatically pair, scan indefinitely, write GATT characteristics,
  issue HID settings commands or probe unrelated nearby Bluetooth devices.
- Never upload a Bluetooth address, device UUID, serial number or scan result.

## Matching and de-duplication

1. Discover a user-selected AJAZZ AJ179 APEX or AJ159 APEX paired device.
2. Confirm a standard Battery Service exists and that Battery Level is readable.
3. Attribute the reading only to that selected device: a matching name is not
   sufficient to merge it with a 2.4 GHz receiver automatically.
4. If the 2.4 GHz receiver is active and has a valid reading, prefer it.
5. When receiver is absent, show a separately labelled Bluetooth reading only
   for the explicitly selected paired mouse.
6. If no verified battery value is available, show **unknown**, never 0%.
7. Use the existing 20/10/5 alert policy only after a fresh, valid reading.

## Hardware acceptance before enabling BLE UI

- [ ] Confirm actual advertised/pairing name on AJ179 APEX in Bluetooth mode.
- [ ] Confirm actual advertised/pairing name on AJ159 APEX in Bluetooth mode.
- [ ] Check whether GATT Battery Service `0x180F` is present on each model.
- [ ] If present, verify read access and Battery Level `0x2A19` encoding.
- [ ] Compare battery percentage with 2.4 GHz dock readings on the same mouse.
- [ ] Test sleep/wake, reconnect and switching to and from 2.4 GHz.
- [ ] Verify notification thresholds and that unknown data never raises alerts.
- [ ] Confirm no scan occurs until user enables Bluetooth discovery.
- [ ] Confirm dual transport mode does not duplicate the same mouse.
- [ ] Validate on real Windows and macOS installations.

Do not claim Bluetooth battery support merely because the mouse supports
Bluetooth connectivity. This task remains experimental until the above
hardware evidence is available.

## Privacy and safety

Only process explicitly selected, paired mice. Do not log or expose Bluetooth
MAC addresses or system-generated device identifiers. Do not put BLE
advertisement contents into diagnostic report or GitHub issues. Never write
to a GATT characteristic in this battery-monitoring workflow.
