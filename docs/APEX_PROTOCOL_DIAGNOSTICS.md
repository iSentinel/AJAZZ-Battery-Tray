# APEX battery protocol diagnostics — Windows

## Scope

Owner reports an APEX-series mouse with no battery reading in our app while
the official utility reads it correctly. Owner confirmed AJ159 APEX
(issue #53); receiver revision remains unverified. The shared USB receiver ID and revision are not a
universal identity or firmware version. Treat the previously working AJ159
and AJ179 as independent regression cases.

## Collect our application trace

1. Disconnect unrelated AJAZZ receivers where practical; leave the target's
   2.4 GHz/8K dock connected. Note printed model and official utility version.
2. Close the official utility, including its tray/background instance.
3. Wake the mouse by moving it. In AJAZZ Battery Tray choose
   **Diagnostics → Full APEX comparison report...**, confirm consent,
   and save the displayed report locally. If polling is in progress, retry.
4. Repeat once after ordinary sleep and again immediately after waking.
   Note whether the mouse is charging and the displayed battery percentage.
5. The full report already includes descriptor inventory and the previous
   ordinary monitor state; a second diagnostic action is unnecessary.
6. Compare three separate captures: working AJ179 APEX, working AJ159 APEX,
   affected AJ159 APEX. Use only the intended receiver, awake and not charging
   if practical. Name files AJ179-working, AJ159-working, AJ159-affected;
   separately note the official app's displayed level and version, if known.

The capture pauses ordinary AJAZZ polling and RTC sync; it performs only the
existing allowlisted SET F7 / GET 05 battery query, at 30, 100 and 250 ms
requested waits and the existing distinct buffer lengths (65–256 bytes).
It completes every allowed length/delay combination, even after success.

Unreleased issue #93 candidate: full capture runs in an isolated worker,
with a 40-second deadline and local status. Raw bytes travel through an
anonymous pipe; incomplete reports are discarded. A Windows kill-on-close
job and start handshake protect the worker lifetime. If termination cannot
be confirmed, AJAZZ polling remains paused. This is a pending CI and GUI
acceptance candidate, not behavior shipped in beta.60.
Up to nine requests per eligible collection (usually six). It records
the sanitized interface, USB revision, HID capacities, full TX and initialized
GET buffers, full returned buffer on successful GET, Win32 failures, UTC and
elapsed timings, and the existing parser's acceptance/rejection reason.
Failed GET buffers are not presented as responses.

HidD_GetFeature reports success/failure, not actual transferred wire length.
The logged RX length is the requested Windows buffer capacity; bytes in it
may include padding. A valid report is still only the previously verified
format; zero and unrecognized reports remain unknown. The mode does not
replace the normal monitor reading or update history. It sends no new opcode.

## Official application reference

Capture separately with a local USB protocol analyzer (for example Wireshark
with USBPcap on Windows). This is passive observation, not command replay.

- Close AJAZZ Battery Tray entirely, including its tray process, before running
  the official program.
- Choose only the USB controller containing the target dock; capture a short
  session, minimize unrelated USB traffic, and do not type sensitive data.
- Start capture before launching the official application; record its reported
  battery percentage and approximate time, wake the mouse, trigger a battery
  refresh if the official interface allows it, then stop capture.
- Record USB VID/PID, bcdDevice, interface, transfer type, directions, report
  IDs, request/response bytes, lengths and delays. Match request and completion
  records rather than treating USB URB framing as part of HID application data.
- Keep the original PCAPNG local. Export only relevant target battery
  transactions after inspecting for serials, input reports and unrelated
  or undocumented personal/device data. Do not upload a whole bus capture.
- If needed, repeat at another actual battery level to distinguish a true
  percentage field from a constant or charging flag.

## Comparison and acceptance

Compare official transport (feature vs input/output), interface/collection,
report ID, exact payload, length, order, initialization and timing with our
capture. Do not send guessed packets or infer percentages by scanning random
bytes. Propose a new allowlist entry only after verified battery-specific
evidence shows a read-only transaction. Avoid replaying profile, DPI, lighting,
RTC, firmware or bootloader operations.

The explicit raw report may contain undocumented sensitive vendor data;
review before sharing. Nothing is uploaded automatically. Normal diagnostic
reports and logs must continue to exclude raw payloads and private paths.

- [ ] Windows/macOS CI passes with unchanged existing parser and polling.
- [x] Owner confirmed affected AJ159 APEX model.
- [ ] Verify official utility version and actual receiver revision.
- [ ] Matching ordinary and official reference captures.
- [ ] Identify the first meaningful difference; validate the candidate parser
  or query against actual samples, including a known valid battery level.
- [ ] Regression: both previously working APEX models, independent receivers,
  sleep/wake, unplug/replug and unavailable responses.
- [ ] Real hardware confirmation before claiming compatibility resolved.
