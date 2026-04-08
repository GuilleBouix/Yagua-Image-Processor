; Inno Setup script for Yagua
; Build requires dist\Yagua\ (PyInstaller one-folder)

[Setup]
AppId={{2A0F8C4B-6E0D-4E7B-9E92-9B8D3D34B6F1}}
AppName=Yagua
AppVersion=1.2.2
AppVerName=Yagua 1.2.2
AppPublisher=GuilleBouix
AppPublisherURL=https://github.com/GuilleBouix
AppSupportURL=https://github.com/GuilleBouix
AppUpdatesURL=https://github.com/GuilleBouix
SetupIconFile=assets\installer\installer_icon.ico
WizardImageFile=assets\installer\wizard_image.bmp
WizardSmallImageFile=assets\installer\wizard_small.bmp
DefaultDirName={pf}\Yagua
DefaultGroupName=Yagua
UninstallDisplayIcon={app}\Yagua.exe
OutputDir=installer
OutputBaseFilename=Yagua_Setup_1.2.2
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\Yagua\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Yagua"; Filename: "{app}\Yagua.exe"
Name: "{commondesktop}\Yagua"; Filename: "{app}\Yagua.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\Yagua.exe"; Description: "Ejecutar Yagua"; Flags: nowait postinstall skipifsilent
