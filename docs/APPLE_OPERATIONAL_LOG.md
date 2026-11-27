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
