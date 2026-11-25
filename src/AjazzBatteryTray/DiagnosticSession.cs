using System.IO.Compression;
using System.Text;
using System.Text.Json;

namespace AjazzBatteryTray;

public enum DiagnosticMarker { Baseline, UsbSelected, BluetoothSelected, Sleep, Wake, Other, ReviewedReport }

/// <summary>Explicit, bounded, in-memory owner observations; markers are not detected facts.</summary>
public sealed class DiagnosticSession
{
    public const int MaximumReports = 32;
    public const int MaximumReportBytes = 1024 * 1024;
    public const int MaximumTotalBytes = 8 * MaximumReportBytes;
    private sealed record Snapshot(DiagnosticMarker Marker, DateTimeOffset AddedUtc, string Report, int Bytes);
    private readonly List<Snapshot> _reports = new();
    private int _bytes;
    public bool Active { get; private set; }
    public int Count => _reports.Count;

    public void Start()
    {
        Clear();
        Active = true;
    }

    public void Clear()
    {
        Active = false;
        _reports.Clear();
        _bytes = 0;
    }

    public bool Add(DiagnosticMarker marker, string report, DateTimeOffset now)
    {
        if (!Active || Count >= MaximumReports || !Enum.IsDefined(marker) ||
            string.IsNullOrWhiteSpace(report) || report.Length > MaximumReportBytes)
            return false;
        int bytes = Encoding.UTF8.GetByteCount(report);
        if (bytes > MaximumReportBytes || _bytes + bytes > MaximumTotalBytes) return false;
        if (Count > 0 && now <= _reports[^1].AddedUtc) return false;
        _reports.Add(new(marker, now.ToUniversalTime(), report, bytes));
        _bytes += bytes;
        return true;
    }

    /// <summary>Write separate unchanged report texts and an owner-marker manifest.</summary>
    public void Export(Stream destination)
    {
        if (!Active || Count < 2) throw new InvalidOperationException("Two snapshots required.");
        using var archive = new ZipArchive(destination, ZipArchiveMode.Create, leaveOpen: true);
        var entries = _reports.Select((x, i) => new {
            file = $"snapshot-{i + 1:D2}.txt", marker = x.Marker.ToString(),
            addedUtc = x.AddedUtc, bytes = x.Bytes
        }).ToArray();
        for (int i = 0; i < entries.Length; i++)
            Write(archive, entries[i].file, _reports[i].Report);
        Write(archive, "manifest.json", JsonSerializer.Serialize(new {
            schema = "diagnostic-session-v1", identityBinding = "NOT_VERIFIED",
            markers = "OWNER_ANNOTATED", entries
        }));
    }

    private static void Write(ZipArchive archive, string name, string text)
    {
        using var stream = archive.CreateEntry(name).Open();
        byte[] bytes = Encoding.UTF8.GetBytes(text);
        stream.Write(bytes);
    }
}
