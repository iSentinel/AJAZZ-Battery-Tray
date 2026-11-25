using AjazzBatteryTray;

// Dependency-free tests run on Windows, macOS or Linux with .NET 8.
int passed = 0;
int failed = 0;

void Check(string name, bool valid)
{
    if (valid)
    {
        passed++;
        Console.WriteLine($"PASS {name}");
    }
    else
    {
        failed++;
        Console.WriteLine($"FAIL {name}");
    }
}

Check("100 percent", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 0, 0, 100, 1, 1, 1, 2 }) == 100);
Check("34 percent", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 0, 0, 34, 1, 1, 1, 2 }) == 34);
Check("missing link", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 0, 0, 0, 0, 0, 0, 0 }) is null);
Check("reject out of range", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 0, 0, 255 }) is null);
Check("reject malformed status", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 1, 0, 90 }) is null);
Check("reject wrong report id", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x04, 0, 0, 50 }) is null);
Check("reject short report", BatteryReportParser.ParseWindowsFeature(
    new byte[] { 0x05, 0, 0 }) is null);

// GearHub F7 shared receiver flags, based on a sanitized response prefix.
/// Actual owner capture: report ID 05, readable=0, mouse battery=0,
/// keyboard offline, mouse online, canSend=1, slot=2, RF boot=0.
byte[] observedAj159F7 = { 5, 0, 0, 0, 1, 0, 1, 2, 0, 0 };
Check("AJ159 observed F7 no false zero battery",
    BatteryReportParser.ParseWindowsFeature(observedAj159F7) is null &&
    BatteryReportParser.DescribeWindowsFeature(observedAj159F7)
        .StartsWith("F7 mouse: reading unavailable"));
byte[] aj159ReadableWithoutCharge = { 5, 1, 0, 0, 1, 0, 1, 2, 0, 0 };
Check("AJ159 readable flag but zero field remains unknown",
    BatteryReportParser.ParseWindowsFeature(aj159ReadableWithoutCharge) is null &&
    BatteryReportParser.DescribeWindowsFeature(aj159ReadableWithoutCharge)
        .Contains("zero battery"));
byte[] syntheticGatedMouse = { 5, 1, 0, 83, 1, 0, 1, 2, 0, 0 };
Check("Gated F7 can decode synthetic 83 percent",
    BatteryReportParser.ParseWindowsFeature(syntheticGatedMouse) == 83 &&
    BatteryReportParser.DescribeWindowsFeature(syntheticGatedMouse) ==
        "accepted by gated F7 mouse parser");
byte[] f7Unreadable = (byte[])syntheticGatedMouse.Clone();
f7Unreadable[1] = 0;
Check("F7 unreadable status rejects stale 83 percent",
    BatteryReportParser.ParseWindowsFeature(f7Unreadable) is null);
byte[] f7Offline = (byte[])syntheticGatedMouse.Clone();
f7Offline[5] = 1;
Check("F7 mouse offline rejects 83 percent",
    BatteryReportParser.ParseWindowsFeature(f7Offline) is null);
byte[] f7CannotSend = (byte[])syntheticGatedMouse.Clone();
f7CannotSend[6] = 0;
Check("F7 mouse cannot-send rejects percent",
    BatteryReportParser.ParseWindowsFeature(f7CannotSend) is null);
byte[] f7RfBoot = (byte[])syntheticGatedMouse.Clone();
f7RfBoot[9] = 1;
Check("F7 RF boot rejects percent",
    BatteryReportParser.ParseWindowsFeature(f7RfBoot) is null);
byte[] f7Above100 = (byte[])syntheticGatedMouse.Clone();
f7Above100[3] = 101;
Check("F7 rejects above-100 battery field",
    BatteryReportParser.ParseWindowsFeature(f7Above100) is null);
byte[] f7DualSlot = (byte[])syntheticGatedMouse.Clone();
f7DualSlot[7] = 3;
Check("F7 mouse in dual slot can parse verified percent",
    BatteryReportParser.ParseWindowsFeature(f7DualSlot) == 83);
byte[] f7KeyboardSlot = (byte[])syntheticGatedMouse.Clone();
f7KeyboardSlot[7] = 1;
Check("F7 keyboard-only reply cannot be mistaken for mouse battery",
    BatteryReportParser.ParseWindowsFeature(f7KeyboardSlot) is null);

f7KeyboardSlot[1] = 0;
Check("Unreadable keyboard slot cannot fall back to compact mouse parsing",
    BatteryReportParser.ParseWindowsFeature(f7KeyboardSlot) is null &&
    BatteryReportParser.DescribeWindowsFeature(f7KeyboardSlot).Contains("keyboard-only"));
var malformedMouse = (byte[])f7Unreadable.Clone();
malformedMouse[4] = 2;
Check("Invalid F7 flag cannot fall back to compact mouse parsing",
    BatteryReportParser.ParseWindowsFeature(malformedMouse) is null);

byte[] aj179OwnerNov24 = Convert.FromHexString("05000064010001020000");
Check("Nov24 AJ179 ready-clear 100 remains unknown telemetry",
    BatteryReportParser.ParseWindowsFeature(aj179OwnerNov24) is null &&
    BatteryReportParser.UnverifiedMouseField(aj179OwnerNov24) == 100);
Check("AJ159 zero never provisional", BatteryReportParser.UnverifiedMouseField(observedAj159F7) is null);
Check("Ready verified is not provisional", BatteryReportParser.UnverifiedMouseField(syntheticGatedMouse) is null);
Check("Invalid flags never provisional", BatteryReportParser.UnverifiedMouseField(malformedMouse) is null);
Check("Keyboard slot never provisional", BatteryReportParser.UnverifiedMouseField(f7KeyboardSlot) is null);
foreach (int index in new[] { 5, 6, 9 })
{
    byte[] bad = (byte[])aj179OwnerNov24.Clone();
    bad[index] ^= 1;
    Check($"Provisional rejects invalid link flag {index}", BatteryReportParser.UnverifiedMouseField(bad) is null);
}
Check("Provisional needs all attempts and two samples",
    BatteryReportParser.ConsistentUnverifiedField(100, 2, 2) == 100 &&
    BatteryReportParser.ConsistentUnverifiedField(100, 1, 2) is null &&
    BatteryReportParser.ConsistentUnverifiedField(100, 1, 1) is null);
Check("Unverified 8 is gray not red",
    TrayIconRenderKey.Create(8, true, false, mouseStyle: true, unverified: true)
        is { Mouse: false, Background: TrayColorRules.Gray, Unverified: true });
Check("Unverified and cached render keys distinct",
    TrayIconRenderKey.Create(100, true, false, unverified: true) !=
    TrayIconRenderKey.Create(100, true, true));

Check("Diagnostic candidate label is explicit",
    BatteryReportParser.DiagnosticUnverifiedField(100) == "unverified mouse field (not telemetry)=100");
Check("Diagnostic candidate suppressed on scheduled skip",
    BatteryReportParser.DiagnosticUnverifiedField(100, false) == "unverified mouse field (not telemetry)=unavailable");
Check("Diagnostic candidate absent or invalid stays unavailable",
    new int?[] { null, 0, -1, 101 }.All(x =>
        BatteryReportParser.DiagnosticUnverifiedField(x) == "unverified mouse field (not telemetry)=unavailable"));

var observationStreak = new UnverifiedObservationStreak();
var streakStart = new DateTimeOffset(2026, 11, 24, 23, 18, 7, TimeSpan.Zero);
observationStreak.Observe(100, streakStart);
observationStreak.Observe(100, streakStart.AddSeconds(30));
observationStreak.Observe(100, streakStart.AddSeconds(30));
Check("Repeated candidate counts distinct ordinary observations only",
    observationStreak.Count == 2 && observationStreak.First == streakStart &&
    observationStreak.Last == streakStart.AddSeconds(30) &&
    observationStreak.DiagnosticText().Contains("span seconds=30.0; not telemetry"));
observationStreak.Observe(98, streakStart.AddSeconds(60));
Check("Changed candidate starts a new observation streak",
    observationStreak.Field == 98 && observationStreak.Count == 1 &&
    observationStreak.First == streakStart.AddSeconds(60));
observationStreak.Observe(100, streakStart.AddSeconds(90));
Check("Return to 100 starts a separate streak",
    observationStreak.Field == 100 && observationStreak.Count == 1);
observationStreak.Observe(100, streakStart.AddSeconds(80));
Check("Clock reversal resets observation streak",
    observationStreak.Count == 1 && observationStreak.First == streakStart.AddSeconds(80));
foreach (int? missingCandidate in new int?[] { null, 0, 101 })
{
    observationStreak.Observe(98, streakStart);
    observationStreak.Observe(missingCandidate, streakStart.AddSeconds(30));
    Check($"No streak for invalid candidate {missingCandidate}",
        observationStreak.Count == 0 && observationStreak.Field is null &&
        observationStreak.First is null && observationStreak.Last is null);
}
observationStreak.Observe(98, streakStart);
observationStreak.Reset();
Check("Absence or unknown presence clears observation streak",
    observationStreak.DiagnosticText() == "no consecutive unverified ordinary observations");

// The Apple and offline readers replay the same sanitized fixtures in CI.
string corpus = Path.Combine(AppContext.BaseDirectory, "fixtures", "apex-f7-v1.csv");
foreach (string row in File.ReadLines(corpus).Skip(1))
{
    string[] fields = row.Split(',');
    int? expected = fields[3] == "unknown" ? null : int.Parse(fields[3]);
    int? actual = BatteryReportParser.ParseWindowsFeature(Convert.FromHexString(fields[2]));
    Check($"Shared F7 corpus {fields[0]}", actual == expected);
    string directory = Path.Combine(Path.GetTempPath(), "ajazz-corpus-" + Guid.NewGuid().ToString("N"));
    try
    {
        var history = new BatteryHistory("test.csv", directory);
        history.Record(DateTimeOffset.UtcNow, actual, receiverPresent: true);
        var sample = history.ReadRecent().SingleOrDefault();
        Check($"Shared F7 history {fields[0]}", sample is not null &&
            sample.Percent == expected && sample.State == (expected is null ? "unavailable" : "online"));
        if (expected is null)
        {
            var connection = new ConnectionAlertPolicy();
            connection.Evaluate(true, true);
            bool first = connection.Evaluate(false, false);
            bool unknown = connection.Evaluate(actual.HasValue, true);
            bool next = connection.Evaluate(false, false);
            Check($"Shared F7 unknown does not trigger disconnect {fields[0]}", !first && !unknown && !next);
        }
    }
    finally { if (Directory.Exists(directory)) Directory.Delete(directory, true); }
}

string previousTrayLanguage = UiText.Language;
foreach (string lang in new[] { "en", "ru", "uk" })
{
    UiText.SetLanguage(lang);
    Check($"Unknown charge distinguishes startup, enumeration, absence, access and reply ({lang})",
        new[] {
            UsbTrayStatus.Reason(false, false, UsbReadIssue.NotChecked),
            UsbTrayStatus.Reason(false, false, UsbReadIssue.None),
            UsbTrayStatus.Reason(true, false, UsbReadIssue.None),
            UsbTrayStatus.Reason(true, true, UsbReadIssue.InterfaceUnavailable),
            UsbTrayStatus.Reason(true, true, UsbReadIssue.None),
            UsbTrayStatus.Reason(false, false, UsbReadIssue.Busy),
            UsbTrayStatus.Reason(false, false, UsbReadIssue.Timeout)
        }.Distinct().Count() == 7);
    Check($"Unknown or timed-out USB does not permit Bluetooth fallback ({lang})",
        !BatteryDisplayState.MayUseBluetooth(false, false) &&
        BatteryDisplayState.Resolve(false, null, true, 75, false).Percent is null);
    string noReply = UsbTrayStatus.Reason(true, true, UsbReadIssue.None);
    Check($"Unknown charge without previous reading has no historical time ({lang})",
        UsbTrayStatus.WithLastVerified(noReply, null) == noReply);
    DateTimeOffset stamp = DateTimeOffset.Parse("2026-11-23T18:32:52Z");
    Check($"Unknown charge displays time of last verified sample ({lang})",
        UsbTrayStatus.WithLastVerified(noReply, stamp).Contains(stamp.ToLocalTime().ToString("g")));
}
UiText.SetLanguage(previousTrayLanguage);

// Diagnostic classification must not broaden the valid battery format.
Check("Protocol reason: empty", BatteryReportParser.DescribeWindowsFeature(Array.Empty<byte>()) == "short buffer");
Check("Protocol reason: wrong ID", BatteryReportParser.DescribeWindowsFeature(new byte[] { 4, 0, 0, 50 }) == "unexpected report ID");
Check("Protocol reason: prefix", BatteryReportParser.DescribeWindowsFeature(new byte[] { 5, 1, 0, 50 }) == "unexpected status prefix");
Check("Protocol reason: zero", BatteryReportParser.DescribeWindowsFeature(new byte[] { 5, 0, 0, 0 }).StartsWith("zero battery field"));
Check("Protocol reason: out of range", BatteryReportParser.DescribeWindowsFeature(new byte[] { 5, 0, 0, 101 }) == "battery field out of range");
Check("Protocol reason: accepted", BatteryReportParser.DescribeWindowsFeature(new byte[] { 5, 0, 0, 100 }) == "accepted by existing parser");

// Diagnostic paths expose descriptors only, never the private instance suffix.
Check("AJ159 alternate receiver metadata", DiagnosticHidIdentity.FromPath(
    "hid#vid_3151&pid_4026&mi_03&col01#private-instance") ==
    "3151:4026 MI_03 COL01");
Check("AJ159 second alternate receiver", DiagnosticHidIdentity.FromPath(
    "hid#VID_3151&PID_4027#private-instance") == "3151:4027 MI_-- COL--");
Check("AJ179 diagnostic identity", DiagnosticHidIdentity.FromPath(
    "hid#vid_3151&pid_5007&mi_02#secret") == "3151:5007 MI_02 COL--");
Check("AULA candidate metadata", DiagnosticHidIdentity.FromPath(
    "hid#vid_05ac&pid_024f&mi_03#secret") == "05AC:024F MI_03 COL--");
Check("Unrelated USB ignored", DiagnosticHidIdentity.FromPath(
    "hid#vid_1234&pid_9876#secret") is null);
Check("Other Apple product ignored", DiagnosticHidIdentity.FromPath(
    "hid#vid_05ac&pid_9999#secret") is null);
Check("Malformed identifier ignored", DiagnosticHidIdentity.FromPath(
    "hid#vid_3151&pid_50070#secret") is null);
Check("Diagnostic header excludes remaining payload",
    DiagnosticHidIdentity.BatteryHeader(new byte[] { 5, 0, 0, 83, 0xff }) ==
    "05000053");
Check("Diagnostic short header", DiagnosticHidIdentity.BatteryHeader(
    new byte[] { 5, 0 }) == "0500");
Check("Safe feature preview redacts trailing HID bytes",
    DiagnosticHidIdentity.SafeFeaturePreview(
        new byte[] { 5, 0, 0, 83, 1, 2, 3, 4, 0xAA }) ==
        "0500005301020304 (1 additional bytes redacted)");
Check("Safe feature preview handles short report",
    DiagnosticHidIdentity.SafeFeaturePreview(new byte[] { 5, 1 }) ==
        "0501 (0 additional bytes redacted)");

// Independent completion-based polling deadlines; no HID I/O.
var deviceSchedule = new DevicePollSchedule();
string fastPollKey = new string('C', 64);
string slowPollKey = new string('D', 64);
Check("New receivers immediately due", deviceSchedule.IsDue(fastPollKey, 0, 15));
deviceSchedule.Complete(fastPollKey, 1000);
deviceSchedule.Complete(slowPollKey, 1000);
Check("Fast receiver not early", !deviceSchedule.IsDue(fastPollKey, 15999, 15));
Check("Fast receiver due at boundary", deviceSchedule.IsDue(fastPollKey, 16000, 15));
Check("Slow receiver independently deferred", !deviceSchedule.IsDue(slowPollKey, 16000, 120));
Check("Force bypasses delay", deviceSchedule.IsDue(slowPollKey, 2000, 120, force: true));
Check("Slow receiver due at boundary", deviceSchedule.IsDue(slowPollKey, 121000, 120));
deviceSchedule.Complete(fastPollKey, 200000);
Check("Missed intervals do not cause catch-up burst", !deviceSchedule.IsDue(fastPollKey, 200001, 15));
Check("Clock discontinuity permits fresh sample", deviceSchedule.IsDue(fastPollKey, 0, 15));
deviceSchedule.Reconcile(Array.Empty<string>(), presenceKnown: false);
Check("Unknown enumeration does not forget schedule", !deviceSchedule.IsDue(fastPollKey, 200001, 15));
deviceSchedule.Reconcile(new[] { slowPollKey }, presenceKnown: true);
Check("Confirmed unplug resets removed receiver", deviceSchedule.IsDue(fastPollKey, 200001, 15));
Check("Invalid key never due even when forced", !deviceSchedule.IsDue("invalid", 0, 15, force: true));
Check("Inherited interval", DevicePollSchedule.ResolveInterval(60, null) == 60);
Check("Custom interval overrides default", DevicePollSchedule.ResolveInterval(60, 15) == 15);
Check("Invalid overrides inherit", DevicePollSchedule.ResolveInterval(60, 0) == 60);
Check("Invalid global normalizes", DevicePollSchedule.ResolveInterval(5, null) == 30);
Check("Clean poll override map", DevicePollSchedule.CleanOverrides(new Dictionary<string, int>
{
    [fastPollKey] = 15, [slowPollKey] = 999, ["invalid"] = 30,
    [DeviceAliasRules.AulaSlot] = 120
}).Count == 2);
deviceSchedule.Reset(slowPollKey);
Check("Explicit reset forces next reading", deviceSchedule.IsDue(slowPollKey, 2000, 120));
var pollSettings = new AppSettings { PollSeconds = 60 };
pollSettings.DevicePollIntervals[fastPollKey] = 15;
pollSettings.DevicePollIntervals[DeviceAliasRules.AulaSlot] = 120;
Check("Settings independent intervals", pollSettings.EffectivePollInterval(fastPollKey) == 15 &&
    pollSettings.EffectivePollInterval(slowPollKey) == 60 &&
    pollSettings.EffectivePollInterval(DeviceAliasRules.AulaSlot) == 120);
var pollRoundtrip = System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
    System.Text.Json.JsonSerializer.Serialize(pollSettings));
Check("Poll settings persist", pollRoundtrip?.EffectivePollInterval(fastPollKey) == 15 &&
    pollRoundtrip.EffectivePollInterval(DeviceAliasRules.AulaSlot) == 120);
pollSettings.DevicePollIntervals.Remove(fastPollKey);
Check("Interval reset inherits", pollSettings.EffectivePollInterval(fastPollKey) == 60);
var scheduleMeasurement = DateTimeOffset.Parse("2026-01-01T00:00:00Z");
var scheduledDashboard = DeviceDashboardState.FromPoll("Mouse", "2.4 GHz",
    true, true, true, 83, scheduleMeasurement, scheduled: true);
Check("Scheduled display preserves measurement time and percent",
    scheduledDashboard.Status == DeviceDashboardStatus.Scheduled &&
    scheduledDashboard.MeasuredAt == scheduleMeasurement && scheduledDashboard.Percent == 83);
Check("Scheduled flag cannot hide confirmed disconnect",
    DeviceDashboardState.FromPoll("Mouse", "2.4 GHz", true, true, false,
        83, scheduleMeasurement, scheduled: true).Status == DeviceDashboardStatus.Disconnected);
Check("Scheduled flag cannot hide unknown presence",
    DeviceDashboardState.FromPoll("Mouse", "2.4 GHz", true, false, true,
        83, scheduleMeasurement, scheduled: true).Status == DeviceDashboardStatus.PresenceUnknown);
Check("Scheduled flag cannot invent a valid reply",
    DeviceDashboardState.FromPoll("Mouse", "2.4 GHz", true, true, true,
        null, scheduleMeasurement, scheduled: true).Status == DeviceDashboardStatus.NoReply);



Check("Separate tray icons default on", new AppSettings().MultipleTrayIcons);

var alertSettings = new AppSettings { AlertBelow25 = false };
string alertDevice = new string('A', 64);
string otherAlertDevice = new string('B', 64);
Check("Device alert default inherits global", alertSettings.EffectiveAlertMask(alertDevice) == 5);
alertSettings.DeviceAlertMasks[alertDevice] = 2;
alertSettings.DeviceAlertMasks[otherAlertDevice] = 0;
Check("Device alert independent override", alertSettings.EffectiveAlertMask(alertDevice) == 2);
Check("Device alert explicit mute", alertSettings.EffectiveAlertMask(otherAlertDevice) == 0);
Check("AULA inherits global by default", alertSettings.EffectiveAlertMask(DeviceAliasRules.AulaSlot) == 5);
alertSettings.DeviceAlertMasks[DeviceAliasRules.AulaSlot] = 7;
Check("AULA independent settings", alertSettings.EffectiveAlertMask(DeviceAliasRules.AulaSlot) == 7);
alertSettings.NotificationsEnabled = false;
Check("Global master still mutes overrides", alertSettings.EffectiveAlertMask(alertDevice) == 0);
alertSettings.NotificationsEnabled = true;
alertSettings.DeviceAlertMasks.Remove(alertDevice);
Check("Reset inherits global thresholds", alertSettings.EffectiveAlertMask(alertDevice) == 5);
alertSettings.DeviceAlertMasks["invalid"] = 3;
alertSettings.DeviceAlertMasks[alertDevice] = 8;
var cleanedAlerts = AppSettings.CleanDeviceAlertMasks(alertSettings.DeviceAlertMasks);
Check("Invalid override keys and values rejected", cleanedAlerts.Count == 2 &&
    cleanedAlerts[otherAlertDevice] == 0 && cleanedAlerts[DeviceAliasRules.AulaSlot] == 7);
