# Apple background journal — separate field acceptance

This is a developer-only check of the background journal integration in
PR #338, not beta.61 release admission. Hosted build and synthetic
results are PASS; actual AppKit/High Sierra/arm64 observations are NOT_RUN.

## Exact development build

The native runs built PR merge checkout
`e0ee3b9ee9fbbf0d213b09071624d0fb6d8ecfec`.
All nine changed blobs match integration `37c252980311d0a7ae3cfb1a48c9f1f237fe5242`.

| Edition | CI run | Artifact ID | Outer GitHub artifact ZIP SHA-256 |
| --- | --- | --- | --- |
| Universal | [46038993964](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/46038993964) | 15218757489 | bd7be8fbd2188914e650fd318bc4c3701df32bc8dc441ead94bb5f5240cc0946 |
| High Sierra Intel | [46038994038](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/46038994038) | 15218567848 | af724103a5d2d5d6ad32adf6c03d6736cb33601cc9e27a5949ea29d8be9837f4 |

GitHub metadata records expiry 2027-02-25 17:05:20 UTC for both.
Outer hashes are metadata observations, not independently downloaded
bytes. Do not substitute a later artifact or compare these hashes
against the inner app ZIP. Download the exact artifact from its run,
verify its outer digest with `shasum -a 256 <downloaded-zip>`, extract
into a new empty directory, then verify the supplied inner ZIP checksum
with `shasum -a 256 -c <companion.sha256>` from that directory.
Extract the inner ZIP into a separate test directory using Archive Utility
or ditto; retain executable permissions. Record the executable SHA-256
and app version/build before testing. Refuse a mismatch. The development
bundles are ad-hoc signed; do not bypass Gatekeeper or other OS policy.
Verify with `codesign --verify --verbose=2 <app>`; this is not trusted
publisher signing or notarization.

## Test conditions

Prefer an existing disposable local test account with a clean journal,
not the daily-use profile. Do not delete, chmod, truncate or move existing
journals. Close the previous tray and all other receiver tools.
Start with no AJAZZ receiver/dock attached; this avoids vendor transfers
while qualifying the journal. Use an available alternate input device.
Do not create permission faults, force I/O hangs, change firmware or send
unreviewed HID commands. No installation or startup-item registration.

Launch the unpacked app from its own directory, without arguments first:

    "./AJAZZ Battery Tray.app/Contents/MacOS/AJAZZBatteryTray"

or on High Sierra:

    "./AJAZZ Battery Tray High Sierra.app/Contents/MacOS/AJAZZBatteryTrayHighSierra"

In a separate session, append `--experimental-isolated-polling` to the
same executable. This is session-only. Do not run both simultaneously.
Record edition, architecture, OS build, executable hash, poll interval,
mode, start/end UTC and whether the receiver is absent. If a prerequisite
is missing, use NOT_RUN rather than manufacturing a passing observation.

## Local-only observations

The normal menu diagnostic contains initialized, failed, dropped,
unavailable, queued and in-flight fields. Copy just these reviewed
aggregate lines locally; do not upload raw diagnostic sessions or logs.
Check the edition-specific journal after the ordinary Quit action:

    journal="$HOME/Library/Application Support/AJAZZBatteryTrayHighSierra-Journal"
    # Universal: use AJAZZBatteryTray-Journal instead.
    stat -f 'mode=%Lp type=%HT' "$journal"
    stat -f 'mode=%Lp links=%l bytes=%z type=%HT' "$journal/app-events.jsonl"
    stat -f 'mode=%Lp links=%l bytes=%z type=%HT' "$journal/app-events.lock"

Expected: directory 700, regular files 600, one link per file, active
size no more than 262144 bytes and zero-byte lock. The previous
generation is optional; if present apply the same checks as active.
Verify ownership locally without recording usernames. Inspect ACLs
locally if desired; POSIX permissions alone do not establish ACL safety.
Read the journal locally; a fresh account/session should show exactly
one ApplicationStarted and, after ordinary quit, one ApplicationStopped.
Isolated mode should additionally show IsolatedPollingEnabled.
Valid unknown/absent replies must not become supervisor failures.
Never share actual journal paths, timestamps, raw logs, usernames,
device names or raw HID payloads publicly. Report only reviewed counts
and pass/fail observations; keep exact build identity separate.

For resource observations, select the actual tray PID in Activity
Monitor; record CPU percentage and resident size during a fixed 60-second
idle period at a documented polling interval. Alternatively, use
`ps -p <confirmed-tray-pid> -o %cpu=,rss=` at fixed 5-second intervals
and record RSS in KiB. This is parent-only process sampling, not peak
RSS, cumulative CPU or child-process-tree measurement. No automatic
CPU threshold or full latency bound is inferred.

## Cases (all initially NOT_RUN)

| ID | Action and expected result |
| --- | --- |
| J01 | Verify artifact identity and OS compatibility; both recorded. |
| J02 | Launch ordinary GUI; responsive menu, initialized writer, no false battery value. |
| J03 | Observe at least three scheduled polls; no device present, no supervisor failure inferred from valid absence. |
| J04 | Open and dismiss menu and diagnostics repeatedly; no visible stall, no queue drops or failures in healthy storage. |
| J05 | Observe 60 seconds of ordinary idle resource use; record scope, interval and units, not a threshold verdict. |
| J06 | Quit normally; app exits, exactly one start/stop for fresh session, private files and size cap. |
| J07 | Launch isolated session; marker present, three polls, menu responsive; record diagnostic aggregates. |
| J08 | Repeat resource observation in isolated mode under matching conditions. |
| J09 | Quit normally in isolated mode; no remaining tray/child observed, one stop for this session; absence of short-lived children is not proven. |
| J10 | Reopen normally; isolated mode is not persisted, new start and no journal corruption. |

For J06/J09, if the stop record is missing, record FAIL or INCONCLUSIVE
with observed exit behavior and storage state; the 100 ms best-effort
budget does not guarantee persistence. Do not rerun until a failure
vanishes and report only the passing attempt.

Report per case PASS, FAIL, INCONCLUSIVE or NOT_RUN, edition, OS build,
architecture, artifact/executable identity and a short scoped
observation. Record all attempts. A responsive menu observation is not
a frame-time measurement. Real resource/GUI data cannot be inferred
from synthetic benchmark metrics. Receiver-attached tests are separate:
follow [isolated polling acceptance](ISOLATED_POLLING_ACCEPTANCE.md)
with the same exact developer artifact, no forced failures and no
new HID commands. Retained beta.61, signing, distribution and release
admission remain unchanged and BLOCKED.
