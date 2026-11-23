using System.Net;
using System.Net.Http.Headers;

namespace AjazzBatteryTray;

/// <summary>One explicit loopback read; no worker, credential persistence or retries.</summary>
public static class HaLocalClient
{
    public static async Task<LocalBatterySnapshot?> ReadAsync(int port, string token,
        CancellationToken cancellationToken = default)
    {
        if (port is < 1 or > 65535 || token is not { Length: 64 } ||
            !token.All(char.IsAsciiHexDigit))
            throw new ArgumentException("Invalid local API endpoint or credential.");
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(5));
        using var handler = new HttpClientHandler
        {
            AllowAutoRedirect = false, UseProxy = false, UseCookies = false
        };
        using var client = new HttpClient(handler);
        using var request = new HttpRequestMessage(HttpMethod.Get,
            $"http://127.0.0.1:{port}/v1/batteries");
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead,
            deadline.Token).ConfigureAwait(false);
        if (response.StatusCode == HttpStatusCode.ServiceUnavailable) return null;
        if (response.StatusCode != HttpStatusCode.OK)
            throw new InvalidDataException("Local API request rejected.");
        if (response.Content.Headers.ContentType?.MediaType != "application/json" ||
            response.Content.Headers.ContentLength > HaSnapshotDecoder.MaximumBytes)
            throw new InvalidDataException("Invalid local API response.");
        using var body = new MemoryStream();
        using var stream = await response.Content.ReadAsStreamAsync(deadline.Token).ConfigureAwait(false);
        byte[] buffer = new byte[4096];
        int count;
        while ((count = await stream.ReadAsync(buffer.AsMemory(), deadline.Token).ConfigureAwait(false)) > 0)
        {
            if (body.Length + count > HaSnapshotDecoder.MaximumBytes)
                throw new InvalidDataException("Local API response too large.");
            body.Write(buffer, 0, count);
        }
        return HaSnapshotDecoder.Decode(body.ToArray());
    }
}