var alertRoundtrip = System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
    System.Text.Json.JsonSerializer.Serialize(alertSettings));
Check("Device alert settings round trip", alertRoundtrip?.EffectiveAlertMask(otherAlertDevice) == 0 &&
    alertRoundtrip.EffectiveAlertMask(DeviceAliasRules.AulaSlot) == 7);
var disconnectSettings = new AppSettings { NotifyOnDisconnect = true };
Check("Receiver disconnect setting defaults to global true",
    disconnectSettings.EffectiveDisconnectAlert(alertDevice));
disconnectSettings.DeviceDisconnectAlerts[alertDevice] = false;
Check("Receiver disconnect override can mute a single device",
    !disconnectSettings.EffectiveDisconnectAlert(alertDevice) &&
    disconnectSettings.EffectiveDisconnectAlert(otherAlertDevice));
disconnectSettings.DeviceDisconnectAlerts[DeviceAliasRules.AulaSlot] = false;
Check("AULA disconnect can be independently muted",
    !disconnectSettings.EffectiveDisconnectAlert(DeviceAliasRules.AulaSlot));
disconnectSettings.NotifyOnDisconnect = false;
disconnectSettings.DeviceDisconnectAlerts[otherAlertDevice] = true;
Check("Individual disconnect can opt in while global default off",
    disconnectSettings.EffectiveDisconnectAlert(otherAlertDevice) &&
    !disconnectSettings.EffectiveDisconnectAlert(alertDevice));
disconnectSettings.DeviceDisconnectAlerts.Remove(alertDevice);
Check("Removing disconnect override inherits current global",
    !disconnectSettings.EffectiveDisconnectAlert(alertDevice));
disconnectSettings.DeviceDisconnectAlerts["invalid"] = true;
var cleanedDisconnects = AppSettings.CleanDeviceDisconnectAlerts(
    disconnectSettings.DeviceDisconnectAlerts);
Check("Invalid disconnect override keys discarded",
    cleanedDisconnects.Count == 2 && cleanedDisconnects[otherAlertDevice] &&
    !cleanedDisconnects[DeviceAliasRules.AulaSlot]);
Check("Null disconnect overrides normalize to empty",
    AppSettings.CleanDeviceDisconnectAlerts(null).Count == 0);
var disconnectRoundtrip = System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
    System.Text.Json.JsonSerializer.Serialize(disconnectSettings));
Check("Device disconnect override survives settings round trip",
    disconnectRoundtrip is not null &&
    disconnectRoundtrip.EffectiveDisconnectAlert(otherAlertDevice) &&
    !disconnectRoundtrip.EffectiveDisconnectAlert(DeviceAliasRules.AulaSlot));
var disconnectLegacy = System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
    """{"NotifyOnDisconnect":true}""");
Check("Legacy config without overrides inherits global",
    disconnectLegacy?.EffectiveDisconnectAlert(alertDevice) == true &&
    disconnectLegacy.DeviceDisconnectAlerts.Count == 0);

Check("Primary stable despite enumeration order",
    ReceiverIdentity.SelectPrimary("b", new[] { "c", "b", "a" }) == "b");
Check("Primary replaced after unplug",
    ReceiverIdentity.SelectPrimary("b", new[] { "c", "a", "a" }) == "a");
Check("No primary when every receiver unplugged",
    ReceiverIdentity.SelectPrimary("a", Array.Empty<string>()) is null);
Check("Receiver identity stable regardless of path case",
    ReceiverIdentity.LocalKey("HID#ReceiverA") == ReceiverIdentity.LocalKey("hid#receivera"));
Check("Distinct receivers keep distinct local histories",
    ReceiverIdentity.LocalKey("HID#ReceiverA") != ReceiverIdentity.LocalKey("HID#ReceiverB"));
Check("Local receiver key does not expose device path",
    ReceiverIdentity.LocalKey("private-receiver-path").Length == 64 &&
    !ReceiverIdentity.LocalKey("private-receiver-path").Contains("private"));
Check("AJ159 revision label", ReceiverIdentity.Label(0x0300).Contains("AJ159"));
Check("Shared rev0002 cannot prove AJ179 or AJ159 model",
    ReceiverIdentity.Label(0x0002).Contains("model unverified") &&
    !ReceiverIdentity.Label(0x0002).Contains("AJ179"));
Check("Unknown revision remains generic", ReceiverIdentity.Label(0x4321) == "AJAZZ (rev. 4321)");
Check("Missing revision remains generic", ReceiverIdentity.Label(null) == "AJAZZ (unknown revision)");

Check("CPU load computes busy fraction", HostMetricsRules.CpuLoad(40, 60, 40) == 60);
Check("CPU idle is legitimate zero", HostMetricsRules.CpuLoad(100, 100, 0) == 0);
Check("CPU counter unavailable", HostMetricsRules.CpuLoad(0, 0, 0) is null);
Check("Reject contradictory CPU counters", HostMetricsRules.CpuLoad(40, 30, 10) is null);
Check("Localized metric decimal", HostMetricsRules.ParseValue("42,5 °C", true) == 42.5);
Check("Reject bad load", HostMetricsRules.ParseValue("101 %", false) is null);
Check("Reject non-temperature unit", HostMetricsRules.ParseValue("44 W", true) is null);
Check("Missing metric stays null", HostMetricsRules.ParseValue("-", false) is null);
Check("Valid zero load", HostMetricsRules.ParseValue("0 %", false) == 0);
const string previewJson = """
{
  "Children": [
    {"HardwareId":"/intelcpu/0","Text":"CPU A","Children":[
      {"Children":[{"SensorId":"/intelcpu/0/load/0","Type":"Load","Text":"CPU Total","RawValue":"27.5 %"}]},
      {"Children":[{"SensorId":"/intelcpu/0/temperature/0","Type":"Temperature","Text":"CPU Package","RawValue":"51 °C"}]}
    ]},
    {"HardwareId":"/gpu-nvidia/0","Text":"GPU A","Children":[
      {"SensorId":"/gpu-nvidia/0/load/0","Type":"Load","Text":"GPU Core","RawValue":"68 %"},
      {"SensorId":"/gpu-nvidia/0/temperature/0","Type":"Temperature","Text":"GPU Core","RawValue":"64 °C"},
      {"SensorId":"/gpu-nvidia/0/temperature/1","Type":"Temperature","Text":"GPU Memory","RawValue":"82 °C"}
    ]},
    {"HardwareId":"/gpu-intel/1","Text":"GPU B","Children":[
      {"SensorId":"/gpu-intel/1/load/0","Type":"Load","Text":"GPU Core","RawValue":"0 %"}
    ]}
  ]
}
""";
var hostMetrics = HostMetricsRules.ParseProvider(System.Text.Encoding.UTF8.GetBytes(previewJson));
Check("Host preview separates all CPUs and GPUs", hostMetrics.Count == 3 &&
    !hostMetrics[0].IsGpu && hostMetrics[1].IsGpu && hostMetrics[2].IsGpu);
Check("CPU package and load parsed", hostMetrics[0].LoadPercent == 27.5 &&
    hostMetrics[0].TemperatureC == 51);
Check("GPU core temperature does not use memory sensor", hostMetrics[1].LoadPercent == 68 &&
    hostMetrics[1].TemperatureC == 64);
Check("Missing GPU temperature is unknown, not zero", hostMetrics[2].LoadPercent == 0 &&
    hostMetrics[2].TemperatureC is null);

AlertPolicy policy = new();
Check("normal battery no alert", policy.Evaluate(75) is null);
Check("at 50 is not below 50", policy.Evaluate(50) is null);
Check("below 50 triggers once", policy.Evaluate(49) == 50);
Check("below 50 is not repeated", policy.Evaluate(48) is null);
Check("at 25 is not below 25", policy.Evaluate(25) is null);
Check("below 25 triggers once", policy.Evaluate(24) == 25);
Check("at 10 is not below 10", policy.Evaluate(10) is null);
Check("below 10 triggers once", policy.Evaluate(9) == 10);
Check("below 10 does not repeat", policy.Evaluate(4) is null);
Check("recharge re-arms 50", policy.Evaluate(55) is null &&
    policy.Evaluate(49) == 50);
Check("invalid values ignored", policy.Evaluate(-1) is null &&
    policy.Evaluate(101) is null);

AlertPolicy only25 = new();
Check("disabled 50 threshold does not alert", only25.Evaluate(
    49, below50: false, below25: true, below10: false) is null);
Check("selected 25 threshold alerts", only25.Evaluate(
    24, below50: false, below25: true, below10: false) == 25);
Check("disabled 10 threshold does not alert", only25.Evaluate(
    9, below50: false, below25: true, below10: false) is null);
Check("25 re-arms after charging", only25.Evaluate(
    30, below50: false, below25: true, below10: false) is null &&
    only25.Evaluate(24, below50: false, below25: true, below10: false) == 25);
AlertPolicy skipLevels = new();
Check("large drop emits only most urgent alert",
    skipLevels.Evaluate(75) is null && skipLevels.Evaluate(9) == 10 &&
    skipLevels.Evaluate(9) is null);
AlertPolicy allDisabled = new();
Check("disabling all thresholds suppresses alerts",
    allDisabled.Evaluate(9, below50: false, below25: false,
        below10: false) is null);
AppSettings defaults = new();
Check("all thresholds default enabled", defaults.AlertBelow50 &&
    defaults.AlertBelow25 && defaults.AlertBelow10);
AppSettings selected = new()
{
    AlertBelow50 = false, AlertBelow25 = true, AlertBelow10 = false
};
string savedSettings = System.Text.Json.JsonSerializer.Serialize(selected);
AppSettings? restored = System.Text.Json.JsonSerializer
    .Deserialize<AppSettings>(savedSettings);
Check("threshold selection round-trips", restored is not null &&
    !restored.AlertBelow50 && restored.AlertBelow25 && !restored.AlertBelow10);
AppSettings? olderSettings = System.Text.Json.JsonSerializer
    .Deserialize<AppSettings>("""{"PollSeconds":30}""");
Check("older settings get new default thresholds", olderSettings is not null &&
    olderSettings.AlertBelow50 && olderSettings.AlertBelow25 &&
    olderSettings.AlertBelow10);

Check("unknown language normalized", UiText.Normalize("invalid") == "en");
Check("Russian language normalized", UiText.Normalize("ru") == "ru");
Check("Ukrainian language normalized", UiText.Normalize("uk") == "uk");
UiText.SetLanguage("en");
Check("English settings label", UiText.Get("Settings") == "Settings");
UiText.SetLanguage("ru");
Check("Russian settings label", UiText.Get("Settings") == "Настройки");
Check("Russian thresholds formatted", UiText.Format("Below {0}%", 25) ==
    "Ниже 25%");
Check("Russian receiver disconnect inheritance label",
    UiText.Get("Use global disconnect setting") ==
    "Использовать общее правило отключения");
UiText.SetLanguage("uk");
Check("Ukrainian settings label", UiText.Get("Settings") == "Налаштування");
Check("Ukrainian notification label",
    UiText.Get("Low battery notifications") == "Сповіщення про низький заряд");
Check("Ukrainian receiver disconnect inheritance label",
    UiText.Get("Use global disconnect setting") ==
    "Використовувати загальне правило відключення");
Check("Ukrainian interval label", UiText.Format("{0} seconds", 30) == "30 с");
UiText.SetLanguage("de");
Check("unsupported language falls back to English",
    UiText.Language == "en" && UiText.Get("Settings") == "Settings");
AppSettings languageChoice = new() { Language = "uk" };
string serializedLanguage = System.Text.Json.JsonSerializer.Serialize(languageChoice);
Check("language choice survives serialization",
    System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
        serializedLanguage)?.Language == "uk");
Check("legacy settings default to English", olderSettings?.Language == "en");

// Cache never replaces fresh observations in history or alerts.
var aulaCache = new AulaBatteryState();
var aulaTime = DateTimeOffset.Parse("2026-11-22T15:17:48Z");
aulaCache.Observe(true, true, 98, aulaTime);
aulaCache.Observe(true, true, null, aulaTime.AddSeconds(31));
Check("AULA retains last good percentage on transient no reply",
    aulaCache.DisplayPercent(true, true, null, aulaTime.AddSeconds(31)) == 98 &&
    aulaCache.ConsecutiveFailures == 1 && aulaCache.LastGoodAt == aulaTime);
Check("AULA cached percentage remains visible during eight-hour sleep",
    aulaCache.DisplayPercent(true, true, null, aulaTime.AddHours(8)) == 98);
Check("AULA cached percentage expires after 24 hours",
    aulaCache.DisplayPercent(true, true, null, aulaTime.AddHours(24)) is null);
Check("AULA unknown presence hides cache",
    aulaCache.DisplayPercent(true, false, null, aulaTime.AddSeconds(32)) is null);
Check("AULA clock rollback hides old cache",
    aulaCache.DisplayPercent(true, true, null, aulaTime.AddSeconds(-1)) is null);
aulaCache.Observe(true, true, 97, aulaTime.AddSeconds(60));
Check("AULA successful recovery clears failure count",
    aulaCache.LastGoodPercent == 97 && aulaCache.ConsecutiveFailures == 0);
aulaCache.Observe(false, true, null, aulaTime.AddSeconds(61));
Check("AULA unplug invalidates cache",
    aulaCache.LastGoodPercent is null && aulaCache.LastGoodAt is null &&
    aulaCache.DisplayPercent(true, true, null, aulaTime.AddSeconds(62)) is null);
aulaCache.Observe(true, true, 96, aulaTime.AddSeconds(70));
aulaCache.Reset();
Check("AULA opt-out invalidates cache", aulaCache.LastGoodPercent is null);
aulaCache.Observe(true, true, 93, aulaTime);
aulaCache.Observe(false, false, null, aulaTime.AddSeconds(30));
Check("AULA uncertain enumeration retains hidden last-good sample",
    aulaCache.LastGoodPercent == 93 && aulaCache.LastGoodAt == aulaTime &&
    aulaCache.DisplayPercent(false, false, null, aulaTime.AddSeconds(30)) is null);
Check("AULA same receiver can reuse cached sample after uncertainty",
    aulaCache.DisplayPercent(true, true, null, aulaTime.AddSeconds(31)) == 93);
aulaCache.Observe(false, true, null, aulaTime.AddSeconds(32));
Check("AULA confirmed unplug still invalidates sample",
    aulaCache.LastGoodPercent is null && aulaCache.LastGoodAt is null);

var aulaIdentity = new AulaReceiverContinuity();
string knownAula = new string('A', 64);
string replacementAula = new string('B', 64);
Check("AULA first confirmed receiver does not clear empty cache",
    !aulaIdentity.MustReset(true, true, knownAula));
Check("AULA uncertain enumeration cannot infer a different receiver",
    !aulaIdentity.MustReset(false, false, null));
Check("AULA same receiver after uncertainty retains cache",
    !aulaIdentity.MustReset(true, true, knownAula));
Check("AULA confirmed different receiver invalidates cache",
    aulaIdentity.MustReset(true, true, replacementAula));
Check("AULA confirmed removal invalidates cache",
    aulaIdentity.MustReset(true, false, null));
Check("AULA confirmed present without an identity cannot inherit cache",
    aulaIdentity.MustReset(true, true, null));
Check("AULA reinsert after confirmed removal starts fresh",
    !aulaIdentity.MustReset(true, true, knownAula));
aulaIdentity.Reset();
Check("AULA explicit reset clears continuity identity",
    !aulaIdentity.MustReset(true, true, replacementAula));

// Setting a palette changes appearance, not battery status.
string colorKeyA = new string('A', 64);
string colorKeyB = new string('B', 64);
Check("Tray palette default unchanged", TrayColorRules.Resolve(80, true, false, null) == 0x1B9767);
Check("Tray palette blue at normal charge", TrayColorRules.Resolve(80, true, false, "blue") == 0x2464C7);
Check("Tray palette low battery overrides color", TrayColorRules.Resolve(10, true, false, "blue") == TrayColorRules.Red);
Check("Tray palette warning overrides color", TrayColorRules.Resolve(20, true, false, "purple") == TrayColorRules.Amber);
Check("Tray palette cached overrides warning", TrayColorRules.Resolve(8, true, true, "blue") == TrayColorRules.Gray);
Check("Tray palette disconnected overrides color", TrayColorRules.Resolve(90, false, false, "pink") == TrayColorRules.Gray);
Check("Tray palette invalid level unavailable", TrayColorRules.Resolve(101, true, false, "pink") == TrayColorRules.Gray);
Check("Tray palette invalid selection uses default", TrayColorRules.Normalize("unknown") == TrayColorRules.Default);
var colors = TrayColorRules.Clean(new Dictionary<string, string>
{
    [colorKeyA] = "blue", [colorKeyB] = "purple",
    [DeviceAliasRules.AulaSlot] = "green", ["path"] = "pink"
});
Check("Tray palettes preserve independent valid preferences",
    colors.Count == 3 && colors[colorKeyA] == "blue" && colors[colorKeyB] == "purple" &&
    colors[DeviceAliasRules.AulaSlot] == "green");
Check("Tray palette null settings safe", TrayColorRules.Clean(null).Count == 0);
Check("Tray colors survive settings round trip",
    System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
        System.Text.Json.JsonSerializer.Serialize(new AppSettings { DeviceTrayColors = colors }))
        ?.DeviceTrayColors[colorKeyB] == "purple");

foreach (string theme in TrayColorRules.AppIcons)
{
    Check($"App icon choice {theme} recognized", TrayColorRules.NormalizeAppIcon(theme) == theme);
    Check($"Critical {theme} is red", TrayColorRules.Resolve(10, true, false, theme) == TrayColorRules.Red);
    Check($"Fresh {theme} normal mouse", TrayColorRules.ShowMouse(21, true, false, true));
}
Check("Unknown icon choice defaults orange", TrayColorRules.NormalizeAppIcon("../bad") == "orange");
Check("Inherit global color", TrayColorRules.EffectiveColor(null, "orange") == "orange");
Check("Explicit green overrides global", TrayColorRules.EffectiveColor("green", "orange") == "green");
Check("Critical always numeric", !TrayColorRules.ShowMouse(10, true, false, true));
Check("Amber warning numeric", !TrayColorRules.ShowMouse(20, true, false, true));
Check("Stale always numeric", !TrayColorRules.ShowMouse(80, true, true, true));
Check("Mouse icon unchanged across normal levels",
    TrayIconRenderKey.Create(80, true, false, color: "orange", mouseStyle: true) ==
    TrayIconRenderKey.Create(79, true, false, color: "orange", mouseStyle: true));
Check("Neutral icon changes with branding",
    TrayIconRenderKey.Create(null, false, false, true, brand: "white") !=
    TrayIconRenderKey.Create(null, false, false, true, brand: "black"));
Check("Critical redraws on percentage change",
    TrayIconRenderKey.Create(8, true, false, color: "orange", mouseStyle: true) !=
    TrayIconRenderKey.Create(7, true, false, color: "orange", mouseStyle: true));
Check("Appearance preferences round trip",
    System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
        System.Text.Json.JsonSerializer.Serialize(new AppSettings
        { ApplicationIconColor = "blue", DefaultTrayColor = "white", MouseTrayIcon = false }))
        is { ApplicationIconColor: "blue", DefaultTrayColor: "white", MouseTrayIcon: false });

// Tray visibility must not alter receiver measurement identity.
string trayKeyA = new string('A', 64);
string trayKeyB = new string('B', 64);
var hiddenTray = TrayVisibilityRules.Clean(new[] { trayKeyA, "raw path", trayKeyA });
Check("Tray visibility defaults on", TrayVisibilityRules.IsVisible(
    new AppSettings().HiddenTrayDevices, trayKeyA));
Check("Tray preference rejects invalid keys and duplicates", hiddenTray.Count == 1);
Check("Hidden preferred receiver replaced by visible receiver",
    TrayVisibilityRules.SelectMouse(trayKeyA, new[] { trayKeyA, trayKeyB }, hiddenTray) == trayKeyB);
Check("No visible receiver returns null",
    TrayVisibilityRules.SelectMouse(trayKeyA, new[] { trayKeyA }, hiddenTray) is null);
Check("Visible preferred receiver remains primary",
    TrayVisibilityRules.SelectMouse(trayKeyB, new[] { trayKeyA, trayKeyB },
        new HashSet<string>()) == trayKeyB);
Check("AULA can be hidden independently", !TrayVisibilityRules.IsVisible(
    TrayVisibilityRules.Clean(new[] { DeviceAliasRules.AulaSlot }), DeviceAliasRules.AulaSlot));
Check("Tray hidden keys survive settings round trip",
    System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
        System.Text.Json.JsonSerializer.Serialize(new AppSettings { HiddenTrayDevices = hiddenTray }))
        ?.HiddenTrayDevices.SetEquals(hiddenTray) == true);

// Local aliases are presentation-only, never hardware identity.
string aliasKeyA = new string('A', 64);
string aliasKeyB = new string('B', 64);
Check("Alias validates local hashed keys only",
    DeviceAliasRules.ValidKey(aliasKeyA) &&
    DeviceAliasRules.ValidKey(DeviceAliasRules.AulaSlot) &&
    !DeviceAliasRules.ValidKey("HID-device-path"));
