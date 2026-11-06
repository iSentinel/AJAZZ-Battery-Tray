using AjazzBatteryTray;

// Dependency-free tests run on Windows, macOS or Linux with .NET 8.
int passed = 0;
int failed = 0;

void Check(string name, bool valid)
{
    if (valid)
    {
        passed++;
        Console.WriteLine($"PASS {name}");
    }
    else
    {
        failed++;
        Console.WriteLine($"FAIL {name}");
    }
}

Check("100 percent", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 0, 0, 100, 1, 1, 1, 2 }) == 100);
Check("34 percent", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 0, 0, 34, 1, 1, 1, 2 }) == 34);
Check("missing link", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 0, 0, 0, 0, 0, 0, 0 }) is null);
Check("reject out of range", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 0, 0, 255 }) is null);
Check("reject malformed status", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 1, 0, 90 }) is null);
Check("reject wrong report id", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x04, 0, 0, 50 }) is null);
Check("reject short report", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 0, 0 }) is null);

AlertPolicy policy = new();
Check("normal battery no alert", policy.Evaluate(60) is null);
Check("first 20 percent alert", policy.Evaluate(20) == 20);
Check("same threshold not repeated", policy.Evaluate(18) is null);
Check("10 percent alert", policy.Evaluate(10) == 10);
Check("5 percent alert", policy.Evaluate(5) == 5);
Check("no duplicate at 4 percent", policy.Evaluate(4) is null);
Check("recharge resets", policy.Evaluate(60) is null && policy.Evaluate(19) == 20);

// The Windows report includes an empty HID report ID at byte 0.
var local = new DateTime(2026, 11, 6, 9, 57, 42);
byte[] clock = DockClockReport.Create(local);
Check("clock report is 65 bytes", clock.Length == 65);
Check("clock opcode and marker", clock[0] == 0 && clock[1] == 0x28 &&
    clock[8] == 0xD7);
Check("clock year is big endian", clock[9] == 0x07 && clock[10] == 0xEA);
Check("clock date", clock[11] == 11 && clock[12] == 6);
Check("clock time", clock[13] == 9 && clock[14] == 57 && clock[15] == 42);
Check("clock reserved bytes zero", clock.Skip(16).All(b => b == 0) &&
    clock.Skip(2).Take(6).All(b => b == 0));
Check("clock length validated", ThrowsBadReportLength());

DockClockSchedule schedule = new();
DateTimeOffset start = new(2026, 11, 6, 10, 0, 0, TimeSpan.Zero);
Check("clock auto disabled", !schedule.ShouldAttempt(start, false, true));
Check("clock initial sync", schedule.ShouldAttempt(start, true, true));
schedule.RecordAttempt(start);
Check("clock no rapid repeats", !schedule.ShouldAttempt(start.AddMinutes(1), true, true));
Check("clock periodic resync", schedule.ShouldAttempt(start.AddMinutes(5), true, true));
schedule.RecordAttempt(start.AddMinutes(5));
Check("clock receiver removed", !schedule.ShouldAttempt(start.AddMinutes(6), true, false));
Check("clock receiver reconnected", schedule.ShouldAttempt(start.AddMinutes(6), true, true));

// A corrected Windows clock must not postpone RTC synchronization for hours.
DockClockSchedule correctedClock = new();
Check("clock correction initial sync", correctedClock.ShouldAttempt(start, true, true));
correctedClock.RecordAttempt(start);
DateTimeOffset rolledBack = start.AddHours(-2);
Check("clock correction backwards triggers resync",
    correctedClock.ShouldAttempt(rolledBack, true, true));
correctedClock.RecordAttempt(rolledBack);
Check("clock correction does not cause repeat writes",
    !correctedClock.ShouldAttempt(rolledBack.AddMinutes(1), true, true));
Check("clock correction restores normal five-minute interval",
    correctedClock.ShouldAttempt(rolledBack.AddMinutes(5), true, true));

bool ThrowsBadReportLength()
{
    try
    {
        DockClockReport.Create(local, 16);
        return false;
    }
    catch (ArgumentOutOfRangeException)
    {
        return true;
    }
}

