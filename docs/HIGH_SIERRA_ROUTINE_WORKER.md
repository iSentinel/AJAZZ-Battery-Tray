# High Sierra routine worker prototype

This separate prototype is not called by the menu timer. The legacy
Objective-C executable can return a fixed-size local response containing
only the existing battery state, percent and collection count. The
parent validates the exact length, enum, 1..100 battery range and
count; unknown or malformed replies cannot become fresh telemetry.

The NSTask supervisor holds an in-process gate until the child has
exited, enforces an eight-second intended read deadline, and maps a
timeout to BatteryTimedOut. The child has a 12-second alarm. The same
per-user vendor lock protects its actual existing ReadReceiver call.
No new HID frame or RTC command is introduced.

The native Intel build runs --self-test-routine-poll with synthetic
frames, gate contention, simulated hang and recovery; no HID access.
This is not proof of actual macOS 10.13 behavior. A kernel stall may
delay child exit. Next: cancellation and opt-in menu integration,
shutdown semantics and physical iMac testing. Normal polling unchanged.
