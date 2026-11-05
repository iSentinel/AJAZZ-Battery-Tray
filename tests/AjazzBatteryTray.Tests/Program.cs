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

Console.WriteLine($"Summary: PASS={passed}, FAIL={failed}");
return failed == 0 ? 0 : 1;
