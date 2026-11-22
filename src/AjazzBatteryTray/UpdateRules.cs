using System.Globalization;
using System.Security.Cryptography;
using System.Text.RegularExpressions;

namespace AjazzBatteryTray;

/// <summary>Strict comparison of the project's stable and beta release tags.</summary>
public sealed record ReleaseVersion(int Major, int Minor, int Patch, int? Beta)
    : IComparable<ReleaseVersion>
{
    public static ReleaseVersion? Parse(string? tag)
    {
        if (tag is null || tag.Length > 80) return null;
        var match = Regex.Match(tag,
            @"\Av?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-beta\.([1-9][0-9]*))?\z",
            RegexOptions.CultureInvariant);
        if (!match.Success) return null;
        int[] values = new int[4];
        for (int i = 1; i <= 4; i++)
            if (match.Groups[i].Success && !int.TryParse(match.Groups[i].Value,
                NumberStyles.None, CultureInfo.InvariantCulture, out values[i - 1])) return null;
        return new(values[0], values[1], values[2], match.Groups[4].Success ? values[3] : null);
    }

    public int CompareTo(ReleaseVersion? other)
    {
        if (other is null) return 1;
        int result = Major.CompareTo(other.Major);
        if (result == 0) result = Minor.CompareTo(other.Minor);
        if (result == 0) result = Patch.CompareTo(other.Patch);
        if (result != 0) return result;
        if (!Beta.HasValue) return other.Beta.HasValue ? 1 : 0;
        return other.Beta.HasValue ? Beta.Value.CompareTo(other.Beta.Value) : -1;
    }
}

public static class UpdateRules
{
    public static ReleaseVersion? Newest(ReleaseVersion current,
        IEnumerable<(string Tag, bool Draft, bool Prerelease)> entries, bool experimental)
        => entries.Where(x => !x.Draft)
            .Select(x => (Version: ReleaseVersion.Parse(x.Tag), x.Prerelease))
            .Where(x => x.Version is not null && x.Prerelease == x.Version.Beta.HasValue &&
                (experimental || !x.Prerelease) && x.Version.CompareTo(current) > 0)
            .Select(x => x.Version).OrderByDescending(x => x).FirstOrDefault();

    /// <summary>Accept exactly one checksum entry for the expected artifact.</summary>
    public static bool VerifyChecksum(Stream artifact, string? manifest, string expectedName)
    {
        if (manifest is null || manifest.Length > 1024 || string.IsNullOrEmpty(expectedName) ||
            expectedName.Any(c => !char.IsAsciiLetterOrDigit(c) && c is not '.' and not '-' and not '_'))
            return false;
        string line = manifest.TrimEnd('\r', '\n');
        var match = Regex.Match(line, @"\A([a-fA-F0-9]{64}) [ *]([^\r\n]+)\z");
        if (!match.Success || !string.Equals(match.Groups[2].Value, expectedName, StringComparison.Ordinal))
            return false;
        byte[] actual = SHA256.HashData(artifact);
        return CryptographicOperations.FixedTimeEquals(actual, Convert.FromHexString(match.Groups[1].Value));
    }
}