Check("Alias trims whitespace and preserves Unicode",
    DeviceAliasRules.TryNormalize("  Моя мышь  ", out string aliasName) && aliasName == "Моя мышь");
Check("Alias empty resets", DeviceAliasRules.TryNormalize(" ", out string emptyAlias) &&
    emptyAlias == "" && DeviceAliasRules.DisplayName("AJ159", emptyAlias) == "AJ159");
Check("Alias rejects overlong names",
    !DeviceAliasRules.TryNormalize(new string('a', 41), out _));
Check("Alias rejects internal controls and invisible formatting",
    !DeviceAliasRules.TryNormalize("a\nb", out _) &&
    !DeviceAliasRules.TryNormalize("a\u202Eb", out _));
Check("Alias keeps detected label",
    DeviceAliasRules.DisplayName("AJ159", "Desk") == "Desk — AJ159");
var cleanAliases = DeviceAliasRules.Clean(new Dictionary<string, string>
{
    [aliasKeyA] = "Desk", [aliasKeyB] = "Desk", ["raw-path"] = "Ignored"
});
Check("Alias keys distinguish duplicate names", cleanAliases.Count == 2 &&
    cleanAliases[aliasKeyA] == cleanAliases[aliasKeyB]);
Check("Alias null settings safe", DeviceAliasRules.Clean(null).Count == 0);
var aliasSettings = new AppSettings { DeviceAliases = cleanAliases };
Check("Aliases round trip in settings",
    System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
        System.Text.Json.JsonSerializer.Serialize(aliasSettings))?.DeviceAliases.Count == 2);

// Windows friendly-name preview is restricted to exact eligible families.
Check("PnP AJAZZ root only", PnpNameRules.IsRoot(@"USB\VID_3151&PID_5007\local") &&
    !PnpNameRules.IsRoot(@"USB\VID_3151&PID_5007&MI_00\local"));
Check("PnP AULA root family", PnpNameRules.Family(@"usb\vid_05ac&pid_024f\local") == "05AC:024F");
Check("PnP HID only primary interface", PnpNameRules.IsPrimaryHid(@"HID\VID_3151&PID_5007&MI_00\local") &&
    !PnpNameRules.IsPrimaryHid(@"HID\VID_3151&PID_5007&MI_02\local"));
Check("PnP unrelated HID rejected", PnpNameRules.Family(@"HID\VID_1234&PID_5678&MI_00\local") is null);
Check("PnP similar PID rejected", PnpNameRules.Family(@"USB\VID_3151&PID_50070\local") is null);
Check("PnP AJ159 revision from root hardware ID", PnpNameRules.Revision("3151:5007",
    new[] { @"USB\VID_3151&PID_5007&REV_0300", @"USB\VID_3151&PID_5007" }) == 0x0300);
Check("PnP ambiguous revision stays unknown", PnpNameRules.Revision("3151:5007",
    new[] { @"USB\VID_3151&PID_5007&REV_0300", @"USB\VID_3151&PID_5007&REV_0002" }) is null);
Check("PnP unrelated revision rejected", PnpNameRules.Revision("3151:5007",
    new[] { @"USB\VID_05AC&PID_024F&REV_0136" }) is null);
Check("PnP unrecognized revision generic", PnpNameRules.Model("3151:5007", 0x9999) == "AJAZZ receiver");
Check("PnP rev0002 does not guess AJ179", PnpNameRules.Model("3151:5007", 0x0002) ==
    "AJAZZ shared receiver (model unverified)");
Check("PnP observed L99 revision provisional suggestion",
    PnpNameRules.Model("05AC:024F", 0x0136) == "AULA L99");

// Device Manager displays observations rather than performing additional reads.
var dashboardAt = DateTimeOffset.Parse("2026-11-22T15:18:19Z");
DeviceDashboardState Dashboard(bool checkedOnce = true, bool known = true,
    bool present = true, int? fresh = null, int? cached = null)
    => DeviceDashboardState.FromPoll("L99", "2.4 GHz", checkedOnce, known,
        present, fresh, dashboardAt, cached, dashboardAt.AddSeconds(-31));
Check("Dashboard initial device not checked",
    Dashboard(checkedOnce: false).Status == DeviceDashboardStatus.NotChecked);
Check("Dashboard unknown presence never reports stale battery",
    Dashboard(known: false, fresh: 98, cached: 98) is
        { Status: DeviceDashboardStatus.PresenceUnknown, Percent: null });
Check("Dashboard disconnected device never reports battery",
    Dashboard(present: false, fresh: 98, cached: 98) is
        { Status: DeviceDashboardStatus.Disconnected, Percent: null });
Check("Dashboard fresh battery takes priority",
    Dashboard(fresh: 97, cached: 98) is
        { Status: DeviceDashboardStatus.Fresh, Percent: 97 });
var cachedDashboard = Dashboard(cached: 98);
Check("Dashboard labels cached percentage and original measurement time",
    cachedDashboard.Status == DeviceDashboardStatus.Cached &&
    cachedDashboard.Percent == 98 &&
    cachedDashboard.MeasuredAt == dashboardAt.AddSeconds(-31));
Check("Dashboard present without reply remains unknown",
    Dashboard() is { Status: DeviceDashboardStatus.NoReply, Percent: null });
Check("Dashboard preserves valid zero percentage",
    Dashboard(fresh: 0) is { Status: DeviceDashboardStatus.Fresh, Percent: 0 });
Check("Dashboard rejects invalid out-of-range values",
    Dashboard(fresh: 101, cached: -1) is
        { Status: DeviceDashboardStatus.NoReply, Percent: null });

string statusLanguage = UiText.Language;
foreach (string language in new[] { "en", "ru", "uk" })
{
    UiText.SetLanguage(language);
    Check($"AULA cached menu retains original time ({language})",
        cachedDashboard.MenuStatus().Contains("98%") &&
        cachedDashboard.MenuStatus().Contains(UiText.Get("Cached reading")) &&
        cachedDashboard.MenuStatus().Contains(cachedDashboard.MeasuredAt!.Value.ToLocalTime().ToString("g")));
    Check($"Manual and fresh status remain distinct ({language})",
        (Dashboard(fresh: 97) with { Status = DeviceDashboardStatus.ManualReading })
            .MenuStatus().Contains(UiText.Get("Manual reading")) &&
        Dashboard(fresh: 97).MenuStatus().Contains(UiText.Get("Fresh reading")));
    Check($"Unknown presence hides numbers and timestamps ({language})",
        Dashboard(known: false, fresh: 98, cached: 98).MenuStatus(dashboardAt) ==
            UiText.Get("Receiver status unknown"));
    Check($"BLE standby hides historical values ({language})",
        new DeviceDashboardState("BLE", "Bluetooth", DeviceDashboardStatus.Standby, null, null)
            .MenuStatus(dashboardAt) == UiText.Get("Standby (USB priority)"));
    Check($"No reply preserves only historical time ({language})",
        Dashboard().MenuStatus(dashboardAt) ==
            UsbTrayStatus.WithLastVerified(UiText.Get("No valid reply"), dashboardAt));
    Check($"BLE zero is valid numeric sample ({language})",
        Dashboard(fresh: 0).MenuStatus().StartsWith("0%"));
}
UiText.SetLanguage(statusLanguage);

// AULA's shared dongle must never be probed unless manually requested/opted in.
Check("AULA opt-in defaults off", !new AppSettings().MonitorAulaL99);
Check("AULA separate history CSV",
    new BatteryHistory("aula-l99-history.csv").FileName ==
    "aula-l99-history.csv");
AppSettings aulaOptIn = new() { MonitorAulaL99 = true };
Check("AULA opt-in setting survives JSON",
    System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
        System.Text.Json.JsonSerializer.Serialize(aulaOptIn))?.MonitorAulaL99 == true);
Check("AULA exact interface matching", AulaL99Protocol.MatchesPath(
    @"\\?\hid#vid_05ac&pid_024f&mi_03#7&abc"));
Check("AULA wrong interface rejected", !AulaL99Protocol.MatchesPath(
    @"\\?\hid#vid_05ac&pid_024f&mi_01#7&abc"));
Check("AULA AJAZZ receiver rejected", !AulaL99Protocol.MatchesPath(
    @"\\?\hid#vid_3151&pid_5007&mi_02#7&abc"));
Check("AULA vendor HID caps only",
    AulaL99Protocol.MatchesCaps(0xff00, 33, 33) &&
    !AulaL99Protocol.MatchesCaps(1, 33, 33) &&
    !AulaL99Protocol.MatchesCaps(0xff00, 65, 65));
byte[] aulaBatteryQuery = AulaL99Protocol.BatteryRequest();
Check("AULA battery request exact 33 bytes",
    aulaBatteryQuery.Length == 33 && aulaBatteryQuery[0] == 0 &&
    aulaBatteryQuery[1] == 0x20 && aulaBatteryQuery[2] == 1 &&
    aulaBatteryQuery[32] == 0x21 &&
    aulaBatteryQuery.Skip(3).Take(29).All(x => x == 0));
Check("AULA only battery query allowlisted",
    AulaL99Protocol.IsApprovedRequest(aulaBatteryQuery));
byte[] otherCommand = (byte[])aulaBatteryQuery.Clone();
otherCommand[1] = 0x05;
Check("AULA settings command blocked",
    !AulaL99Protocol.IsApprovedRequest(otherCommand));
byte[] aulaReply = new byte[33];
aulaReply[1] = 0x20;
aulaReply[2] = 1;
aulaReply[4] = 83;
Check("AULA battery 83% parsing", AulaL99Protocol.ParseBatteryReply(
    aulaReply) == 83);
Check("AULA raw 32 byte reply parsing", AulaL99Protocol.ParseBatteryReply(
    aulaReply.AsSpan(1)) == 83);
aulaReply[4] = 0;
Check("AULA no reading is not zero", AulaL99Protocol.ParseBatteryReply(
    aulaReply) is null);
aulaReply[4] = 101;
Check("AULA invalid percentage rejected", AulaL99Protocol.ParseBatteryReply(
    aulaReply) is null);
aulaReply[4] = 100;
aulaReply[1] = 0x05;
Check("AULA unrelated response rejected", AulaL99Protocol.ParseBatteryReply(
    aulaReply) is null);

// The Windows report includes an empty HID report ID at byte 0.
var local = new DateTime(2026, 11, 6, 9, 57, 42);
byte[] clock = DockClockReport.Create(local);
Check("clock report is 65 bytes", clock.Length == 65);
Check("clock opcode and marker", clock[0] == 0 && clock[1] == 0x28 &&
    clock[8] == 0xD7);
Check("clock year is big endian", clock[9] == 0x07 && clock[10] == 0xEA);
Check("clock date", clock[11] == 11 && clock[12] == 6);
Check("clock time", clock[13] == 9 && clock[14] == 57 && clock[15] == 42);
Check("clock reserved bytes zero", clock.Skip(16).All(b => b == 0) &&
    clock.Skip(2).Take(6).All(b => b == 0));
Check("clock length validated", ThrowsBadReportLength());

DockClockSchedule schedule = new();
DateTimeOffset start = new(2026, 11, 6, 10, 0, 0, TimeSpan.Zero);
Check("clock auto disabled", !schedule.ShouldAttempt(start, false, true));
Check("clock initial sync", schedule.ShouldAttempt(start, true, true));
schedule.RecordAttempt(start);
Check("clock no rapid repeats", !schedule.ShouldAttempt(start.AddMinutes(1), true, true));
Check("clock periodic resync", schedule.ShouldAttempt(start.AddMinutes(5), true, true));
schedule.RecordAttempt(start.AddMinutes(5));
Check("clock receiver removed", !schedule.ShouldAttempt(start.AddMinutes(6), true, false));
Check("clock receiver reconnected", schedule.ShouldAttempt(start.AddMinutes(6), true, true));

// A transient unknown presence must not restart the dock RTC schedule.
DockClockSchedule uncertainClock = new();
Check("clock initially present", uncertainClock.ShouldAttempt(start, true, true));
uncertainClock.RecordAttempt(start);
Check("clock unknown absence never writes",
    !uncertainClock.ShouldAttempt(start.AddMinutes(1), true, false, presenceKnown: false));
Check("clock unknown presence never writes",
    !uncertainClock.ShouldAttempt(start.AddMinutes(1), true, true, presenceKnown: false));
Check("clock same confirmed receiver after uncertainty is not a reconnect",
    !uncertainClock.ShouldAttempt(start.AddMinutes(2), true, true));
Check("clock deadline remains due after uncertainty",
    uncertainClock.ShouldAttempt(start.AddMinutes(5), true, true));
uncertainClock.RecordAttempt(start.AddMinutes(5));
Check("clock confirmed unplug still resets",
    !uncertainClock.ShouldAttempt(start.AddMinutes(6), true, false));
Check("clock confirmed replug still synchronizes",
    uncertainClock.ShouldAttempt(start.AddMinutes(6), true, true));

// A corrected Windows clock must not postpone RTC synchronization for hours.
DockClockSchedule correctedClock = new();
Check("clock correction initial sync", correctedClock.ShouldAttempt(start, true, true));
correctedClock.RecordAttempt(start);
DateTimeOffset rolledBack = start.AddHours(-2);
Check("clock correction backwards triggers resync",
    correctedClock.ShouldAttempt(rolledBack, true, true));
correctedClock.RecordAttempt(rolledBack);
Check("clock correction does not cause repeat writes",
    !correctedClock.ShouldAttempt(rolledBack.AddMinutes(1), true, true));
Check("clock correction restores normal five-minute interval",
    correctedClock.ShouldAttempt(rolledBack.AddMinutes(5), true, true));

bool ThrowsBadReportLength()
{
    try
    {
        DockClockReport.Create(local, 16);
        return false;
    }
    catch (ArgumentOutOfRangeException)
    {
        return true;
    }
}

// History and connection rules run without real mouse hardware.
DateTimeOffset t0 = new(2026, 11, 6, 12, 0, 0, TimeSpan.Zero);
BatterySample online = new(t0, 74, "online");
Check("state with battery", BatteryHistoryRules.State(true, 74) == "online");
Check("state with asleep mouse", BatteryHistoryRules.State(true, null) == "unavailable");
Check("state without receiver", BatteryHistoryRules.State(false, null) == "disconnected");
Check("new point stored", BatteryHistoryRules.ShouldRecord(null, online));
Check("duplicate point suppressed", !BatteryHistoryRules.ShouldRecord(
    online, online with { Timestamp = t0.AddMinutes(1) }));
Check("five-minute sample kept", BatteryHistoryRules.ShouldRecord(
    online, online with { Timestamp = t0.AddMinutes(5) }));
Check("percentage change kept", BatteryHistoryRules.ShouldRecord(
    online, online with { Timestamp = t0.AddSeconds(30), Percent = 73 }));
Check("disconnect event kept", BatteryHistoryRules.ShouldRecord(
    online, new BatterySample(t0.AddSeconds(30), null, "disconnected")));
Check("history retention", BatteryHistoryRules.Retain(
    new[] { online with { Timestamp = t0.AddDays(-32) }, online },
    t0.AddSeconds(1)).Count == 1);

ConnectionAlertPolicy disconnectPolicy = new();
Check("no alert before first online", !disconnectPolicy.Evaluate(false, false));
Check("first online no disconnect alert", !disconnectPolicy.Evaluate(true, true));
Check("one missing poll ignored", !disconnectPolicy.Evaluate(false, false));
Check("second missing poll alerts", disconnectPolicy.Evaluate(false, false));
Check("no duplicate disconnect alert", !disconnectPolicy.Evaluate(false, false));
Check("reconnect resets disconnect", !disconnectPolicy.Evaluate(true, true));
Check("receiver present asleep ignored", !disconnectPolicy.Evaluate(false, true));
Check("disconnect alert after reconnect", !disconnectPolicy.Evaluate(false, false) &&
    disconnectPolicy.Evaluate(false, false));

// CSV must preserve valid values while rejecting inconsistent state rows.
string timeText = t0.ToString("O");
Check("CSV valid 0% online", BatteryHistoryCsv.Parse(
    $"{timeText},0,online")?.Percent == 0);
Check("CSV valid 100% online", BatteryHistoryCsv.Parse(
    $"{timeText},100,online")?.Percent == 100);
Check("CSV unavailable without percentage", BatteryHistoryCsv.Parse(
    $"{timeText},,unavailable")?.State == "unavailable");
Check("CSV disconnect without percentage", BatteryHistoryCsv.Parse(
    $"{timeText},,disconnected")?.State == "disconnected");
Check("CSV rejects online without percent", BatteryHistoryCsv.Parse(
    $"{timeText},,online") is null);
Check("CSV rejects disconnected with percent", BatteryHistoryCsv.Parse(
    $"{timeText},20,disconnected") is null);
Check("CSV rejects unavailable with percent", BatteryHistoryCsv.Parse(
    $"{timeText},20,unavailable") is null);
Check("CSV rejects invalid negative percentage", BatteryHistoryCsv.Parse(
    $"{timeText},-1,online") is null);
Check("CSV rejects 101 percent", BatteryHistoryCsv.Parse(
    $"{timeText},101,online") is null);
Check("CSV rejects malformed date", BatteryHistoryCsv.Parse(
    "not-a-date,40,online") is null);
Check("CSV rejects malformed state", BatteryHistoryCsv.Parse(
    $"{timeText},50,pending") is null);
Check("CSV rejects extra columns", BatteryHistoryCsv.Parse(
    $"{timeText},70,online,extra") is null);
Check("CSV rejects header as a sample",
    BatteryHistoryCsv.Parse(BatteryHistoryCsv.Header) is null);
BatterySample csvSample = new(t0, 0, "online");
Check("CSV round-trip preserves 0%", BatteryHistoryCsv.Parse(
    BatteryHistoryCsv.Format(csvSample)) == csvSample);
BatterySample gapSample = new(t0, null, "unavailable");
Check("CSV round-trip preserves gap", BatteryHistoryCsv.Parse(
    BatteryHistoryCsv.Format(gapSample)) == gapSample);
DateTimeOffset offsetTime = new(2026, 11, 7, 1, 30, 0,
    TimeSpan.FromHours(2));
BatterySample shifted = new(offsetTime, 86, "online");
Check("CSV normalizes timestamp to UTC", BatteryHistoryCsv.Parse(
    BatteryHistoryCsv.Format(shifted))?.Timestamp.Offset == TimeSpan.Zero);
Check("CSV header unchanged for existing files",
    BatteryHistoryCsv.Header == "utc_timestamp,percent,state");

// SetupAPI must not treat a failed HID scan as confirmed USB removal.
Check("SetupAPI normal end recognized",
    HidEnumerationRules.IsNormalEnd(HidEnumerationRules.NoMoreItems));
Check("SetupAPI access denied is not end",
    !HidEnumerationRules.IsNormalEnd(5));
Check("SetupAPI invalid parameter is not end",
    !HidEnumerationRules.IsNormalEnd(87));
Check("SetupAPI error code zero is not end",
    !HidEnumerationRules.IsNormalEnd(0));
Check("SetupAPI detail size probe accepts expected Win32 error",
    HidEnumerationRules.IsExpectedSizeQueryError(122));
Check("SetupAPI detail size probe rejects access denied",
    !HidEnumerationRules.IsExpectedSizeQueryError(5));
Check("SetupAPI detail size probe rejects false success",
    !HidEnumerationRules.IsExpectedSizeQueryError(0));
Check("SetupAPI detail size rejects short buffer",
    !HidEnumerationRules.IsValidDetailSize(7));
Check("SetupAPI detail size accepts minimum",
    HidEnumerationRules.IsValidDetailSize(8));
Check("SetupAPI detail size accepts maximum",
    HidEnumerationRules.IsValidDetailSize(65536));
Check("SetupAPI detail size rejects huge buffer",
    !HidEnumerationRules.IsValidDetailSize(65537));

// Stop unknown or malformed HID writes before they reach the receiver.
byte[] telemetry = new byte[65];
telemetry[1] = 0xF7;
Check("safe telemetry allowed", HidFeaturePolicy.IsApproved(telemetry));
Check("safe dock clock allowed", HidFeaturePolicy.IsApproved(clock));
Check("blocked button matrix command", !AllowedCommand(0x50));
Check("blocked screen upload", !AllowedCommand(0x25));
Check("blocked 24-bit display upload", !AllowedCommand(0x29));
Check("blocked GIF begin", !AllowedCommand(0x18));
Check("blocked firmware bootloader", !AllowedCommand(0x40));
byte[] damagedClock = (byte[])clock.Clone();
damagedClock[8] = 0;
Check("clock marker required", !HidFeaturePolicy.IsApproved(damagedClock));
damagedClock = (byte[])clock.Clone();
damagedClock[12] = 31;
damagedClock[11] = 2;
Check("impossible date rejected", !HidFeaturePolicy.IsApproved(damagedClock));
telemetry[5] = 42;
Check("nonzero telemetry payload blocked", !HidFeaturePolicy.IsApproved(telemetry));

bool AllowedCommand(byte opcode)
{
    byte[] frame = new byte[65];
    frame[1] = opcode;
    return HidFeaturePolicy.IsApproved(frame);
}

