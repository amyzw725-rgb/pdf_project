; Inno Setup 6 — optional Windows setup.exe
; Prerequisite: run from repo root:  pwsh .\build_release.ps1
; Then compile this script with Inno Setup Compiler (iscc.exe).
; Output: installer\Output\InvoicePDFHelper-Setup-x.x.exe

#define MyAppName "Invoice PDF Helper"
#define MyAppVersion "1.0.0"
#define StagingRel "..\dist\InvoicePDFHelper_package"

[Setup]
AppId={{B2F8C4E1-9A0D-4F1E-9C2A-0023456789AB}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=InvoicePDFHelper-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#StagingRel}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\run_app.bat"; WorkingDir: "{app}"; Comment: "Start Invoice PDF Helper"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\Klero.vbs"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\安装说明.txt"; Description: "View installation notes"; Flags: shellexec postinstall skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
