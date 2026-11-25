# AJAZZ Battery Tray architecture

- Windows .NET 8 WinForms (Windows 10 19041+ target): TrayAppContext
  orchestrates settings, scheduling and presentation; AjazzHidReader/HidNative
  transport and HidFeaturePolicy write allowlist; BatteryReportParser validates
  data; ReceiverMonitor owns per-receiver observation/history/notifications.
  RoutinePollWorker and FullHidCapture use bounded local child processes;
  routine isolation is opt-in. AULA and BLE are separate transport paths.
- macOS 13+ Universal: Swift/AppKit/IOKit/CoreBluetooth, native arm64 and
  x86_64 build, shared AjazzBatteryReport.h decoder and AjazzIoLease.h.
  High Sierra Intel: separate Objective-C executable and version/tag,
  same conservative parser and lease. Native hosted Intel CI is not
  physical High Sierra or arm64 acceptance.
- LocalBatterySnapshot and LocalApiServer: session-only opt-in authenticated
  IPv4 loopback read-only sanitized projection. HA preview is .NET 8 consumer;
  unverified values never enter shared telemetry.
- AppSettings, BatteryHistory: local user persistence; installer per-machine
  Inno Setup, portable EXE and Apple ZIP distributions. No global database.
- tools/: dependency-free Python offline analysis and PowerShell measurement
  helpers; tests/ contains C# console regression, WinForms native smoke and
  sanitized shared corpus. Hosted CI must not access physical devices.
- No distributed controller or production deployment service.
  See docs/LOCAL_API.md, docs/DOCK_PROTOCOL_SAFETY.md,
  docs/ISOLATED_POLLING_ACCEPTANCE.md and docs/VALIDATION_MATRIX.md.
