namespace AjazzBatteryTray;

/// <summary>Serialize explicit/manual and automatic update requests without a worker or timer.</summary>
public sealed class UpdateRequestGate
{
    private readonly SemaphoreSlim _gate = new(1, 1);

    public async Task<T> RunAsync<T>(Func<CancellationToken, Task<T>> operation,
        CancellationToken cancellationToken)
    {
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            cancellationToken.ThrowIfCancellationRequested();
            return await operation(cancellationToken).ConfigureAwait(false);
        }
        finally { _gate.Release(); }
    }
}
