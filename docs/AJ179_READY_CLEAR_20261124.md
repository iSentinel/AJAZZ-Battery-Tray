# AJ179 owner report — 2026-11-24

Owner identifies AJ179 APEX. Two reports at 21:22 and 21:23 UTC, build
8db6fb6, Windows 10.0.26300.0. VID/PID 3151:5007, rev 0002,
MI_02 FFFF:0002, feature 65. Six successful 65/67-byte F7/05 requests
at 30/100/250 ms all show prefix 05 00 00 64 01 00 01 02 00 00.
The ordinary polls also show header 05000064. Valid readings 0/6.
AULA 76 fresh, Bluetooth fallback disabled. No independent vendor
display observation; the raw field 100 is not validated telemetry.

Windows display-only candidate requires rev 0002, mouse slot 2,
read-ready clear, valid link flags, 1..100 field, and identical candidate
in every attempted length/delay with at least two replies. Gray 100?
and explicit unverified tooltip/menu only. Not passed to Percent, history,
alerts, estimates or HA; clear on failed/inconsistent/unknown/absent
poll; scheduled skip suppresses it. No GET00 or new vendor writes.
Owner should record official GearHub percentage at the same time at
two different levels; if the field remains 100 despite a change it
must not be promoted. Apple strict decoding unchanged.

AULA reported numeric icon text overflowing: use actual glyph ink bounds
with 44x34 safe rectangle in a 64px circle. Native pixel-boundary tests
cover 76%, 100%, cached and unverified markers. Real tray DPI still open.