// Standard Battery Level is one byte 0..100; zero is a valid measured value.
Check("BLE candidate AJAZZ", BluetoothBatteryRules.IsCandidateName("AJAZZ AJ179"));
Check("BLE candidate AJ159", BluetoothBatteryRules.IsCandidateName("AJ159 APEX"));
Check("BLE reject unrelated", !BluetoothBatteryRules.IsCandidateName("Keyboard"));
Check("BLE reject empty name", !BluetoothBatteryRules.IsCandidateName(""));
Check("BLE 0% is valid", BatteryLevelMatches(new byte[] { 0 }, 0));
Check("BLE 57% is valid", BatteryLevelMatches(new byte[] { 57 }, 57));
Check("BLE 100% is valid", BatteryLevelMatches(new byte[] { 100 }, 100));
Check("BLE 101% invalid", !BluetoothBatteryRules.TryParseLevel(
    new byte[] { 101 }, out _));
Check("BLE no data invalid", !BluetoothBatteryRules.TryParseLevel(
    Array.Empty<byte>(), out _));
Check("BLE extra bytes invalid", !BluetoothBatteryRules.TryParseLevel(
    new byte[] { 55, 0 }, out _));

bool BatteryLevelMatches(byte[] bytes, int expected)
    => BluetoothBatteryRules.TryParseLevel(bytes, out int level) &&
       level == expected;

Check("history captures backward clock change",
    BatteryHistoryRules.ShouldRecord(online,
        online with { Timestamp = t0.AddMinutes(-15) }));
Check("Bluetooth timeout accepts completed task",
    BluetoothOperationTimeout.Run(Task.FromResult(73),
        TimeSpan.FromSeconds(1)).GetAwaiter().GetResult() == 73);
Check("Bluetooth timeout rejects invalid limit",
    ThrowsBadBluetoothLimit());
Check("Bluetooth pending operation times out",
    BluetoothTaskTimesOut());

bool ThrowsBadBluetoothLimit()
{
    try
    {
        BluetoothOperationTimeout.Run(Task.FromResult(1), TimeSpan.Zero);
        return false;
    }
    catch (ArgumentOutOfRangeException)
    {
        return true;
    }
}

bool BluetoothTaskTimesOut()
{
    try
    {
        TaskCompletionSource<int> pending = new();
        BluetoothOperationTimeout.Run(pending.Task,
            TimeSpan.FromMilliseconds(20)).GetAwaiter().GetResult();
        return false;
    }
    catch (TimeoutException)
    {
        return true;
    }
}

Check("Windows byte battery 0% accepted",
    WindowsLevelEquals((byte)0, 0));
Check("Windows byte battery 65% accepted",
    WindowsLevelEquals((byte)65, 65));
Check("Windows integer battery 100% accepted",
    WindowsLevelEquals(100, 100));
Check("Windows unknown sentinel 101 rejected",
    !BluetoothBatteryRules.TryParseWindowsLevel((byte)101, out _));
Check("Windows battery 255 rejected",
    !BluetoothBatteryRules.TryParseWindowsLevel((byte)255, out _));
Check("Windows battery negative rejected",
    !BluetoothBatteryRules.TryParseWindowsLevel(-1, out _));
Check("Windows null battery rejected",
    !BluetoothBatteryRules.TryParseWindowsLevel(null, out _));
Check("Windows battery string rejected",
    !BluetoothBatteryRules.TryParseWindowsLevel("75", out _));
Check("Bluetooth unnamed not auto-matched",
    !BluetoothBatteryRules.IsCandidateName("Unnamed paired device"));

bool WindowsLevelEquals(object raw, int expected)
    => BluetoothBatteryRules.TryParseWindowsLevel(raw, out int level) &&
       level == expected;

// A generic Windows mouse name must not be hidden after explicit Show all.
Check("BLE standard AJAZZ visible by default",
    BluetoothBatteryRules.ShouldShow("AJAZZ AJ179", false));
Check("BLE generic paired mouse hidden by default",
    !BluetoothBatteryRules.ShouldShow("Bluetooth Mouse", false));
Check("BLE generic paired mouse visible with Show all",
    BluetoothBatteryRules.ShouldShow("Bluetooth Mouse", true));
Check("BLE unnamed endpoint visible with Show all",
    BluetoothBatteryRules.ShouldShow(null, true));

// Automatic BLE fallback requires explicit opt-in and a direct GATT reading.
BluetoothAutoPolicy automaticBle = new();
Check("BLE auto disabled by default", !automaticBle.Enabled);
Check("BLE no polling without opt-in", !automaticBle.ShouldRead(false, t0));
int initialGeneration = automaticBle.Generation;
automaticBle.Enable(83, t0);
Check("BLE selection changes generation",
    automaticBle.Generation == initialGeneration + 1);
Check("BLE fresh 83% visible without USB", automaticBle.VisiblePercent(
    false, t0.AddSeconds(10)) == 83);
Check("BLE status shows USB primary", automaticBle.StatusText(
    true, false, t0.AddSeconds(10)).Contains("USB primary"));
Check("BLE status shows fresh GATT", automaticBle.StatusText(
    false, false, t0.AddSeconds(10)).Contains("83%"));
Check("BLE status shows polling", automaticBle.StatusText(
    false, true, t0.AddSeconds(10)).Contains("checking battery"));
Check("USB receiver always takes priority", automaticBle.VisiblePercent(
    true, t0.AddSeconds(10)) is null);
Check("BLE no read before one minute", !automaticBle.ShouldRead(
    false, t0.AddSeconds(59)));
Check("BLE read due after one minute", automaticBle.ShouldRead(
    false, t0.AddSeconds(60)));
Check("BLE no background read while USB present", !automaticBle.ShouldRead(
    true, t0.AddMinutes(5)));
Check("BLE reading expires instead of staying stale", automaticBle.VisiblePercent(
    false, t0.AddSeconds(121)) is null);
BluetoothBatteryResult direct = new(82, BluetoothBatterySource.DirectGatt,
    "Display text can change without changing trust.");
BluetoothBatteryResult cached = new(77, BluetoothBatterySource.WindowsCached,
    "Fresh GATT Battery Level (2A19) read.");
BluetoothBatteryResult missing = new(null, BluetoothBatterySource.Unavailable,
    "No battery response");
Check("typed GATT source accepts different display text", direct.IsFreshGatt);
Check("typed Windows cache rejected despite misleading text", !cached.IsFreshGatt);
Check("typed unavailable rejected", !missing.IsFreshGatt);
Check("direct out-of-range rejected", !new BluetoothBatteryResult(
    255, BluetoothBatterySource.DirectGatt, "GATT").IsFreshGatt);

automaticBle.RecordRead(direct, t0.AddMinutes(2));
Check("BLE direct refresh updates percent", automaticBle.VisiblePercent(
    false, t0.AddMinutes(2)) == 82);
automaticBle.RecordRead(cached, t0.AddMinutes(3));
Check("BLE cached read clears current value", automaticBle.VisiblePercent(
    false, t0.AddMinutes(3)) is null);
Check("BLE cached read counts one failure", automaticBle.ConsecutiveFailures == 1);
Check("BLE unavailable status shows failures", automaticBle.StatusText(
    false, false, t0.AddMinutes(3)).Contains("1 failed"));
Check("BLE last successful reading retained for diagnostics",
    automaticBle.LastSuccessfulRead == t0.AddMinutes(2));
automaticBle.RecordRead(new BluetoothBatteryResult(0,
    BluetoothBatterySource.DirectGatt, "GATT"), t0.AddMinutes(4));
Check("BLE zero accepted from valid GATT", automaticBle.VisiblePercent(
    false, t0.AddMinutes(4)) == 0);
Check("BLE fresh direct read clears failure count",
    automaticBle.ConsecutiveFailures == 0);
Check("BLE status can display measured zero", automaticBle.StatusText(
    false, false, t0.AddMinutes(4)).Contains("0%"));
automaticBle.RecordRead(missing, t0.AddMinutes(5));
Check("BLE missing reading shows unknown", automaticBle.VisiblePercent(
    false, t0.AddMinutes(5)) is null);
Check("BLE missing response increments failure count",
    automaticBle.ConsecutiveFailures == 1);
Check("BLE last success preserved after missing response",
    automaticBle.LastSuccessfulRead == t0.AddMinutes(4));
Check("BLE last GATT attempt timestamp recorded",
    automaticBle.LastAttempt == t0.AddMinutes(5));
Check("BLE backward clock correction triggers read", automaticBle.ShouldRead(
    false, t0.AddMinutes(-2)));

BatteryDisplayState usb = BatteryDisplayState.Resolve(true, 83, true, 77);
Check("USB receiver takes priority over BLE", usb.Source == BatteryTransport.Usb24GHz &&
    usb.Percent == 83);
BatteryDisplayState sleepingUsb = BatteryDisplayState.Resolve(true, null, true, 77);
Check("sleeping USB mouse does not use BLE", sleepingUsb.Source ==
    BatteryTransport.Usb24GHz && sleepingUsb.Percent is null);
BatteryDisplayState activeBle = BatteryDisplayState.Resolve(false, null, true, 77);
Check("absent USB uses BLE source", activeBle.Source ==
    BatteryTransport.Bluetooth && activeBle.Percent == 77);
BatteryDisplayState unavailableBle = BatteryDisplayState.Resolve(false,
    null, true, null);
Check("BLE unknown labelled as Bluetooth", unavailableBle.Source ==
    BatteryTransport.Bluetooth && !unavailableBle.HasReading);
BatteryDisplayState fallbackOff = BatteryDisplayState.Resolve(false,
    null, false, 77);
Check("disabled BLE not shown in tray", fallbackOff.Source ==
    BatteryTransport.Usb24GHz && !fallbackOff.HasReading);
Check("no USB disconnect alert during BLE fallback",
    !BatteryDisplayState.NotifyReceiverDisconnect(true, true));
// Windows HID enumeration failure is unknown, not physical USB removal.
Check("unknown USB state treated as present for alerts",
    BatteryDisplayState.SafeReceiverPresent(false, false));
Check("confirmed USB absence stays absent",
    !BatteryDisplayState.SafeReceiverPresent(false, true));
Check("confirmed USB presence stays present",
    BatteryDisplayState.SafeReceiverPresent(true, true));
Check("unknown USB cannot activate BLE fallback",
    !BatteryDisplayState.MayUseBluetooth(false, false));
Check("confirmed absence may activate opted-in BLE",
    BatteryDisplayState.MayUseBluetooth(false, true));
Check("present USB cannot activate BLE fallback",
    !BatteryDisplayState.MayUseBluetooth(true, true));
BatteryDisplayState uncertainUsb = BatteryDisplayState.Resolve(
    false, null, true, 83, presenceKnown: false);
Check("unknown USB status suppresses stale BLE reading",
    uncertainUsb.Source == BatteryTransport.Usb24GHz &&
    uncertainUsb.Percent is null);
Check("unknown USB status becomes unavailable history",
    BatteryHistoryRules.State(
        BatteryDisplayState.SafeReceiverPresent(false, false),
        null) == "unavailable");
ConnectionAlertPolicy transientError = new();
transientError.Evaluate(true, true);
Check("HID error does not count as disconnected",
    !transientError.Evaluate(false,
        BatteryDisplayState.SafeReceiverPresent(false, false)));
Check("first confirmed missing poll after error ignored",
    !transientError.Evaluate(false, false));
Check("second confirmed missing poll raises warning",
    transientError.Evaluate(false, false));

ConnectionAlertPolicy interruptedAbsence = new();
interruptedAbsence.Evaluate(true, true);
Check("first absent poll is debounced", !interruptedAbsence.Evaluate(false, false));
interruptedAbsence.ObserveUnknown();
Check("unknown between absent polls interrupts the sequence",
    !interruptedAbsence.Evaluate(false, false));
Check("two consecutive confirmed absences still notify",
    interruptedAbsence.Evaluate(false, false));
interruptedAbsence.ObserveUnknown();
Check("unknown does not reset a delivered disconnect alert",
    !interruptedAbsence.Evaluate(false, false) &&
    !interruptedAbsence.Evaluate(false, false));

Check("USB disconnect alert preserved without BLE",
    BatteryDisplayState.NotifyReceiverDisconnect(true, false));

int beforeDisableGeneration = automaticBle.Generation;
automaticBle.Disable();
Check("BLE disable invalidates pending request generation",
    automaticBle.Generation == beforeDisableGeneration + 1);
Check("BLE disable erases transient reading", !automaticBle.Enabled &&
    automaticBle.VisiblePercent(false, t0.AddMinutes(5)) is null);
Check("BLE disable removes diagnostic counters",
    automaticBle.ConsecutiveFailures == 0 &&
    automaticBle.LastSuccessfulRead is null && automaticBle.LastAttempt is null);
Check("BLE status clearly shows off", automaticBle.StatusText(
    false, false, t0.AddMinutes(5)).EndsWith("off"));
automaticBle.RecordRead(missing, t0.AddMinutes(6));
Check("late BLE response ignored when disabled",
    automaticBle.ConsecutiveFailures == 0 && automaticBle.LastAttempt is null);

automaticBle.Enable(70, t0.AddMinutes(6));
Check("BLE reselect invalidates old request generation",
    automaticBle.Generation > beforeDisableGeneration + 1);
automaticBle.Disable();

// Repeated BLE errors trigger a conservative retry schedule, not constant reads.
BluetoothAutoPolicy backoff = new();
Check("BLE forced refresh requires opt-in", !backoff.CanRefreshNow(false));
backoff.Enable(83, t0);
Check("BLE force request allowed with USB absent", backoff.CanRefreshNow(false));
Check("BLE force request blocked while USB present", !backoff.CanRefreshNow(true));
Check("BLE normal interval is one minute",
    BluetoothAutoPolicy.RetryInterval(0) == TimeSpan.FromMinutes(1));
Check("BLE one failure delays two minutes",
    BluetoothAutoPolicy.RetryInterval(1) == TimeSpan.FromMinutes(2));
Check("BLE two failures delay five minutes",
    BluetoothAutoPolicy.RetryInterval(2) == TimeSpan.FromMinutes(5));
Check("BLE repeated failures cap at ten minutes",
    BluetoothAutoPolicy.RetryInterval(6) == TimeSpan.FromMinutes(10));
DateTimeOffset failedAt = t0.AddMinutes(1);
backoff.RecordRead(missing, failedAt);
Check("BLE no retry before two minutes", !backoff.ShouldRead(
    false, failedAt.AddSeconds(119)));
Check("BLE retry at two minutes", backoff.ShouldRead(
    false, failedAt.AddMinutes(2)));
failedAt = failedAt.AddMinutes(2);
backoff.RecordRead(missing, failedAt);
Check("BLE two failures wait five minutes", !backoff.ShouldRead(
    false, failedAt.AddMinutes(4)));
Check("BLE retry after five minutes", backoff.ShouldRead(
    false, failedAt.AddMinutes(5)));
failedAt = failedAt.AddMinutes(5);
backoff.RecordRead(missing, failedAt);
Check("BLE third failure delays ten minutes", !backoff.ShouldRead(
    false, failedAt.AddMinutes(9)));
Check("BLE retry at ten minutes", backoff.ShouldRead(
    false, failedAt.AddMinutes(10)));
backoff.RecordRead(direct, failedAt.AddMinutes(10));
Check("BLE good GATT read resets backoff", backoff.ConsecutiveFailures == 0 &&
    BluetoothAutoPolicy.RetryInterval(backoff.ConsecutiveFailures) ==
    TimeSpan.FromMinutes(1));
backoff.Disable();
Check("BLE manual refresh disabled after opting out",
    !backoff.CanRefreshNow(false));

// Estimate only a recent contiguous discharge trend.
var analyticsStart = DateTimeOffset.Parse("2026-01-01T10:00:00Z");
BatterySample[] analyticsSamples = {
    new(analyticsStart, 80, "online"),
    new(analyticsStart.AddMinutes(15), 77, "online"),
    new(analyticsStart.AddMinutes(30), 74, "online")
};
var analyticsNow = analyticsStart.AddMinutes(30);
var drainEstimate = BatteryAnalytics.EstimateDrain(analyticsSamples, analyticsNow);
Check("Drain estimate observed rate", drainEstimate?.PercentPerHour == 12);
Check("Drain estimate projected time", drainEstimate is not null &&
    Math.Abs(drainEstimate.HoursRemaining - 74.0 / 12) < 0.0001);
Check("Drain estimate measured span", drainEstimate?.ObservationSpan == TimeSpan.FromMinutes(30) &&
    drainEstimate.Observations == 3);
Check("Insufficient observations", BatteryAnalytics.EstimateDrain(analyticsSamples.Take(2).ToArray(), analyticsNow) is null);
Check("Stale final sample", BatteryAnalytics.EstimateDrain(analyticsSamples, analyticsNow.AddMinutes(16)) is null);
Check("Future final sample", BatteryAnalytics.EstimateDrain(analyticsSamples, analyticsNow.AddSeconds(-1)) is null);
Check("Charge increase breaks trend", BatteryAnalytics.EstimateDrain(new[] {
    analyticsSamples[0], analyticsSamples[1], new BatterySample(analyticsNow, 90, "online")
}, analyticsNow) is null);
Check("Missing battery breaks trend", BatteryAnalytics.EstimateDrain(new[] {
    analyticsSamples[0], new BatterySample(analyticsStart.AddMinutes(15), null, "unavailable"), analyticsSamples[2]
}, analyticsNow) is null);
Check("Gap breaks trend", BatteryAnalytics.EstimateDrain(new[] {
    analyticsSamples[0] with { Timestamp = analyticsStart.AddMinutes(-1) },
    analyticsSamples[1], analyticsSamples[2]
}, analyticsNow) is null);
Check("Flat trend has no runtime estimate", BatteryAnalytics.EstimateDrain(analyticsSamples.Select(x =>
    x with { Percent = 80 }).ToArray(), analyticsNow) is null);
Check("Duplicate timestamps break trend", BatteryAnalytics.EstimateDrain(new[] {
    analyticsSamples[0], analyticsSamples[1] with { Timestamp = analyticsStart }, analyticsSamples[2]
}, analyticsNow) is null);

Check("Observed discharge sums percentage drops",
    BatteryAnalytics.ObservedDischargeEquivalent(analyticsSamples, analyticsNow) is double observedEquivalent &&
    Math.Abs(observedEquivalent - 0.06) < 0.0001);
Check("Observed discharge ignores charge increases",
    BatteryAnalytics.ObservedDischargeEquivalent(new[] {
        analyticsSamples[0], analyticsSamples[1], analyticsSamples[2] with { Percent = 90 }
    }, analyticsNow) is double mixedEquivalent && Math.Abs(mixedEquivalent - 0.03) < 0.0001);
Check("No valid pairs means unavailable",
    BatteryAnalytics.ObservedDischargeEquivalent(analyticsSamples.Take(1).ToArray(), analyticsNow) is null);
Check("Flat valid observations mean zero observed drain",
    BatteryAnalytics.ObservedDischargeEquivalent(analyticsSamples.Select(x => x with { Percent = 80 }).ToArray(), analyticsNow) == 0);
Check("Unavailable rows do not bridge gaps",
    BatteryAnalytics.ObservedDischargeEquivalent(new[] {
        analyticsSamples[0], analyticsSamples[1] with { Percent = null, State = "unavailable" }, analyticsSamples[2]
    }, analyticsNow) is null);
Check("Excessive gaps do not count toward equivalent",
    BatteryAnalytics.ObservedDischargeEquivalent(new[] { analyticsSamples[0], analyticsSamples[2] }, analyticsNow) is null);
Check("Future pairs do not count",
    BatteryAnalytics.ObservedDischargeEquivalent(analyticsSamples, analyticsStart) is null);

// Independent opted-in BLE slots; one in-flight operation globally.
var multiBle = new BluetoothMultiSession();
var multiAt = DateTimeOffset.Parse("2026-01-01T12:00:00Z");
var bleDirect = new BluetoothBatteryResult(83, BluetoothBatterySource.DirectGatt, "direct");
var bleCached = new BluetoothBatteryResult(83, BluetoothBatterySource.WindowsCached, "cached");
var bleFailed = new BluetoothBatteryResult(null, BluetoothBatterySource.Unavailable, "failed");
Check("Multi BLE rejects cached opt-in", !multiBle.Enable("a", bleCached, multiAt));
Check("Multi BLE enables two independent slots", multiBle.Enable("a", bleDirect, multiAt) &&
    multiBle.Enable("b", bleDirect with { Percent = 62 }, multiAt) && multiBle.Count == 2);
Check("Multi BLE hides values when USB presence unknown", multiBle.VisiblePercent("a", false, false, multiAt) is null);
Check("Multi BLE does not sample with USB present", multiBle.TryBegin(true, true, multiAt.AddMinutes(2)) is null);
Check("Multi BLE does not sample with unknown USB", multiBle.TryBegin(false, false, multiAt.AddMinutes(2)) is null);
Check("Multi BLE not due immediately", multiBle.TryBegin(true, false, multiAt) is null);
var firstBleRequest = multiBle.TryBegin(true, false, multiAt.AddMinutes(1));
Check("Multi BLE earliest opted-in first", firstBleRequest?.Key == "a");
Check("Multi BLE enforces one in-flight request", multiBle.TryBegin(true, false, multiAt.AddMinutes(1), "b") is null);
Check("Multi BLE failure recorded for one slot", firstBleRequest is not null &&
    multiBle.Complete(firstBleRequest, bleFailed, multiAt.AddMinutes(1), true, false) &&
    multiBle.Failures("a") == 1 && multiBle.Failures("b") == 0);
