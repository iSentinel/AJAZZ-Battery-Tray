using System.Security.Cryptography;
using System.Text;

namespace AjazzBatteryTray;

/// <summary>Verify a user-selected local Windows distribution; never execute it.</summary>
public static class LocalArtifactVerifier
{
    public const string SetupName = "AJAZZBatteryTray-Setup-win-x64.exe";
    public const string PortableName = "AJAZZBatteryTray-win-x64.exe";
    public const long MaximumArtifactBytes = 512L * 1024 * 1024;
    public const int MaximumManifestBytes = 1024;

    public static string? ManifestName(string artifactName) => artifactName switch
    {
        SetupName => "AJAZZBatteryTray-Setup-win-x64.sha256",
        PortableName => "AJAZZBatteryTray-win-x64.sha256",
        _ => null
    };

    public static async Task<bool> VerifyAsync(string artifactPath, string manifestPath,
        CancellationToken cancellationToken = default)
    {
        string name = Path.GetFileName(artifactPath);
        string expectedManifest = ManifestName(name)
            ?? throw new InvalidDataException("Unsupported artifact name.");
        if (Path.GetFileName(manifestPath) != expectedManifest)
            throw new InvalidDataException("Wrong checksum manifest name.");
        using var manifest = new FileStream(manifestPath, FileMode.Open, FileAccess.Read,
            FileShare.Read, 4096, FileOptions.Asynchronous);
        if (manifest.Length is <= 0 or > MaximumManifestBytes)
            throw new InvalidDataException("Invalid checksum manifest size.");
        byte[] data = new byte[(int)manifest.Length];
        await manifest.ReadExactlyAsync(data, cancellationToken).ConfigureAwait(false);
        if (data.Any(value => value > 127))
            throw new InvalidDataException("Checksum manifest must be ASCII.");
        using var artifact = new FileStream(artifactPath, FileMode.Open, FileAccess.Read,
            FileShare.Read, 65536, FileOptions.Asynchronous | FileOptions.SequentialScan);
        if (artifact.Length is <= 0 or > MaximumArtifactBytes)
            throw new InvalidDataException("Invalid artifact size.");
        byte[]? expected = UpdateRules.ExpectedChecksum(Encoding.ASCII.GetString(data), name);
        if (expected is null) return false;
        byte[] actual = await SHA256.HashDataAsync(artifact, cancellationToken).ConfigureAwait(false);
        return CryptographicOperations.FixedTimeEquals(actual, expected);
    }
}
