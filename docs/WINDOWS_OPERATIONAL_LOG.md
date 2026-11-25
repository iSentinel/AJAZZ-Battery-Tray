# Windows operational journal (ENG-05)

The operational journal uses schema 1 JSON Lines: UTC timestamp, closed
event identifier, severity and closed reason code. No caller-supplied
message, exception type name/message, device alias, numeric battery level,
path, credential or raw HID buffer is serialized. Detailed measurements
remain in the existing separately controlled battery history/diagnostics.
A display-event marker means the display changed, not a verified measurement.
Example (synthetic):

    {"schema":1,"utc":"2026-11-25T00:00:00.0000000+00:00","level":"WARN","event":"HidReadFailed","reason":"io_error"}

The active file and one previous generation are capped at 256 KiB each.
A persistent zero-byte lock file coordinates cooperating .NET writers
using exclusive file sharing; contention or expected I/O failure drops
the event rather than indefinitely retrying. Failures are counted per
process and the extended diagnostic report exposes the count for the tray
process, not its child workers. A partial final record after interruption
is moved to the previous generation before new appends. A previous file
may therefore contain an incomplete last line; do not claim crash-durable
or atomic multi-file evidence. Oversized preexisting journal files are
refused instead of silently deleted. Existing app.log is left untouched,
may contain private legacy text, and must not be uploaded.

Files live in the existing per-user AppData directory; final reparse-point
checks reject redirecting files and directories. This is ordinary
cooperating-process logging, not an adversarial same-user filesystem
sandbox: inherited ACLs, hard links/TOCTOU and redirected parent directories
require separate Windows qualification. No changed permissions, hardware
I/O, network transmission or release action. Timestamps are wall-clock
UTC; operation durations are not inferred where unmeasured. Native tests
use unique temporary directories and cover safe reason/UTC/schema,
privacy canary, rotation, partial tail, lock contention and refusal.
Apple logging, native operational timing and ACL qualification remain open.
