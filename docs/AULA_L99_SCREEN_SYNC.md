# AULA L99 system-screen synchronization: evidence and gates

## Owner hardware baseline
The owner's L99 returned 100% on two Windows ordinary battery reads on
2026-11-22. Dongle: 05AC:024F MI_03, FF60:0061, 33-byte input/output,
USB revision 0136. This confirms the battery exchange only; no screen commands
were sent. VID/PID is shared with other AULA keyboards.

## External protocol research (not imported code)
- gavindi/Aula_L99_Linux at 30f170af, [system-monitor notes](https://github.com/gavindi/Aula_L99_Linux/blob/30f170af/tools/aula_l99_hacky/re_notes/system_monitor_block.md)
  and [protocol](https://github.com/gavindi/Aula_L99_Linux/blob/30f170af/tools/aula_l99_hacky/protocol.py).
- livvaa/AulaToolkit, [radio framing](https://github.com/livvaa/AulaToolkit/blob/main/src/shared/protocols/aula04.ts)
  and [transport](https://github.com/livvaa/AulaToolkit/blob/main/src/main/hid/drivers/aula04Driver.ts).

The upstream L99 research reports hardware-tested **wired** RTC telemetry:
CPU load/temperature and GPU load/temperature occupy body offsets 13–16.
The same record contains time and weather. It is not an image upload.
Radio RTC operation 0x0C is a candidate from the reverse-engineered code.
The L99 vendor binary's proposed radio layout puts hardware values at body
offsets 17–20 and trailer at 26–27, while an F75-derived radio clock example
has a different one-byte shift and earlier trailer. The vendor radio path
was not captured in that report. A session-handshake result does not prove
an RTC or monitor update. Do not splice layouts or send either candidate
blindly. Windows report ID and body indices must be kept separate.

## beta.29 host-only preview
No additional HID operation or automatic telemetry transfer.
- Sample Windows CPU utilization over 400 ms from GetSystemTimes.
  On machines with more than 64 logical CPUs this API describes the
  calling thread's primary processor group, not necessarily the whole host.
- Optional local LibreHardwareMonitor 0.9.6 data.json provider. The user
  starts and configures it independently; no provider/driver installation,
  privilege elevation or external HTTP connections by this app.
- Manual read only: GET http://127.0.0.1:8085/data.json, no proxies,
  redirects, cookies, credentials, or control requests, three-second deadline
  and two-megabyte response cap. Configure the provider to listen on
  loopback only, not a LAN interface. Do not disable protections to obtain
  sensor access.
- Keep CPU packages and GPUs distinct. Report unknown values as unavailable;
  CPU package / AMD Tdie or Tctl/Tdie / Core Max and GPU core temperatures
  are prioritized. Do not substitute memory temperature or fabricated zero.
- The provider WMI interface was removed in 0.9.5
  ([upstream issue](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/issues/2143));
  this preview uses the documented local HTTP tree of v0.9.6 instead.
  Some sensors need separate existing provider permissions or hardware support.
  No third-party binary is bundled in this stage.

## Required evidence before keyboard writes
1. Confirm beta.28 three-device behavior and beta.29 host preview on Windows.
2. Obtain a narrowly filtered capture of the official L99 utility updating
   Instant Data over **2.4 GHz**, with known displayed values/time. If using a
   USB capture utility, capture only the target receiver traffic, do not type
   private information while capturing, and do not share unrelated HID reports,
   device paths, serials, credentials, or an unfiltered USB trace.
3. Establish exact MI/usage, Windows report ID, payload length, opcode,
   fields, checksum, optional acknowledgment and whether a session handshake
   is required. Determine the effect of omitted weather fields. Record an
   independently reproducible packet fixture, not just guessed bytes.
4. Add a narrow, telemetry-only encoder and exact allowlist, tests against
   the capture, serialized transport with battery polling, and a manual
   opt-in one-shot test. Never send a generic command or automatic alternate
   layouts; stop on absence, invalid sensors, failed replies or ambiguity.
5. Owner confirms time and all four values physically on the screen; only
   then consider periodic opt-in sync, per-GPU selection and rate limits.
   Weather is a distinct later stage and requires explicit consent and format
   verification.

No screen sync or new device command is enabled by beta.29 preview.
