; CI-only fixture, never packaged or published as AJAZZ.
[Setup]
AppId=AJAZZ-Inno674-Compiler-Probe
AppName=AJAZZ Inno 6.7.4 Compiler Probe
AppVersion=1.0
DefaultDirName={localappdata}\AJAZZ-Inno674-Compiler-Probe
PrivilegesRequired=lowest
DisableDirPage=yes
DisableProgramGroupPage=yes
UsePreviousAppDir=no
CreateUninstallRegKey=no
Uninstallable=yes
OutputBaseFilename=AJAZZ-Inno674-Compiler-Probe
Compression=lzma2
SolidCompression=yes

[Files]
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
