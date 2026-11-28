# AJAZZ Battery Tray engineering and UX review

Reviewed against Windows 0.3.0-beta.60, the universal macOS 13+ app, and the separate Intel High Sierra edition. Source baseline 95cdf35. The field evidence comes from the owner's Windows 11 beta.59 diagnostics and the repository's sanitized AJ159 and AJ179 observations. The Windows logs show one matching collection, a 65-byte feature descriptor and six completed transactions without a validated charge.

## Findings and changes

| Area | User impact in the baseline | Change and regression check |
| --- | --- | --- |
| Windows full HID capture | An indefinitely blocked native read kept ordinary AJAZZ polling stopped. Even a successful capture kept polling paused throughout manual report review. | Run the consented raw capture in a separate process with a 40-second deadline. Transfer the result over a private stdout pipe, resume polling after the child exits, and review the result separately. The published-executable smoke test exercises both a completed reply and a hanging child without touching HID. |
| Windows F7 decoding | A full keyboard-only frame with readable=0, a compact-looking prefix and a nonzero field could fall through to the legacy parser. Malformed flag bytes could produce the same result. | Reserve full frames carrying a recognized slot for slot-aware decoding. Regression fixtures cover stale keyboard and malformed mouse frames. Legacy short layouts remain covered. |
| Both macOS parsers | The compact-only checks could reject a readable mouse report and present an unreadable mouse field as fresh. The two implementations had drifted from Windows. | Use one portable decoder for Swift and Objective-C. Validate the slot and status flags before returning a percentage. Both entry points exercise numbered and stripped replies. |
| macOS receiver state and dock | Failure to open the HID manager appeared as a detected receiver, and an unsupported collection could count as an unplug. A manual sync during an active poll waited for the next timer tick. | Distinguish access failure, unsupported collection and absence. Only confirmed compatible presence permits RTC sync. Process a pending manual request when the current poll finishes. |
| High Sierra alerts and startup | A reading below threshold while alerts were disabled could suppress the first alert after enabling them. Before the first reading the menu claimed the receiver was present. | Mark thresholds after an eligible warning, keep recharge hysteresis, and display a localized checking state until the first result. |
| History and settings | Windows stretched the first and last samples across the chart, so ten minutes of data could look like seven days. A history containing only gaps produced an empty plot on both desktop apps with charts. In Windows the threshold editor could display old overrides while inheritance was checked. | Draw the selected time window, label a period with zero charge measurements, translate the latest absent state, and show the effective global values while preserving unsaved custom choices when toggling back. |

## Hardware result and compatibility trade-off

The affected AJ159 and working AJ179 share VID/PID 3151:5007 and revision 0002. A successful HID transaction and a matching descriptor establish transport availability. Neither identifies the model or validates the charge field. Windows beta.60 already removed the incorrect automatic AJ179 label.

The AJ159 field remained zero in the available captures. A synthetic gated 83% reply exercises the decoder only. The historical AJ179 reference includes a 100 field with readable=0, including 258 of the 266 matched official bridge replies with send=1. The conservative Windows beta.60 rule rejects this as fresh. Aligning the Mac readers with it may replace a previously visible percentage with unknown on that receiver. Hardware acceptance must include **both** mice. An explicit last-reported value with its own provenance and age would be preferable to silently treating an ambiguous field as fresh. Compare with the official utility at two different observed charge levels before changing the live rule.

## Improvements in priority order

