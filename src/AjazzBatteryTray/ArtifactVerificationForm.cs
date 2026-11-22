using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Explicit offline comparison of an artifact and its checksum manifest.</summary>
internal sealed class ArtifactVerificationForm : Form
{
    private readonly CancellationTokenSource _cancel = new();
    private readonly Label _artifact = new() { AutoSize = true, MaximumSize = new Size(480, 0) };
    private readonly Label _manifest = new() { AutoSize = true, MaximumSize = new Size(480, 0) };
    private readonly Label _status = new() { AutoSize = true, MaximumSize = new Size(480, 0) };
    private readonly Button _chooseArtifact = new() { AutoSize = true };
    private readonly Button _chooseManifest = new() { AutoSize = true };
    private readonly Button _verify = new() { AutoSize = true, Enabled = false };
    private string? _artifactPath, _manifestPath;
    private bool _busy;

    internal ArtifactVerificationForm()
    {
        Text = UiText.Get("Verify downloaded release...");
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = MinimizeBox = false;
        AutoSize = true;
        AutoSizeMode = AutoSizeMode.GrowAndShrink;
        var panel = new FlowLayoutPanel { FlowDirection = FlowDirection.TopDown,
            WrapContents = false, AutoSize = true, Dock = DockStyle.Fill, Padding = new Padding(14) };
        panel.Controls.Add(new Label { AutoSize = true, MaximumSize = new Size(480, 0),
            Text = UiText.Get("Choose the EXE and SHA-256 file from the same GitHub release.") });
        _chooseArtifact.Text = UiText.Get("Choose EXE...");
        _chooseArtifact.Click += (_, _) => ChooseArtifact();
        _chooseManifest.Text = UiText.Get("Choose SHA-256...");
        _chooseManifest.Click += (_, _) => ChooseManifest();
        _verify.Text = UiText.Get("Verify checksum");
        _verify.Click += async (_, _) => await VerifyAsync();
        var close = new Button { Text = UiText.Get("Close"), AutoSize = true };
        close.Click += (_, _) => Close();
        panel.Controls.AddRange(new Control[] { _chooseArtifact, _artifact, _chooseManifest,
            _manifest, _verify, _status, new Label { AutoSize = true, MaximumSize = new Size(480, 0),
                Text = UiText.Get("A matching checksum is not a publisher signature. No file is executed.") }, close });
        Controls.Add(panel);
        RefreshSelection();
    }

    private static string? ChooseFile(string filter)
    {
        using var dialog = new OpenFileDialog { Filter = filter, CheckFileExists = true,
            Multiselect = false, RestoreDirectory = true, DereferenceLinks = false };
        return dialog.ShowDialog() == DialogResult.OK ? dialog.FileName : null;
    }

    private void ChooseArtifact()
    {
        var path = ChooseFile("Windows EXE (*.exe)|*.exe");
        if (path is null) return;
        _artifactPath = path;
        _manifestPath = null;
        RefreshSelection();
    }

    private void ChooseManifest()
    {
        var path = ChooseFile("SHA-256 (*.sha256)|*.sha256");
        if (path is null) return;
        _manifestPath = path;
        RefreshSelection();
    }

    private void RefreshSelection()
    {
        _artifact.Text = _artifactPath is null ? UiText.Get("No EXE selected.") : Path.GetFileName(_artifactPath);
        _manifest.Text = _manifestPath is null ? UiText.Get("No checksum selected.") : Path.GetFileName(_manifestPath);
        var expected = _artifactPath is null ? null : LocalArtifactVerifier.ManifestName(Path.GetFileName(_artifactPath));
        _verify.Enabled = !_busy && expected is not null && _manifestPath is not null &&
            Path.GetFileName(_manifestPath) == expected;
        _status.Text = _artifactPath is not null && expected is null ?
            UiText.Get("Unsupported release filename.") :
            _manifestPath is not null && !_verify.Enabled ? UiText.Get("Choose the matching checksum file.") : "";
    }

    private async Task VerifyAsync()
    {
        if (_busy || !_verify.Enabled || _artifactPath is null || _manifestPath is null) return;
        _busy = true;
        _chooseArtifact.Enabled = _chooseManifest.Enabled = _verify.Enabled = false;
        _status.Text = UiText.Get("Verifying SHA-256...");
        try
        {
            bool ok = await LocalArtifactVerifier.VerifyAsync(_artifactPath, _manifestPath, _cancel.Token);
            if (!IsDisposed && !_cancel.IsCancellationRequested)
                _status.Text = UiText.Get(ok ? "SHA-256 matches." : "SHA-256 mismatch. Do not run this file.");
        }
        catch (Exception)
        {
            if (!IsDisposed && !_cancel.IsCancellationRequested)
                _status.Text = UiText.Get("Verification failed; check the selected files.");
        }
        finally
        {
            _busy = false;
            if (!IsDisposed && !_cancel.IsCancellationRequested)
                _chooseArtifact.Enabled = _chooseManifest.Enabled = _verify.Enabled = true;
        }
    }

    protected override void OnFormClosed(FormClosedEventArgs e)
    {
        _cancel.Cancel();
        base.OnFormClosed(e);
    }
}
