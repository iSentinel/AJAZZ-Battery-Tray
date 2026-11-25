# Apple GUI diagnostics and peer-project review

## Owner request (2026-11-25)

Run diagnostic capture from the macOS status menu, without Terminal, on
Universal macOS 13+ and High Sierra 10.13+. Keep CLI automation.
No change to battery verification or protocol command allowlist.

## Peer review

Reviewed project README and implementation excerpts at the following
immutable Git revisions (no external source copied into this project):

- BatteryBar: https://github.com/l351i3/BatteryBar/tree/c231d6b0bc6677fc175902b1dc1aff28a68dcd0b
  `aggregator.py` models provider status, duration and cache; `app.py`
  exposes provider results in a submenu and dispatches a worker.
- Juicy: https://github.com/RagnArUCi/juicy/tree/69023fa80f970859bca15c681e01fdd40c8ca0df
  README describes throttled off-main-thread accessory enumeration;
  `Sources/Juicy/Services/BatteryReader.swift` separates reader logic.
- Nibble: https://github.com/ben0128/nibble/tree/eeed965a97b2c783548476667cca96933d846f60
  `Sources/Transport.swift` filters HID collections, retains IOReturn
  failures, registers removal callbacks and bounds response matching.
- Stats: https://github.com/exelban/stats — README and release/issue
  review: monitoring resource cost, stale Bluetooth entries, event-based
  power-source updates.
- Solaar: https://github.com/pwr-Solaar/Solaar — issue #3263 and
  `lib/solaar/gtk.py` review: per-device availability, debug modes and
  receiver-specific diagnostics.

These are architecture and UX references, not AJAZZ protocol evidence.
Do not transplant Logitech HID++ commands, assume shared VID/PID maps,
or treat cached platform values as verified F7 telemetry.

## Menu

Diagnostics > Device diagnostics: view existing in-memory state
without a fresh HID operation. Copy diagnostics copies that snapshot.
Run HID diagnostics: explicit consent, same-binary supervised worker
off main thread, existing F7/05 and existing 65/67 length attempts only,
30 ms nominal delay and early exit after a verified reply. This is not
the full Windows delay matrix. The report separates the previous ordinary
state from a new trace and includes version/build, UTC, OS, matching
collection metadata, operation status, bounded prefix and elapsed time.
No identity identifiers, firmware query, RTC or configuration action.
Universal trace uses the existing 8-second supervisor; complete short
records are retained on timeout or abnormal termination. Legacy wraps the existing 20-second
CLI trace supervisor, preserving captured partial text when available,
capped at 4096 bytes. An ordinary in-flight poll causes a busy message;
the UI guard and shared vendor I/O lease prevent overlapping requests.
Do not update the normal tray reading, alerts, history or fallback from
diagnostic results. The tray resumes normal monitoring independently.

Review the report, then Copy / Save / Close. Save creates a new 0600 file
with exclusive creation and no final symlink following. Existing files
are deliberately refused; choose another name. No automatic upload,
automatic clipboard write for active captures, or raw full vendor buffer.
On I/O failure a partial private output file may remain. All new menu
actions and confirmation text are available in EN/RU/UK. Diagnostic
field keys remain English to support automated comparisons.

## Next improvements (separate gates)

1. One provider-status dashboard: USB and explicit Bluetooth observations,
   operation status, timing, provenance and unknown/present states.
2. Explicit paired GATT comparison export, session-only, without addresses
   or silently initiating new scans. Keep independent transport evidence.
3. Versioned redacted report schema, importer and cross-platform comparison;
   separate passive state, fresh query, cached and unverified fields.
4. Time-bounded multi-snapshot capture with explicit opt-in and a cancel
   control, preserve partial diagnostics consistently on timeout.
5. Event-driven attach/detach investigation and resource baselines; do not
   add always-on high-frequency Bluetooth/HID traffic.
6. Physical acceptance on High Sierra and Universal: menu launch without
   Terminal, busy/timeout/quit, copy, no-clobber save, locale, sleep/wake,
   receiver absent and valid/unknown battery. Test developer builds first.

Native compile/test and real-device UI acceptance required. Linux Gateway
cannot verify AppKit behavior; no release admission or compatibility
promotion from this implementation alone.

## Independent manual Bluetooth evidence

