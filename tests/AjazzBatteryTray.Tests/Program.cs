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

Console.WriteLine($"Summary: PASS={passed}, FAIL={failed}");
return failed == 0 ? 0 : 1;