var secondBleRequest = multiBle.TryBegin(true, false, multiAt.AddMinutes(1));
Check("Multi BLE other slot progresses independently", secondBleRequest?.Key == "b");
multiBle.Disable("b");
Check("Multi BLE reselect replaces session", multiBle.Enable("b", bleDirect, multiAt.AddMinutes(1)));
Check("Multi BLE disabled request stays isolated until completion", multiBle.IsBusy);
Check("Multi BLE discards reply after reselect", secondBleRequest is not null &&
    !multiBle.Complete(secondBleRequest, bleFailed, multiAt.AddMinutes(1), true, false) &&
    multiBle.Failures("b") == 0 && !multiBle.IsBusy);
var forcedBleRequest = multiBle.TryBegin(true, false, multiAt.AddMinutes(1), "b");
Check("Multi BLE explicit refresh bypasses backoff", forcedBleRequest?.Key == "b");
Check("Multi BLE discards reply if USB returns", forcedBleRequest is not null &&
    !multiBle.Complete(forcedBleRequest, bleDirect, multiAt.AddMinutes(1), true, true));
multiBle.DisableAll();
Check("Multi BLE opt-out clears all visible state", multiBle.Count == 0 &&
    multiBle.VisiblePercent("a", true, false, multiAt) is null);

var pausedBle = new BluetoothMultiSession();
pausedBle.Enable("x", bleDirect, multiAt);
var pausedRequest = pausedBle.TryBegin(true, false, multiAt.AddMinutes(1));
pausedBle.ObserveUsbPresence(true, true);
Check("USB transition invalidates old percentage", pausedBle.VisiblePercent("x", true, false, multiAt.AddMinutes(1)) is null);
pausedBle.ObserveUsbPresence(true, false);
Check("USB roundtrip invalidates in-flight reply", pausedRequest is not null &&
    !pausedBle.Complete(pausedRequest, bleDirect, multiAt.AddMinutes(1), true, false));
var resumedRequest = pausedBle.TryBegin(true, false, multiAt.AddMinutes(1));
Check("BLE resume requires fresh attempt", resumedRequest?.Key == "x");
Check("Fresh resume response accepted", resumedRequest is not null &&
    pausedBle.Complete(resumedRequest, bleDirect, multiAt.AddMinutes(1), true, false));
pausedBle.ObserveUsbPresence(false, false);
Check("Unknown USB invalidates visible value", pausedBle.VisiblePercent("x", true, false, multiAt.AddMinutes(1)) is null);
pausedBle.Enable("y", bleDirect, multiAt.AddMinutes(1));
pausedBle.ObserveUsbPresence(true, false);
Check("Opt-in while USB blocked requires a new read", pausedBle.VisiblePercent("y", true, false, multiAt.AddMinutes(1)) is null);

// Release checks are local, deterministic, and perform no HTTP requests.
var installedVersion = ReleaseVersion.Parse("v0.3.0-beta.41")!;
Check("Update accepts beta tag", installedVersion.Beta == 41);
Check("Update compares beta numbers numerically",
    ReleaseVersion.Parse("0.3.0-beta.100")!.CompareTo(installedVersion) > 0);
Check("Stable beats same base beta", ReleaseVersion.Parse("0.3.0")!.CompareTo(installedVersion) > 0);
Check("Older base beta never beats newer stable",
    ReleaseVersion.Parse("0.2.99-beta.100")!.CompareTo(ReleaseVersion.Parse("0.3.0")) < 0);
Check("Reject malformed release tags", new[] { "0.3", "v0.3.0-rc.1", "0.3.0-beta.0",
    "0.03.0", "0.3.0-beta.2147483648", "0.3.0+build", "0.3.0\n" }
    .All(tag => ReleaseVersion.Parse(tag) is null));
var releaseRows = new (string Tag, bool Draft, bool Prerelease)[] {
    ("v0.3.0-beta.42", false, false), ("v0.3.0-beta.43", false, true),
    ("v0.3.0-beta.99", true, false), ("v0.3.0-beta.40", false, false),
    ("v0.3.0-rc.1", false, true), ("v9.0.0", false, true) };
Check("Experimental accepts project beta marked Latest",
    UpdateRules.Newest(installedVersion, releaseRows.Take(1), true)?.Beta == 42);
Check("Experimental picks highest beta excluding draft and invalid tags",
    UpdateRules.Newest(installedVersion, releaseRows, true)?.Beta == 43);
Check("Stable channel never accepts beta tagged Latest",
    UpdateRules.Newest(installedVersion, releaseRows, false) is null);
Check("Stable channel accepts actual stable release",
    UpdateRules.Newest(installedVersion, releaseRows.Append(("v0.3.0", false, false)), false)
        == ReleaseVersion.Parse("0.3.0"));
Check("Equal and older releases ignored",
    UpdateRules.Newest(installedVersion, new[] { ("v0.3.0-beta.41", false, false),
        ("v0.3.0-beta.39", false, false) }, true) is null);
byte[] updateFixture = System.Text.Encoding.UTF8.GetBytes("local test fixture");
string updateHash = Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(updateFixture));
const string updateName = "AJAZZBatteryTray-win-x64.exe";
bool VerifyUpdate(string manifest, string name = updateName) =>
    UpdateRules.VerifyChecksum(new System.IO.MemoryStream(updateFixture), manifest, name);
Check("Update validates actual SHA256 manifest format", VerifyUpdate($"{updateHash}  {updateName}\r\n"));
Check("Update validates binary checksum format", VerifyUpdate($"{updateHash} *{updateName}"));
Check("Update rejects hash mismatch", !VerifyUpdate($"{new string('0', 64)}  {updateName}"));
Check("Update rejects wrong artifact or additional entries",
    !VerifyUpdate($"{updateHash}  Other.exe") &&
    !VerifyUpdate($"{updateHash}  {updateName}\n{updateHash}  Other.exe"));
Check("Update rejects unsafe artifact names", !VerifyUpdate($"{updateHash}  ../x.exe", "../x.exe"));
Check("Update rejects malformed hash", !VerifyUpdate($"not-a-hash  {updateName}"));

// No HTTP calls: exercise the exact GitHub response decoder.
byte[] ReleaseJson(string value) => System.Text.Encoding.UTF8.GetBytes(value);
var sampleListing = ReleaseJson("""
    [{"tag_name":"v0.3.0-beta.42","draft":false,"prerelease":false,"html_url":"https://example.invalid"},
     {"tag_name":"v0.3.0-beta.50","draft":true,"prerelease":false},
     {"tag_name":"v0.3.0-beta.43","draft":false,"prerelease":true}]
    """);
var candidateRelease = UpdateClient.Parse(sampleListing, installedVersion, true);
Check("Release decoder picks newest eligible tag", candidateRelease?.Tag == "v0.3.0-beta.43");
Check("Release link is constructed on fixed repository",
    candidateRelease?.Page == UpdateClient.ReleasesPage + "/tag/v0.3.0-beta.43");
Check("Release decoder stable filter rejects beta Latest",
    UpdateClient.Parse(sampleListing, installedVersion, false) is null);
Check("Release decoder empty listing", UpdateClient.Parse(ReleaseJson("[]"), installedVersion, true) is null);
Check("Release decoder ignores unsupported tag",
    UpdateClient.Parse(ReleaseJson("""[{"tag_name":"../evil","draft":false,"prerelease":false}]"""),
        installedVersion, true) is null);
bool RejectReleaseJson(byte[] sample)
{
    try { UpdateClient.Parse(sample, installedVersion, true); return false; }
    catch (System.Text.Json.JsonException) { return true; }
    catch (InvalidDataException) { return true; }
}
Check("Release decoder rejects object not array", RejectReleaseJson(ReleaseJson("{}")));
Check("Release decoder rejects corrupt JSON", RejectReleaseJson(ReleaseJson("[")));
Check("Release decoder rejects absent flags",
    RejectReleaseJson(ReleaseJson("""[{"tag_name":"v0.3.0"}]""")));
Check("Release decoder rejects nonboolean flags",
    RejectReleaseJson(ReleaseJson("""[{"tag_name":"v0.3.0","draft":"false","prerelease":false}]""")));
Check("Release decoder rejects over-limit body", RejectReleaseJson(new byte[2 * 1024 * 1024 + 1]));
var ordinaryApexPlan = ApexProtocolMatrix.Build(65, false);
Check("Ordinary APEX retains original two lengths and 30ms", ordinaryApexPlan.SequenceEqual(new[] { (65, 30), (67, 30) }));
var fullApexPlan = ApexProtocolMatrix.Build(65, true);
Check("Full APEX six combinations for common descriptor", fullApexPlan.Count == 6 &&
    fullApexPlan.SequenceEqual(new[] { (65, 30), (67, 30), (65, 100), (67, 100), (65, 250), (67, 250) }));
Check("Distinct descriptor length first at each delay", ApexProtocolMatrix.Build(128, true).Count == 9 &&
    ApexProtocolMatrix.Build(128, true)[3] == (128, 100));
Check("Invalid descriptor sizes filtered", ApexProtocolMatrix.Build(257, true).SequenceEqual(fullApexPlan) &&
    ApexProtocolMatrix.Build(0, true).SequenceEqual(fullApexPlan));

var comparisonPlan = ApexProtocolMatrix.CompareGetIds(65);
Check("GET comparison uses 12 paired probes", comparisonPlan.Count == 12);
Check("GET comparison uses only the existing lengths and delays",
    comparisonPlan.Where(x => x.ReportId == 0x05)
        .Select(x => (x.Length, x.DelayMs)).SequenceEqual(fullApexPlan));
Check("GET comparison alternates 05 and 00 for each probe",
    comparisonPlan.Chunk(2).All(pair => pair.Length == 2 &&
        pair[0].ReportId == 0x05 && pair[1].ReportId == 0x00 &&
        pair[0].Length == pair[1].Length && pair[0].DelayMs == pair[1].DelayMs));
Check("GET comparison filters invalid descriptor lengths",
    ApexProtocolMatrix.CompareGetIds(257).SequenceEqual(comparisonPlan));

// Local verification uses synthetic files only; no network or executable launch.
string verifyDirectory = Path.Combine(Path.GetTempPath(), "ajazz-verify-" + Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(verifyDirectory);
try
{
    string portable = Path.Combine(verifyDirectory, LocalArtifactVerifier.PortableName);
    string checksum = Path.Combine(verifyDirectory, LocalArtifactVerifier.ManifestName(LocalArtifactVerifier.PortableName)!);
    string setup = Path.Combine(verifyDirectory, LocalArtifactVerifier.SetupName);
    string setupChecksum = Path.Combine(verifyDirectory, LocalArtifactVerifier.ManifestName(LocalArtifactVerifier.SetupName)!);
    File.WriteAllBytes(portable, updateFixture);
    File.WriteAllBytes(setup, updateFixture);
    File.WriteAllText(checksum, $"{updateHash}  {LocalArtifactVerifier.PortableName}\n");
    File.WriteAllText(setupChecksum, $"{updateHash}  {LocalArtifactVerifier.SetupName}\r\n");
    bool VerifyLocal(string artifact, string manifest) =>
        LocalArtifactVerifier.VerifyAsync(artifact, manifest).GetAwaiter().GetResult();
    bool RejectLocal(string artifact, string manifest)
    {
        try { VerifyLocal(artifact, manifest); return false; }
        catch (InvalidDataException) { return true; }
        catch (IOException) { return true; }
    }
    Check("Local portable checksum matches", VerifyLocal(portable, checksum));
    Check("Local setup checksum matches", VerifyLocal(setup, setupChecksum));
    Check("Local wrong manifest filename rejected", RejectLocal(portable, setupChecksum));
    Check("Local unsupported artifact filename rejected", RejectLocal(Path.Combine(verifyDirectory, "other.exe"), checksum));
    File.AppendAllText(portable, "changed");
    Check("Local modified artifact mismatch", !VerifyLocal(portable, checksum));
    File.WriteAllBytes(portable, updateFixture);
    File.WriteAllText(checksum, $"{updateHash}  {LocalArtifactVerifier.SetupName}");
    Check("Local wrong manifest entry mismatch", !VerifyLocal(portable, checksum));
    File.WriteAllBytes(checksum, new byte[LocalArtifactVerifier.MaximumManifestBytes + 1]);
    Check("Local oversized manifest rejected", RejectLocal(portable, checksum));
    File.WriteAllBytes(checksum, new byte[] { 255 });
    Check("Local non-ASCII manifest rejected", RejectLocal(portable, checksum));
    File.WriteAllBytes(checksum, Array.Empty<byte>());
    Check("Local empty manifest rejected", RejectLocal(portable, checksum));
    File.WriteAllText(checksum, $"{updateHash}  {LocalArtifactVerifier.PortableName}");
    File.WriteAllBytes(portable, Array.Empty<byte>());
    Check("Local empty executable rejected", RejectLocal(portable, checksum));
    File.Delete(portable);
    Check("Local missing executable rejected", RejectLocal(portable, checksum));
    File.WriteAllBytes(portable, updateFixture);
    using var verifyCancellation = new CancellationTokenSource();
    verifyCancellation.Cancel();
    bool cancelled = false;
    try { LocalArtifactVerifier.VerifyAsync(portable, checksum, verifyCancellation.Token).GetAwaiter().GetResult(); }
    catch (OperationCanceledException) { cancelled = true; }
    Check("Local verification observes cancellation", cancelled);
}
finally { Directory.Delete(verifyDirectory, true); }

// Opt-in automatic checks use elapsed ticks, not wall-clock time.
var updatePolicy = new AutomaticUpdatePolicy();
const long autoStart = 1000;
var betaUpdate = ReleaseVersion.Parse("v0.3.0-beta.45")!;
Check("Automatic update disabled by default", updatePolicy.TryBegin(autoStart) is null);
updatePolicy.Configure(true, true, autoStart);
Check("Automatic update startup delay", updatePolicy.TryBegin(autoStart + 59999) is null);
long autoDue = autoStart + AutomaticUpdatePolicy.InitialDelayMs;
var autoRequest = updatePolicy.TryBegin(autoDue);
Check("Automatic update begins after explicit opt-in", autoRequest?.Experimental == true);
Check("Automatic update serializes requests", updatePolicy.TryBegin(autoDue + 1) is null);
Check("Automatic update notifies new candidate", autoRequest is not null &&
    updatePolicy.Complete(autoRequest, true, betaUpdate, autoDue));
Check("Automatic update success interval", updatePolicy.TryBegin(autoDue + AutomaticUpdatePolicy.SuccessDelayMs - 1) is null);
autoDue += AutomaticUpdatePolicy.SuccessDelayMs;
var autoRepeat = updatePolicy.TryBegin(autoDue);
Check("Automatic update suppresses duplicate candidate", autoRepeat is not null &&
    !updatePolicy.Complete(autoRepeat, true, betaUpdate, autoDue));
autoDue += AutomaticUpdatePolicy.SuccessDelayMs;
var autoFailure = updatePolicy.TryBegin(autoDue);
Check("Automatic update failure suppresses notification", autoFailure is not null &&
    !updatePolicy.Complete(autoFailure, false, betaUpdate, autoDue));
Check("Automatic update failure backoff", updatePolicy.TryBegin(autoDue + AutomaticUpdatePolicy.FailureDelayMs - 1) is null);
autoDue += AutomaticUpdatePolicy.FailureDelayMs;
var autoStale = updatePolicy.TryBegin(autoDue);
updatePolicy.Configure(false, true, autoDue);
updatePolicy.Configure(true, false, autoDue);
Check("Automatic update opt-out/reconfigure keeps pending gate", updatePolicy.TryBegin(autoDue + 60000) is null);
Check("Automatic update discards prior channel reply", autoStale is not null &&
    !updatePolicy.Complete(autoStale, true, betaUpdate, autoDue));
autoDue += AutomaticUpdatePolicy.InitialDelayMs;
var autoStable = updatePolicy.TryBegin(autoDue);
Check("Automatic update switches channel", autoStable?.Experimental == false);
Check("Automatic stable policy rejects beta candidate", autoStable is not null &&
    !updatePolicy.Complete(autoStable, true, betaUpdate, autoDue));
autoDue += AutomaticUpdatePolicy.SuccessDelayMs;
var autoStable2 = updatePolicy.TryBegin(autoDue);
Check("Automatic stable policy accepts stable candidate", autoStable2 is not null &&
    updatePolicy.Complete(autoStable2, true, ReleaseVersion.Parse("1.0.0"), autoDue));
updatePolicy.Configure(false, false, autoDue);
Check("Automatic opt-out stops scheduling", updatePolicy.TryBegin(long.MaxValue - 1) is null);

// Consent must not become enabled by an upgrade from older preferences.
Check("Update preferences default to disabled stable",
    !new AppSettings().AutomaticUpdateChecks && !new AppSettings().ExperimentalUpdateChannel);
var legacyUpdateSettings = System.Text.Json.JsonSerializer.Deserialize<AppSettings>("""{"PollSeconds":30}""");
Check("Legacy settings do not silently authorize networking", legacyUpdateSettings is not null &&
    !legacyUpdateSettings.AutomaticUpdateChecks && !legacyUpdateSettings.ExperimentalUpdateChannel);
var updatePreferenceRoundtrip = System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
    System.Text.Json.JsonSerializer.Serialize(new AppSettings {
        AutomaticUpdateChecks = true, ExperimentalUpdateChannel = true }));
Check("Explicit update consent and channel roundtrip", updatePreferenceRoundtrip is not null &&
    updatePreferenceRoundtrip.AutomaticUpdateChecks && updatePreferenceRoundtrip.ExperimentalUpdateChannel);
var mutedUpdatePolicy = new AutomaticUpdatePolicy();
mutedUpdatePolicy.Configure(true, true, 0);
var mutedRequest = mutedUpdatePolicy.TryBegin(60000);
mutedUpdatePolicy.Configure(false, true, 60001);
mutedUpdatePolicy.Configure(true, true, 60002);
Check("Notification off/on invalidates old reply", mutedRequest is not null &&
    !mutedUpdatePolicy.Complete(mutedRequest, true, betaUpdate, 60003));
Check("Notification re-enable requires fresh delay",
    mutedUpdatePolicy.TryBegin(120001) is null && mutedUpdatePolicy.TryBegin(120002) is not null);

// Backup schema never serializes AppSettings or any device-specific identifier.
var backupSource = new AppSettings { Language = "uk", PollSeconds = 60,
    AlertBelow25 = false, AutomaticUpdateChecks = true, ExperimentalUpdateChannel = true,
    AutomaticDockClockSync = true, MonitorAulaL99 = true };
backupSource.DeviceAliases[new string('A', 64)] = "private-alias";
var portableBackup = PreferencesBackup.Capture(backupSource);
byte[] backupBytes = portableBackup.Export();
string backupJson = System.Text.Encoding.UTF8.GetString(backupBytes);
Check("Backup global preferences roundtrip", PreferencesBackup.Parse(backupBytes) == portableBackup);
Check("Backup excludes device identifiers and aliases", !backupJson.Contains("private-alias") &&
    !backupJson.Contains("DeviceAliases") && !backupJson.Contains(new string('A', 64)));
Check("Backup excludes network consent and hardware settings", !backupJson.Contains("AutomaticUpdate") &&
    !backupJson.Contains("ExperimentalUpdateChannel") && !backupJson.Contains("DockClock") &&
    !backupJson.Contains("MonitorAula"));
