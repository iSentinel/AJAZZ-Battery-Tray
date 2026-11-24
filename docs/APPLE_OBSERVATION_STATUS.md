# Apple USB observation status

Universal macOS distinguishes a matching HID collection that cannot be
opened from one opened successfully but returning no validated charge.
If no matching device opens, the result is access unknown; it cannot
authorize RTC synchronization. High Sierra already distinguishes those
cases. Both retain only the timestamp of the last verified USB sample
in the current process session. The timestamp never appears as a fresh
percentage and never enters history or low-battery policy. It is
cleared after confirmed receiver absence, not advanced on unknown
results, and localized in EN/RU/UK. Apple readers do not expose a
stable per-receiver identity, so this is explicitly a session observation
rather than a claim about the currently attached device. A receiver
swapped without observed absence cannot be identified by this label.
No persistent cache, BLE merge or new HID report is introduced.
Offline native self-tests cover unknown/absence timestamp transitions
and Universal open-failure classification. Physical acceptance remains
separate.
