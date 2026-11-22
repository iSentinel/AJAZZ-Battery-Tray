# Battery history analytics (Windows)

Local per-device history is the only input. The legacy aggregate history
does not expose estimates because it may combine devices/transports. The
AULA history represents the single monitoring profile, not a manufacturer
verified serial identity; if the physical keyboard changes, its old history
may not represent the new keyboard.

## Runtime projection
- Use the latest contiguous non-increasing online segment with a maximum
  15-minute gap, at least 30 minutes, three observations and three percentage
  points of decline; require a final observation no more than 15 minutes old.
- A rise, missing/invalid observation, duplicate or backwards timestamp,
  or excessive gap terminates that segment.
- Rate is endpoint percentage difference divided by observed hours; projected
  remaining hours = final percent / rate. It is an estimate at the last
  measurement, not a countdown, guaranteed runtime or a charging-state sensor.
- Display the actual observation count, span and last timestamp. Refresh the
  history window to update the estimate. Insufficient evidence is unavailable.

## Observed discharge equivalents
Sum only adjacent observed downward changes between valid online samples
separated by no more than 15 minutes, divided by 100 percentage points.
This is observed movement within the selected time range, not physical
charge cycles, battery capacity, health or manufacturer cycle count.
Gaps and missing rows can undercount; noisy/quantized readings can overcount.
No valid adjacent pairs means unavailable rather than zero.

No new HID traffic, telemetry collection, uploads, or CSV format changes.
Real-device comparison and UI layout checks remain separate from CI.
