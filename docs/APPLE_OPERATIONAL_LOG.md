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

## Sixth stage: synthetic storage overhead benchmark

The separate C benchmark executes exactly 4096 identical closed timed
records through the production Universal edition storage helper in a
fresh private temporary directory, using the production 256 KiB cap.
It measures monotonic append latency in nanoseconds; normal and expected
rotation writes have separate counts and nearest-rank p50/p95/max.
The rotation classification follows the exact encoded record size and
fixed generation capacity, with both retained generations reopened and
all retained record bytes checked. The write-loop elapsed time and
process user+system CPU delta are reported separately; peak RSS is the
whole benchmark process high-water mark, normalized to bytes (Darwin
bytes, Linux KiB). Temporary fixture files are removed after verification.
Linux and Intel macOS hosted jobs compile with -O2 and warnings as errors,
retain only aggregate JSON, and fail on execution or integrity failure.
No latency threshold, durability/fsync guarantee, physical HID, real GUI
or tray CPU/RAM inference is made. Benchmark metrics are observational.

## Seventh stage: isolated routine outcome provenance

The supervisor outcome is separate from the battery presentation state.
Both editions preserve Reply, Timeout, Cancelled, Busy and Failed without
changing the previous UI result. Only an actual supervisor timeout emits
IsolatedPollTimedOut, with measured duration. Busy emits
IsolatedPollUnavailable/busy and Failed emits
IsolatedPollUnavailable/unsuccessful, without inferred duration or cause.
A valid reply with unknown battery, absent receiver or access error is
not a supervisor failure. Cancellation does not emit a failure record.
Legacy IPC bytes, worker launch arguments, timeout budgets and HID
commands are unchanged. New encoder vocabulary has eight reasons; the
standalone fixture covers all 80 combinations and five outcome mappings.
Existing native worker self-tests exercise provenance without HID.

Benchmark #333 run 46031570517, checkout 61ddc6b: both hosts wrote 4096
records (4095 ordinary, one rotation) and retained exact records. Linux
ordinary p50/p95/max 20210/22194/84538 ns; Intel macOS
244000/346000/83028000 ns. Rotation 56966/306000 ns respectively.
CPU delta 83732/806847 us, peak RSS 1847296/696320 bytes. The single
rotation sample and macOS latency outlier do not establish a stable
performance bound. Hosted logs and artifact metadata were reviewed;
artifact bytes were not independently downloaded. Real UI latency and
resource use remain unqualified.

## Eighth stage: bounded background queue state core

AjazzOperationalQueue.h is a fixed-size FIFO core with no allocations,
file I/O, threads or waiting. It admits at most 63 ordinary queued events
plus one reserved stop record and one separately claimed in-flight event.
Overflow drops the newest record; invalid and post-seal offers are also
counted as drops. Seal appends one final stop record, refuses repetition,
and does not guarantee a flush. The sole consumer claims and completes
one record at a time; successful/failed writes and drops saturate at
UINT64_MAX. Queued values contain only closed enums, timestamp and duration.
All operations require caller-owned serialization; this core is NOT a
thread-safe queue by itself. Deterministic Linux/Intel macOS fixtures
exercise full-buffer FIFO, stop reservation, refusal, wraparound and
accounting. Next: connect a serialized nonblocking producer and one
background writer, with bounded shutdown semantics and concurrency tests.
Do not hold a queue lock across filesystem I/O. Current GUI writes remain
synchronous; no latency improvement has yet been demonstrated.

## Ninth stage: serialized background writer adapter

AjazzOperationalWriter.h wraps the fixed queue in one pthread mutex and
condition variable with exactly one worker. The sink runs outside the
mutex; producers do not wait for capacity or filesystem operations,
but can briefly contend for queue state. Seal appends the reserved stop
and does not promise persistence. The caller owns the writer and sink
context for their entire lifetime; after sealing, all producers must
stop before a single lifecycle owner joins and destroys the adapter.
Monotonic wait observes completion with a 1 ms polling interval; timeout
does not cancel the sink, free resources, or imply a successful flush.
A join is refused while the worker has not completed. Scheduling can
delay an observation; this is not a hard real-time guarantee.

Synthetic fixtures exercise four concurrent producers while a sink is
deliberately blocked, drop-newest accounting, uniqueness, final stop
ordering, failed sink accounting, wait timeout, recovery and idle wake.
The Linux/Intel macOS CI workflow compiles the standalone adapter with
pthread and the existing warnings-as-errors policy. Hosted results are
pending. No production journal sink or GUI call site is connected, and
no actual application performance, physical device or 10.13 runtime
claim is made. The pinned beta.61 and HID policy are unchanged.

