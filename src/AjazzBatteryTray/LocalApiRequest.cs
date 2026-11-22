using System.Security.Cryptography;
using System.Text;

namespace AjazzBatteryTray;

/// <summary>Strict, single-request loopback HTTP policy. No body or write routes.</summary>
public static class LocalApiRequest
{
    public const string Route = "/v1/batteries";
    public const int MaximumHeaderBytes = 8192;
    public static string NewToken() => Convert.ToHexString(RandomNumberGenerator.GetBytes(32));

    public static int Check(string header, int port, string token)
    {
        if (header.Length > MaximumHeaderBytes || !header.EndsWith("\r\n\r\n", StringComparison.Ordinal))
            return 400;
        if (header.Any(c => c != '\r' && c != '\n' && (c < 32 || c > 126)))
            return 400;
        string[] lines = header[..^4].Split("\r\n");
        if (lines.Any(line => line.Contains('\r') || line.Contains('\n'))) return 400;
        string[] request = lines[0].Split(' ');
        if (request.Length != 3 || request[2] != "HTTP/1.1") return 400;
        var headers = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (string line in lines.Skip(1))
        {
            int colon = line.IndexOf(':');
            if (colon <= 0 || !line[..colon].All(c => char.IsAsciiLetterOrDigit(c) || c == '-')
                || !headers.TryAdd(line[..colon], line[(colon + 1)..].Trim()))
                return 400;
        }
        if (!headers.TryGetValue("Host", out var host) || host != $"127.0.0.1:{port}")
            return 400;
        if (headers.ContainsKey("Transfer-Encoding") ||
            (headers.TryGetValue("Content-Length", out var length) && length != "0"))
            return 400;
        if (headers.ContainsKey("Origin")) return 403;
        if (!headers.TryGetValue("Authorization", out var auth) ||
            !TokenMatches(auth, token)) return 401;
        if (request[0] != "GET") return 405;
        if (request[1] != Route) return 404;
        return 200;
    }

    private static bool TokenMatches(string auth, string token)
    {
        const string prefix = "Bearer ";
        if (!auth.StartsWith(prefix, StringComparison.Ordinal) ||
            auth.Length != prefix.Length + token.Length) return false;
        return CryptographicOperations.FixedTimeEquals(
            Encoding.ASCII.GetBytes(auth[prefix.Length..]), Encoding.ASCII.GetBytes(token));
    }
}
