# GearHub F7 status investigation — 2026-11-22

## Source snapshot

- Public Web driver: https://qmk.top/v4/ (page title GearHub).
- Client module inspected by static HTTP download, without running its code:
  https://qmk.top/v4/js/index.58137dcb.js
- Module size: 2,845,916 bytes; SHA-256:
  7dfb0851189a6287c1a03b36dc785237adc905b1cf10ac136a751c12e6e2d0b1
- Relevant methods: ___dongleCheck24GStatusByF7, ___commonFeature,
  ___sendFeature, ___getFeature and WebHID sendFeature/getFeature.
- Registry has multiple AJ159 and AJ179 APEX entries. The AJ159 APEX
  dongle entry 3347 and generic AJAZZ APEX entry 3480 share 3151:5007.
  Mouse registry entries 1755, 3346, 3806 (AJ159) and 1852, 3849
  (AJ179) share 3151:4026. Do not equate these registry IDs with USB
  revision or firmware version.

## Wire-format hypothesis, not hardware-confirmed

The web implementation selects the first feature report from its device
metadata, uses its ID for both feature operations, pads the F7 payload to
the report count, and uses a 10 ms interval before the write and read.
Its WebHID wrapper removes one leading byte for a nonzero report ID before
passing the resulting payload to the status decoder. It polls every 2 sec.

| Field | GearHub payload offset | Hypothesized Windows buffer offset |
|---|---:|---:|
| Ready to read | 0 | 1 |
| Keyboard battery | 1 | 2 |
| Mouse battery | 2 | 3 |
| Keyboard link | 3 | 4 |
| Mouse link (0 online) | 4 | 5 |
| Ready to send | 5 | 6 |
| Device type mask (2 mouse, 3 both) | 6 | 7 |
| RF boot flag | 8 | 9 |

The existing Windows parser requires report ID 05 and zero offsets 1/2.
The vendor logic does not require those two payload fields to be zero
before reading mouse battery; therefore a flag or keyboard battery could
explain a rejection. The different report-ID selection and 10 ms timing
are also investigation leads, not confirmed causes. Do not change the
live parser, command allowlist, or normal timing before hardware evidence.

## Compare beta.41 captures without any new binary

Run locally against reviewed plain-text full comparison reports:
```sh
python3 tools/compare_apex_reports.py AJ179-working.txt AJ159-working.txt AJ159-problem.txt
python3 tools/test_compare_apex_reports.py
```

The analyzer reads the fresh protocol matrix only, counts returned buffers,
and prints old parser results plus candidate values under conservative
status checks. It does not read USB or send anything to the network.
A matching candidate is not proof of alignment, freshness, or charge.
Compare against the web driver's displayed charge and repeat at another
known value before proposing a live parser change.

## Owner data collection

Use the same beta.41+ full report on all three devices. Close GearHub and
the desktop vendor utility while the tray app records its report. Then exit
the tray app and load qmk.top/v4 in a WebHID-capable browser. Select only
the target receiver and record the displayed charge and model if available.
Do not change settings or update firmware during the comparison. A browser
screen showing charge is a reference observation, not a USB traffic capture.
If the web driver also fails, record that outcome. No whole-bus capture or
private identifiers are needed for the initial comparison.