bool RejectBackup(string json)
{
    try { PreferencesBackup.Parse(System.Text.Encoding.UTF8.GetBytes(json)); return false; }
    catch (System.Text.Json.JsonException) { return true; }
    catch (InvalidDataException) { return true; }
}
Check("Backup rejects unsupported schema", RejectBackup(backupJson.Replace("\"SchemaVersion\": 1", "\"SchemaVersion\": 2")));
Check("Backup rejects invalid poll interval", RejectBackup(backupJson.Replace("\"PollSeconds\": 60", "\"PollSeconds\": 2")));
Check("Backup rejects invalid language", RejectBackup(backupJson.Replace("\"Language\": \"uk\"", "\"Language\": \"xx\"")));
Check("Backup rejects unexpected fields", RejectBackup(backupJson.Insert(1, "\"DeviceAliases\": {}, ")));
Check("Backup rejects duplicate fields", RejectBackup(backupJson.Insert(1, "\"SchemaVersion\": 1, ")));
Check("Backup rejects missing fields", RejectBackup("{}"));
Check("Backup rejects wrong field type", RejectBackup(backupJson.Replace("\"PollSeconds\": 60", "\"PollSeconds\": \"60\"")));
Check("Backup rejects oversized input", RejectBackup(new string(' ', PreferencesBackup.MaximumBytes + 1)));
Check("Backup rejects array or malformed JSON", RejectBackup("[]") && RejectBackup("{"));
string backupDir = Path.Combine(Path.GetTempPath(), "ajazz-preferences-" + Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(backupDir);
try
{
    string backupPath = Path.Combine(backupDir, "backup.json");
    portableBackup.WriteNewFile(backupPath);
    Check("Backup file export and local preview", PreferencesBackup.ReadFile(backupPath) == portableBackup);
    bool existed = false;
    try { portableBackup.WriteNewFile(backupPath); }
    catch (IOException) { existed = true; }
    Check("Backup does not overwrite existing file", existed &&
        PreferencesBackup.ReadFile(backupPath) == portableBackup);
}
finally { Directory.Delete(backupDir, true); }
Check("Backup preview leaves source settings unchanged", backupSource.AutomaticUpdateChecks &&
    backupSource.DeviceAliases.Count == 1 && backupSource.PollSeconds == 60);

// Restore changes only the visible schema and rolls back on failed persistence.
var restoreTarget = new AppSettings { Language = "en", PollSeconds = 120,
    AutomaticUpdateChecks = true, ExperimentalUpdateChannel = true,
    MonitorAulaL99 = true, AutomaticDockClockSync = false };
string restoreKey = new string('B', 64);
restoreTarget.DeviceAliases[restoreKey] = "keep-local";
restoreTarget.DevicePollIntervals[restoreKey] = 15;
restoreTarget.DeviceAlertMasks[restoreKey] = 0;
restoreTarget.HiddenTrayDevices.Add(restoreKey);
restoreTarget.DeviceTrayColors[restoreKey] = "blue";
var oldBackup = PreferencesBackup.Capture(restoreTarget);
int persistCalls = 0;
Check("Restore failed save rolls back all allowed values",
    !portableBackup.TryRestore(restoreTarget, () => { persistCalls++; return false; }) &&
    PreferencesBackup.Capture(restoreTarget) == oldBackup && persistCalls == 1);
Check("Restore thrown persistence error rolls back",
    !portableBackup.TryRestore(restoreTarget, () => throw new IOException("synthetic")) &&
    PreferencesBackup.Capture(restoreTarget) == oldBackup);
Check("Restore persistence sees proposed settings",
    portableBackup.TryRestore(restoreTarget, () => PreferencesBackup.Capture(restoreTarget) == portableBackup));
Check("Restore updates all allowed values", PreferencesBackup.Capture(restoreTarget) == portableBackup);
Check("Restore preserves device overrides and names", restoreTarget.DeviceAliases[restoreKey] == "keep-local" &&
    restoreTarget.DevicePollIntervals[restoreKey] == 15 && restoreTarget.DeviceAlertMasks[restoreKey] == 0 &&
    restoreTarget.HiddenTrayDevices.Contains(restoreKey) && restoreTarget.DeviceTrayColors[restoreKey] == "blue");
Check("Restore preserves hardware flags and explicit network consent",
    restoreTarget.AutomaticUpdateChecks && restoreTarget.ExperimentalUpdateChannel &&
    restoreTarget.MonitorAulaL99 && !restoreTarget.AutomaticDockClockSync);
bool invalidRestore = false;
try { (portableBackup with { PollSeconds = -1 }).TryRestore(restoreTarget, () => { persistCalls++; return true; }); }
catch (InvalidDataException) { invalidRestore = true; }
Check("Restore invalid object rejected before save or changes", invalidRestore && persistCalls == 1 &&
    PreferencesBackup.Capture(restoreTarget) == portableBackup);

// API projection contains no device identifiers and never promotes old readings.
var snapshotNow = new DateTimeOffset(2026, 11, 23, 0, 0, 0, TimeSpan.Zero);
LocalBatterySnapshot.Input SnapshotInput(DeviceDashboardStatus status, int? percent,
    DateTimeOffset? measured, int slot = 1) => new(LocalBatterySource.ApexReceiver, slot,
        new DeviceDashboardState("private-name", "private-transport", status, percent, measured));
LocalBatterySnapshot.Entry SnapshotRow(DeviceDashboardStatus status, int? percent, DateTimeOffset? measured) =>
    LocalBatterySnapshot.Create(snapshotNow, new[] { SnapshotInput(status, percent, measured) }).Devices[0];
var apiFresh = SnapshotRow(DeviceDashboardStatus.Fresh, 83, snapshotNow.AddMinutes(-1));
Check("API fresh measurement is numeric", apiFresh.BatteryPercent == 83 && apiFresh.LastKnownPercent is null);
var apiOld = SnapshotRow(DeviceDashboardStatus.Fresh, 83, snapshotNow.AddMinutes(-6));
Check("API old fresh measurement demoted to stale", apiOld.Status == "stale" && apiOld.BatteryPercent is null && apiOld.LastKnownPercent == 83);
var apiCache = SnapshotRow(DeviceDashboardStatus.Cached, 70, snapshotNow.AddHours(-2));
Check("API cached data never current", apiCache.Status == "cached" && apiCache.BatteryPercent is null && apiCache.LastKnownPercent == 70);
Check("API scheduled data never current", SnapshotRow(DeviceDashboardStatus.Scheduled, 70, snapshotNow).BatteryPercent is null);
Check("API expired data unavailable", SnapshotRow(DeviceDashboardStatus.Cached, 70, snapshotNow.AddHours(-25)).LastKnownPercent is null);
Check("API future measurement unavailable", SnapshotRow(DeviceDashboardStatus.Fresh, 50, snapshotNow.AddSeconds(1)).BatteryPercent is null);
Check("API missing timestamp unavailable", SnapshotRow(DeviceDashboardStatus.Fresh, 50, null).BatteryPercent is null);
Check("API invalid percentage unavailable", SnapshotRow(DeviceDashboardStatus.Fresh, 101, snapshotNow).Status == "unavailable");
Check("API manual reading not promoted", SnapshotRow(DeviceDashboardStatus.ManualReading, 50, snapshotNow).BatteryPercent is null);
Check("API unknown presence hides all numeric data", SnapshotRow(DeviceDashboardStatus.PresenceUnknown, 50, snapshotNow).LastKnownPercent is null);
Check("API zero is valid fresh battery", SnapshotRow(DeviceDashboardStatus.Fresh, 0, snapshotNow).BatteryPercent == 0);
var apiSnapshot = LocalBatterySnapshot.Create(snapshotNow, new[] {
    SnapshotInput(DeviceDashboardStatus.Fresh, 1, snapshotNow, 2),
    SnapshotInput(DeviceDashboardStatus.Fresh, 2, snapshotNow, 1) });
string apiJson = System.Text.Encoding.UTF8.GetString(apiSnapshot.Export());
Check("API snapshot canonical order and schema", apiSnapshot.SchemaVersion == 1 && apiSnapshot.Devices[0].SessionSlot == 1);
Check("API projection excludes all original labels", !apiJson.Contains("private-name") && !apiJson.Contains("private-transport"));
bool RejectSnapshot(IEnumerable<LocalBatterySnapshot.Input> rows)
{
    try { LocalBatterySnapshot.Create(snapshotNow, rows); return false; }
    catch (InvalidDataException) { return true; }
}
Check("API duplicate session slot rejected", RejectSnapshot(new[] {
    SnapshotInput(DeviceDashboardStatus.Disabled, null, null), SnapshotInput(DeviceDashboardStatus.Disabled, null, null) }));
Check("API oversized set rejected", RejectSnapshot(Enumerable.Range(1, 65)
    .Select(i => SnapshotInput(DeviceDashboardStatus.Disabled, null, null, i))));
Check("API invalid session slot rejected", RejectSnapshot(new[] { SnapshotInput(DeviceDashboardStatus.Disabled, null, null, 0) }));

var snapshotStore = new LocalSnapshotStore();
Check("Snapshot store initially unavailable", snapshotStore.Read(snapshotNow) is null);
snapshotStore.Publish(snapshotNow, new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 83, snapshotNow) });
Check("Snapshot store publishes current reading", snapshotStore.Read(snapshotNow)?.Devices[0].BatteryPercent == 83);
var agedSnapshot = snapshotStore.Read(snapshotNow.AddMinutes(6));
Check("Snapshot read automatically ages fresh value", agedSnapshot?.Devices[0].LastKnownPercent == 83 &&
    agedSnapshot.Devices[0].BatteryPercent is null && agedSnapshot.Devices[0].Status == "stale");
Check("Snapshot read does not rewrite generation or measurement time",
    agedSnapshot?.GeneratedAt == snapshotNow && agedSnapshot.Devices[0].MeasuredAt == snapshotNow);
Check("Snapshot read expires old values", snapshotStore.Read(snapshotNow.AddHours(25))?.Devices[0].LastKnownPercent is null);
Check("Snapshot clock rollback unavailable", snapshotStore.Read(snapshotNow.AddSeconds(-1)) is null);
bool invalidSnapshotPublish = false;
try { snapshotStore.Publish(snapshotNow, new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 1, snapshotNow, 0) }); }
catch (InvalidDataException) { invalidSnapshotPublish = true; }
Check("Snapshot projection failure invalidates previous value", invalidSnapshotPublish && snapshotStore.Read(snapshotNow) is null);
snapshotStore.Publish(snapshotNow, new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 44, snapshotNow) });
var retainedSnapshot = snapshotStore.Read(snapshotNow);
snapshotStore.Publish(snapshotNow.AddSeconds(1), new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 45, snapshotNow.AddSeconds(1)) });
Check("Snapshot previously returned value remains immutable", retainedSnapshot?.Devices[0].BatteryPercent == 44 &&
    snapshotStore.Read(snapshotNow.AddSeconds(1))?.Devices[0].BatteryPercent == 45);
snapshotStore.Clear();
Check("Snapshot clear hides prior data", snapshotStore.Read(snapshotNow) is null);

// Strict HTTP parser and real loopback tests, no external traffic.
string localToken = LocalApiRequest.NewToken();
Check("API token contains 256 random bits in hex", localToken.Length == 64 &&
    localToken.All(char.IsAsciiHexDigit) && LocalApiRequest.NewToken() != localToken);
string ApiHeader(string method = "GET", string route = "/v1/batteries",
    string host = "127.0.0.1:18789", string? auth = null, string extra = "") =>
    $"{method} {route} HTTP/1.1\r\nHost: {host}\r\n" +
    (auth is null ? "" : $"Authorization: Bearer {auth}\r\n") + extra + "\r\n";
int CheckHeader(string header) => LocalApiRequest.Check(header, 18789, localToken);
Check("API GET authenticates", CheckHeader(ApiHeader(auth: localToken)) == 200);
Check("API missing credential rejected", CheckHeader(ApiHeader()) == 401);
Check("API wrong credential rejected", CheckHeader(ApiHeader(auth: new string('0', 64))) == 401);
Check("API rejects non-loopback host", CheckHeader(ApiHeader(host: "example.invalid", auth: localToken)) == 400);
Check("API rejects browser origin", CheckHeader(ApiHeader(auth: localToken, extra: "Origin: https://example.invalid\r\n")) == 403);
Check("API rejects write method", CheckHeader(ApiHeader(method: "POST", auth: localToken)) == 405);
Check("API rejects other route or query", CheckHeader(ApiHeader(route: "/v1/batteries?token=x", auth: localToken)) == 404);
Check("API rejects duplicate headers", CheckHeader(ApiHeader(auth: localToken, extra: "Host: 127.0.0.1:18789\r\n")) == 400);
Check("API rejects framing for a body", CheckHeader(ApiHeader(auth: localToken, extra: "Content-Length: 1\r\n")) == 400 &&
    CheckHeader(ApiHeader(auth: localToken, extra: "Transfer-Encoding: chunked\r\n")) == 400);
Check("API rejects malformed or oversized header", CheckHeader("GET") == 400 &&
    CheckHeader(ApiHeader(auth: localToken, extra: "X-Test: " + new string('x', 8192) + "\r\n")) == 400);
Check("API rejects stray header line break", CheckHeader(ApiHeader(auth: localToken, extra: "X-Test: a\nb\r\n")) == 400);

async Task TestLoopbackApi()
{
    var liveStore = new LocalSnapshotStore();
    await using var localServer = new LocalApiServer(liveStore, 0);
    using var client = new System.Net.Http.HttpClient(new System.Net.Http.HttpClientHandler { UseProxy = false, AllowAutoRedirect = false });
    client.Timeout = TimeSpan.FromSeconds(8);
    using var unauthorized = await client.GetAsync(localServer.Endpoint);
    Check("HTTP loopback rejects unauthenticated request", (int)unauthorized.StatusCode == 401);
    client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", localServer.Token);
    using var empty = await client.GetAsync(localServer.Endpoint);
    Check("HTTP loopback reports unavailable snapshot", (int)empty.StatusCode == 503);
    var measured = DateTimeOffset.UtcNow.AddSeconds(-1);
    liveStore.Publish(measured, new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 76, measured) });
    using var valid = await client.GetAsync(localServer.Endpoint);
    string body = await valid.Content.ReadAsStringAsync();
    Check("HTTP loopback returns sanitized snapshot", (int)valid.StatusCode == 200 &&
        body.Contains("\"batteryPercent\":76") && !body.Contains("private-name"));
    using var unknown = await client.GetAsync(localServer.Endpoint + "/unknown");
    Check("HTTP loopback rejects unknown route", (int)unknown.StatusCode == 404);
    using var postRequest = new System.Net.Http.HttpRequestMessage(System.Net.Http.HttpMethod.Post, localServer.Endpoint);
    using var rejected = await client.SendAsync(postRequest);
    Check("HTTP loopback rejects POST", (int)rejected.StatusCode == 405);
    bool portBusy = false;
    try { await using var duplicate = new LocalApiServer(liveStore, localServer.Port); }
    catch (System.Net.Sockets.SocketException) { portBusy = true; }
    Check("HTTP loopback rejects occupied port", portBusy);
    using var stalled = new System.Net.Sockets.TcpClient();
    await stalled.ConnectAsync(System.Net.IPAddress.Loopback, localServer.Port);
    await localServer.DisposeAsync();
    bool stopped = false;
    using var probe = new System.Net.Sockets.TcpClient();
    try { await probe.ConnectAsync(System.Net.IPAddress.Loopback, localServer.Port); }
    catch (System.Net.Sockets.SocketException) { stopped = true; }
    Check("HTTP loopback releases listener on stop", stopped);
}
TestLoopbackApi().GetAwaiter().GetResult();

// Equivalent pixel states reuse the existing GDI icon.
var iconBase = TrayIconRenderKey.Create(83, true, false);
Check("Icon same display state is reusable", iconBase == TrayIconRenderKey.Create(83, true, false));
Check("Icon changed battery must redraw", iconBase != TrayIconRenderKey.Create(82, true, false));
Check("Icon cached marker must redraw", iconBase != TrayIconRenderKey.Create(83, true, true));
Check("Icon unavailable must redraw", iconBase != TrayIconRenderKey.Create(null, false, false));
Check("Icon custom color must redraw", iconBase != TrayIconRenderKey.Create(83, true, false, color: "blue"));
Check("Icon default and normalized color equivalent", iconBase == TrayIconRenderKey.Create(83, true, false, color: "green"));
Check("Icon low battery overrides custom color", TrayIconRenderKey.Create(8, true, false, color: "blue") ==
    TrayIconRenderKey.Create(8, true, false, color: "purple"));
Check("Icon cached palette ignores custom color", TrayIconRenderKey.Create(83, true, true, color: "blue") ==
    TrayIconRenderKey.Create(83, true, true, color: "pink"));
Check("Icon unknown ignores stale flag and palette", TrayIconRenderKey.Create(null, false, false) ==
    TrayIconRenderKey.Create(null, false, true, color: "blue"));
Check("Icon neutral state ignores all other inputs", TrayIconRenderKey.Create(null, false, false, true) ==
    TrayIconRenderKey.Create(83, true, true, true, "pink"));
Check("Icon neutral differs from unknown", TrayIconRenderKey.Create(null, false, false, true) !=
    TrayIconRenderKey.Create(null, false, false));

// History startup must not open files until an actual recording or graph request.
var historyNow = DateTimeOffset.UtcNow;
var historyEarlier = new BatterySample(historyNow.AddMinutes(-2), 70, "online");
var historyTie = historyEarlier with { Percent = 71 };
var historyRows = new[] { historyEarlier, historyTie,
    new BatterySample(historyNow.AddDays(-31), 50, "online"),
    new BatterySample(historyNow.AddMinutes(5), 99, "online") };
Check("History latest matches full retention including tied timestamps",
    BatteryHistoryRules.Latest(historyRows, historyNow) ==
    BatteryHistoryRules.Retain(historyRows, historyNow).LastOrDefault());
Check("History latest skips future and expired rows", BatteryHistoryRules.Latest(historyRows.Skip(2), historyNow) is null);
Check("History unchanged primitive sample suppressed",
    !BatteryHistoryRules.ShouldRecord(historyEarlier, historyNow, 70, "online"));
Check("History five-minute boundary still records",
    BatteryHistoryRules.ShouldRecord(historyEarlier, historyEarlier.Timestamp.AddMinutes(5), 70, "online"));
