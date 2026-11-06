# DPI and Polling Rate — Read-only Protocol Research

**Status:** documentation and candidate identification only.
**No new HID requests or writes are enabled in AJAZZ Battery Tray.**

The aim is to expose the active DPI stage and polling rate **only after**
a non-mutating, model-specific read/response exchange is verified on real
hardware. The application's validated HID write allowlist still accepts
only the telemetry poll `0xF7` and dock RTC sync `0x28`.

## Source and hardware applicability

An independent reverse engineering of the official AJAZZ control stack
documents related command families in:
- [AJ-series opcode table](https://github.com/Aiacos/ajazz-control-center/blob/develop/docs/protocols/mouse/aj_series_opcode_table.md)
- [AJ-series vendor analysis](https://github.com/Aiacos/ajazz-control-center/blob/develop/docs/protocols/mouse/aj_series_vendor.md)

These are **third-party protocol notes**, not a complete specification for
our physical AJ179 APEX on USB receiver `3151:5007`. The reverse engineering
also discusses AJ159 wired `3151:5008` and other receivers. Do not assume
model-specific results carry over between USB interfaces.

## Candidate read-side operations (not yet approved)

| Setting | Vendor GET opcode | Documented response | What remains unverified |
| --- | --- | --- | --- |
| Firmware revision | `0x80` | uint16-LE at payload bytes 1..2 | Correct framing and model/firmware semantics |
| Active profile | `0x85` | profile index in payload byte 1 | Valid profiles and safe request form |
| Polling rate | `0x84` | coded rate rather than a raw Hz count | Response byte offset, mapping and receiver-specific capabilities |
| DPI stages | `0xD4` | active stage at payload byte 2; enabled count at byte 3; eight uint16-LE values at bytes 8..23 | Full 64-byte response and report-ID offset on physical receiver |
| Mouse options | `0xD3` | vendor notes include rate code at payload byte 9 and LOD at byte 52 | Actual response layout and unknown status bits |

The vendor's rate-code table describes `0x08`→125 Hz, `0x04`→250 Hz,
`0x02`→500 Hz, `0x01`→1000 Hz, `0x84`→2000 Hz,
`0x82`→4000 Hz, and `0x81`→8000 Hz **on supported SKUs**.
These are candidate values, not measured capabilities of an AJ179 8K dock.
Do not label an unknown response `8000 Hz` based on its byte pattern alone.

### Critical transport warning

A command named `GET` in vendor code does **not** necessarily mean a
pure USB HID `GetFeature` with no host-to-device transfer. The original
client may issue a `SetFeature` request carrying the GET opcode and then
call `GetFeature` to retrieve its response. That host-to-device request is
a HID write at the transport level, regardless of its semantic name.

**Do not expand `HidFeaturePolicy` to permit `0x80`, `0x84`,
`0x85`, `0xD3` or `0xD4` without a hardware-confirmed harmless
round trip, error response and recovery path.** This research does not
authorize a speculative probe.

## Evidence collection with the original utility

Use the existing [safe dock capture guide](DOCK_CAPTURE_GUIDE.md). Gather
separate, short and locally filtered traces:

1. Confirm exact mouse model, Windows version, 2.4 GHz receiver VID/PID,
   HID vendor usage `FFFF:0002`, and firmware version reported by the
   official utility. Do not publish serial numbers or device IDs.
2. Close AJAZZ Battery Tray and other competing HID utilities. Record the
   current DPI stage and polling rate from the official software.
3. Capture the utility **opening the DPI screen without changing anything**.
   Identify requests, report IDs, response lengths and whether all bytes
   are stable across two reads.
4. With the official utility, change only one reversible DPI stage, capture
   the setting and the **subsequent readback**, then restore the prior stage.
5. In a separate capture, inspect polling-rate display/readback before and
   after changing a supported rate using the official utility. Restore it.
6. Distinguish the physical receiver and its HID interfaces from the wired
   mouse PID. Disambiguate payload indices from Windows report-ID framing.
7. Produce a redacted table listing candidate opcode, direction, report ID,
   response length, observed fields, user-visible value, and restoration.
   **Never post an unredacted multi-device USBPcap file.**

No direct HID request needs to be sent by this project's code during this
evidence-gathering stage.

## Implementation gates

- [ ] Real AJ179 APEX 2.4 GHz request/response captured for each candidate.
- [ ] Passive observation confirms the read does not change mouse settings.
- [ ] Windows report-ID framing and byte offsets verified (including errors).
- [ ] Current DPI stage, enabled count, values and polling rate cross-checked
      with the official utility across at least two distinct states.
- [ ] Receiver limitations per mode and model documented (not inferred).
- [ ] Parser developed from **captured real responses** with negative tests.
- [ ] Any required host-to-device request separately reviewed and approved.
- [ ] USB disconnect, sleep/wake, and device failure restore unknown status
      without writing configuration or affecting unrelated HID devices.
- [ ] AJ159 and macOS remain experimental pending their own hardware evidence.

Until these gates pass, do not display guessed DPI, polling, firmware or
LOD values. Do not implement mouse-profile writes, RGB/GIF upload, reset,
key-matrix, OTA or bootloader commands.

## Safety context

The vendor analysis identifies `0x50` as a mouse **key-matrix write**,
not a generic save/commit operation. Other mutating operations include
`0x04` (polling-rate setter), `0x53` (omnibus settings), and
`0x54` (DPI table setter). None belongs in a read-only discovery path.

See [protocol safety matrix](DOCK_PROTOCOL_SAFETY.md),
[hardware acceptance](HARDWARE_ACCEPTANCE.md), and
[implementation validation matrix](VALIDATION_MATRIX.md).
