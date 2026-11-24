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
GearHub does not expose a numeric percentage according to the owner.
Compare the visual gauge and simultaneous raw field at different natural
charge levels; this is qualitative evidence, not numeric calibration.
If the field remains 100 despite a gauge change it must not be promoted. Apple strict decoding unchanged.

AULA reported numeric icon text overflowing: use actual glyph ink bounds
with 44x34 safe rectangle in a 64px circle. Native pixel-boundary tests
cover 76%, 100%, cached and unverified markers. Real tray DPI still open.

## Owner follow-up and diagnostic visibility

Build 9cd415b is the PR #130 merge test, identical tree to audit 6f165c3.
The 21:35 UTC report repeated all six ready-clear 100 prefixes and
AULA returned fresh 75. Owner confirmed GearHub's gauge looked full
(no numeric display), gray 100? appeared instead of ?, and AULA 75%
fit fully inside the tray icon. Visual acceptance 2/2 PASS; numeric
AJ179 accuracy still open. All six audit checks PASS at 6f165c3.

The next diagnostic format retains Battery: unavailable and the
existing matrix result when charge is unverified. It additionally
prints unverified mouse field (not telemetry)=100 in the ordinary
poll, per-receiver and full capture sections, and the agreement count
for the full matrix. A deferred sample does not expose the candidate
as current. No raw payloads or device identity are newly exported
by the extended report. No protocol/alert/history changes.

The diagnostic visibility PR #131 passed Windows, Universal and upgrade
CI and merged at c467172. Device Manager now renders the same display-only
candidate as the tray (100?, localized unverified status and tooltip).
The optional field belongs to the WinForms Entry only, not the shared
DeviceDashboardState used by the local API. The measurement time remains
unknown; verified, invalid, absent, unknown or skipped samples suppress the
candidate. Native EN/RU/UK transition smoke tests pending.
