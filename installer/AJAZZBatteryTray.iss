; AJAZZ Battery Tray - per-machine installer for Windows x64.
; Self-contained portable EXE is created by dotnet publish before ISCC runs.
#define AppName "AJAZZ Battery Tray"
#define AppVersion "0.3.0-beta.11"
#define AppExe "AJAZZBatteryTray.exe"

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
OutputBaseFilename=AJAZZBatteryTray-Setup-win-x64
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
UninstallDisplayName=AJAZZ Battery Tray
UninstallDisplayIcon={app}\{#AppExe}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\app\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\AJAZZ Battery Tray"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{autodesktop}\AJAZZ Battery Tray"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch AJAZZ Battery Tray"; Flags: nowait postinstall skipifsilent runasoriginaluser
