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

Console.WriteLine($"Summary: PASS={passed}, FAIL={failed}");
return failed == 0 ? 0 : 1;
