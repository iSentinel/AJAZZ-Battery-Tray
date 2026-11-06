# AJAZZ APEX — Safe Windows Dock Protocol Capture

This guide documents how to collect evidence for future **RGB, display image,
GIF, DPI and polling-rate** features. It does not enable those commands in
AJAZZ Battery Tray.

**Do not send guessed HID commands.** Use the official vendor utility on
your own device, change one reversible setting, capture the USB exchange,
and return the setting to its original value.

## Tools and environment

- A Windows 10/11 system with a connected AJAZZ 8K dock / USB receiver.
- Wireshark with USBPcap installed from trusted upstream sources.
- The official AJAZZ configuration utility for your exact model.
- A spare USB keyboard/mouse if possible. USBPcap is a kernel capture driver
  and installing it may require a restart or interfere with input devices.
- A text note file with the device model, connection mode, firmware version
  as *reported by the vendor utility*, and which setting was changed.

Reference:
- https://wiki.wireshark.org/CaptureSetup/USB
- https://www.wireshark.org/docs/dfref/u/usb.html
- https://github.com/liquidctl/liquidctl/blob/main/docs/developer/capturing-usb-traffic.md

## Preparation

1. Save the current mouse profile using the vendor utility if supported.
2. Close AJAZZ Battery Tray and any other application polling the same HID
   interface. Only the vendor utility should control the dock.
3. Check that the receiver is physically present. On Windows PowerShell:

   ```powershell
   Get-PnpDevice -PresentOnly |
       Where-Object InstanceId -Match 'VID_3151&PID_5007' |
       Select-Object FriendlyName, Class, Status
   ```

4. Install Wireshark and the USBPcap component if needed. Reboot if the
   installer asks. Do not change kernel security settings to enable capture.
5. In Wireshark, choose the USBPcap interface corresponding to the receiver
   USB controller / root hub. If unknown, disconnect/reconnect the receiver
   and look for its enumeration to identify the hub.
6. Keep the capture short and avoid using unrelated USB devices. Raw USB
   captures may contain private data from *other* devices on the same hub.

## Capture sequence: one setting at a time

1. Record the initial state, e.g. RGB effect "Off", DPI stage, clock,
   selected display page, firmware version shown in the official utility.
2. Start capturing on the correct USBPcap interface.
3. In the official utility, change **only one** reversible setting.
4. Wait for the device display/effect to reflect the change.
5. If the utility offers a readback, inspect the setting again.
6. Return the setting to its previous value while still capturing.
7. Stop capture and record the exact before/after/restore actions and
   timestamps. Use a separate capture file for each independent setting.
8. Do **not** test device reset, firmware updates or bootloader commands.

Suggested captures (each independent): dock-clock sync, RGB on/off,
RGB brightness, next display page, an image upload already supported by
the vendor utility. GIF transfers may be large: do them only after simple
clock/RGB round trips have been examined.

## Inspecting the capture

In Wireshark, first identify the correct device address and USB bus. Filter
to that bus and device for the actual exchange; these numbers can change
on reconnect. Inspect **control transfers**, including requests with
`usb.setup.bRequest == 0x09` (HID SET_REPORT) and
`usb.setup.bRequest == 0x01` (HID GET_REPORT), when present.

Useful supported Wireshark field names include `usb.setup.bRequest`,
`usb.setup.wValue`, `usb.setup.wIndex` and `usb.setup.wLength`.
Packet payload bytes, direction, transfer length and URB status matter.
Do not assume the first byte is a firmware command: USB/HID report IDs
and Windows/macOS framing differ.

For each request/response, record:

| Field | What to document |
|---|---|
| Timestamp | Relative to the one setting changed |
| Direction | Host to dock / dock to host |
| USB setup | bRequest, wValue, wIndex, wLength |
| HID interface | Confirm vendor usage FFFF:0002 and receiver 3151:5007 |
| Report | Report ID, length, command bytes, redacted payload |
| Response | Status, acknowledgement or readback |
| Reversal | Captured command that restores the original value |

A payload must be matched with its associated USB transfer response, not
judged only by a single byte in isolation.

## Redaction and sharing

**Never upload raw multi-device USBPcap captures to a public issue.** They
can include serial numbers, device addresses, keyboard activity and unrelated
USB payloads. Use a local filtered copy containing only the relevant dock
exchange; remove identifying descriptors and unrelated packets. If you cannot
verify adequate redaction, provide only the textual table above.

Do not include personal identifiers, serial numbers, Bluetooth addresses,
raw timestamps unrelated to the test, or local account details.

## Acceptance gates before adding an opcode to AJAZZ Battery Tray

- Confirm model, firmware, receiver interface and full packet framing.
- Observe the same setting changed and then reverted by the official utility.
- Separate USB report headers from vendor payload.
- Confirm status / readback from the real dock, not just host success.
- Test wake/reconnect and recovery from a failed transfer.
- Add model-specific guards, explicit UI confirmation, and parser tests.
- Keep the default HID write allowlist at commands `0xF7` and `0x28` until
  every requirement is satisfied; do not simply copy speculative opcodes.
- Never add firmware, bootloader, unsafe profile-commit or key-matrix writes.

See [Dock Protocol Safety Matrix](DOCK_PROTOCOL_SAFETY.md) and
[Hardware Acceptance Checklist](HARDWARE_ACCEPTANCE.md).
