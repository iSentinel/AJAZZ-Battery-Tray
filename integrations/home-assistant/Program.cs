using AjazzBatteryTray;

if (args.Length == 1 && args[0] is "-h" or "--help")
{
    Console.WriteLine("AjazzHaPreview [--port PORT]");
    Console.WriteLine("Explicit local API preview. Requires an interactive terminal.");
    Console.WriteLine("Start Local API in the tray and paste its current token when prompted.");
    Console.WriteLine("No auto-start, MQTT, persistence or background service.");
    return 0;
}
int port = 18789;
if (args.Length != 0 && (args.Length != 2 || args[0] != "--port" ||
    !int.TryParse(args[1], out port) || port is < 1 or > 65535))
{
    Console.Error.WriteLine("FAIL: invalid arguments. See --help.");
    return 2;
}
if (Console.IsInputRedirected)
{
    Console.Error.WriteLine("FAIL: interactive terminal required.");
    return 2;
}
using var cancel = new CancellationTokenSource();
Console.CancelKeyPress += (_, e) => { e.Cancel = true; cancel.Cancel(); };
try
{
    string token = ReadToken();
    var first = await HaLocalClient.ReadAsync(port, token, cancel.Token);
    if (first is null)
    {
        Console.Error.WriteLine("FAIL: snapshot unavailable.");
        return 1;
    }
    Console.WriteLine("Available session rows (not permanent device identities):");
    for (int i = 0; i < first.Devices.Count; i++)
    {
        var row = first.Devices[i];
        Console.WriteLine($"{i + 1,3}  {row.Source,-16} {row.SessionSlot,3}  {row.Status}");
    }
    Console.Write("Select a row number, or q to exit: ");
    string? choice = Console.ReadLine();
    if (choice == "q") return 0;
    if (!int.TryParse(choice, out int index) || index < 1 || index > first.Devices.Count)
    {
        Console.Error.WriteLine("FAIL: invalid selection.");
        return 2;
    }
    var selected = first.Devices[index - 1];
    Console.Write($"Bind {selected.Source} slot {selected.SessionSlot} for this API session? [y/N] ");
    if (Console.ReadLine() != "y") return 0;
    var mapping = HaSessionMapping.Bind(first, selected.Source, selected.SessionSlot);
    var next = await HaLocalClient.ReadAsync(port, token, cancel.Token);
    var reading = mapping.Read(next, DateTimeOffset.UtcNow);
    Console.WriteLine(reading.Available
        ? $"PASS: fresh battery {reading.BatteryPercent}%"
        : $"UNAVAILABLE: {reading.Status}");
    return reading.Available ? 0 : 1;
}
catch (Exception error) when (error is ArgumentException or InvalidDataException or
    HttpRequestException or IOException or OperationCanceledException)
{
    // Never print request headers, tokens, raw responses or exception messages.
    Console.Error.WriteLine("FAIL: local API preview failed or was cancelled.");
    return 1;
}

static string ReadToken()
{
    Console.Write("API token (hidden): ");
    var token = new System.Text.StringBuilder(64);
    while (true)
    {
        var key = Console.ReadKey(intercept: true);
        if (key.Key == ConsoleKey.Enter) break;
        if (key.Key == ConsoleKey.Escape) throw new OperationCanceledException();
        if (key.Key == ConsoleKey.Backspace)
        {
            if (token.Length > 0) token.Length--;
        }
        else if (char.IsAsciiHexDigit(key.KeyChar) && token.Length < 64)
            token.Append(key.KeyChar);
        else if (!char.IsControl(key.KeyChar))
            throw new ArgumentException("Invalid token.");
    }
    Console.WriteLine();
    if (token.Length != 64) throw new ArgumentException("Invalid token.");
    return token.ToString();
}
