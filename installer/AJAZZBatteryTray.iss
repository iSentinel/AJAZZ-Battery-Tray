; AJAZZ Battery Tray - per-machine installer for Windows x64.
; Self-contained portable EXE is created by dotnet publish before ISCC runs.
#define AppName "AJAZZ Battery Tray"
#ifndef AppVersion
#define AppVersion "0.3.0-beta.61"
#endif
#define AppExe "AJAZZBatteryTray.exe"
#ifdef InstallerLifecycleProbe
#define LaunchArgs "--internal-installer-lifecycle-probe"
#else
#define LaunchArgs ""
#endif

#ifdef ProductionNoticeCandidate
#ifndef ProductNoticeProbe
#error ProductionNoticeCandidate requires ProductNoticeProbe
#endif
#endif

#ifdef ProductNoticeProbe
#ifndef NoticeRoot
#error ProductNoticeProbe requires NoticeRoot
#endif
#ifdef InstallerLifecycleProbe
#error ProductNoticeProbe cannot be combined with InstallerLifecycleProbe
#endif
#else
#ifdef NoticeRoot
#error NoticeRoot requires ProductNoticeProbe
#endif
#endif

[Setup]
AppId={{9829045F-37F0-4AC3-ACBD-1B5E4129A179}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=iSentinel
AppPublisherURL=https://github.com/iSentinel/AJAZZ-Battery-Tray
AppSupportURL=https://github.com/iSentinel/AJAZZ-Battery-Tray/issues
AppUpdatesURL=https://github.com/iSentinel/AJAZZ-Battery-Tray/releases
DefaultDirName={autopf}\AJAZZ Battery Tray
DefaultGroupName=AJAZZ Battery Tray
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
#ifdef ProductNoticeProbe
#ifdef ProductionNoticeCandidate
OutputBaseFilename=AJAZZBatteryTray-Setup-win-x64
#else
OutputBaseFilename=AJAZZBatteryTray-Notice-Probe-win-x64
#endif
#else
OutputBaseFilename=AJAZZBatteryTray-Setup-win-x64
#endif
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
UninstallDisplayName=AJAZZ Battery Tray
SetupIconFile=..\src\AjazzBatteryTray\Assets\AppIcon.ico
UninstallDisplayIcon={app}\{#AppExe}
; Let Restart Manager close only applications using our installed executable.
CloseApplications=yes
CloseApplicationsFilter=AJAZZBatteryTray.exe
; One explicit launch below; do not also ask Restart Manager to restart it.
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\app\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\src\AjazzBatteryTray\Assets\AppIcon.ico"; DestDir: "{app}\Icons"; Flags: ignoreversion
Source: "..\src\AjazzBatteryTray\Assets\AppIcon-white.ico"; DestDir: "{app}\Icons"; Flags: ignoreversion
Source: "..\src\AjazzBatteryTray\Assets\AppIcon-black.ico"; DestDir: "{app}\Icons"; Flags: ignoreversion
Source: "..\src\AjazzBatteryTray\Assets\AppIcon-blue.ico"; DestDir: "{app}\Icons"; Flags: ignoreversion

#ifdef ProductNoticeProbe
Source: "{#NoticeRoot}\AJAZZ\LICENSE"; DestDir: "{app}\Notices\AJAZZ"; Flags: ignoreversion
Source: "{#NoticeRoot}\DotNet\core\LICENSE.TXT"; DestDir: "{app}\Notices\DotNet\core"; Flags: ignoreversion
Source: "{#NoticeRoot}\DotNet\core\THIRD-PARTY-NOTICES.TXT"; DestDir: "{app}\Notices\DotNet\core"; Flags: ignoreversion
Source: "{#NoticeRoot}\DotNet\desktop\LICENSE"; DestDir: "{app}\Notices\DotNet\desktop"; Flags: ignoreversion
Source: "{#NoticeRoot}\DotNet\host\LICENSE.TXT"; DestDir: "{app}\Notices\DotNet\host"; Flags: ignoreversion
Source: "{#NoticeRoot}\DotNet\host\THIRD-PARTY-NOTICES.TXT"; DestDir: "{app}\Notices\DotNet\host"; Flags: ignoreversion
Source: "{#NoticeRoot}\Inno\Inno-Setup-LICENSE.txt"; DestDir: "{app}\Notices\Inno"; Flags: ignoreversion
Source: "{#NoticeRoot}\Inno\LZMA-SDK-7zC.txt"; DestDir: "{app}\Notices\Inno"; Flags: ignoreversion
Source: "{#NoticeRoot}\Inno\Pascal-Script-LICENSE.txt"; DestDir: "{app}\Notices\Inno"; Flags: ignoreversion
Source: "{#NoticeRoot}\manifest.json"; DestDir: "{app}\Notices"; Flags: ignoreversion
#endif

[Icons]
Name: "{autoprograms}\AJAZZ Battery Tray"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{autodesktop}\AJAZZ Battery Tray"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Parameters: "{#LaunchArgs}"; WorkingDir: "{app}"; StatusMsg: "Starting AJAZZ Battery Tray..."; Flags: nowait runasoriginaluser; Check: ShouldLaunchTray

[Code]
function ShouldLaunchTray: Boolean;
var
  Launch: String;
begin
  { Interactive setup launches by default. Unattended setup requires opt-in. }
  Launch := ExpandConstant('{param:LAUNCH|}');
  if Launch = '0' then
    Result := False
  else if Launch = '1' then
    Result := True
  else
    Result := not WizardSilent;
end;

