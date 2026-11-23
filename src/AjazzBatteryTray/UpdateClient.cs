using System.Net;
using System.Net.Http;
using System.Text.Json;

namespace AjazzBatteryTray;

/// <summary>Read-only release lookup for the fixed project repository.</summary>
public sealed class UpdateClient
{
    public const string ReleasesPage = "https://github.com/iSentinel/AJAZZ-Battery-Tray/releases";
    private const string Api = "https://api.github.com/repos/iSentinel/AJAZZ-Battery-Tray/releases?per_page=100";
    private const int MaximumBytes = 2 * 1024 * 1024;
    public sealed record Candidate(ReleaseVersion Version, string Tag, string Page);

    private static readonly Lazy<UpdateRequestGate> Gate = new(() => new UpdateRequestGate());

    public static async Task<Candidate?> CheckAsync(ReleaseVersion installed,
        bool experimental, CancellationToken cancellationToken = default)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(15));
        return await Gate.Value.RunAsync(token => CheckCoreAsync(installed, experimental, token),
            timeout.Token).ConfigureAwait(false);
    }

    private static async Task<Candidate?> CheckCoreAsync(ReleaseVersion installed,
        bool experimental, CancellationToken cancellationToken)
    {
        using var handler = new HttpClientHandler { AllowAutoRedirect = false, UseCookies = false };
        using var client = new HttpClient(handler);
        using var request = new HttpRequestMessage(HttpMethod.Get, Api);
        request.Headers.UserAgent.ParseAdd("AJAZZBatteryTray-UpdateChecker/1.0");
        request.Headers.Accept.ParseAdd("application/vnd.github+json");
        using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead,
            cancellationToken).ConfigureAwait(false);
        if (response.StatusCode == HttpStatusCode.Forbidden ||
            response.StatusCode == HttpStatusCode.TooManyRequests)
            throw new HttpRequestException("GitHub release lookup limited.");
        response.EnsureSuccessStatusCode();
        if (response.Content.Headers.ContentLength > MaximumBytes)
            throw new InvalidDataException("Release listing exceeds size limit.");
        using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        using var body = new MemoryStream();
        byte[] buffer = new byte[8192];
        int count;
        while ((count = await stream.ReadAsync(buffer.AsMemory(), cancellationToken).ConfigureAwait(false)) > 0)
        {
            if (body.Length + count > MaximumBytes)
                throw new InvalidDataException("Release listing exceeds size limit.");
            body.Write(buffer, 0, count);
        }
        return Parse(body.ToArray(), installed, experimental);
    }

    /// <summary>Accept known tags and construct links locally, never trust remote URL fields.</summary>
    public static Candidate? Parse(ReadOnlyMemory<byte> json, ReleaseVersion installed, bool experimental)
    {
        if (json.Length > MaximumBytes) throw new InvalidDataException("Release listing too large.");
        using var document = JsonDocument.Parse(json);
        if (document.RootElement.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException("Invalid release listing.");
        var entries = new List<(string Tag, bool Draft, bool Prerelease)>();
        foreach (var item in document.RootElement.EnumerateArray())
        {
            if (item.ValueKind != JsonValueKind.Object ||
                !item.TryGetProperty("tag_name", out var tag) || tag.ValueKind != JsonValueKind.String ||
                !item.TryGetProperty("draft", out var draft) || !IsBoolean(draft) ||
                !item.TryGetProperty("prerelease", out var pre) || !IsBoolean(pre))
                throw new InvalidDataException("Invalid release metadata.");
            string name = tag.GetString()!;
            if (ReleaseVersion.Parse(name) is not null)
                entries.Add((name, draft.GetBoolean(), pre.GetBoolean()));
        }
        var version = UpdateRules.Newest(installed, entries, experimental);
        if (version is null) return null;
        var selected = entries.First(x => !x.Draft &&
            (version.Beta.HasValue ? experimental : !x.Prerelease) &&
            ReleaseVersion.Parse(x.Tag) == version);
        return new(version, selected.Tag, ReleasesPage + "/tag/" + Uri.EscapeDataString(selected.Tag));
    }

    private static bool IsBoolean(JsonElement item)
        => item.ValueKind is JsonValueKind.True or JsonValueKind.False;
}
