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
Check("AJ179 revision label", ReceiverIdentity.Label(0x0002).Contains("AJ179"));
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
UiText.SetLanguage("uk");
Check("Ukrainian settings label", UiText.Get("Settings") == "Налаштування");
Check("Ukrainian notification label",
    UiText.Get("Low battery notifications") == "Сповіщення про низький заряд");
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
Check("AULA uncertain receiver identity invalidates cache",
    aulaCache.LastGoodPercent is null && aulaCache.LastGoodAt is null);

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
    colors.Count == 2 && colors[colorKeyA] == "blue" && colors[colorKeyB] == "purple");
Check("Tray palette null settings safe", TrayColorRules.Clean(null).Count == 0);
Check("Tray colors survive settings round trip",
    System.Text.Json.JsonSerializer.Deserialize<AppSettings>(
        System.Text.Json.JsonSerializer.Serialize(new AppSettings { DeviceTrayColors = colors }))
        ?.DeviceTrayColors[colorKeyB] == "purple");

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

Console.WriteLine($"Summary: PASS={passed}, FAIL={failed}");
return failed == 0 ? 0 : 1;
