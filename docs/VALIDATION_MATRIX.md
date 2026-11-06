# AJAZZ APEX — Implementation and Hardware Validation Matrix

This table separates **implemented code**, **GitHub CI results**, and
**tests actually completed with a physical mouse**. A successful build
is not evidence that a dock clock or wireless handover works on hardware.

## Evidence snapshot — 2026-11-06

| Capability | Implementation / CI | Physical validation |
| --- | --- | --- |
| AJ179 APEX battery via 2.4 GHz / 8K receiver | Windows implemented; CI PASS | **Confirmed:** real mouse battery percentage was shown in Windows |
| AJ179 APEX standard BLE Battery Level | Manual Windows GATT reader implemented; CI PASS | **Confirmed:** user read **83% — Fresh GATT Battery Level (2A19) read** |
| Windows automatic Bluetooth tray fallback | Explicit opt-in, session-only, no saved ID | **Pending:** USB unplug/replug, sleep/wake and repeated fresh GATT reads |
| USB vs Bluetooth priority | USB receiver wins while physically attached | **Pending:** verify real mode switching |
| Bluetooth retry delay | 1 / 2 / 5 / 10 minutes after repeated failures | **Pending:** sleeping/waking AJ179 APEX |
| Manual Bluetooth refresh | User initiated, selected paired device only | **Pending:** real sleep recovery |
| Windows low-battery and receiver alerts | Implemented and unit tested | **Pending:** real low-battery and disconnect scenario |
| Temporary Windows HID enumeration error | Unknown state kept separate from confirmed USB absence in code | **Pending:** real transient HID error |

| USB receiver disconnect and reconnect | State-handling code and unit tests | **Pending:** real sleep/replug matrix |
| Dock time and date sync | Documented 0x28 report implemented and tested | **Pending:** visibly confirm clock update on dock screen |
| AJ159 APEX via 8K receiver | Experimental shared-receiver implementation | **Pending:** actual AJ159 hardware |
| AJ159 APEX via Bluetooth | Standard Battery Service inspector available | **Pending:** actual AJ159 hardware |
| macOS battery / dock RTC | Swift universal build and self-tests PASS | **Pending:** real AJ179/AJ159 on a Mac |
| macOS Bluetooth and notifications | Manual CoreBluetooth and notification code build PASS | **Pending:** actual device and OS permission prompts |
| Windows installer | Inno Setup x64; GitHub smoke-test PASS | **Pending:** end-user upgrade/uninstall on own PC |
| RGB, GIF, DPI, polling-rate writes | Blocked by HID safety allowlist | **Not enabled:** requires confirmed read-back and recovery |
| Bluetooth charging status | Not implemented | **No validated charging report** |

The observed **83%** is one historical reading, not a permanent battery
level, and does not prove compatibility of all firmware variants or AJ159.

## Highest-value Windows hardware acceptance sequence

Use the newest package from
[GitHub Latest](https://github.com/iSentinel/AJAZZ-Battery-Tray/releases/latest).

1. Close the vendor AJAZZ utility to avoid HID conflicts, then run Battery
   Tray. Verify battery percentage over 2.4 GHz. Note the displayed source.
2. Switch AJ179 APEX to Bluetooth. Open **Check paired Bluetooth battery...**,
   select **AJ179 APEX**, click **Read selected battery** and confirm the
   message says **Fresh GATT Battery Level (2A19) read**.
3. Explicitly enable **Use this mouse in tray when 2.4 GHz receiver is
   absent (this session)**. The Bluetooth device ID stays in memory only.
4. **Physically unplug the 2.4 GHz USB receiver.** Confirm the tray switches
   to **Bluetooth** and shows a fresh percent, or clearly says unavailable.
5. Check another automatic GATT reading after 60 seconds. It must not be a
   Windows cached BatteryLife value. If the mouse sleeps, the indicator
   should become unavailable rather than remain at an obsolete percentage.
6. Wake the mouse. Use **Refresh Bluetooth battery now** to bypass the
   automatic retry delay. The success state should reset failure count.
7. Reinsert the USB receiver. Verify the tray now prioritizes USB.
   **If the USB receiver is present but the mouse is still in Bluetooth mode,
   the expected USB display may be unavailable**; Bluetooth is intentionally
   not substituted while USB is present.
8. Disable Bluetooth fallback, confirm the UI and diagnostics report it off,
   restart the application, and verify it has not silently re-enabled.
9. Copy **Bluetooth monitor status** and record the result. The copied report
   contains timestamps, counts and transport labels, **not MAC/USB IDs**.

## Dock clock acceptance

With the physical 8K receiver connected, run **Sync dock time now**. Compare
the displayed date/time on the dock against the Windows local date/time.
The application's "command sent" status confirms only that Windows accepted
the HID transfer, **not** that the dock applied it. Repeat after unplug,
resume from Windows sleep, and automatic five-minute synchronization.
Capture a screenshot of the dock only if needed, excluding personal data.

## Reporting

Use the [hardware validation issue form](https://github.com/iSentinel/AJAZZ-Battery-Tray/issues/new?template=hardware-validation.yml)
or paste the privacy-safe **Copy Bluetooth monitor status** text into this
conversation. Report PASS/FAIL and observed source/percentage, not device
instance IDs, serial numbers, addresses, raw packet dumps or unrelated
USB captures.

Do not enable unverified RGB/GIF/DPI/firmware operations to try to fix a
battery or clock problem.