1. **Validate the receiver matrix.** Record separate, labeled AJ159 and AJ179 runs after wake, after sleep, and after replug. Record the actual USB field, readiness flag, app state and manufacturer display side by side. Repeat on the Intel iMac. Real readings establish the supported combinations. See [F7 evidence](AJ159_APEX_F7_HAR_FORENSICS_20261123.md) and [AJ179 reference](APEX_GEARHUB.md).
2. **Make the tray explain an unknown reading.** Show connection method, last successful measurement time and one short reason, such as receiver absent, HID access failed, or receiver returned no fresh charge. Display stale data explicitly. Keep alerts and discharge estimates tied to verified samples. AULA already distinguishes cached measurements and provides a model for this interaction.
3. **Reduce Device Manager action density.** The Windows dashboard puts ten buttons in one wrapping row. Keep Refresh and History visible, group rename, color, intervals and alerts under a selected-device settings menu, and move telemetry into Diagnostics. Check keyboard navigation and Russian/Ukrainian text at 125%, 150% and 200% scaling on the minimum window size.
4. **Contain ordinary polling stalls.** The change bounds explicit full-vendor capture. Ordinary synchronous Windows HID reads and the macOS IOKit poll are separate paths. Reuse the worker isolation only after measuring normal-poll startup cost and testing sleep, wake and shutdown. A timeout should stop further I/O for that attempt before starting another.
5. **Consolidate behavioral fixtures.** Run the same versioned, sanitized report corpus against C#, the Apple decoder and offline analysis. Mark a case as physical evidence or synthetic, distinguish legacy interpretation from the current parser, and assert history/notification side effects. Preserve the distinction between 0–100 BLE GATT and the receiver's 1–100 validated HID range.

Visual findings come from the layout and rendering code. The hardware matrix, interactive Windows DPI checks, and an in-place installer upgrade require a separate acceptance run.

## Follow-up review, 25 November 2026

Reviewed the integrated development branch at c105bbf, including per-receiver
presentation, ordinary poll diagnostics, snapshot projection, history storage,
chart summaries and locale changes. The public beta.60 release and draft PR 99
represent different code. The open Apple F7 trace work in PR 265 is separate.

### Evidence and behavior

The owner's two Windows reports from 25 November show a fresh AULA L99 charge
of 70%. The APEX capture contains six completed replies, zero validated
percentages and an unverified mouse field of 99 in all six. The reports identify
a shared rev 0002 receiver. Its model and actual charge cannot be established
from that field. The current Windows code has independent paths for presentation
(including cached or unverified data), history and alert evaluation. Snapshot
projection also distinguishes current charge from last-known values. Keep this
distinction when presenting a dashboard row or a copied diagnostic.

### History and interface defects

| Defect | Reproduction and impact | Correction |
| --- | --- | --- |
| Next observation lost after an interrupted or unterminated CSV row | Append a new percentage after a valid row without a final newline. The concatenated line fails CSV validation and the next retention pass can drop both samples. A malformed tail can also swallow a disconnect event. | The Windows and universal Mac writers delimit the old tail before appending a whole new observation. Native tests exercise a valid tail, a damaged tail, a charge and a disconnect. |
| Universal Mac fails to read Windows-formatted history | The Swift reader split on a newline character and used a whole-second formatter. CRLF rows or Windows fractional UTC timestamps could be skipped, including during pruning. | The reader and pruner recognize newline variants and use the same whole/fractional timestamp decoder. An end-to-end fixture retains a seven-digit timestamp with an explicit offset across an append and a prune. |
| Unreadable history looks like zero observations | A locked Windows file or unreadable Mac CSV produced the same empty plot as a new installation. This can lead the user to investigate the receiver when the failure is in storage. | Distinguish a missing history file from a read failure. Show a localized read error and clear obsolete summaries. A subsequent refresh retries the read. |
| Universal Mac history takes extra work and leaks English labels | The first window open read the file twice, parsing allocated a formatter per row, and a disconnected final reading displayed the raw CSV state. The rightmost axis label used a fixed offset and could clip. | Load once on opening, reuse formatters for the scan, translate the state, and place time labels using their measured width. |

### Priorities after the fixes

1. Obtain a second known charge for the same physical mouse and compare it
   with the manufacturer's display, ready flag and connection state. Record
   exact build and transport. A stable raw 99 by itself is insufficient.
2. Measure chart open and refresh on 20,000 rows at 24 hours, seven days and
   thirty days. Run on Windows and universal Mac. If the UI stalls, move CSV
   loading off the UI thread and discard outdated results after range changes.
3. Check the graph in Windows high-contrast themes and at 125–200% scaling.
   The Windows plot uses fixed colors. Test grid, labels, focus and series
   visibility against system colors before adopting a new palette.
4. Include an interrupted-write/reopen case in installer-upgrade acceptance
   using a disposable data directory. Confirm the prior observations still
   appear and a fresh measurement appends exactly once.

Physical USB/BLE behavior, actual charge, visual appearance on an owner's
desktop and installer upgrade need independent field evidence. The separate
High Sierra edition has no history chart in this change.
