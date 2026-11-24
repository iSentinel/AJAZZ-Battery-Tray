# Windows dock RTC and uncertain USB discovery

Before connecting the routine-read worker to the tray timer, distinguish
failed or incomplete discovery from confirmed unplug. The existing
DockClockSchedule used only receiverPresent and therefore treated an
unknown batch as absence. A subsequent valid enumeration could restart
the five-minute clock-write schedule early.

The schedule now ignores unknown presence without altering its
last-attempt or confirmed-presence state. QueryAndSync issues no RTC
command for an unknown batch, preserves an outstanding manual request
for a later ordinary poll, and does not report a send attempt that
never took place. A confirmed absence retains the existing behavior.
A manual request is not replayed after an ambiguous write exception.

Seven deterministic schedule assertions cover initial presence,
unknown absence/presence, same receiver recovery, normal deadline,
confirmed unplug and replug. These do not prove physical dock RTC
behavior. No change to the approved RTC frame, poll interval,
automatic clock setting or BLE/AULA paths.
