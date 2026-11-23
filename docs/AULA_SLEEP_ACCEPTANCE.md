# AULA L99 — Windows sleep and recovery acceptance

## Scope

Validate beta.51 or newer on an actual L99 using the known 2.4 GHz receiver.
This is an observation procedure, not a new HID test or firmware operation.
Record the installed version, Windows version, effective AULA polling
interval, whether automatic monitoring is enabled, and history setting.
Close vendor software before starting. Use only the Battery Tray UI;
do not change keyboard firmware, RGB, sleep configuration, or power plan
during a comparison. If no physical L99 is available, mark NOT RUN.

## Acceptance matrix

| ID | Action | Expected observation |
| --- | --- | --- |
| A01 | Start with AULA automatic monitoring disabled | No automatic AULA reading; Device Manager initially Disabled |
| A02 | Read AULA battery once while disabled | Successful explicit reading is Manual reading; no background timer is armed |
| A03 | Enable Monitor AULA automatically (experimental) with keyboard awake | Fresh reading and measurement time after a successful response |
| A04 | Leave keyboard idle without touching it; let it enter its ordinary sleep mode | If the receiver stays present but stops replying, last good value is Cached reading, with the original measurement timestamp |
| A05 | Continue ordinary sleep for a longer period, ideally overnight | Cached value stays display-only for less than 24 hours; original timestamp remains unchanged |
| A06 | Wake keyboard with ordinary typing | A successful subsequent normal poll replaces cache with Fresh reading, new timestamp and reset failure count |
| A07 | Disable monitoring during an ongoing read | No stale completion updates the state or starts a new automatic read |
| A08 | Re-enable while an old read is still pending, if observable | Old reply discarded; next read scheduled promptly after completion, with no overlapping AULA requests |
| A09 | With keyboard awake, unplug the AULA receiver and allow ordinary polling | Confirmed absence clears cache; no battery value shown |
| A10 | Reinsert the same receiver and allow ordinary polling | Fresh value restored only after a successful reply |
| A11 | Change the supported AULA polling interval while enabled | Subsequent polls respect the configured interval; no extra periodic timer |
| A12 | Exit application during an active read | Application exits without a visible late update |

Use the actual selected interval. The reader can retry once, so allow a
reasonable extra read-completion delay; do not demand a new value at the
exact configured second. Do not force refresh during A04–A06. A keyboard
that still replies during sleep is not evidence of cache handling: mark
that scenario NOT OBSERVED. A07–A08 may be difficult to reproduce manually;
mark NOT RUN if the race cannot be observed. A11–A12 validate visible
behavior only; concurrency/timer internals require instrumentation.

## Collect evidence without new HID traffic

At each checkpoint open the AULA L99 (experimental) menu and select
**Copy AULA diagnostic summary**. This reads existing in-memory state.
A Device Manager screenshot is optional; open it without using Refresh.
The summary includes last successful percentage/time, latest poll time,
receiver presence, consecutive no-reply count and cache-active flag.
For the sleep scenario, record one awake, one sleeping and one recovered
summary. The optional local snapshot can be copied separately without
starting the HTTP listener. It must contain a cached lastKnownPercent
rather than a fresh batteryPercent during a valid no-reply cache state.

Report each checkpoint with PASS / FAIL / NOT RUN / NOT OBSERVED,
observed timestamps, percentage and expected/actual status. Do not include
raw HID paths, serials or unrelated captures. No need to share full
history files. The 24-hour expiration can be marked NOT RUN if a full
24-hour real-device observation is impractical; synthetic coverage
does not count as physical acceptance.

## Resource comparison

Follow [RESOURCE_OPTIMIZATION.md](RESOURCE_OPTIMIZATION.md) on the same PC
and with matching device/monitoring settings. Three comparable five-minute
runs per version are recommended. Keep the AULA acceptance sequence
separate from idle measurement runs. No runtime improvement is claimed
until actual measurements exist.
