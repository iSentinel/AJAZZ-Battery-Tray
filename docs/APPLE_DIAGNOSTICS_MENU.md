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
Universal trace uses the existing 8-second supervisor; on timeout the
partial child trace is not returned. Legacy wraps the existing 20-second
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
