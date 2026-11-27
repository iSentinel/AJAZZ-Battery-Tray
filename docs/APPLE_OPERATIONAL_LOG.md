# Apple operational journal — ENG-05 first stage

The shared C header AjazzOperationalEvent.h defines the initial closed
operational event and reason vocabulary for Swift and Objective-C. It
emits one schema-1 JSONL record with UTC at second resolution and
Windows-compatible event, severity and reason names. It accepts only
enums and a timestamp, not arbitrary strings or raw exceptions. Failed
encoding returns zero; callers must not append partial output. There is
no file I/O, HID operation, network access, or automatic logging yet.

The standalone C fixture checks all 70 event/reason combinations and
invalid inputs, under UTC and a non-UTC TZ setting. Native CI compiles
with warnings as errors on Linux and Intel macOS targeting 10.13.
Hosted Intel macOS does not qualify actual High Sierra or arm64 execution.
This is an encoder component, not a complete operational journal.

## Remaining implementation

- Add private, bounded storage with an active and one previous 256 KiB
  generation, nonblocking cooperating-writer lease and partial-tail handling.
- Validate ownership, private permissions, single-link regular files and
  no-follow directory/file opening. Reject unsafe or oversized existing
  files; never modify legacy logs. State the remaining filesystem races.
- Add synthetic rotation, refusal, contention and interrupted-tail tests
  before wiring events to either app. Keep tests in fresh temporary roots.
- Integrate minimal lifecycle and read-failure events only after reviewing
  both app call sites. Preserve hardware policy, CLI output and diagnostics.
- Measure durations with a monotonic clock only for actual operations.
  Review runtime overhead and actual macOS/High Sierra behavior separately.

No release authorization, package replacement or application behavior
change follows from this first-stage implementation.

## Second stage: bounded private storage candidate

AjazzOperationalJournal.h accepts a closed event and a caller-provided
existing owner-private directory (0700). It opens the final directory
without following symlinks, uses directory-relative opens, requires
regular single-link owner files (0600), and coordinates cooperating
writers through a persistent zero-byte lock with nonblocking flock.
Active and previous files are each limited to 256 KiB; oversized or
unsafe existing files are refused. A partial tail is preserved by
rotation. A short write is reported as failure, not retried; no fsync
or multi-file transaction is claimed. No live application call sites
are connected yet. Parent path trust and adversarial same-user races
remain outside this design; native ACL and actual OS tests are open.

The standalone synthetic storage fixture uses a fresh /tmp directory,
a 256-byte cap and checks rotation, torn-tail preservation, lock
contention, recovery, permissions, hard links, symlinks and oversized
previous files. CI uses Linux and Intel macOS; the deployment target
is 10.13, not an actual High Sierra execution. Retained beta.61 bytes
are not changed. Original encoder reference #328 passed 70 combinations
under two TZ values on both hosts; combined checkout must pass again.

## Native qualification correction and lifecycle integration design

Initial combined run 45987778921: Linux job 140467678485 passed encoding
and storage. Intel macOS job 140467678902 passed the encoder under both
TZ values, but strict POSIX C compilation hid O_NOFOLLOW, flock, LOCK_EX,
LOCK_NB and mkdtemp. Expose Darwin extensions with -D_DARWIN_C_SOURCE
only on Darwin, preserving -Werror and the 10.13 deployment target.
Repeat combined CI before integration; do not remove no-follow or locking.

Review of a78a0e6 identifies the actual tray delegate methods in both
macos/main.swift and macos/high-sierra/main.m. The first integration should
emit ApplicationStarted from applicationDidFinishLaunching and
ApplicationStopped from a new applicationWillTerminate callback. Do not
log stopped in applicationShouldTerminate: that callback may defer exit
until a diagnostic or poll worker is reaped. Keep CLI/self-tests and
child workers out of the live journal. Universal's BatteryHistoryWriter
already creates Application Support/AJAZZBatteryTray without guaranteeing
0700; do not change existing history-directory permissions. Use a separate
private journal directory under the user-owned support location, validate
it before writing, and refuse unsafe existing entries without chmod or
replacement. Keep each edition's directory distinct to preserve its own
operational provenance. Establish closed failure counters before adding
periodic poll events; do not label ordinary disconnected/unknown states
as transport failures. This is a design checkpoint, not wired behavior.

## Third stage: GUI lifecycle integration candidate

#329 qualified the shared encoder and storage on Linux and Intel macOS.
The new lifecycle helper opens the existing user Application Support
directory without following its final symlink, verifies ownership and
rejects group/other write permissions, then creates a fixed edition child
using mkdirat (0700). It never chmods existing directories. The child is
opened relative to the held parent descriptor; existing journal storage
checks still apply. Universal uses AJAZZBatteryTray-Journal and High
Sierra uses AJAZZBatteryTrayHighSierra-Journal. Missing support directory,
unsafe permissions and failed writes are refused; no alternate location.
Parent ancestors and ACLs remain outside the qualification.

Both actual AppKit delegates record ApplicationStarted after menu setup
and ApplicationStopped only in applicationWillTerminate. A deferred
termination request is not a stopped event. Forced termination can omit
that final record. Only GUI lifecycle paths call the helper; synthetic
self-tests, CLI diagnostics and workers do not. The saturating process
failure counter is included in the existing menu diagnostic snapshot;
no path or journal contents are exported. Failures do not prevent startup
or exit. This stage does not add poll, history or clock events or measure
runtime overhead. Existing history directories and permissions are unchanged.
The standalone fixture verifies both fixed names and exact start/stop
records, private permissions, refusal of an unsafe existing directory
without chmod, and refusal of a symlink. Actual GUI launch is NOT_RUN.

## Fourth stage: scoped GUI operation events

The edition-relative helper now accepts closed event/reason enums. Both
GUI delegates log IsolatedPollingEnabled when the existing opt-in mode
is active and IsolatedPollTimedOut on actual isolated worker timeout.
High Sierra's existing 20-second in-process watchdog emits PollFailed
with reason timeout once for that watchdog callback, not on every display
refresh or the eventual ordinary completion. Closing/cancelled operations
are not interpreted as failures. Universal records DockClockSucceeded or
DockClockFailed only for an attempted clock operation through its existing
result handler. Success means the existing transfer returned true, not
verified dock time; failure means unsuccessful, not a diagnosed cause.
High Sierra has no equivalent clock action wired here. Unknown charge,
absence, unsupported collection and unattempted operations do not emit
new failure events. Polling policy, worker deadlines and HID writes are
unchanged. No operation durations or real GUI observations are claimed.
Synthetic fixtures verify five event/reason pairs through both edition
storage paths, in addition to existing encoder and lifecycle tests.

## Fifth stage: measured operation duration candidate

Optional duration_ms is a whole millisecond count, 0..86400000. It is
only admitted for isolated poll timeout and attempted clock transfer
outcomes. Unmeasured records retain the exact existing schema-1 bytes.
The shared converter rejects negative, reversed, nonfinite or excessive
elapsed intervals and returns -1 (omit duration). Both editions measure
the existing isolated read call using process systemUptime immediately
before and after the call, including worker startup/cleanup. Universal
also measures each attempted clock transfer separately. These are wall
elapsed monotonic intervals, not CPU time or pure device latency. The
High Sierra in-process watchdog is intentionally untimed because its
callback does not prove completion of the underlying I/O. No new poll
or clock action is scheduled. UTC timestamp remains wall-clock metadata.
Synthetic checks cover exact optional field, invalid durations, unchanged
untimed records and mixed storage for both editions. Actual performance
and GUI/physical qualification remain separate.