// History and connection rules run without real mouse hardware.
DateTimeOffset t0 = new(2026, 11, 6, 12, 0, 0, TimeSpan.Zero);
BatterySample online = new(t0, 74, "online");
Check("state with battery", BatteryHistoryRules.State(true, 74) == "online");
Check("state with asleep mouse", BatteryHistoryRules.State(true, null) == "unavailable");
Check("state without receiver", BatteryHistoryRules.State(false, null) == "disconnected");
Check("new point stored", BatteryHistoryRules.ShouldRecord(null, online));
Check("duplicate point suppressed", !BatteryHistoryRules.ShouldRecord(
    online, online with { Timestamp = t0.AddMinutes(1) }));
Check("five-minute sample kept", BatteryHistoryRules.ShouldRecord(
    online, online with { Timestamp = t0.AddMinutes(5) }));
Check("percentage change kept", BatteryHistoryRules.ShouldRecord(
    online, online with { Timestamp = t0.AddSeconds(30), Percent = 73 }));
Check("disconnect event kept", BatteryHistoryRules.ShouldRecord(
    online, new BatterySample(t0.AddSeconds(30), null, "disconnected")));
Check("history retention", BatteryHistoryRules.Retain(
    new[] { online with { Timestamp = t0.AddDays(-32) }, online },
    t0.AddSeconds(1)).Count == 1);

ConnectionAlertPolicy disconnectPolicy = new();
Check("no alert before first online", !disconnectPolicy.Evaluate(false, false));
Check("first online no disconnect alert", !disconnectPolicy.Evaluate(true, true));
Check("one missing poll ignored", !disconnectPolicy.Evaluate(false, false));
Check("second missing poll alerts", disconnectPolicy.Evaluate(false, false));
Check("no duplicate disconnect alert", !disconnectPolicy.Evaluate(false, false));
Check("reconnect resets disconnect", !disconnectPolicy.Evaluate(true, true));
Check("receiver present asleep ignored", !disconnectPolicy.Evaluate(false, true));
Check("disconnect alert after reconnect", !disconnectPolicy.Evaluate(false, false) &&
    disconnectPolicy.Evaluate(false, false));

// CSV must preserve valid values while rejecting inconsistent state rows.
string timeText = t0.ToString("O");
Check("CSV valid 0% online", BatteryHistoryCsv.Parse(
    $"{timeText},0,online")?.Percent == 0);
Check("CSV valid 100% online", BatteryHistoryCsv.Parse(
    $"{timeText},100,online")?.Percent == 100);
Check("CSV unavailable without percentage", BatteryHistoryCsv.Parse(
    $"{timeText},,unavailable")?.State == "unavailable");
Check("CSV disconnect without percentage", BatteryHistoryCsv.Parse(
    $"{timeText},,disconnected")?.State == "disconnected");
Check("CSV rejects online without percent", BatteryHistoryCsv.Parse(
    $"{timeText},,online") is null);
Check("CSV rejects disconnected with percent", BatteryHistoryCsv.Parse(
    $"{timeText},20,disconnected") is null);
Check("CSV rejects unavailable with percent", BatteryHistoryCsv.Parse(
    $"{timeText},20,unavailable") is null);
Check("CSV rejects invalid negative percentage", BatteryHistoryCsv.Parse(
    $"{timeText},-1,online") is null);
Check("CSV rejects 101 percent", BatteryHistoryCsv.Parse(
    $"{timeText},101,online") is null);
Check("CSV rejects malformed date", BatteryHistoryCsv.Parse(
    "not-a-date,40,online") is null);
Check("CSV rejects malformed state", BatteryHistoryCsv.Parse(
    $"{timeText},50,pending") is null);
Check("CSV rejects extra columns", BatteryHistoryCsv.Parse(
    $"{timeText},70,online,extra") is null);
Check("CSV rejects header as a sample",
    BatteryHistoryCsv.Parse(BatteryHistoryCsv.Header) is null);
BatterySample csvSample = new(t0, 0, "online");
Check("CSV round-trip preserves 0%", BatteryHistoryCsv.Parse(
    BatteryHistoryCsv.Format(csvSample)) == csvSample);
BatterySample gapSample = new(t0, null, "unavailable");
Check("CSV round-trip preserves gap", BatteryHistoryCsv.Parse(
    BatteryHistoryCsv.Format(gapSample)) == gapSample);
DateTimeOffset offsetTime = new(2026, 11, 7, 1, 30, 0,
    TimeSpan.FromHours(2));
