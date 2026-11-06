using Windows.Devices.Bluetooth;
using Windows.Devices.Bluetooth.GenericAttributeProfile;
using Windows.Devices.Enumeration;
using Windows.Storage.Streams;

namespace AjazzBatteryTray;

/// <summary>One paired Windows Bluetooth endpoint, held in memory only.</summary>
public sealed record BluetoothCandidate(
    string DisplayName, string DeviceId, bool IsLowEnergy, int? WindowsPercent)
{
    public override string ToString()
        => $"{DisplayName} ({(IsLowEnergy ? "BLE" : "Classic")})";
}

/// <summary>Device counts and errors without addresses or Windows instance IDs.</summary>
public sealed record BluetoothDiscovery(
    IReadOnlyList<BluetoothCandidate> Candidates,
    int LeCount, int ClassicCount,
    string? LeError, string? ClassicError)
{
    public string Summary =>
        $"Found {LeCount} BLE and {ClassicCount} Classic paired endpoints." +
        (LeError is null ? "" : $" BLE query failed: {LeError}.") +
        (ClassicError is null ? "" : $" Classic query failed: {ClassicError}.");
}

/// <summary>Manually inspects paired devices and standard battery metadata.</summary>
public static class BluetoothBatteryReader
{
    private static readonly string[] Properties =
    {
        "System.Devices.BatteryLife",
        "System.Devices.Aep.ModelName"
    };

    /// <summary>Search both paired transports, tolerating one unavailable API.</summary>
    public static async Task<BluetoothDiscovery> FindPairedAsync(bool showAll = false)
    {
        var le = QuerySafeAsync(
            BluetoothLEDevice.GetDeviceSelectorFromPairingState(true), true);
        var classic = QuerySafeAsync(
            BluetoothDevice.GetDeviceSelectorFromPairingState(true), false);
        TransportResult[] results = await Task.WhenAll(le, classic);
        var candidates = results.SelectMany(x => x.Devices)
            .Where(x => BluetoothBatteryRules.ShouldShow(x.DisplayName, showAll))
            .GroupBy(x => x.DeviceId, StringComparer.OrdinalIgnoreCase)
            .Select(x => x.First())
            .OrderBy(x => x.DisplayName, StringComparer.OrdinalIgnoreCase)
            .ToArray();
        return new BluetoothDiscovery(candidates, results[0].Devices.Count,
            results[1].Devices.Count, results[0].Error, results[1].Error);
    }

    private sealed record TransportResult(
        IReadOnlyList<BluetoothCandidate> Devices, string? Error);

    /// <summary>Bound each transport separately to preserve partial results.</summary>
    private static async Task<TransportResult> QuerySafeAsync(
        string selector, bool lowEnergy)
    {
        try
        {
            var devices = await BluetoothOperationTimeout.Run(
                QueryPairedAsync(selector, lowEnergy), TimeSpan.FromSeconds(8));
            return new TransportResult(devices, null);
        }
        catch (Exception error)
        {
            string transport = lowEnergy ? "BLE" : "Classic";
            string kind = error.GetType().Name;
            FileLog.Write("WARN", $"{transport} paired lookup failed: {kind}");
            return new TransportResult(Array.Empty<BluetoothCandidate>(), kind);
        }
    }

    private static async Task<IReadOnlyList<BluetoothCandidate>> QueryPairedAsync(
        string selector, bool lowEnergy)
    {
        DeviceInformationCollection devices;
        try
        {
            devices = await DeviceInformation.FindAllAsync(selector, Properties,
                DeviceInformationKind.AssociationEndpoint);
        }
        catch (ArgumentException)
        {
            devices = await DeviceInformation.FindAllAsync(selector);
        }

        // The selector already requires pairing. Some Windows AEP entries
        // report Pairing.IsPaired inconsistently, so do not filter twice.
        return devices.Select(x => CreateCandidate(x, lowEnergy)).ToArray();
    }

