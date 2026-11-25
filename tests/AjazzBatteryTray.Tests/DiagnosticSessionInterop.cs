using AjazzBatteryTray;

/// <summary>Export two synthetic passive reports through the actual C# session writer.</summary>
internal static class DiagnosticSessionInterop
{
    public static int Run(string[] args)
    {
        if (args.Length != 2 || args[0] != "--export-diagnostic-session-fixture") return 2;
        var session = new DiagnosticSession();
        session.Start();
        var first = DateTimeOffset.Parse("2026-11-25T07:00:00.1234567+00:00");
        var second = first.AddMinutes(1);
        if (!session.Add(DiagnosticMarker.Baseline, Report(first, false), first.AddSeconds(1)) ||
            !session.Add(DiagnosticMarker.BluetoothSelected, Report(second, true), second.AddSeconds(1)))
            return 1;
        try
        {
            using var output = new FileStream(args[1], FileMode.CreateNew, FileAccess.Write, FileShare.None);
            session.Export(output);
            Console.WriteLine("PASS: synthetic diagnostic session exported through production writer");
            return 0;
        }
        catch (IOException)
        {
            Console.Error.WriteLine("FAIL: unable to create new synthetic fixture");
            return 1;
        }
    }

    private static string Report(DateTimeOffset stamp, bool sampled)
    {
        string time = stamp.ToString("O");
        string sample = sampled ? time : "never";
        string present = sampled ? "True" : "unknown";
        string aulaBattery = sampled ? "62" : "unavailable";
        string inspector = sampled
            ? "[Bluetooth manual inspection — historical, not a fresh request]\n" +
              "Manual operation pending: False\n" +
              $"Last manual result: AJ179 APEX; transport=BLE; battery=83; source=DirectGatt; completed UTC={time}; historical=true\n" +
              $"Last direct GATT result: AJ179 APEX; transport=BLE; battery=83; source=DirectGatt; completed UTC={time}; historical=true"
            : "[Bluetooth manual inspection — historical] Not opened this session.";
        return $"""
            AJAZZ Battery Tray extended diagnostic report
            Report schema: windows-extended-v1
            App version: synthetic-interop
            Report UTC: {time}
            [AJAZZ last ordinary poll — not a fresh request]
            Completed UTC: {sample}
            Receiver present: {present}; presence known: {present}
            Battery: unavailable; status: synthetic fixture
            [AULA L99 last measurement]
            Auto monitoring: True; interval=30s; UTC: {sample}
            Receiver present: {present}; presence known: {present}
            Battery: {aulaBattery}; status: synthetic fixture
            Last successful battery: {aulaBattery}; UTC: {sample}; Consecutive no-reply polls: 0; Cache lifetime hours: 24; Display cache active: False
            {inspector}
            """;
    }
}