BatterySample shifted = new(offsetTime, 86, "online");
Check("CSV normalizes timestamp to UTC", BatteryHistoryCsv.Parse(
    BatteryHistoryCsv.Format(shifted))?.Timestamp.Offset == TimeSpan.Zero);
Check("CSV header unchanged for existing files",
    BatteryHistoryCsv.Header == "utc_timestamp,percent,state");

// Stop unknown or malformed HID writes before they reach the receiver.
byte[] telemetry = new byte[65];
telemetry[1] = 0xF7;
Check("safe telemetry allowed", HidFeaturePolicy.IsApproved(telemetry));
Check("safe dock clock allowed", HidFeaturePolicy.IsApproved(clock));
Check("blocked button matrix command", !AllowedCommand(0x50));
Check("blocked screen upload", !AllowedCommand(0x25));
Check("blocked 24-bit display upload", !AllowedCommand(0x29));
Check("blocked GIF begin", !AllowedCommand(0x18));
Check("blocked firmware bootloader", !AllowedCommand(0x40));
byte[] damagedClock = (byte[])clock.Clone();
damagedClock[8] = 0;
Check("clock marker required", !HidFeaturePolicy.IsApproved(damagedClock));
damagedClock = (byte[])clock.Clone();
damagedClock[12] = 31;
damagedClock[11] = 2;
Check("impossible date rejected", !HidFeaturePolicy.IsApproved(damagedClock));
telemetry[5] = 42;
Check("nonzero telemetry payload blocked", !HidFeaturePolicy.IsApproved(telemetry));

bool AllowedCommand(byte opcode)
{
    byte[] frame = new byte[65];
    frame[1] = opcode;
    return HidFeaturePolicy.IsApproved(frame);
}

// Standard Battery Level is one byte 0..100; zero is a valid measured value.
Check("BLE candidate AJAZZ", BluetoothBatteryRules.IsCandidateName("AJAZZ AJ179"));
Check("BLE candidate AJ159", BluetoothBatteryRules.IsCandidateName("AJ159 APEX"));
Check("BLE reject unrelated", !BluetoothBatteryRules.IsCandidateName("Keyboard"));
Check("BLE reject empty name", !BluetoothBatteryRules.IsCandidateName(""));
Check("BLE 0% is valid", BatteryLevelMatches(new byte[] { 0 }, 0));
Check("BLE 57% is valid", BatteryLevelMatches(new byte[] { 57 }, 57));
Check("BLE 100% is valid", BatteryLevelMatches(new byte[] { 100 }, 100));
Check("BLE 101% invalid", !BluetoothBatteryRules.TryParseLevel(
    new byte[] { 101 }, out _));
Check("BLE no data invalid", !BluetoothBatteryRules.TryParseLevel(
    Array.Empty<byte>(), out _));
Check("BLE extra bytes invalid", !BluetoothBatteryRules.TryParseLevel(
    new byte[] { 55, 0 }, out _));

bool BatteryLevelMatches(byte[] bytes, int expected)
    => BluetoothBatteryRules.TryParseLevel(bytes, out int level) &&
       level == expected;

Check("history captures backward clock change",
    BatteryHistoryRules.ShouldRecord(online,
        online with { Timestamp = t0.AddMinutes(-15) }));
Check("Bluetooth timeout accepts completed task",
    BluetoothOperationTimeout.Run(Task.FromResult(73),
        TimeSpan.FromSeconds(1)).GetAwaiter().GetResult() == 73);
Check("Bluetooth timeout rejects invalid limit",
    ThrowsBadBluetoothLimit());
Check("Bluetooth pending operation times out",
    BluetoothTaskTimesOut());

bool ThrowsBadBluetoothLimit()
{
    try
    {
        BluetoothOperationTimeout.Run(Task.FromResult(1), TimeSpan.Zero);
        return false;
    }
    catch (ArgumentOutOfRangeException)
    {
        return true;
    }
}

bool BluetoothTaskTimesOut()
{
    try
    {
        TaskCompletionSource<int> pending = new();
        BluetoothOperationTimeout.Run(pending.Task,
            TimeSpan.FromMilliseconds(20)).GetAwaiter().GetResult();
        return false;
    }
    catch (TimeoutException)
    {
        return true;
    }
}

Check("Windows byte battery 0% accepted",
    WindowsLevelEquals((byte)0, 0));
