; ============================================================
;  Frontchat Empregos em Massa - Instalador (Inno Setup 6)
;  Compile este arquivo no Inno Setup Compiler.
;  Gera o instalador FrontchatEmpregosEmMassa-Setup.exe
; ============================================================

#define MyAppName "Frontchat Empregos em Massa"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Frontchat"
#define MyAppExeName "FrontchatEmpregosEmMassa.exe"

[Setup]
AppId={{7C6A2F1E-9B3A-4D5C-A1E2-0B7C4F9A1D33}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\installer_output
OutputBaseFilename=FrontchatEmpregosEmMassa-Setup
SetupIconFile=..\assets\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName} agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Os dados do usuario em %LOCALAPPDATA%\FrontchatEmpregosEmMassa NAO sao
; removidos automaticamente (LGPD). O usuario pode apaga-los nas Configuracoes.
Type: filesandordirs; Name: "{userappdata}\FrontchatEmpregosEmMassa\logs"
