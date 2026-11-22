using System.Net;
using System.Net.Sockets;
using System.Text;

namespace AjazzBatteryTray;

/// <summary>Explicitly started, IPv4 loopback-only, read-only snapshot listener.</summary>
public sealed class LocalApiServer : IAsyncDisposable
{
    private readonly TcpListener _listener;
    private readonly LocalSnapshotStore _store;
    private readonly CancellationTokenSource _stop = new();
    private readonly Task _worker;
    private int _disposed;
    public string Token { get; } = LocalApiRequest.NewToken();
    public int Port { get; }
    public string Endpoint => $"http://127.0.0.1:{Port}{LocalApiRequest.Route}";

    public LocalApiServer(LocalSnapshotStore store, int port = 18789)
    {
        _store = store;
        _listener = new TcpListener(IPAddress.Loopback, port);
        _listener.ExclusiveAddressUse = true;
        try { _listener.Start(8); }
        catch { _listener.Stop(); _stop.Dispose(); throw; }
        Port = ((IPEndPoint)_listener.LocalEndpoint).Port;
        _worker = Task.Run(RunAsync);
    }

    private async Task RunAsync()
    {
        while (!_stop.IsCancellationRequested)
        {
            TcpClient client;
            try { client = await _listener.AcceptTcpClientAsync(_stop.Token).ConfigureAwait(false); }
            catch (OperationCanceledException) { break; }
            catch (SocketException) when (_stop.IsCancellationRequested) { break; }
            catch (ObjectDisposedException) when (_stop.IsCancellationRequested) { break; }
            using (client)
            {
                if (_stop.IsCancellationRequested) break;
                using var deadline = CancellationTokenSource.CreateLinkedTokenSource(_stop.Token);
                deadline.CancelAfter(TimeSpan.FromSeconds(3));
                try { await RespondAsync(client, deadline.Token).ConfigureAwait(false); }
                catch (IOException) { }
                catch (SocketException) { }
                catch (OperationCanceledException) { }
            }
        }
    }

    private async Task RespondAsync(TcpClient client, CancellationToken cancellationToken)
    {
        using var stream = client.GetStream();
        string? header = await ReadHeaderAsync(stream, cancellationToken).ConfigureAwait(false);
        int status = header is null ? 400 : LocalApiRequest.Check(header, Port, Token);
        byte[] body = Array.Empty<byte>();
        if (status == 200)
        {
            var snapshot = _store.Read(DateTimeOffset.UtcNow);
            if (snapshot is null) status = 503;
            else body = snapshot.Export();
        }
        string reason = status switch
        {
            200 => "OK", 400 => "Bad Request", 401 => "Unauthorized",
            403 => "Forbidden", 404 => "Not Found", 405 => "Method Not Allowed",
            _ => "Service Unavailable"
        };
        var response = Encoding.ASCII.GetBytes($"HTTP/1.1 {status} {reason}\r\n" +
            $"Content-Type: application/json\r\nContent-Length: {body.Length}\r\n" +
            "Cache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\n" +
            (status == 401 ? "WWW-Authenticate: Bearer\r\n" : "") +
            (status == 405 ? "Allow: GET\r\n" : "") + "Connection: close\r\n\r\n");
        await stream.WriteAsync(response, cancellationToken).ConfigureAwait(false);
        if (body.Length > 0)
            await stream.WriteAsync(body, cancellationToken).ConfigureAwait(false);
    }

    private static async Task<string?> ReadHeaderAsync(NetworkStream stream, CancellationToken token)
    {
        byte[] buffer = new byte[LocalApiRequest.MaximumHeaderBytes];
        int used = 0;
        while (used < buffer.Length)
        {
            int count = await stream.ReadAsync(buffer.AsMemory(used), token).ConfigureAwait(false);
            if (count == 0) return null;
            int first = Math.Max(3, used);
            used += count;
            for (int i = first; i < used; i++)
            {
                if (buffer[i - 3] != 13 || buffer[i - 2] != 10 ||
                    buffer[i - 1] != 13 || buffer[i] != 10) continue;
                if (i != used - 1 || buffer.Take(used).Any(b => b > 127)) return null;
                return Encoding.ASCII.GetString(buffer, 0, used);
            }
        }
        return null;
    }

    public async ValueTask DisposeAsync()
    {
        if (Interlocked.Exchange(ref _disposed, 1) != 0) return;
        _stop.Cancel();
        _listener.Stop();
        try { await _worker.ConfigureAwait(false); }
        finally { _stop.Dispose(); }
    }
}
