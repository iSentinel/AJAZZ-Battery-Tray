using System.Runtime.InteropServices;
using System.Text;

namespace AjazzBatteryTray;

/// <summary>Read-only Configuration Manager inventory. Never exposes instance paths.</summary>
internal static class PnpNamePreview
{
    private const uint Present = 0x100;
    private const uint StringType = 0x12;
    private const uint StringListType = 0x2012;
    private const uint BufferSmall = 0x1A;

    [StructLayout(LayoutKind.Sequential)]
    private struct PropertyKey
    {
        internal Guid Format;
        internal uint Id;
    }

    private static PropertyKey Key(uint id) => new()
    {
        Format = new Guid("a45c254e-df1c-4efd-8020-67d146a850e0"),
        Id = id
    };

    [DllImport("cfgmgr32.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint CM_Get_Device_ID_List_SizeW(out uint length, string? filter, uint flags);

    [DllImport("cfgmgr32.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint CM_Get_Device_ID_ListW(string? filter, [Out] byte[] buffer, uint length, uint flags);

    [DllImport("cfgmgr32.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint CM_Locate_DevNodeW(out uint node, string instance, uint flags);

    [DllImport("cfgmgr32.dll", ExactSpelling = true)]
    private static extern uint CM_Get_Parent(out uint parent, uint node, uint flags);

    [DllImport("cfgmgr32.dll", ExactSpelling = true)]
    private static extern uint CM_Get_DevNode_PropertyW(uint node, ref PropertyKey key,
        out uint type, [Out] byte[] buffer, ref uint length, uint flags);

    private sealed record Node(uint Handle, string Family, bool Root);
    internal sealed record Entry(int Group, string Family, ushort? Revision,
        string Role, string CurrentName, string ProposedName);

    private static string[] PresentIds()
    {
        for (int retry = 0; retry < 3; retry++)
        {
            uint result = CM_Get_Device_ID_List_SizeW(out uint count, null, Present);
            if (result != 0 || count is 0 or > 2_000_000)
                throw new InvalidOperationException("PnP inventory size unavailable.");
            byte[] buffer = new byte[checked((int)count * 2)];
            result = CM_Get_Device_ID_ListW(null, buffer, count, Present);
            if (result == 0)
                return Encoding.Unicode.GetString(buffer).Split('\0', StringSplitOptions.RemoveEmptyEntries);
            if (result != BufferSmall) break;
        }
        throw new InvalidOperationException("PnP inventory unavailable.");
    }

    private static string[] ReadProperty(uint node, uint id, uint expected)
    {
        PropertyKey key = Key(id);
        byte[] buffer = new byte[65536];
        uint length = (uint)buffer.Length;
        uint result = CM_Get_DevNode_PropertyW(node, ref key, out uint type,
            buffer, ref length, 0);
        if (result != 0 || type != expected || length > buffer.Length || length % 2 != 0)
            return Array.Empty<string>();
        return Encoding.Unicode.GetString(buffer, 0, (int)length)
            .Split('\0', StringSplitOptions.RemoveEmptyEntries);
    }

    private static string CurrentName(uint node)
        => ReadProperty(node, 14, StringType).FirstOrDefault()
        ?? ReadProperty(node, 2, StringType).FirstOrDefault() ?? "unavailable";

    internal static IReadOnlyList<Entry> Read()
    {
        List<Node> nodes = new();
        foreach (string id in PresentIds())
        {
            string? family = PnpNameRules.Family(id);
            if (family is not null && CM_Locate_DevNodeW(out uint node, id, 0) == 0)
                nodes.Add(new(node, family, PnpNameRules.IsRoot(id)));
        }
        var roots = nodes.Where(n => n.Root).Distinct().ToArray();
        var children = nodes.Where(n => !n.Root).Distinct().ToArray();
        List<Entry> entries = new();
        for (int i = 0; i < roots.Length; i++)
        {
            Node root = roots[i];
            ushort? revision = PnpNameRules.Revision(root.Family,
                ReadProperty(root.Handle, 3, StringListType));
            string model = PnpNameRules.Model(root.Family, revision);
            entries.Add(new(i + 1, root.Family, revision, "USB receiver",
                CurrentName(root.Handle), model + " (2.4 GHz receiver)"));
            foreach (Node child in children.Where(n => n.Family == root.Family &&
                         HasAncestor(n.Handle, root.Handle)))
                entries.Add(new(i + 1, root.Family, revision,
                    root.Family == "3151:5007" ? "Mouse HID" : "Keyboard HID",
                    CurrentName(child.Handle), model + " (2.4 GHz)"));
        }
        return entries;
    }

    private static bool HasAncestor(uint child, uint root)
    {
        HashSet<uint> visited = new();
        for (int depth = 0; depth < 16 && visited.Add(child); depth++)
        {
            if (CM_Get_Parent(out uint parent, child, 0) != 0) return false;
            if (parent == root) return true;
            child = parent;
        }
        return false;
    }
}