    private static BluetoothCandidate CreateCandidate(DeviceInformation item,
        bool lowEnergy)
    {
        string name = item.Name;
        if (string.IsNullOrWhiteSpace(name) &&
            item.Properties.TryGetValue("System.Devices.Aep.ModelName", out var model))
        {
            name = model as string ?? "";
        }

        if (string.IsNullOrWhiteSpace(name)) name = "Unnamed paired device";
        int? cached = item.Properties.TryGetValue(
            "System.Devices.BatteryLife", out var raw) &&
            BluetoothBatteryRules.TryParseWindowsLevel(raw, out int percent)
                ? percent : null;
        return new BluetoothCandidate(name, item.Id, lowEnergy, cached);
    }

    /// <summary>Read direct GATT when possible; label Windows cache separately.</summary>
    public static async Task<BluetoothBatteryResult> ReadAsync(
        BluetoothCandidate selected)
    {
        if (!selected.IsLowEnergy) return ReadWindowsBattery(selected);

        BluetoothBatteryResult gatt;
        try
        {
            gatt = await ReadGattAsync(selected.DeviceId);
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "GATT read unavailable: " +
                error.GetType().Name);
            gatt = Missing("Unable to read the GATT Battery Service.");
        }

        return gatt.IsFreshGatt ? gatt :
            selected.WindowsPercent.HasValue ? ReadWindowsBattery(selected) : gatt;
    }

    private static BluetoothBatteryResult ReadWindowsBattery(
        BluetoothCandidate selected)
        => selected.WindowsPercent.HasValue
            ? new(selected.WindowsPercent, BluetoothBatterySource.WindowsCached,
                "Battery reported by Windows (cached; may be stale).")
            : Missing("Windows does not expose a battery percentage for this endpoint.");

    private static BluetoothBatteryResult Missing(string status)
        => new(null, BluetoothBatterySource.Unavailable, status);

    private static async Task<BluetoothBatteryResult> ReadGattAsync(string deviceId)
    {
        using BluetoothLEDevice? device =
            await BluetoothLEDevice.FromIdAsync(deviceId);
        if (device is null)
            return Missing("BLE endpoint cannot be opened by Windows.");

        var services = await device.GetGattServicesForUuidAsync(
            GattServiceUuids.Battery, BluetoothCacheMode.Uncached);
        if (services.Status != GattCommunicationStatus.Success)
            return Missing("Battery Service is unavailable or the mouse is asleep.");
        return await ReadServicesAsync(services.Services);
    }

    private static async Task<BluetoothBatteryResult> ReadServicesAsync(
        IReadOnlyList<GattDeviceService> services)
    {
        try
        {
            if (services.Count == 0)
                return Missing("Battery Service (180F) not exposed.");
            foreach (GattDeviceService service in services)
            {
                BluetoothBatteryResult result = await ReadServiceAsync(service);
                if (result.IsFreshGatt) return result;
            }
            return Missing("No readable standard Battery Level (2A19).");
        }
        finally
        {
            foreach (GattDeviceService service in services) service.Dispose();
        }
    }

    private static async Task<BluetoothBatteryResult> ReadServiceAsync(
        GattDeviceService service)
    {
        var found = await service.GetCharacteristicsForUuidAsync(
            GattCharacteristicUuids.BatteryLevel, BluetoothCacheMode.Uncached);
        if (found.Status != GattCommunicationStatus.Success)
            return Missing("Battery Level characteristic unavailable.");

        foreach (GattCharacteristic characteristic in found.Characteristics)
        {
            var read = await characteristic.ReadValueAsync(
                BluetoothCacheMode.Uncached);
            if (read.Status != GattCommunicationStatus.Success) continue;
            using DataReader reader = DataReader.FromBuffer(read.Value);
            byte[] value = new byte[read.Value.Length];
            reader.ReadBytes(value);
            if (BluetoothBatteryRules.TryParseLevel(value, out int percent))
                return new(percent, BluetoothBatterySource.DirectGatt,
                    "Fresh GATT Battery Level (2A19) read.");
        }

        return Missing("Battery Level is absent or has an invalid value.");
    }
}