Check("Windows byte battery 65% accepted",
    WindowsLevelEquals((byte)65, 65));
Check("Windows integer battery 100% accepted",
    WindowsLevelEquals(100, 100));
Check("Windows unknown sentinel 101 rejected",
    !BluetoothBatteryRules.TryParseWindowsLevel((byte)101, out _));
Check("Windows battery 255 rejected",
    !BluetoothBatteryRules.TryParseWindowsLevel((byte)255, out _));
Check("Windows battery negative rejected",
    !BluetoothBatteryRules.TryParseWindowsLevel(-1, out _));
Check("Windows null battery rejected",
    !BluetoothBatteryRules.TryParseWindowsLevel(null, out _));
Check("Windows battery string rejected",
    !BluetoothBatteryRules.TryParseWindowsLevel("75", out _));
Check("Bluetooth unnamed not auto-matched",
    !BluetoothBatteryRules.IsCandidateName("Unnamed paired device"));

bool WindowsLevelEquals(object raw, int expected)
    => BluetoothBatteryRules.TryParseWindowsLevel(raw, out int level) &&
       level == expected;

// A generic Windows mouse name must not be hidden after explicit Show all.
Check("BLE standard AJAZZ visible by default",
    BluetoothBatteryRules.ShouldShow("AJAZZ AJ179", false));
Check("BLE generic paired mouse hidden by default",
    !BluetoothBatteryRules.ShouldShow("Bluetooth Mouse", false));
Check("BLE generic paired mouse visible with Show all",
    BluetoothBatteryRules.ShouldShow("Bluetooth Mouse", true));
Check("BLE unnamed endpoint visible with Show all",
    BluetoothBatteryRules.ShouldShow(null, true));

// Automatic BLE fallback requires explicit opt-in and a direct GATT reading.
BluetoothAutoPolicy automaticBle = new();
Check("BLE auto disabled by default", !automaticBle.Enabled);
Check("BLE no polling without opt-in", !automaticBle.ShouldRead(false, t0));
int initialGeneration = automaticBle.Generation;
automaticBle.Enable(83, t0);
Check("BLE selection changes generation",
    automaticBle.Generation == initialGeneration + 1);
Check("BLE fresh 83% visible without USB", automaticBle.VisiblePercent(
    false, t0.AddSeconds(10)) == 83);
Check("BLE status shows USB primary", automaticBle.StatusText(
    true, false, t0.AddSeconds(10)).Contains("USB primary"));
Check("BLE status shows fresh GATT", automaticBle.StatusText(
    false, false, t0.AddSeconds(10)).Contains("83%"));
Check("BLE status shows polling", automaticBle.StatusText(
    false, true, t0.AddSeconds(10)).Contains("checking battery"));
Check("USB receiver always takes priority", automaticBle.VisiblePercent(
    true, t0.AddSeconds(10)) is null);
Check("BLE no read before one minute", !automaticBle.ShouldRead(
    false, t0.AddSeconds(59)));
Check("BLE read due after one minute", automaticBle.ShouldRead(
    false, t0.AddSeconds(60)));
Check("BLE no background read while USB present", !automaticBle.ShouldRead(
    true, t0.AddMinutes(5)));
Check("BLE reading expires instead of staying stale", automaticBle.VisiblePercent(
    false, t0.AddSeconds(121)) is null);
BluetoothBatteryResult direct = new(82, BluetoothBatterySource.DirectGatt,
    "Display text can change without changing trust.");
BluetoothBatteryResult cached = new(77, BluetoothBatterySource.WindowsCached,
    "Fresh GATT Battery Level (2A19) read.");
BluetoothBatteryResult missing = new(null, BluetoothBatterySource.Unavailable,
    "No battery response");
Check("typed GATT source accepts different display text", direct.IsFreshGatt);
Check("typed Windows cache rejected despite misleading text", !cached.IsFreshGatt);
Check("typed unavailable rejected", !missing.IsFreshGatt);
Check("direct out-of-range rejected", !new BluetoothBatteryResult(
    255, BluetoothBatterySource.DirectGatt, "GATT").IsFreshGatt);

automaticBle.RecordRead(direct, t0.AddMinutes(2));
Check("BLE direct refresh updates percent", automaticBle.VisiblePercent(
    false, t0.AddMinutes(2)) == 82);
