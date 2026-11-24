namespace AjazzBatteryTray;

/// <summary>Session-local, thread-owned gate for AJAZZ vendor I/O.</summary>
internal sealed class AjazzIoLease : IDisposable
{
    internal const string Name = "Local\\AJAZZBatteryTray_ApexVendorIo_v1";
    private readonly Mutex _mutex;

    private AjazzIoLease(Mutex mutex) => _mutex = mutex;

    internal static AjazzIoLease? TryAcquire()
    {
        Mutex mutex = new(false, Name);
        bool acquired = false;
        try
        {
            try { acquired = mutex.WaitOne(0); }
            catch (AbandonedMutexException) { acquired = true; }
            return acquired ? new AjazzIoLease(mutex) : null;
        }
        finally { if (!acquired) mutex.Dispose(); }
    }

    public void Dispose()
    {
        try { _mutex.ReleaseMutex(); }
        finally { _mutex.Dispose(); }
    }
}
