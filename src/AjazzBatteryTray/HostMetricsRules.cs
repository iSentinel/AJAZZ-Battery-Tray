using System.Globalization;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace AjazzBatteryTray;

/// <summary>Host-only metrics. Missing values must never be substituted with zero.</summary>
public sealed record HostHardwareMetrics(string Name, bool IsGpu,
    double? LoadPercent, double? TemperatureC);

/// <summary>Parse only CPU/GPU sensor readings from the local provider's JSON tree.</summary>
public static class HostMetricsRules
{
    private static readonly Regex ValuePattern = new(
        @"^\s*([+-]?\d+(?:[.,]\d+)?)\s*(%|°C)\s*$",
        RegexOptions.CultureInvariant, TimeSpan.FromMilliseconds(100));

    public static double? CpuLoad(ulong idleDelta, ulong kernelDelta, ulong userDelta)
    {
        double total = (double)kernelDelta + userDelta;
        return total > 0 && idleDelta <= kernelDelta
            ? 100.0 * (total - idleDelta) / total : null;
    }

    public static double? ParseValue(string? text, bool temperature)
    {
        if (string.IsNullOrWhiteSpace(text) || text.Length > 64) return null;
        Match match = ValuePattern.Match(text);
        if (!match.Success || match.Groups[2].Value != (temperature ? "°C" : "%"))
            return null;
        if (!double.TryParse(match.Groups[1].Value.Replace(',', '.'),
                NumberStyles.AllowLeadingSign | NumberStyles.AllowDecimalPoint,
                CultureInfo.InvariantCulture, out double value) || !double.IsFinite(value))
            return null;
        return temperature ? value is >= -50 and <= 150 ? value : null
            : value is >= 0 and <= 100 ? value : null;
    }

    public static IReadOnlyList<HostHardwareMetrics> ParseProvider(ReadOnlyMemory<byte> json)
    {
        using JsonDocument document = JsonDocument.Parse(json,
            new JsonDocumentOptions { MaxDepth = 32 });
        List<HostHardwareMetrics> result = new();
        foreach (JsonElement node in Walk(document.RootElement))
        {
            string? id = GetString(node, "HardwareId");
            string family = id?.Split('/', StringSplitOptions.RemoveEmptyEntries).FirstOrDefault() ?? "";
            bool gpu = family is "gpu-nvidia" or "gpu-amd" or "gpu-intel";
            bool cpu = family is "intelcpu" or "amdcpu" or "genericcpu";
            if (!gpu && !cpu) continue;
            result.Add(ReadHardware(node, gpu));
        }
        return result;
    }

    private static HostHardwareMetrics ReadHardware(JsonElement node, bool gpu)
    {
        JsonElement[] sensors = OwnSensors(node).ToArray();
        string[] loadNames = gpu ? new[] { "GPU Core", "GPU Total" }
            : new[] { "CPU Total" };
        string[] tempNames = gpu ? new[] { "GPU Core" }
            : new[] { "CPU Package", "Core (Tdie)", "Core (Tctl/Tdie)",
                "CPU (Tctl/Tdie)", "Core Max" };
        string name = GetString(node, "Text") ?? (gpu ? "GPU" : "CPU");
        name = new string(name.Where(c => !char.IsControl(c)).Take(100).ToArray());
        return new HostHardwareMetrics(name, gpu,
            Pick(sensors, "Load", loadNames, temperature: false),
            Pick(sensors, "Temperature", tempNames, temperature: true));
    }

    private static double? Pick(IEnumerable<JsonElement> sensors, string type,
        IEnumerable<string> names, bool temperature)
    {
        foreach (string name in names)
        foreach (JsonElement sensor in sensors)
        {
            if (GetString(sensor, "Type") != type ||
                GetString(sensor, "Text") != name) continue;
            double? value = ParseValue(GetString(sensor, "RawValue") ??
                GetString(sensor, "Value"), temperature);
            if (value.HasValue) return value;
        }
        return null;
    }

    private static IEnumerable<JsonElement> OwnSensors(JsonElement node)
    {
        foreach (JsonElement child in Children(node))
        {
            if (GetString(child, "HardwareId") is not null) continue;
            if (GetString(child, "SensorId") is not null) yield return child;
            foreach (JsonElement descendant in OwnSensors(child))
                yield return descendant;
        }
    }

    private static IEnumerable<JsonElement> Walk(JsonElement node)
    {
        if (node.ValueKind != JsonValueKind.Object) yield break;
        yield return node;
        foreach (JsonElement child in Children(node))
        foreach (JsonElement item in Walk(child))
            yield return item;
    }

    private static IEnumerable<JsonElement> Children(JsonElement node)
    {
        if (node.ValueKind == JsonValueKind.Object &&
            node.TryGetProperty("Children", out JsonElement children) &&
            children.ValueKind == JsonValueKind.Array)
            foreach (JsonElement child in children.EnumerateArray())
                yield return child;
    }

    private static string? GetString(JsonElement node, string property)
        => node.ValueKind == JsonValueKind.Object &&
            node.TryGetProperty(property, out JsonElement item) &&
            item.ValueKind == JsonValueKind.String ? item.GetString() : null;
}
