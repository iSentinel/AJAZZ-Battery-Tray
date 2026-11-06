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
