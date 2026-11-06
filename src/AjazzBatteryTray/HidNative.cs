using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace AjazzBatteryTray;

/// <summary>Windows HID and SetupAPI calls, with no third-party driver needed.</summary>
internal static class HidNative
{
    private const uint PresentDeviceInterfaces = 0x12;
    private const uint ShareReadWrite = 0x03;
    private const uint OpenExisting = 3;
    private const uint ReadWrite = 0xC0000000;
    private static readonly IntPtr InvalidPointer = new(-1);

    [StructLayout(LayoutKind.Sequential)]
    private struct InterfaceData
    {
        public uint Size;
        public Guid ClassGuid;
        public uint Flags;
        public IntPtr Reserved;
    }

    [StructLayout(LayoutKind.Sequential)]
    internal struct HidCaps
    {
        public ushort Usage;
        public ushort UsagePage;
        public ushort InputReportByteLength;
        public ushort OutputReportByteLength;
        public ushort FeatureReportByteLength;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 17)]
        public ushort[] Reserved;
        public ushort NumberLinkCollectionNodes;
        public ushort NumberInputButtonCaps;
        public ushort NumberInputValueCaps;
        public ushort NumberInputDataIndices;
        public ushort NumberOutputButtonCaps;
        public ushort NumberOutputValueCaps;
        public ushort NumberOutputDataIndices;
        public ushort NumberFeatureButtonCaps;
        public ushort NumberFeatureValueCaps;
        public ushort NumberFeatureDataIndices;
    }

    [DllImport("hid.dll")]
    private static extern void HidD_GetHidGuid(out Guid guid);

    [DllImport("setupapi.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr SetupDiGetClassDevs(
        ref Guid classGuid, string? enumerator, IntPtr parent, uint flags);

    [DllImport("setupapi.dll", SetLastError = true)]
    private static extern bool SetupDiEnumDeviceInterfaces(
        IntPtr deviceSet, IntPtr deviceInfo, ref Guid classGuid,
        uint index, ref InterfaceData data);

    [DllImport("setupapi.dll", EntryPoint = "SetupDiGetDeviceInterfaceDetailW",
        CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool SetupDiGetDeviceInterfaceDetail(
        IntPtr deviceSet, ref InterfaceData data, IntPtr detail,
        uint detailSize, out uint needed, IntPtr deviceInfo);

    [DllImport("setupapi.dll", SetLastError = true)]
    private static extern bool SetupDiDestroyDeviceInfoList(IntPtr deviceSet);

    [DllImport("kernel32.dll", EntryPoint = "CreateFileW", CharSet = CharSet.Unicode,
        SetLastError = true)]
    private static extern SafeFileHandle CreateFile(
        string name, uint desiredAccess, uint shareMode, IntPtr security,
        uint creation, uint flags, IntPtr template);

    [DllImport("hid.dll", SetLastError = true)]
    private static extern bool HidD_GetPreparsedData(
        SafeFileHandle device, out IntPtr data);

    [DllImport("hid.dll")]
    private static extern bool HidD_FreePreparsedData(IntPtr data);

    [DllImport("hid.dll")]
    private static extern int HidP_GetCaps(IntPtr data, out HidCaps caps);

    [DllImport("hid.dll", SetLastError = true)]
    internal static extern bool HidD_SetFeature(
        SafeFileHandle device, [In] byte[] report, int reportLength);

    [DllImport("hid.dll", SetLastError = true)]
    internal static extern bool HidD_GetFeature(
        SafeFileHandle device, [In, Out] byte[] report, int reportLength);


    [StructLayout(LayoutKind.Sequential)]
    internal struct HidAttributes
    {
        public uint Size;
        public ushort VendorID;
        public ushort ProductID;
        public ushort VersionNumber;
    }

    [DllImport("hid.dll", SetLastError = true)]
    private static extern bool HidD_GetAttributes(
        SafeFileHandle device, ref HidAttributes attributes);

    [DllImport("hid.dll", SetLastError = true)]
    private static extern bool HidD_GetProductString(
        SafeFileHandle device, [Out] byte[] buffer, int length);

    /// <summary>Read manufacturer-provided product metadata, never the serial.</summary>
    internal static string? GetProductName(SafeFileHandle handle)
    {
        byte[] buffer = new byte[256];
        if (!HidD_GetProductString(handle, buffer, buffer.Length)) return null;
        string value = Encoding.Unicode.GetString(buffer).Split('\0')[0];
        string clean = new(value.Where(ch => !char.IsControl(ch)).Take(100).ToArray());
        return string.IsNullOrWhiteSpace(clean) ? null : clean.Trim();
    }

    /// <summary>Retrieve USB revision (bcdDevice), not firmware version.</summary>
    internal static HidAttributes? GetAttributes(SafeFileHandle handle)
    {
        HidAttributes value = new() { Size = (uint)Marshal.SizeOf<HidAttributes>() };
        return HidD_GetAttributes(handle, ref value) ? value : null;
    }

    /// <summary>Enumerates current HID interface paths (not all PnP devices).</summary>
    internal static IReadOnlyList<string> FindAjazzPaths()
    {
        HidD_GetHidGuid(out Guid guid);
        IntPtr deviceSet = SetupDiGetClassDevs(ref guid, null,
            IntPtr.Zero, PresentDeviceInterfaces);
        if (deviceSet == InvalidPointer)
        {
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }

        try
        {
            return ReadPaths(deviceSet, ref guid);
        }
        finally
        {
            SetupDiDestroyDeviceInfoList(deviceSet);
        }
    }

    private static IReadOnlyList<string> ReadPaths(IntPtr deviceSet, ref Guid guid)
    {
        List<string> paths = new();
        for (uint index = 0; ; index++)
        {
            InterfaceData data = new() { Size = (uint)Marshal.SizeOf<InterfaceData>() };
            if (!SetupDiEnumDeviceInterfaces(deviceSet, IntPtr.Zero,
                    ref guid, index, ref data))
            {
                break;
            }

            string? path = ReadPath(deviceSet, ref data);
            if (path is not null && path.Contains("vid_3151&pid_5007&mi_02",
                    StringComparison.OrdinalIgnoreCase))
            {
                paths.Add(path);
            }
        }

        return paths;
    }

    private static string? ReadPath(IntPtr deviceSet, ref InterfaceData data)
    {
        SetupDiGetDeviceInterfaceDetail(deviceSet, ref data,
            IntPtr.Zero, 0, out uint needed, IntPtr.Zero);
        if (needed < 8 || needed > 65536)
        {
            return null;
        }

        IntPtr buffer = Marshal.AllocHGlobal((int)needed);
        try
        {
            // cbSize differs between 64-bit and 32-bit Windows.
            Marshal.WriteInt32(buffer, IntPtr.Size == 8 ? 8 : 6);
            bool ok = SetupDiGetDeviceInterfaceDetail(deviceSet,
                ref data, buffer, needed, out _, IntPtr.Zero);
            return ok ? Marshal.PtrToStringUni(IntPtr.Add(buffer, 4)) : null;
        }
        finally
        {
            Marshal.FreeHGlobal(buffer);
        }
    }

    internal static SafeFileHandle Open(string path)
    {
        SafeFileHandle handle = CreateFile(path, ReadWrite,
            ShareReadWrite, IntPtr.Zero, OpenExisting, 0, IntPtr.Zero);
        if (!handle.IsInvalid)
        {
            return handle;
        }

        handle.Dispose();
        return CreateFile(path, 0, ShareReadWrite,
            IntPtr.Zero, OpenExisting, 0, IntPtr.Zero);
    }

    internal static bool TryGetCaps(SafeFileHandle handle, out HidCaps caps)
    {
        caps = default;
        if (!HidD_GetPreparsedData(handle, out IntPtr data))
        {
            return false;
        }

        try
        {
            return HidP_GetCaps(data, out caps) >= 0;
        }
        finally
        {
            HidD_FreePreparsedData(data);
        }
    }
}
