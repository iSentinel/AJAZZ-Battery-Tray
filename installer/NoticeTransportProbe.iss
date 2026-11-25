; CI-only fixture: no application, no hardware access, no release packaging.
#ifndef NoticeRoot
  #error NoticeRoot must be supplied for the isolated CI fixture
#endif

[Setup]
AppId=AJAZZ-Notice-Transport-Probe
AppName=AJAZZ Notice Transport Probe
AppVersion=1.0
DefaultDirName={localappdata}\AJAZZ-Notice-Transport-Probe
DisableDirPage=yes
DisableProgramGroupPage=yes
UsePreviousAppDir=no
CreateUninstallRegKey=no
PrivilegesRequired=lowest
Uninstallable=yes
OutputBaseFilename=AJAZZ-Notice-Transport-Probe
Compression=lzma2
SolidCompression=yes

[Files]
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
