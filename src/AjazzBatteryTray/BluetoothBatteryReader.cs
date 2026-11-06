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

/// <summary>Manually inspects paired devices and standard battery metadata.</summary>
public static class BluetoothBatteryReader
{
    private static readonly string[] Properties =
    {
        "System.Devices.BatteryLife",
        "System.Devices.Aep.ModelName"
    };

    /// <summary>List paired LE and Classic devices; never scan unpaired devices.</summary>
    public static async Task<IReadOnlyList<BluetoothCandidate>> FindPairedAsync(
        bool showAll = false)
    {
        var le = QueryPairedAsync(
            BluetoothLEDevice.GetDeviceSelectorFromPairingState(true), true);
        var classic = QueryPairedAsync(
            BluetoothDevice.GetDeviceSelectorFromPairingState(true), false);
        var results = await Task.WhenAll(le, classic);
        return results.SelectMany(x => x)
            .Where(x => showAll || BluetoothBatteryRules.IsCandidateName(x.DisplayName))
            .GroupBy(x => x.DeviceId, StringComparer.OrdinalIgnoreCase)
            .Select(x => x.First())
            .OrderBy(x => x.DisplayName, StringComparer.OrdinalIgnoreCase)
            .ToArray();
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

        return devices.Where(x => x.Pairing.IsPaired)
            .Select(x => CreateCandidate(x, lowEnergy)).ToArray();
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

    /// <summary>GATT read for BLE; Windows's cached property for Classic.</summary>
    public static async Task<(int? Percent, string Status)> ReadAsync(
        BluetoothCandidate selected)
    {
        if (!selected.IsLowEnergy)
            return ReadWindowsBattery(selected);

        var gatt = await ReadGattAsync(selected.DeviceId);
        if (gatt.Percent.HasValue) return gatt;
        return selected.WindowsPercent.HasValue
            ? (selected.WindowsPercent,
                "Battery reported by Windows (cached; may be stale).")
            : gatt;
    }

    private static (int?, string) ReadWindowsBattery(BluetoothCandidate selected)
        => selected.WindowsPercent.HasValue
            ? (selected.WindowsPercent,
                "Battery reported by Windows (cached; may be stale).")
            : (null, "Windows does not expose a battery percentage for this endpoint.");

    private static async Task<(int? Percent, string Status)> ReadGattAsync(
        string deviceId)
    {
        using BluetoothLEDevice? device = await BluetoothLEDevice.FromIdAsync(deviceId);
        if (device is null)
            return (null, "BLE endpoint cannot be opened by Windows.");

        var services = await device.GetGattServicesForUuidAsync(
            GattServiceUuids.Battery, BluetoothCacheMode.Uncached);
        if (services.Status != GattCommunicationStatus.Success)
            return (null, "Battery Service is unavailable or the mouse is asleep.");
        return await ReadServicesAsync(services.Services);
    }

    private static async Task<(int?, string)> ReadServicesAsync(
        IReadOnlyList<GattDeviceService> services)
    {
        try
        {
            if (services.Count == 0)
                return (null, "Battery Service (180F) not exposed.");
            foreach (GattDeviceService service in services)
            {
                var result = await ReadServiceAsync(service);
                if (result.Item1.HasValue) return result;
            }
            return (null, "No readable standard Battery Level (2A19).");
        }
        finally
        {
            foreach (GattDeviceService service in services) service.Dispose();
        }
    }

    private static async Task<(int?, string)> ReadServiceAsync(
        GattDeviceService service)
    {
        var found = await service.GetCharacteristicsForUuidAsync(
            GattCharacteristicUuids.BatteryLevel, BluetoothCacheMode.Uncached);
        if (found.Status != GattCommunicationStatus.Success)
            return (null, "Battery Level characteristic unavailable.");
        foreach (GattCharacteristic characteristic in found.Characteristics)
        {
            var read = await characteristic.ReadValueAsync(BluetoothCacheMode.Uncached);
            if (read.Status != GattCommunicationStatus.Success) continue;
            using DataReader reader = DataReader.FromBuffer(read.Value);
            byte[] value = new byte[read.Value.Length];
            reader.ReadBytes(value);
            if (BluetoothBatteryRules.TryParseLevel(value, out int level))
                return (level, "Fresh GATT Battery Level (2A19) read.");
        }
        return (null, "Battery Level is absent or has an invalid value.");
    }
}