automaticBle.RecordRead(cached, t0.AddMinutes(3));
Check("BLE cached read clears current value", automaticBle.VisiblePercent(
    false, t0.AddMinutes(3)) is null);
Check("BLE cached read counts one failure", automaticBle.ConsecutiveFailures == 1);
Check("BLE unavailable status shows failures", automaticBle.StatusText(
    false, false, t0.AddMinutes(3)).Contains("1 failed"));
Check("BLE last successful reading retained for diagnostics",
    automaticBle.LastSuccessfulRead == t0.AddMinutes(2));
automaticBle.RecordRead(new BluetoothBatteryResult(0,
    BluetoothBatterySource.DirectGatt, "GATT"), t0.AddMinutes(4));
Check("BLE zero accepted from valid GATT", automaticBle.VisiblePercent(
    false, t0.AddMinutes(4)) == 0);
Check("BLE fresh direct read clears failure count",
    automaticBle.ConsecutiveFailures == 0);
Check("BLE status can display measured zero", automaticBle.StatusText(
    false, false, t0.AddMinutes(4)).Contains("0%"));
automaticBle.RecordRead(missing, t0.AddMinutes(5));
Check("BLE missing reading shows unknown", automaticBle.VisiblePercent(
    false, t0.AddMinutes(5)) is null);
Check("BLE missing response increments failure count",
    automaticBle.ConsecutiveFailures == 1);
Check("BLE last success preserved after missing response",
    automaticBle.LastSuccessfulRead == t0.AddMinutes(4));
Check("BLE last GATT attempt timestamp recorded",
    automaticBle.LastAttempt == t0.AddMinutes(5));
Check("BLE backward clock correction triggers read", automaticBle.ShouldRead(
    false, t0.AddMinutes(-2)));

BatteryDisplayState usb = BatteryDisplayState.Resolve(true, 83, true, 77);
Check("USB receiver takes priority over BLE", usb.Source == BatteryTransport.Usb24GHz &&
    usb.Percent == 83);
BatteryDisplayState sleepingUsb = BatteryDisplayState.Resolve(true, null, true, 77);
Check("sleeping USB mouse does not use BLE", sleepingUsb.Source ==
    BatteryTransport.Usb24GHz && sleepingUsb.Percent is null);
BatteryDisplayState activeBle = BatteryDisplayState.Resolve(false, null, true, 77);
Check("absent USB uses BLE source", activeBle.Source ==
    BatteryTransport.Bluetooth && activeBle.Percent == 77);
BatteryDisplayState unavailableBle = BatteryDisplayState.Resolve(false,
    null, true, null);
Check("BLE unknown labelled as Bluetooth", unavailableBle.Source ==
    BatteryTransport.Bluetooth && !unavailableBle.HasReading);
BatteryDisplayState fallbackOff = BatteryDisplayState.Resolve(false,
    null, false, 77);
Check("disabled BLE not shown in tray", fallbackOff.Source ==
    BatteryTransport.Usb24GHz && !fallbackOff.HasReading);
Check("no USB disconnect alert during BLE fallback",
    !BatteryDisplayState.NotifyReceiverDisconnect(true, true));
// Windows HID enumeration failure is unknown, not physical USB removal.
Check("unknown USB state treated as present for alerts",
    BatteryDisplayState.SafeReceiverPresent(false, false));
Check("confirmed USB absence stays absent",
    !BatteryDisplayState.SafeReceiverPresent(false, true));
Check("confirmed USB presence stays present",
    BatteryDisplayState.SafeReceiverPresent(true, true));
Check("unknown USB cannot activate BLE fallback",
    !BatteryDisplayState.MayUseBluetooth(false, false));
Check("confirmed absence may activate opted-in BLE",
    BatteryDisplayState.MayUseBluetooth(false, true));
Check("present USB cannot activate BLE fallback",
    !BatteryDisplayState.MayUseBluetooth(true, true));
BatteryDisplayState uncertainUsb = BatteryDisplayState.Resolve(
    false, null, true, 83, presenceKnown: false);
Check("unknown USB status suppresses stale BLE reading",
    uncertainUsb.Source == BatteryTransport.Usb24GHz &&
    uncertainUsb.Percent is null);