## Tenth stage: edition-specific background storage adapter

AjazzOperationalEditionWriter.h owns a bounded absolute support path
(maximum 4095 bytes plus terminator), edition flag and the existing writer.
Creation copies the path and starts an idle worker without filesystem
access. The sink invokes the unchanged AjazzJournalEditionTimedEvent on
the worker thread; edition paths, owner checks, permissions, rotation,
lease and closed record encoding retain their existing semantics.
Successful enqueue does not mean persistence. A timeout is not a flush.
The single lifecycle owner must stop producers, seal, and destroy only
after completion; unsuccessful destruction leaves ownership intact.
The adapter does not log its path and has no automatic synchronous
fallback. The null snapshot is empty and must not be treated as evidence
of successful initialization.

The standalone fixture uses private temporary storage, checks exact
start/timed timeout/stop bytes for both editions, proves the input path
is copied, checks post-seal drops and refuses premature destruction.
A pre-existing 0755 edition directory must remain unchanged without
creating an active log or lease; both queued events count as failed.
Null, relative and oversized paths are rejected. Hosted Linux and Intel
macOS results are pending. No real GUI, user profile, HID or pinned
release candidate changes. Production lifecycle integration is separate.

## Eleventh stage: AppKit background journal integration

Both editions use AjazzGuiJournal.h as main-thread lifecycle state.
Only applicationDidFinishLaunching starts a writer; internal CLI and
HID worker modes remain unchanged. All prior GUI operational events
enqueue closed values with timestamps captured at offer time. No
filesystem write or synchronous fallback occurs on the ordinary UI
event path. The worker owns a copied support path, not an AppKit object.

applicationWillTerminate seals the reserved stop once, observes
completion for up to 100 ms using the monotonic best-effort wait, then
joins only a completed worker. If the budget expires, pending records
may be lost at process exit; the independent heap context is not freed
under a running sink. Delegate deallocation makes a non-waiting repeat
collection attempt, without a duplicate stop. Existing HID cancellation
and AppKit termination decisions are unchanged. The 100 ms budget is
an engineering choice, not a measured real-time or durability guarantee.

The menu diagnostic retains the failed-write label (now completed
failed sink operations only) and adds queue drops, unavailable events,
initialization state, queued count and in-flight state. These are
process snapshots, not a guarantee of persisted records. Failed
initialization and offers after stop count as unavailable; no paths or
raw exceptions are emitted. The shared C fixture exercises start,
duplicate start, stop retry, exact FIFO records, cached final status
and missing path for both editions. Hosted native builds and actual
GUI/hardware performance and shutdown qualification remain separate.

## Twelfth stage: paced synthetic producer benchmark

The fixed standalone fixture submits 4096 timed events through the
same GUI adapter as the two applications, in batches of 32. The
producer-only monotonic measurement excludes explicit batch drain
waits. The total elapsed time and process CPU include the consumer
and pacing; peak RSS is process-wide, not a measured incremental
tray cost. The first shutdown observation is recorded separately;
additional attempts are solely for safe benchmark cleanup.

Qualification requires 4098 completed records including start/stop,
zero failed, dropped and unavailable events, and exact ordered
content of both retained generations. Synthetic timestamps distinguish
record ordering. Only aggregate JSON is retained. This is a paced
workload, not an unbounded stress test or real AppKit measurement.
No comparison of different scopes implies real UI latency or battery
polling performance. Parent #338 and hosted results remain required.

Initial benchmark evidence: #339 run 46039186400, tested checkout
a637182, jobs 140642238193 (Linux) and 140642237745 (Intel macOS).
Both hosts completed 4096 offers and 4098 writes; zero drops, failures
and unavailable events, exact retained generations MATCH. Linux offer
p50/p95/max 50/391/17042 ns; Intel macOS 0/1000/106000 ns (clock
resolution limits the zero median). First stop 1069364/4941000 ns,
both complete. Process CPU 120133/922929 us and peak RSS
1986560/729088 bytes. These are scoped paced synthetic observations,
not incremental tray resource use or a real UI speedup. Parent #338
merged 37c2529 with 5/5 workflows, 7/7 jobs and all nine changed blobs
matching e0ee3b9. Repeat qualification against integrated base required.
