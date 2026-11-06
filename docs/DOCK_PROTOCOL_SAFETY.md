# AJAZZ 8K Dock — Protocol Safety Matrix

A shared VID/PID does not prove identical firmware across APEX variants.

| Operation | Evidence | This app |
|---|---|---|
| Battery status | 0xF7 poll; GET_FEATURE 0x05, tested on AJ179 Windows | Supported |
| Dock RTC | 0x28 + D7 marker, transfer supported Windows/macOS | Experimental |
| Product name | Standard OS HID metadata query | Read-only |
| USB bcdDevice revision | Windows HidD_GetAttributes, not firmware version | Read-only |
| DPI/polling/sensor state | Vendor GET commands; model framing uncertain | Not queried |
| RGB brightness/effects | Public notes, no AJ179 round-trip | Disabled |
| Screen pixels/GIF | 0x25/0x29 and 0x18/0x19 not verified on physical dock | Disabled |
| EEPROM commit | 0x50 can modify button mapping on AJ-series | Forbidden |
| OTA/bootloader | Changes firmware | Forbidden |

## Acceptance gates for any write feature

1. Confirm physical model, firmware and HID collection.
2. Record a vendor-app before/after transaction (USBPcap/Wireshark).
3. Remove serial numbers and other identifying data from captured evidence.
4. Confirm packet framing, checksum, payload and response.
5. Prove read-back and rollback on the same real hardware.
6. Test replugging, sleep/wake and conflict with the vendor utility.
7. Expose settings only after verified recovery and explicit user control.

The application now enforces this at runtime:

- Windows: `HidFeaturePolicy.IsApproved` is called before
  `HidD_SetFeature`, permitting only exact `0xF7` battery polls or
  valid `0x28` clock packets.
- macOS: an equivalent guard validates the command payload before
  `IOHIDDeviceSetReport`.
- Unknown and malformed commands fail closed. No override option exists.

No speculative vendor write opcodes are sent by this application.

## Sources
- https://github.com/Aiacos/ajazz-control-center
- https://github.com/Aiacos/ajazz-control-center/blob/develop/docs/protocols/mouse/aj_series_opcode_table.md
- https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidsdi/nf-hidsdi-hidd_getproductstring
- https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidsdi/nf-hidsdi-hidd_getattributes