Check("unknown USB status becomes unavailable history",
    BatteryHistoryRules.State(
        BatteryDisplayState.SafeReceiverPresent(false, false),
        null) == "unavailable");
ConnectionAlertPolicy transientError = new();
transientError.Evaluate(true, true);
Check("HID error does not count as disconnected",
    !transientError.Evaluate(false,
        BatteryDisplayState.SafeReceiverPresent(false, false)));
Check("first confirmed missing poll after error ignored",
    !transientError.Evaluate(false, false));
Check("second confirmed missing poll raises warning",
    transientError.Evaluate(false, false));

Check("USB disconnect alert preserved without BLE",
    BatteryDisplayState.NotifyReceiverDisconnect(true, false));

int beforeDisableGeneration = automaticBle.Generation;
automaticBle.Disable();
Check("BLE disable invalidates pending request generation",
    automaticBle.Generation == beforeDisableGeneration + 1);
Check("BLE disable erases transient reading", !automaticBle.Enabled &&
    automaticBle.VisiblePercent(false, t0.AddMinutes(5)) is null);
Check("BLE disable removes diagnostic counters",
    automaticBle.ConsecutiveFailures == 0 &&
    automaticBle.LastSuccessfulRead is null && automaticBle.LastAttempt is null);
Check("BLE status clearly shows off", automaticBle.StatusText(
    false, false, t0.AddMinutes(5)).EndsWith("off"));
automaticBle.RecordRead(missing, t0.AddMinutes(6));
Check("late BLE response ignored when disabled",
    automaticBle.ConsecutiveFailures == 0 && automaticBle.LastAttempt is null);

automaticBle.Enable(70, t0.AddMinutes(6));
Check("BLE reselect invalidates old request generation",
    automaticBle.Generation > beforeDisableGeneration + 1);
automaticBle.Disable();

// Repeated BLE errors trigger a conservative retry schedule, not constant reads.
BluetoothAutoPolicy backoff = new();
Check("BLE forced refresh requires opt-in", !backoff.CanRefreshNow(false));
backoff.Enable(83, t0);
Check("BLE force request allowed with USB absent", backoff.CanRefreshNow(false));
Check("BLE force request blocked while USB present", !backoff.CanRefreshNow(true));
Check("BLE normal interval is one minute",
    BluetoothAutoPolicy.RetryInterval(0) == TimeSpan.FromMinutes(1));
Check("BLE one failure delays two minutes",
    BluetoothAutoPolicy.RetryInterval(1) == TimeSpan.FromMinutes(2));
Check("BLE two failures delay five minutes",
    BluetoothAutoPolicy.RetryInterval(2) == TimeSpan.FromMinutes(5));
Check("BLE repeated failures cap at ten minutes",
    BluetoothAutoPolicy.RetryInterval(6) == TimeSpan.FromMinutes(10));
DateTimeOffset failedAt = t0.AddMinutes(1);
backoff.RecordRead(missing, failedAt);
Check("BLE no retry before two minutes", !backoff.ShouldRead(
    false, failedAt.AddSeconds(119)));
Check("BLE retry at two minutes", backoff.ShouldRead(
    false, failedAt.AddMinutes(2)));
failedAt = failedAt.AddMinutes(2);
backoff.RecordRead(missing, failedAt);
Check("BLE two failures wait five minutes", !backoff.ShouldRead(
    false, failedAt.AddMinutes(4)));
Check("BLE retry after five minutes", backoff.ShouldRead(
    false, failedAt.AddMinutes(5)));
failedAt = failedAt.AddMinutes(5);
backoff.RecordRead(missing, failedAt);
Check("BLE third failure delays ten minutes", !backoff.ShouldRead(
    false, failedAt.AddMinutes(9)));
Check("BLE retry at ten minutes", backoff.ShouldRead(
    false, failedAt.AddMinutes(10)));
backoff.RecordRead(direct, failedAt.AddMinutes(10));
Check("BLE good GATT read resets backoff", backoff.ConsecutiveFailures == 0 &&
    BluetoothAutoPolicy.RetryInterval(backoff.ConsecutiveFailures) ==
    TimeSpan.FromMinutes(1));
backoff.Disable();
Check("BLE manual refresh disabled after opting out",
    !backoff.CanRefreshNow(false));

Console.WriteLine($"Summary: PASS={passed}, FAIL={failed}");
return failed == 0 ? 0 : 1;
