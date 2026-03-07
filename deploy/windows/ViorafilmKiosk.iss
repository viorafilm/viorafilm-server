#ifndef AppName
  #define AppName "Viorafilm Kiosk"
#endif
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef Publisher
  #define Publisher "Viorafilm"
#endif
#ifndef ExeName
  #define ExeName "ViorafilmKiosk.exe"
#endif
#ifndef SourceDir
  #error SourceDir is required. Pass /DSourceDir=...
#endif
#ifndef OutputDir
  #error OutputDir is required. Pass /DOutputDir=...
#endif
#ifndef OutputBaseFilename
  #define OutputBaseFilename "ViorafilmKiosk_Setup"
#endif

[Setup]
AppId={{AFCC5A4B-7A22-4D6B-B7E2-AE0AD5792F55}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#Publisher}
DefaultDirName={autopf64}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
WizardStyle=modern
SetupLogging=yes
UninstallDisplayIcon={app}\{#ExeName}

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{commonappdata}\ViorafilmKiosk"; Permissions: users-modify
Name: "{commonappdata}\ViorafilmKiosk\config"; Permissions: users-modify
Name: "{commonappdata}\ViorafilmKiosk\secure"; Permissions: users-modify
Name: "{commonappdata}\ViorafilmKiosk\out"; Permissions: users-modify
Name: "{commonappdata}\ViorafilmKiosk\sessions"; Permissions: users-modify
Name: "{commonappdata}\ViorafilmKiosk\logs"; Permissions: users-modify

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[UninstallDelete]
Type: filesandordirs; Name: "{commonappdata}\ViorafilmKiosk\secure"

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#ExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