The menu report includes the last manual connected-device discovery count,
whether a selected GATT read is pending, and the most recent completed
manual 180F/2A19 outcome, verified percent or unknown, UTC and elapsed
milliseconds. These are session observations without a device identity
binding. A prior USB and GATT measurement must not be treated as a
simultaneous same-device calibration. A fresh valid GATT value can be
0..100 inclusive, unlike the narrower F7 parser. No scan, discovery,
pairing, connection or GATT read is initiated by copying/viewing reports.
A failed later read reports unknown rather than presenting the older
percent as current. Device names, Bluetooth identifiers and raw values
are not included. No persistent history, alert, tray or fallback mutation.

Universal timeout now checks attempt generation in addition to selected
peripheral; both editions require matching 180F service and 2A19
characteristic before decoding. A stale timeout is distinct from
arbitrary delayed CoreBluetooth callbacks: physical repeat-read and
disconnect tests are still required. Native self-tests exercise initial
passive state and existing GATT payload validation.

## Universal partial trace

The explicit worker emits fixed newline-delimited records as the operations
progress, including markers before potentially blocking HID calls. At most
16 detail records (192 bytes each) plus truncation/status/end records keep
the producer below 4096 bytes. The supervisor reaps the child before
reading the pipe. On timeout, cancellation or abnormal exit only complete
UTF-8 non-terminal records are returned, with an explicit INCOMPLETE
label; terminal battery claims and an unfinished final line are discarded.
Successful completion requires the terminal marker. This does not
change routine IPC, protocol commands or telemetry. Native synthetic
workers exercise timeout, abnormal exit, malformed/oversized output and
normal completion without HID. Quit cancels the worker, but interactive
cancellation and multi-snapshot collection remain separate tasks.

## Versioned Apple snapshot import

Both editions emit Report schema: apple-menu-v1 and stable Bluetooth
snapshot keys even if Bluetooth was never requested. The local CLI:

    python tools/analyze_apple_diagnostics.py report.txt

accepts one versioned report (UTF-8, at most 64 KiB), normalizes the
ordinary USB state, prior verified-session timestamp and independent
manual GATT result, and indicates whether an active trace is present.
It intentionally omits the trace contents, device names and arbitrary
free text from JSON. It rejects duplicate required fields, concatenated
reports, unknown schema, invalid timestamps and inconsistent percent/state.
A GATT 0% is valid; USB 0% is not. A valid imported snapshot is not
evidence of a simultaneous measurement, physical device identity or
verified active HID capture. Unversioned reports and Windows reports
are outside this initial parser's scope. No upload, I/O or telemetry
promotion occurs. Actual native report fixtures and cross-platform
comparison remain open.

## Cross-platform redacted summary

Windows extended reports now include Report schema: windows-extended-v1.
The local tool:

    python tools/normalize_device_diagnostics.py report.txt

accepts the two versioned Apple layouts and the reviewed Windows extended
or full comparison layout. Unversioned Windows reports with that exact
layout are labelled windows-extended-legacy, not silently upgraded.
Output uses device-diagnostics-summary-v1 with platform-specific observation
fields inside a common envelope. Windows ordinary completion time is not
the Apple last-verified USB session time. Windows manual and last direct
GATT observations remain separate; cached Windows battery is never direct
GATT or USB telemetry. Unknown presence remains unknown. The seventh .NET
fractional-second digit is truncated to Python microsecond precision.
Raw trace and arbitrary labels are omitted; full-matrix presence is not
evidence of successful capture. AULA and other unrelated device readings
are not imported by this adapter. No identity or simultaneity claim.

The importer uses bounded regular-file reads (one MiB Windows, 64 KiB Apple).
Six synthetic regression tests cover independent sources, historical layouts,
full trace redaction, missing inspector, unknown presence and malformed data.
Physical native report fixtures and active trace outcome normalization remain
open. No protocol or polling change.

## Universal interactive cancellation

Diagnostics > Cancel HID diagnostics is enabled only during an explicit
capture, until cancellation is requested. The UI sets the existing
thread-safe worker token and shows a localized cancelling state; it does
not signal the child or release the ordinary poll exclusion itself.
The supervisor stops and reaps the child, then the GUI presents a
partial report with no fresh battery claim. Cancellation before launch
or after worker completion but before UI delivery is also handled
conservatively. Rebuilding the menu or changing language does not
reset cancellation state. No new HID command or history update.
Native synthetic cancellation and recovery are included in the bounded
worker self-test. High Sierra retains its existing bounded capture and
requires a separate safe supervisor cancellation implementation.
Actual AppKit interaction and physical HID acceptance remain open.
