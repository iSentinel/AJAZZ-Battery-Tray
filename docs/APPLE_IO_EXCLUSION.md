# Shared Apple vendor I/O exclusion

Both Apple editions use the same per-user Darwin temporary directory
and lock name, held with a nonblocking exclusive flock across the
entire AJAZZ vendor transaction. The file must be regular, owned by
the current effective user, private, and not a symlink or hard link.
The lock file is never removed by participating processes; closing
the descriptor or process exit releases the lock. It coordinates
new participating builds for the same macOS user, not older versions,
other users, or GearHub. The gate is deliberately conservative when
its storage cannot be validated.

The Universal battery read and existing dock clock write, and High
Sierra battery/diagnostic trace acquire the gate before opening IOKit.
A denied gate maps to access unknown (or unsuccessful RTC send), not
physical removal or a verified charge. No new HID commands or retry
loops are introduced. Metadata-only Universal inventory and BLE remain
separate. Regular menu timers retain their current reader architecture.

CI verifies that each built executable refuses a gate held by another
process and can acquire it after release, using only a synthetic
lease mode. No receiver is opened during that test. This does not
establish physical device compatibility, and the gate cannot guarantee
that unrelated third-party software will not send vendor reports.

Next: cancellable Universal supervisor and opt-in timer integration;
High Sierra isolated regular reader and actual owner hardware tests.
