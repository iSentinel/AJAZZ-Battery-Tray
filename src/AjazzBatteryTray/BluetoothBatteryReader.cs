using Windows.Devices.Bluetooth;
using Windows.Devices.Bluetooth.GenericAttributeProfile;
using Windows.Devices.Enumeration;
using Windows.Storage.Streams;

namespace AjazzBatteryTray;

/// <summary>A paired LE mouse candidate; ID remains in memory only.</summary>
public sealed record BluetoothCandidate(string DisplayName, string DeviceId)
{
    public override string ToString() => DisplayName;
}

/// <summary>Explicit, read-only GATT Battery Service inspector for Windows.</summary>
public static class BluetoothBatteryReader
{
    /// <summary>Enumerate paired BLE devices only, never start an unpaired scan.</summary>
    public static async Task<IReadOnlyList<BluetoothCandidate>> FindPairedAsync()
    {
        string selector = BluetoothLEDevice.GetDeviceSelectorFromPairingState(true);
        DeviceInformationCollection devices = await DeviceInformation.FindAllAsync(selector);
        return devices.Where(x => x.Pairing.IsPaired &&
                                  BluetoothBatteryRules.IsCandidateName(x.Name))
            .OrderBy(x => x.Name, StringComparer.OrdinalIgnoreCase)
            .Select((x, index) => new BluetoothCandidate(
                $"{x.Name} (paired #{index + 1})", x.Id)).ToArray();
    }

    /// <summary>Read a standard one-byte battery value from the selected device.</summary>
    public static async Task<(int? Percent, string Status)> ReadAsync(
        BluetoothCandidate selected)
    {
        using BluetoothLEDevice? device =
            await BluetoothLEDevice.FromIdAsync(selected.DeviceId);
        if (device is null)
            return (null, "Selected device cannot be opened by Windows.");

        var services = await device.GetGattServicesForUuidAsync(
            GattServiceUuids.Battery, BluetoothCacheMode.Uncached);
        if (services.Status != GattCommunicationStatus.Success)
            return (null, "Battery Service query failed or device is sleeping.");

        return await ReadServicesAsync(services.Services);
    }

    private static async Task<(int?, string)> ReadServicesAsync(
        IReadOnlyList<GattDeviceService> services)
    {
        try
        {
            if (services.Count == 0)
                return (null, "Standard GATT Battery Service (180F) not exposed.");
            foreach (GattDeviceService service in services)
            {
                var result = await ReadServiceAsync(service);
                if (result.Item1.HasValue) return result;
            }
            return (null, "No readable standard Battery Level (2A19) value.");
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
                return (level, "Standard GATT Battery Level (2A19) read.");
        }

        return (null, "Characteristic absent or returned an invalid value.");
    }
}