string lazyHistoryDir = Path.Combine(Path.GetTempPath(), "ajazz-lazy-history-" + Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(lazyHistoryDir);
try
{
    string lazyHistoryPath = Path.Combine(lazyHistoryDir, "history.csv");
    var lazyHistory = new BatteryHistory("history.csv", lazyHistoryDir);
    Check("History construction does not create file", !File.Exists(lazyHistoryPath));
    File.WriteAllLines(lazyHistoryPath, new[] { BatteryHistoryCsv.Header, BatteryHistoryCsv.Format(historyEarlier) });
    lazyHistory.Record(historyNow, 70, true);
    Check("History first record loads existing last sample lazily", File.ReadAllLines(lazyHistoryPath).Length == 2);
    lazyHistory.Record(historyNow, 69, true);
    Check("History new sample written and retained", lazyHistory.ReadRecent().LastOrDefault()?.Percent == 69);
    lazyHistory.Record(historyNow.AddSeconds(1), 69, true);
    Check("History repeated sample does not append", File.ReadAllLines(lazyHistoryPath).Length == 3);
    // Unknown enumeration is a history gap, including when the same level returns.
    lazyHistory.Record(historyNow.AddSeconds(2), null, receiverPresent: true);
    lazyHistory.Record(historyNow.AddSeconds(3), 69, receiverPresent: true);
    var gapRows = File.ReadAllLines(lazyHistoryPath).Skip(1)
        .Select(BatteryHistoryCsv.Parse).OfType<BatterySample>().ToArray();
    Check("Unknown history gap contains no charge or disconnected state",
        gapRows.Length == 4 && gapRows[2].Percent is null &&
        gapRows[2].State == "unavailable" && gapRows[3].Percent == 69 &&
        gapRows[3].State == "online");
}
finally { Directory.Delete(lazyHistoryDir, true); }

// Hot-path selection must preserve the former ordinal order and preferred receiver.
Check("Primary streaming selection handles duplicates and unsorted keys",
    ReceiverIdentity.SelectPrimary(null, new[] { "c", "a", "b", "a" }) == "a");
Check("Primary streaming selection retains preferred receiver",
    ReceiverIdentity.SelectPrimary("c", new[] { "a", "c", "b" }) == "c");
Check("Primary streaming selection falls back when preferred absent",
    ReceiverIdentity.SelectPrimary("z", new[] { "b", "a" }) == "a");
Check("Primary streaming selection handles empty inventory",
    ReceiverIdentity.SelectPrimary("a", Array.Empty<string>()) is null);
Check("Primary streaming selection remains ordinal",
    ReceiverIdentity.SelectPrimary(null, new[] { "a", "B" }) == "B");
Check("Discovery interval empty overrides uses global",
    DevicePollSchedule.DiscoverySeconds(60, new Dictionary<string, int>()) == 60);
Check("Discovery interval excludes AULA override",
    DevicePollSchedule.DiscoverySeconds(60, new Dictionary<string, int> { [DeviceAliasRules.AulaSlot] = 15 }) == 60);
Check("Discovery interval picks shortest USB override",
    DevicePollSchedule.DiscoverySeconds(60, new Dictionary<string, int> { ["one"] = 120, ["two"] = 15 }) == 15);
Check("Discovery interval normalizes invalid override",
    DevicePollSchedule.DiscoverySeconds(60, new Dictionary<string, int> { ["one"] = 17 }) == 30);
Check("Discovery interval retains shorter global",
    DevicePollSchedule.DiscoverySeconds(15, new Dictionary<string, int> { ["one"] = 120 }) == 15);

// Compare the allocation-free threshold policy to its former set-based behavior.
int? ReferenceAlert(HashSet<int> notified, int percent, int mask)
{
    if (percent is < 0 or > 100) return null;
    int[] levels = { 50, 25, 10 };
    foreach (int level in levels)
        if (percent >= level + 5) notified.Remove(level);
    int? reached = null;
    foreach (int level in levels.Reverse())
    {
        int bit = level == 50 ? 1 : level == 25 ? 2 : 4;
        if ((mask & bit) != 0 && percent < level && !notified.Contains(level))
        {
            reached = level;
            break;
        }
    }
    if (reached.HasValue)
        foreach (int level in levels)
            if (percent < level) notified.Add(level);
    return reached;
}
bool equivalentAlerts = true;
var alertRandom = new Random(48049);
for (int scenario = 0; scenario < 32; scenario++)
{
    var optimized = new AlertPolicy();
    var reference = new HashSet<int>();
    for (int sample = 0; sample < 256; sample++)
    {
        int percent = alertRandom.Next(-1, 102);
        int mask = alertRandom.Next(8);
        int? expected = ReferenceAlert(reference, percent, mask);
        int? actual = optimized.Evaluate(percent, (mask & 1) != 0,
            (mask & 2) != 0, (mask & 4) != 0);
        if (expected != actual) equivalentAlerts = false;
    }
}
Check("Alert bitmask matches old policy across 8192 deterministic samples", equivalentAlerts);
var longAbsent = new ConnectionAlertPolicy();
longAbsent.Evaluate(true, true);
bool longAbsentOnce = !longAbsent.Evaluate(false, false) && longAbsent.Evaluate(false, false);
for (int i = 0; i < 10000; i++)
    longAbsentOnce &= !longAbsent.Evaluate(false, false);
longAbsent.Evaluate(true, true);
Check("Long disconnection saturates and re-arms after reconnect",
    longAbsentOnce && !longAbsent.Evaluate(false, false) && longAbsent.Evaluate(false, false));

// One-shot timer must follow the same monotonic update policy deadlines.
var deadlinePolicy = new AutomaticUpdatePolicy();
Check("Update deadline disabled has no timer", deadlinePolicy.NextDelayMilliseconds(1000) is null);
deadlinePolicy.Configure(true, false, 1000);
Check("Update deadline initial timer sixty seconds", deadlinePolicy.NextDelayMilliseconds(1000) == 60000);
Check("Update deadline remaining time", deadlinePolicy.NextDelayMilliseconds(61000 - 123) == 123);
Check("Update deadline due and overdue clamp to one", deadlinePolicy.NextDelayMilliseconds(61000) == 1 &&
    deadlinePolicy.NextDelayMilliseconds(62000) == 1);
var deadlineRequest = deadlinePolicy.TryBegin(61000)!;
Check("Update deadline pending has no timer", deadlinePolicy.NextDelayMilliseconds(61000) is null);
deadlinePolicy.Complete(deadlineRequest, true, null, 62000);
Check("Update deadline success schedules one day", deadlinePolicy.NextDelayMilliseconds(62000) == 86400000);
var deadlineRetry = deadlinePolicy.TryBegin(62000 + 86400000)!;
deadlinePolicy.Complete(deadlineRetry, false, null, 63000 + 86400000);
Check("Update deadline failure schedules one hour",
    deadlinePolicy.NextDelayMilliseconds(63000 + 86400000) == 3600000);
deadlinePolicy.Configure(false, false, 64000 + 86400000);
Check("Update deadline opt-out cancels timer", deadlinePolicy.NextDelayMilliseconds(64000 + 86400000) is null);
deadlinePolicy.Configure(true, false, 100);
var oldDeadlineRequest = deadlinePolicy.TryBegin(60100)!;
deadlinePolicy.Configure(true, true, 60200);
Check("Update deadline channel change waits for stale request", deadlinePolicy.NextDelayMilliseconds(60200) is null);
deadlinePolicy.Complete(oldDeadlineRequest, true, null, 60300);
Check("Update deadline stale reply preserves new deadline", deadlinePolicy.NextDelayMilliseconds(60300) == 59900);
Check("Update deadline very large remaining time clamps", deadlinePolicy.NextDelayMilliseconds(long.MinValue) == int.MaxValue);

// The shared gate prevents overlapping network work and releases on failure.
var extremeDeadline = new AutomaticUpdatePolicy();
extremeDeadline.Configure(true, false, long.MaxValue - 10);
Check("Update deadline does not overflow near monotonic maximum",
    extremeDeadline.NextDelayMilliseconds(long.MaxValue - 10) == 10);
var gate = new UpdateRequestGate();
var gateRelease = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
var gateFirst = gate.RunAsync(_ => gateRelease.Task, CancellationToken.None);
bool gateSecondStarted = false;
using var gateCancel = new CancellationTokenSource();
var gateSecond = gate.RunAsync(_ =>
{
    gateSecondStarted = true;
    return Task.FromResult(2);
}, gateCancel.Token);
Check("Update gate serializes simultaneous callers", !gateSecondStarted && !gateSecond.IsCompleted);
gateCancel.Cancel();
bool gateCanceled = false;
try { gateSecond.GetAwaiter().GetResult(); }
catch (OperationCanceledException) { gateCanceled = true; }
Check("Update gate cancels queued lookup without network work", gateCanceled && !gateSecondStarted);
gateRelease.SetResult(1);
Check("Update gate completes original request", gateFirst.GetAwaiter().GetResult() == 1);
bool gateFailed = false;
try
{
    gate.RunAsync<int>(_ => throw new IOException("synthetic"), CancellationToken.None).GetAwaiter().GetResult();
}
catch (IOException) { gateFailed = true; }
Check("Update gate releases after operation failure", gateFailed &&
    gate.RunAsync(_ => Task.FromResult(3), CancellationToken.None).GetAwaiter().GetResult() == 3);

// Optional AULA timer and single-flight transitions without Windows or HID.
var aulaLifecycle = new AulaPollLifecycle();
Check("AULA lifecycle defaults to disabled with no timer",
    !aulaLifecycle.Enabled && !aulaLifecycle.CanArm && aulaLifecycle.TryBegin(false) is null);
long manualAulaTicket = aulaLifecycle.TryBegin(true)!.Value;
Check("AULA lifecycle permits explicit read while disabled",
    aulaLifecycle.IsBusy && aulaLifecycle.MayApply(manualAulaTicket) && !aulaLifecycle.CanArm);
Check("AULA lifecycle rejects duplicate manual read", aulaLifecycle.TryBegin(true) is null);
Check("AULA lifecycle manual completion does not start automatic timer",
    aulaLifecycle.Complete(manualAulaTicket, 30000) is null && !aulaLifecycle.IsBusy);
aulaLifecycle.Configure(true);
Check("AULA lifecycle enabled can arm timer", aulaLifecycle.CanArm);
long autoAulaTicket = aulaLifecycle.TryBegin(false)!.Value;
Check("AULA lifecycle busy automatic poll suppresses timer and duplicates",
    !aulaLifecycle.CanArm && aulaLifecycle.TryBegin(false) is null);
Check("AULA lifecycle completion uses configured interval",
    aulaLifecycle.Complete(autoAulaTicket, 60000) == 60000);
long oldAulaTicket = aulaLifecycle.TryBegin(false)!.Value;
aulaLifecycle.Configure(false);
Check("AULA lifecycle disable invalidates pending reply",
    !aulaLifecycle.MayApply(oldAulaTicket) && !aulaLifecycle.CanArm);
Check("AULA lifecycle disabled completion does not re-arm",
    aulaLifecycle.Complete(oldAulaTicket, 30000) is null);
aulaLifecycle.Configure(true);
long replacedAulaTicket = aulaLifecycle.TryBegin(false)!.Value;
aulaLifecycle.Configure(false);
aulaLifecycle.Configure(true);
Check("AULA lifecycle re-enable cannot overlap pending request",
    aulaLifecycle.TryBegin(true) is null && !aulaLifecycle.MayApply(replacedAulaTicket));
Check("AULA lifecycle re-enable schedules prompt replacement",
    aulaLifecycle.Complete(replacedAulaTicket, 120000) == 100);
long currentAulaTicket = aulaLifecycle.TryBegin(false)!.Value;
Check("AULA lifecycle duplicate completion cannot release newer worker",
    aulaLifecycle.Complete(replacedAulaTicket, 30000) is null &&
    aulaLifecycle.IsBusy && aulaLifecycle.MayApply(currentAulaTicket));
aulaLifecycle.Close();
Check("AULA lifecycle shutdown invalidates result and timer",
    !aulaLifecycle.MayApply(currentAulaTicket) &&
    aulaLifecycle.Complete(currentAulaTicket, 30000) is null &&
    aulaLifecycle.TryBegin(true) is null && !aulaLifecycle.CanArm);
aulaLifecycle.Configure(true);
Check("AULA lifecycle closed state cannot be re-enabled", !aulaLifecycle.Enabled);

// AULA dashboard and optional API must classify real sleep/recovery consistently.
var aulaSleep = new AulaBatteryState();
DateTimeOffset sleepStart = DateTimeOffset.Parse("2026-11-22T12:00:00Z");
DeviceDashboardState AulaSleepView(bool automatic, bool checkedOnce, bool known,
    bool present, int? fresh, DateTimeOffset? measured, DateTimeOffset now)
    => aulaSleep.Dashboard("L99", automatic, checkedOnce, known, present, fresh, measured, now);
Check("AULA disabled before first manual check",
    AulaSleepView(false, false, false, false, null, null, sleepStart).Status == DeviceDashboardStatus.Disabled);
Check("AULA automatic before first poll not checked",
    AulaSleepView(true, false, false, false, null, null, sleepStart).Status == DeviceDashboardStatus.NotChecked);
aulaSleep.Observe(true, true, 87, sleepStart);
Check("AULA completed automatic poll is fresh, not scheduled",
    AulaSleepView(true, true, true, true, 87, sleepStart, sleepStart) is
    { Status: DeviceDashboardStatus.Fresh, Percent: 87 });
Check("AULA explicit read while disabled is manual only",
    AulaSleepView(false, true, true, true, 87, sleepStart, sleepStart).Status == DeviceDashboardStatus.ManualReading);
for (int n = 1; n <= 960; n++)
    aulaSleep.Observe(true, true, null, sleepStart.AddSeconds(n * 30));
var sleepView = AulaSleepView(true, true, true, true, null, sleepStart.AddHours(8), sleepStart.AddHours(8));
Check("AULA eight-hour simulated sleep preserves cached timestamp",
    sleepView is { Status: DeviceDashboardStatus.Cached, Percent: 87 } &&
    sleepView.MeasuredAt == sleepStart && aulaSleep.ConsecutiveFailures == 960);
var sleepSnapshot = LocalBatterySnapshot.Create(sleepStart.AddHours(8),
    new[] { new LocalBatterySnapshot.Input(LocalBatterySource.AulaReceiver, 1, sleepView) });
Check("AULA sleep snapshot separates cached value from fresh telemetry",
    sleepSnapshot.Devices[0] is { Status: "cached", BatteryPercent: null, LastKnownPercent: 87 });
Check("AULA expired sleep cache has no reply status",
    AulaSleepView(true, true, true, true, null, sleepStart.AddHours(24), sleepStart.AddHours(24)) is
    { Status: DeviceDashboardStatus.NoReply, Percent: null });
Check("AULA unknown presence hides cache in unified view",
    AulaSleepView(true, true, false, true, null, sleepStart, sleepStart.AddHours(8)) is
    { Status: DeviceDashboardStatus.PresenceUnknown, Percent: null });
var wakeAt = sleepStart.AddHours(25);
aulaSleep.Observe(true, true, 83, wakeAt);
var wakeView = AulaSleepView(true, true, true, true, 83, wakeAt, wakeAt);
Check("AULA recovered reply becomes fresh with new timestamp",
    wakeView is { Status: DeviceDashboardStatus.Fresh, Percent: 83 } &&
    wakeView.MeasuredAt == wakeAt && aulaSleep.ConsecutiveFailures == 0);
var wakeSnapshot = LocalBatterySnapshot.Create(wakeAt,
    new[] { new LocalBatterySnapshot.Input(LocalBatterySource.AulaReceiver, 1, wakeView) });
Check("AULA recovered snapshot publishes only fresh percentage",
    wakeSnapshot.Devices[0] is { Status: "fresh", BatteryPercent: 83, LastKnownPercent: null });
aulaSleep.Reset();
Check("AULA invalid zero response never becomes fresh",
    AulaSleepView(true, true, true, true, 0, wakeAt, wakeAt) is
    { Status: DeviceDashboardStatus.NoReply, Percent: null });
Check("AULA future measurement never becomes fresh",
    AulaSleepView(true, true, true, true, 83, wakeAt.AddSeconds(1), wakeAt) is
    { Status: DeviceDashboardStatus.NoReply, Percent: null });

// HA consumers must explicitly bind to a API activation and a source/slot.
var haStore = new LocalSnapshotStore();
haStore.Publish(snapshotNow, new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 83, snapshotNow) });
var haSnapshot = haStore.Read(snapshotNow)!;
var haMapping = HaSessionMapping.Bind(haSnapshot, "apex_receiver", 1);
Check("HA session-bound fresh reading available", haMapping.Read(haSnapshot, snapshotNow).BatteryPercent == 83);
Check("HA rejects missing snapshot", !haMapping.Read(null, snapshotNow).Available);
Check("HA rejects stale reading", !haMapping.Read(haSnapshot, snapshotNow.AddMinutes(6)).Available);
Check("HA rejects clock rollback", !haMapping.Read(haSnapshot, snapshotNow.AddSeconds(-1)).Available);
haStore.Publish(snapshotNow.AddSeconds(1), new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 82, snapshotNow.AddSeconds(1)) });
var haNext = haStore.Read(snapshotNow.AddSeconds(1))!;
Check("HA session epoch stays unchanged across publication", haNext.SessionEpoch == haSnapshot.SessionEpoch);
Check("HA existing mapping reads next sample", haMapping.Read(haNext, snapshotNow.AddSeconds(1)).BatteryPercent == 82);
var haOther = new LocalSnapshotStore();
haOther.Publish(snapshotNow, new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 50, snapshotNow) });
Check("HA new API activation cannot inherit prior slot mapping", haMapping.Read(haOther.Read(snapshotNow), snapshotNow).Status == "mapping_required");
Check("HA rejects missing mapped slot", !haMapping.Read(haSnapshot with { Devices = Array.Empty<LocalBatterySnapshot.Entry>() }, snapshotNow).Available);
Check("HA rejects ambiguous mapped slot", !haMapping.Read(haSnapshot with { Devices = new[] { haSnapshot.Devices[0], haSnapshot.Devices[0] } }, snapshotNow).Available);
haStore.Publish(snapshotNow, new[] { SnapshotInput(DeviceDashboardStatus.Cached, 80, snapshotNow) });
Check("HA does not report cached battery as current", !haMapping.Read(haStore.Read(snapshotNow), snapshotNow).Available);
bool rejectedHaBind = false;
try { HaSessionMapping.Bind(haSnapshot with { SessionEpoch = null }, "apex_receiver", 1); }
catch (InvalidDataException) { rejectedHaBind = true; }
Check("HA legacy snapshot requires session mapping support", rejectedHaBind);
Check("HA session epoch serialized without hardware ID",
    System.Text.Encoding.UTF8.GetString(haSnapshot.Export()).Contains("sessionEpoch"));

Check("One-off snapshot omits session epoch",
    !System.Text.Encoding.UTF8.GetString(LocalBatterySnapshot.Create(snapshotNow,
        new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 83, snapshotNow) }).Export()).Contains("sessionEpoch"));
haStore.Clear();
Check("HA stopped API has no snapshot", haStore.Read(snapshotNow) is null);
Check("HA rejects unsupported schema",
    !haMapping.Read(haSnapshot with { SchemaVersion = 2 }, snapshotNow).Available);
Check("HA rejects future measurement",
    !haMapping.Read(haSnapshot with { Devices = new[] { haSnapshot.Devices[0] with
        { MeasuredAt = snapshotNow.AddSeconds(1) } } }, snapshotNow).Available);
Check("HA rejects invalid battery percentage",
    !haMapping.Read(haSnapshot with { Devices = new[] { haSnapshot.Devices[0] with
        { BatteryPercent = 101 } } }, snapshotNow).Available);

// Strict optional consumer checks against the actual producer serialization.
var decodedHa = HaSnapshotDecoder.Decode(haSnapshot.Export());
Check("HA wire round trip retains binding and fresh reading",
    haMapping.Read(decodedHa, snapshotNow).BatteryPercent == 83);
string haWire = System.Text.Encoding.UTF8.GetString(haSnapshot.Export());
bool RejectHaWire(string value)
{
    try { HaSnapshotDecoder.Decode(System.Text.Encoding.UTF8.GetBytes(value)); return false; }
    catch (InvalidDataException) { return true; }
}
Check("HA wire rejects duplicate schema property",
    RejectHaWire(haWire.Replace("\"schemaVersion\":1", "\"schemaVersion\":1,\"schemaVersion\":1")));
Check("HA wire rejects unsupported schema",
    RejectHaWire(haWire.Replace("\"schemaVersion\":1", "\"schemaVersion\":2")));
Check("HA wire rejects missing epoch",
    RejectHaWire(System.Text.Encoding.UTF8.GetString((haSnapshot with { SessionEpoch = null }).Export())));
Check("HA wire rejects duplicate rows",
    RejectHaWire(System.Text.Encoding.UTF8.GetString((haSnapshot with
        { Devices = new[] { haSnapshot.Devices[0], haSnapshot.Devices[0] } }).Export())));
Check("HA wire rejects wrong percent type",
    RejectHaWire(haWire.Replace("\"batteryPercent\":83", "\"batteryPercent\":\"83\"")));
Check("HA wire rejects contradictory fresh and cached values",
    RejectHaWire(haWire.Replace("\"lastKnownPercent\":null", "\"lastKnownPercent\":82")));
Check("HA wire rejects oversized input", RejectHaWire(new string(' ', 65537)));
Check("HA wire rejects malformed JSON", RejectHaWire("{"));
Check("HA wire rejects future measurement",
    RejectHaWire(System.Text.Encoding.UTF8.GetString((haSnapshot with
        { Devices = new[] { haSnapshot.Devices[0] with
            { MeasuredAt = snapshotNow.AddSeconds(1) } } }).Export())));
var haCachedWire = HaSnapshotDecoder.Decode((haSnapshot with
    { Devices = new[] { haSnapshot.Devices[0] with
        { Status = "cached", BatteryPercent = null, LastKnownPercent = 83 } } }).Export());
Check("HA wire cached state never becomes available",
    !haMapping.Read(haCachedWire, snapshotNow).Available);
var haOtherWire = HaSnapshotDecoder.Decode(haOther.Read(snapshotNow)!.Export());
Check("HA wire new activation never inherits old binding",
    haMapping.Read(haOtherWire, snapshotNow).Status == "mapping_required");

// Actual loopback HTTP producer/consumer interoperability, without external services.
async Task TestHaLoopback()
{
    var store = new LocalSnapshotStore();
    await using var server = new LocalApiServer(store, 0);
    Check("HA client handles unavailable server snapshot",
        await HaLocalClient.ReadAsync(server.Port, server.Token) is null);
    var now = DateTimeOffset.UtcNow;
    store.Publish(now, new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 71, now) });
    var snapshot = (await HaLocalClient.ReadAsync(server.Port, server.Token))!;
    var mapping = HaSessionMapping.Bind(snapshot, "apex_receiver", 1);
    Check("HA client reads real local API bytes",
        mapping.Read(snapshot, DateTimeOffset.UtcNow).BatteryPercent == 71);
    bool wrongToken = false;
    try { await HaLocalClient.ReadAsync(server.Port, new string('0', 64)); }
    catch (InvalidDataException) { wrongToken = true; }
    Check("HA client rejects invalid API authentication", wrongToken);
    bool invalidEndpoint = false;
    try { await HaLocalClient.ReadAsync(0, server.Token); }
    catch (ArgumentException) { invalidEndpoint = true; }
    Check("HA client rejects invalid endpoint before request", invalidEndpoint);
    using var cancelled = new CancellationTokenSource();
    cancelled.Cancel();
    bool cancelledRead = false;
    try { await HaLocalClient.ReadAsync(server.Port, server.Token, cancelled.Token); }
    catch (OperationCanceledException) { cancelledRead = true; }
    Check("HA client honors cancellation", cancelledRead);
    await server.DisposeAsync();
    var replacementStore = new LocalSnapshotStore();
    await using var replacement = new LocalApiServer(replacementStore, 0);
    now = DateTimeOffset.UtcNow;
    replacementStore.Publish(now, new[] { SnapshotInput(DeviceDashboardStatus.Fresh, 69, now) });
    var changed = await HaLocalClient.ReadAsync(replacement.Port, replacement.Token);
    Check("HA client refuses old mapping after actual API restart",
        mapping.Read(changed, DateTimeOffset.UtcNow).Status == "mapping_required");
}
TestHaLoopback().GetAwaiter().GetResult();

// AULA API session slots cannot be silently rebound after a receiver change.
var sessionSlots = new SnapshotSessionSlots();
Check("AULA no identity uses status placeholder", sessionSlots.Aula(null) == 1);
int firstAulaSlot = sessionSlots.Aula("receiver-a");
Check("AULA valid receiver gets a separate bindable slot", firstAulaSlot == 2);
Check("AULA same known receiver preserves slot during no-reply sleep",
    sessionSlots.Aula("receiver-a") == firstAulaSlot);
int otherAulaSlot = sessionSlots.Aula("receiver-b");
Check("AULA replacement gets a new slot", otherAulaSlot == 3);
Check("AULA unknown or disconnected retires the active slot", sessionSlots.Aula(null) == 1);
Check("AULA replug after observed interruption gets a new slot",
    sessionSlots.Aula("receiver-b") == 4);
Check("AULA and APEX slot namespaces remain independent",
    sessionSlots.Apex("receiver-a") == 1 && sessionSlots.Apex("receiver-b") == 2 &&
    sessionSlots.Apex("receiver-a") == 1);
var exhaustedAulaSlots = new SnapshotSessionSlots();
for (int n = 2; n <= LocalBatterySnapshot.MaximumDevices; n++)
    exhaustedAulaSlots.Aula(n.ToString());
bool rejectedExhaustedAula = false;
try { exhaustedAulaSlots.Aula("new"); }
catch (InvalidDataException) { rejectedExhaustedAula = true; }
Check("AULA slot exhaustion fails closed", rejectedExhaustedAula);
var placeholderAula = haSnapshot with { Devices = new[] {
    new LocalBatterySnapshot.Entry("aula_receiver", 1, "disabled", null, null, null) } };
bool rejectedPlaceholder = false;
try { HaSessionMapping.Bind(placeholderAula, "aula_receiver", 1); }
catch (InvalidDataException) { rejectedPlaceholder = true; }
Check("HA cannot bind the AULA status placeholder", rejectedPlaceholder);
var oldAulaSnapshot = haSnapshot with { Devices = new[] {
    new LocalBatterySnapshot.Entry("aula_receiver", 2, "fresh", 83, null, snapshotNow) } };
