# AJ159 APEX shared receiver / F7 battery evidence — 2026-11-23

## Provenance and privacy

Owner supplied three extended Windows 11 diagnostics, one beta.59
`--hid-diagnose` report, and two GearHub V4 HAR files:
`qmk.top1.har` and `qmk.top2.har`. The HARs include local
`http://127.0.0.1:3838/hid.HidService/` gRPC-web-text
Feature Reports through the GearHub helper. Do not commit raw
HARs: they contain private Windows HID interface paths, local
device/session identifiers, configuration content and full vendor
payloads. Only aggregate, sanitized facts appear here.

## Observed AJ159 2.4 GHz receiver

- Owner confirms the physical mouse is AJ159, but beta.59 labels
  shared `3151:5007`, `bcdDevice=0002` as AJ179.
- Local diagnostic found exactly one matching `MI_02`,
  `Usage FFFF:0002`, feature length 65.
- Existing `SET F7 / GET 05` completed all six 65/67-byte
  and 30/100/250 ms probes with Win32 success but 0/6 valid levels.
- All six responses have the prefix `05 00 00 00 01 00 01 02`.
  The leading `05` is the Windows report ID, not battery.
- The full report revealed the same stable response pattern as
  the safe redacted trace.

## New GearHub forensic observations

- `qmk.top1.har`: 313 network entries, including 106
  `SendFeatureReport` and 90 `GetFeatureReport` gRPC-web POSTs.
- `qmk.top2.har`: 773 entries, 171 sends and 142 gets; this
  includes overlapping activity, so counts must not be summed
  as independent captures.
- GearHub sends `00 F7 ...` as a 65-byte feature request, and
  asks the local HID bridge for a report with initial ID `00`.
  Our app uses `00 F7 ...` but requests report ID `05`.
  That difference is not yet proven to change the measured field.
- The visible GearHub JS status routine
  `___dongleCheck24GStatusByF7` strips the leading report ID,
  then reads `isCanRead` from payload byte 0, mouse battery
  from byte 2, mouse-online from byte 4, send-capable from byte 5,
  device slot from byte 6 (mouse 2 or combined 3) and RF boot
  from byte 8.
- In immediately adjacent F7/GET pairs, 77 (first HAR) and
  114 (second HAR) return mouse slot 2 and battery field zero.
  The read-available flag is set in 16 and 26 respective pairs,
  but battery remains zero even then. These are temporal
  correlations, not a promise of exclusive HID execution.
- GearHub's bundled catalog has `AJ159 APEX`, dongle entry
  `id=3347, VID=12625 (3151), PID=20487 (5007)`, but
  multiple unrelated device entries share that VID/PID.
  The descriptor and USB revision cannot by themselves prove
  a specific model.

## Changes and release gate

- Remove hardcoded AJ179 certainty from revision 0002 on the
  application label and Windows PnP preview. Keep the owner's
  existing per-receiver alias support for a user-confirmed name.
- Parse the recognized F7 mouse status conservatively after the
  Windows report ID. Accept percent only when readable=1,
  mouse online=1, canSend=1, RF boot=0, slot mouse/combined,
  and battery is in 1..100.
- Preserve a legacy compact reply parser for non-F7 framing.
- Never present 0% or fabricate a missing value. No additional
  feature requests or new vendor commands were introduced.
- The synthetic test for a verified 83% response demonstrates
  algorithm behavior, **not** actual AJ159 battery compatibility.

## Pending owner test

Once beta.60 is available, repeat a live `--hid-diagnose`
capture immediately after waking AJ159. If the F7 battery
field remains zero, the outcome must stay UNKNOWN, even if the
USB receiver is available and sends/receives successfully.
Check battery with manufacturer software and/or opt-in
Bluetooth GATT separately; only actual nonzero verified data
can close the hardware battery acceptance.
