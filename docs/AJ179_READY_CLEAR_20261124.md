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

#132 Device Manager EN/RU/UK transition smoke checks PASS after correcting
the missing linked source and explicit tooltip replacement. Merged ef4e3c3.

For two new full reports from the same owner-confirmed receiver:

    python3 tools/compare_ready_clear.py --earlier earlier.txt --later later.txt

The offline comparator requires one rev 0002 receiver, the 65-byte
descriptor and all six 65/67-byte responses at 30/100/250 ms. It reports
CHANGED FIELD or UNCHANGED FIELD only for consistent, unverified matrices,
INCONCLUSIVE for missing/disagreeing evidence. Exit 0 is complete comparison,
not hardware validation. Distinct chronological UTC timestamps required.
It does not identify the physical receiver or validate GearHub's gauge.
No raw capture is committed or uploaded.

#133 passed Windows, Universal and Python checks (89 tests), merged
cff8181. The comparison now checks exact allowlisted F7 TX, GET 05
zero-filled request, successful response marker, matching header/length,
and ordering of each probe. An offline reconstruction of the two owner
report times and six identical status prefixes yields UNCHANGED FIELD.
This is replay of the visible sanitized evidence, not a new measurement or
an independent calibration. No physical proof of charge accuracy.

## Power-cycle follow-up — Nov 25, 01:19 Kyiv

Owner observed a lower tray value after switching the mouse off and on.
At 23:19:43 UTC the ordinary poll recorded 98, two successful headers
05000062 (65 and 67 bytes), not verified telemetry. The full matrix
at 23:19:53 UTC again contained 100 in all six responses, exact prefix
05000064010001020000, ready clear and 0/6 verified. The earlier 23:18:20
capture was 100. AULA was fresh 71 in both. This is evidence that the
field can vary, but it is not evidence of accurate or current charge.
Cause of the difference is unknown: cached or alternating receiver
status, capture timing or another device state are possible. Never
promote the field to telemetry. Keep ordinary and matrix observations
separate and flag disagreement in the offline comparison; an otherwise
unchanged full matrix must be INCONCLUSIVE if the ordinary field differs.
Do not send new opcodes or power-cycle automatically. Raw reports remain
local. Compare natural wake and next ordinary polls before another
explicit full capture, with GearHub closed.

## Owner follow-up: power-cycle-only changes

Owner reports the tray field stays unchanged during normal use and
changes only after switching the mouse off/on. This is consistent with,
but does not establish, cached status or radio battery update behavior.
#135 ordinary/full disagreement detection passed all three checks
(97 Python tests), merged 99a271a.

Windows extended reports now include a session-only streak for each
receiver: current unverified field, count of consecutive sampled
ordinary observations, first/last UTC and observed duration. Scheduled
skips do not increment the count, duplicate timestamp/field does not
count twice, changed fields or reversed timestamps start a new streak,
missing/invalid fields or absent/unknown receiver clear the streak.
A full matrix is not applied to the ordinary monitor, so it cannot
increment the streak. No extra HID I/O, disk persistence, alerts,
battery history, estimates or API fields. Long unchanged streaks do
not prove stale data or determine the true charge.

For the next field run, capture ordinary extended reports (not the
full vendor matrix) before switching the mouse off/on, after one normal
poll, and after several ordinary polls. Include whether GearHub is
closed and whether its gauge changes independently. No forced
discharge or repeated power-cycle automation.

## Additional ready-clear field observations — Nov 25

Two beta.60 owner reports at 05:39:38 and 05:43:23 UTC show respectively
95 and 94 in the ordinary poll and all six matching full F7/05 responses
(65/67 bytes, 30/100/250 ms), 0/6 validated battery readings each.
One receiver, 3151:5007 rev 0002, MI_02 FFFF:0002, feature length 65.
The ready flag remains clear. Values changed between captures, but the
reports do not independently establish physical model, charge, continuity
without power cycling, or freshness. Bluetooth fallback disabled; neither
capture contains an independent fresh GATT observation. Keep field
display-only and unverified. No new protocol requests or telemetry,
no raw captures published. AULA cached-to-fresh observation is recorded
separately in AULA_SLEEP_ACCEPTANCE.md.