var oldAulaMapping = HaSessionMapping.Bind(oldAulaSnapshot, "aula_receiver", 2);
var replacementAulaSnapshot = oldAulaSnapshot with { Devices = new[] {
    oldAulaSnapshot.Devices[0] with { SessionSlot = 3 } } };
Check("HA old AULA binding cannot read a replacement slot",
    !oldAulaMapping.Read(replacementAulaSnapshot, snapshotNow).Available);

// Pure MQTT 5 publication intent. No broker, credentials or network traffic.
var mqttFresh = HaMqttAvailabilityPolicy.Plan(haMapping, haSnapshot, snapshotNow);
Check("MQTT fresh intent publishes battery before online",
    mqttFresh.Count == 2 && mqttFresh[0].TopicSuffix == "battery" &&
    mqttFresh[0].Payload == "83" && mqttFresh[1].TopicSuffix == "availability" &&
    mqttFresh[1].Payload == "online");
Check("MQTT fresh battery is not retained; availability is retained",
    !mqttFresh[0].Retain && mqttFresh[1].Retain &&
    mqttFresh.All(x => x.Qos == 1 &&
        x.ExpirySeconds == HaMqttAvailabilityPolicy.FreshExpirySeconds));
var mqttMissing = HaMqttAvailabilityPolicy.Plan(haMapping, null, snapshotNow);
Check("MQTT absent API marks offline before clearing battery",
    mqttMissing.Count == 2 && mqttMissing[0] is
    { TopicSuffix: "availability", Payload: "offline", ExpirySeconds: null } &&
    mqttMissing[1] is { TopicSuffix: "battery", Payload: "", ExpirySeconds: null });
Check("MQTT offline intent retains its status and clearing command",
    mqttMissing.All(x => x.Retain && x.Qos == 1));
var mqttStale = HaMqttAvailabilityPolicy.Plan(haMapping, haSnapshot, snapshotNow.AddMinutes(6));
Check("MQTT expired snapshot never publishes online", mqttStale[0].Payload == "offline");
var mqttRestart = HaMqttAvailabilityPolicy.Plan(haMapping, haOtherWire, snapshotNow);
Check("MQTT changed API session never publishes online", mqttRestart[0].Payload == "offline");
var mqttCached = HaMqttAvailabilityPolicy.Plan(haMapping, haCachedWire, snapshotNow);
Check("MQTT cached reading cannot advertise fresh charge", mqttCached[0].Payload == "offline");
var mqttFuture = HaMqttAvailabilityPolicy.Plan(haMapping,
    haSnapshot with { GeneratedAt = snapshotNow.AddSeconds(1) }, snapshotNow);
Check("MQTT future snapshot is unavailable", mqttFuture[0].Payload == "offline");
var mqttUnknown = HaMqttAvailabilityPolicy.Plan(haMapping,
    haSnapshot with { Devices = Array.Empty<LocalBatterySnapshot.Entry>() }, snapshotNow);
Check("MQTT missing row is unavailable", mqttUnknown[0].Payload == "offline");
var mqttRecovery = HaMqttAvailabilityPolicy.Plan(haMapping, haNext, snapshotNow.AddSeconds(1));
Check("MQTT new fresh sample restores online state", mqttRecovery[0].Payload == "82" &&
    mqttRecovery[1].Payload == "online");
Check("MQTT publication plan has only bounded topic suffixes",
    mqttFresh.Concat(mqttMissing).All(x =>
        x.TopicSuffix is "battery" or "availability" && x.Payload.Length <= 7));
Check("MQTT policy does not modify the snapshot",
    haSnapshot.Devices[0].BatteryPercent == 83 &&
    haSnapshot.Devices[0].Status == "fresh");

// MQTT expiry and zero-value boundaries must never alias unavailable.
var mqttZero = HaMqttAvailabilityPolicy.Plan(haMapping,
    haSnapshot with { Devices = new[] { haSnapshot.Devices[0] with { BatteryPercent = 0 } } },
    snapshotNow);
Check("MQTT zero percent is a valid fresh value", mqttZero[0].Payload == "0" &&
    mqttZero[1].Payload == "online");
var mqttInvalid = HaMqttAvailabilityPolicy.Plan(haMapping,
    haSnapshot with { Devices = new[] { haSnapshot.Devices[0] with { BatteryPercent = -1 } } },
    snapshotNow);
Check("MQTT invalid percentage must fail closed", mqttInvalid[0].Payload == "offline");
var mqttOutOfRange = HaMqttAvailabilityPolicy.Plan(haMapping,
    haSnapshot with { Devices = new[] { haSnapshot.Devices[0] with { BatteryPercent = 101 } } },
    snapshotNow);
Check("MQTT over-range percentage must fail closed", mqttOutOfRange[0].Payload == "offline");
var mqttChangedSchema = HaMqttAvailabilityPolicy.Plan(haMapping,
    haSnapshot with { SchemaVersion = 999 }, snapshotNow);
Check("MQTT unsupported schema must fail closed", mqttChangedSchema[0].Payload == "offline");

// Retained MQTT expiry must be bounded by remaining sample freshness.
var mqttAfterFourMinutes = HaMqttAvailabilityPolicy.Plan(haMapping, haSnapshot,
    snapshotNow.AddMinutes(4));
Check("MQTT expiry follows remaining measurement lifetime",
    mqttAfterFourMinutes[0].ExpirySeconds == 60 &&
    mqttAfterFourMinutes[1].ExpirySeconds == 60);
var mqttFraction = HaMqttAvailabilityPolicy.Plan(haMapping, haSnapshot,
    snapshotNow.AddMinutes(4).AddMilliseconds(1));
Check("MQTT fractional lifetime rounds down, never extends freshness",
    mqttFraction[0].ExpirySeconds == 59 && mqttFraction[1].ExpirySeconds == 59);
var mqttBoundary = HaMqttAvailabilityPolicy.Plan(haMapping, haSnapshot,
    snapshotNow.AddMinutes(5));
Check("MQTT zero remaining lifetime fails closed",
    mqttBoundary[0].Payload == "offline" && mqttBoundary[1].Payload == "");
var mqttMeasuredLater = haSnapshot with
{
    GeneratedAt = snapshotNow.AddMinutes(3),
    Devices = new[] { haSnapshot.Devices[0] with
        { MeasuredAt = snapshotNow.AddMinutes(2) } }
};
var mqttLaterPlan = HaMqttAvailabilityPolicy.Plan(haMapping, mqttMeasuredLater,
    snapshotNow.AddMinutes(4));
Check("MQTT expiry considers both snapshot and measurement ages",
    mqttLaterPlan[0].ExpirySeconds == 180 &&
    mqttLaterPlan[1].ExpirySeconds == 180);

// Offline delivery gate prevents a partial publish from advertising online.
async Task TestMqttAcknowledgmentGate()
{
    var accepted = new List<string>();
    bool ok = await HaMqttDeliveryGate.PublishAsync(mqttFresh, (message, _) =>
    {
        accepted.Add(message.TopicSuffix);
        return Task.FromResult(true);
    }, CancellationToken.None);
    Check("MQTT gate permits online only after battery acknowledgment", ok &&
        accepted.SequenceEqual(new[] { "battery", "availability" }));
    accepted.Clear();
    bool rejected = await HaMqttDeliveryGate.PublishAsync(mqttFresh, (message, _) =>
    {
        accepted.Add(message.TopicSuffix);
        return Task.FromResult(false);
    }, CancellationToken.None);
    Check("MQTT failed battery acknowledgment blocks online", !rejected &&
        accepted.SequenceEqual(new[] { "battery" }));
    accepted.Clear();
    bool offline = await HaMqttDeliveryGate.PublishAsync(mqttMissing, (message, _) =>
    {
        accepted.Add(message.TopicSuffix);
        return Task.FromResult(true);
    }, CancellationToken.None);
    Check("MQTT offline acknowledgment precedes battery clear", offline &&
        accepted.SequenceEqual(new[] { "availability", "battery" }));
    accepted.Clear();
    bool failedOffline = await HaMqttDeliveryGate.PublishAsync(mqttMissing, (message, _) =>
    {
        accepted.Add(message.TopicSuffix);
        return Task.FromResult(false);
    }, CancellationToken.None);
    Check("MQTT failed offline acknowledgment blocks stale-value clear",
        !failedOffline && accepted.SequenceEqual(new[] { "availability" }));
    bool retainedState = false;
    try
    {
        await HaMqttDeliveryGate.PublishAsync(new[]
        {
            mqttFresh[0] with { Retain = true }, mqttFresh[1]
        }, (message, _) => Task.FromResult(true), CancellationToken.None);
    }
    catch (InvalidDataException) { retainedState = true; }
    Check("MQTT gate rejects retained fresh sensor state", retainedState);
    bool malformed = false;
    try
    {
        await HaMqttDeliveryGate.PublishAsync(new[] { mqttFresh[1], mqttFresh[0] },
            (message, _) => Task.FromResult(true), CancellationToken.None);
    }
    catch (InvalidDataException) { malformed = true; }
    Check("MQTT gate rejects unsafe online ordering", malformed);
    bool invalidTopic = false;
    try
    {
        await HaMqttDeliveryGate.PublishAsync(new[]
        {
            mqttFresh[0] with { TopicSuffix = "arbitrary/topic" }, mqttFresh[1]
        }, (message, _) => Task.FromResult(true), CancellationToken.None);
    }
    catch (InvalidDataException) { invalidTopic = true; }
    Check("MQTT gate rejects injected topic suffix", invalidTopic);
    using var cancelled = new CancellationTokenSource();
    cancelled.Cancel();
    bool cancelledBeforePublish = false;
    try
    {
        await HaMqttDeliveryGate.PublishAsync(mqttFresh,
            (message, _) => Task.FromResult(true), cancelled.Token);
    }
    catch (OperationCanceledException) { cancelledBeforePublish = true; }
    Check("MQTT gate honors pre-cancellation", cancelledBeforePublish);
    accepted.Clear();
    using var cancelledDuring = new CancellationTokenSource();
    bool cancelledBeforeOnline = false;
    try
    {
        await HaMqttDeliveryGate.PublishAsync(mqttFresh, (message, _) =>
        {
            accepted.Add(message.TopicSuffix);
            cancelledDuring.Cancel();
            return Task.FromResult(true);
        }, cancelledDuring.Token);
    }
    catch (OperationCanceledException) { cancelledBeforeOnline = true; }
    Check("MQTT cancellation after battery blocks online",
        cancelledBeforeOnline && accepted.SequenceEqual(new[] { "battery" }));
}
TestMqttAcknowledgmentGate().GetAwaiter().GetResult();

// No broker can be contacted until an explicit secure opt-in is supplied.
var brokerGuard = new HaMqttBrokerPreflight(ExplicitlyEnabled: true,
    BrokerHost: "broker.example.invalid", BrokerPort: 8883,
    TopicPrefix: "owner-chosen/battery", CredentialsSuppliedForSession: true);
bool BrokerRejected(HaMqttBrokerPreflight options)
{
    try { options.Validate(); return false; }
    catch (InvalidDataException) { return true; }
}
Check("MQTT broker preflight accepts explicit secure parameters",
    !BrokerRejected(brokerGuard));
Check("MQTT broker preflight defaults fully disabled",
    BrokerRejected(new HaMqttBrokerPreflight()));
Check("MQTT broker preflight requires explicit opt-in",
    BrokerRejected(brokerGuard with { ExplicitlyEnabled = false }));
Check("MQTT broker preflight rejects plaintext transport",
    BrokerRejected(brokerGuard with { UseTls = false }));
Check("MQTT broker preflight forbids invalid certificate bypass",
    BrokerRejected(brokerGuard with { VerifyServerCertificate = false }));
Check("MQTT broker preflight requires MQTT 5",
    BrokerRejected(brokerGuard with { UseMqtt5 = false }));
Check("MQTT broker preflight requires session credentials",
    BrokerRejected(brokerGuard with { CredentialsSuppliedForSession = false }));
Check("MQTT broker preflight rejects URLs as broker host",
    BrokerRejected(brokerGuard with { BrokerHost = "mqtts://broker.example.invalid" }));
Check("MQTT broker preflight rejects invalid ports",
    BrokerRejected(brokerGuard with { BrokerPort = 0 }) &&
    BrokerRejected(brokerGuard with { BrokerPort = 65536 }));
Check("MQTT broker preflight rejects wildcard and reserved MQTT topics",
    BrokerRejected(brokerGuard with { TopicPrefix = "owner/+/battery" }) &&
    BrokerRejected(brokerGuard with { TopicPrefix = "homeassistant/sensor" }));
Check("MQTT broker preflight rejects topic paths with empty segments",
    BrokerRejected(brokerGuard with { TopicPrefix = "owner//battery" }) &&
    BrokerRejected(brokerGuard with { TopicPrefix = "/owner/battery" }));
Check("MQTT broker preflight accepts a custom TLS port without opening it",
    !BrokerRejected(brokerGuard with { BrokerPort = 8884 }));

Check("MQTT broker preflight rejects absent broker hostname",
    BrokerRejected(brokerGuard with { BrokerHost = null! }));
Check("MQTT broker preflight rejects absent topic prefix",
    BrokerRejected(brokerGuard with { TopicPrefix = null! }));
Check("MQTT broker preflight rejects whitespace in broker hostname",
    BrokerRejected(brokerGuard with { BrokerHost = "broker example.invalid" }));

// Reconcile reuses scratch storage without changing known/unknown semantics.
var reconcileSchedule = new DevicePollSchedule();
var pollKeys = Enumerable.Range(0, 64).Select(n => n.ToString("X64")).ToArray();
for (int i = 0; i < pollKeys.Length; i++)
    reconcileSchedule.Complete(pollKeys[i], 100000);
reconcileSchedule.Reconcile(pollKeys.Where((_, index) => index % 2 == 0),
    presenceKnown: false);
Check("USB unknown discovery retains all per-device deadlines",
    pollKeys.All(key => !reconcileSchedule.IsDue(key, 101000, 60)));
reconcileSchedule.Reconcile(pollKeys.Where((_, index) => index % 2 == 0),
    presenceKnown: true);
Check("USB known discovery retains present receiver deadlines",
    pollKeys.Where((_, index) => index % 2 == 0)
        .All(key => !reconcileSchedule.IsDue(key, 101000, 60)));
Check("USB known discovery forgets only absent receiver deadlines",
    pollKeys.Where((_, index) => index % 2 != 0)
        .All(key => reconcileSchedule.IsDue(key, 101000, 60)));
reconcileSchedule.Reconcile(pollKeys.Where((_, index) => index % 2 == 0),
    presenceKnown: true);
Check("USB repeat discovery does not reset surviving deadlines",
    !reconcileSchedule.IsDue(pollKeys[0], 101000, 60));
int enumerations = 0;
IEnumerable<string> PresentOnce()
{
    enumerations++;
    yield return pollKeys[0];
}
reconcileSchedule.Reconcile(PresentOnce(), presenceKnown: true);
Check("USB reconcile enumerates fresh discovery once", enumerations == 1);
Check("USB later confirmed removal resets previously retained receiver",
    reconcileSchedule.IsDue(pollKeys[2], 101000, 60));
Check("USB surviving receiver still follows its interval",
    !reconcileSchedule.IsDue(pollKeys[0], 101000, 60));
reconcileSchedule.Reconcile(Array.Empty<string>(), presenceKnown: false);
Check("USB unknown empty inventory cannot erase last deadline",
    !reconcileSchedule.IsDue(pollKeys[0], 101000, 60));
reconcileSchedule.Reconcile(Array.Empty<string>(), presenceKnown: true);
Check("USB confirmed empty inventory clears all deadlines",
    reconcileSchedule.IsDue(pollKeys[0], 101000, 60));
reconcileSchedule.Complete(pollKeys[1], 101000);
reconcileSchedule.Reconcile(new[] { pollKeys[1] }, presenceKnown: true);
Check("USB discovery after full cleanup preserves new completion",
    !reconcileSchedule.IsDue(pollKeys[1], 101001, 60));

// Receiver/icon reconciliation scratch must be reusable without stale keys.
var scratch = new InventoryFrameScratch();
scratch.Begin();
scratch.Add("receiver-a");
scratch.Add("receiver-b");
Check("Scratch tracks current receiver identities",
    scratch.Contains("receiver-a") && scratch.Contains("receiver-b"));
Check("Scratch detects absent receiver without changing live inputs",
    scratch.Missing(new[] { "receiver-a", "receiver-c" })
        .SequenceEqual(new[] { "receiver-c" }));
Check("Scratch picks only missing keys with ordinal case sensitivity",
    scratch.Missing(new[] { "Receiver-a", "receiver-a" })
        .SequenceEqual(new[] { "Receiver-a" }));
Check("Scratch preserves stable primary selection in current frame",
    ReceiverIdentity.SelectPrimary("receiver-b", scratch.Keys) == "receiver-b");
scratch.End();
Check("Scratch end clears all formerly seen identities",
    !scratch.Contains("receiver-a") && !scratch.Keys.Any());
scratch.Begin();
scratch.Add("receiver-c");
Check("Scratch reuse does not inherit prior receiver identity",
    !scratch.Contains("receiver-a") && scratch.Contains("receiver-c"));
Check("Scratch reusable missing collection starts empty",
    scratch.Missing(new[] { "receiver-c" }).Count == 0);
Check("Scratch captures snapshot of missing dictionary identities",
    scratch.Missing(new[] { "receiver-b" }).SequenceEqual(new[] { "receiver-b" }));
scratch.End();
Check("Scratch releases missing keys on completion",
    scratch.Missing(Array.Empty<string>()).Count == 0);
var largeScratch = new InventoryFrameScratch();
var inventoryKeys = Enumerable.Range(0, 64).Select(n => n.ToString("X4")).ToArray();
for (int round = 0; round < 1000; round++)
{
    largeScratch.Begin();
    foreach (string key in inventoryKeys)
        if (round % 2 == 0 || key != inventoryKeys[0]) largeScratch.Add(key);
    var absent = largeScratch.Missing(inventoryKeys);
    if (absent.Count != (round % 2 == 0 ? 0 : 1))
        throw new Exception("Scratch reconciliation mismatch.");
    largeScratch.End();
}
Check("Scratch thousand-frame inventory parity", !largeScratch.Keys.Any());

// An aborted identity enumeration must not retain stale identities.
var failingScratch = new InventoryFrameScratch();
IEnumerable<string> FailingKeys()
{
    yield return "temporary-identity";
    throw new InvalidOperationException("Synthetic inventory failure");
}
failingScratch.Begin();
failingScratch.Add("present");
bool enumerationFailed = false;
try
{
    failingScratch.Missing(FailingKeys());
}
catch (InvalidOperationException)
{
    enumerationFailed = true;
}
finally
{
    failingScratch.End();
}
Check("Scratch exception path clears seen and missing identities",
    enumerationFailed && !failingScratch.Keys.Any() &&
    failingScratch.Missing(Array.Empty<string>()).Count == 0);
failingScratch.Begin();
failingScratch.Add("reconnected");
Check("Scratch resumes after exception without stale identities",
    failingScratch.Contains("reconnected") && !failingScratch.Contains("present"));
failingScratch.End();

// Streaming BLE selection preserves stable ordering and explicit force reads.
var bleSelection = new BluetoothMultiSession();
bleSelection.Enable("alpha", bleDirect, multiAt);
bleSelection.Enable("bravo", bleDirect, multiAt);
bleSelection.Enable("charlie", bleDirect, multiAt);
bleSelection.Enable("alpha", bleDirect, multiAt);
var chosenBle = bleSelection.TryBegin(true, false, multiAt.AddMinutes(1));
Check("BLE streaming selector respects earliest enable generation",
    chosenBle?.Key == "bravo");
Check("BLE selection remains single flight",
    bleSelection.TryBegin(true, false, multiAt.AddMinutes(1), "alpha") is null);
Check("BLE streaming selector records completed failed attempt",
    chosenBle is not null &&
    bleSelection.Complete(chosenBle, bleFailed, multiAt.AddMinutes(1), true, false));
var secondBle = bleSelection.TryBegin(true, false, multiAt.AddMinutes(1));
Check("BLE streaming selector skips backed-off failed slot",
    secondBle?.Key == "charlie");
bleSelection.Disable("charlie");
Check("BLE selector preserves in-flight token until completion after opt-out",
    secondBle is not null && bleSelection.IsBusy);
Check("BLE streaming selector invalidates removed in-flight reply",
    secondBle is not null &&
    !bleSelection.Complete(secondBle, bleDirect, multiAt.AddMinutes(1), true, false));
var forceBle = bleSelection.TryBegin(true, false, multiAt.AddMinutes(1), "alpha");
Check("BLE forced selection bypasses deadline for exact key", forceBle?.Key == "alpha");
Check("BLE forced selection cannot select a different key while busy",
    bleSelection.TryBegin(true, false, multiAt.AddMinutes(1), "bravo") is null);
Check("BLE forced selection completes without slot corruption",
    forceBle is not null &&
    bleSelection.Complete(forceBle, bleDirect, multiAt.AddMinutes(1), true, false));
Check("BLE streaming selector honors conservative USB priority",
    bleSelection.TryBegin(true, true, multiAt.AddMinutes(5)) is null &&
    bleSelection.TryBegin(false, false, multiAt.AddMinutes(5)) is null);
bleSelection.DisableAll();

SafeLogTests.Run(Check);

Console.WriteLine($"Summary: PASS={passed}, FAIL={failed}");
return failed == 0 ? 0 : 1;
