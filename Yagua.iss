; Instalador de Yagua generado con Inno Setup.
; Requiere dist\Yagua\, la carpeta creada por PyInstaller.

[Setup]
; Identidad y rutas predeterminadas del instalador de Windows.
AppId={{2A0F8C4B-6E0D-4E7B-9E92-9B8D3D34B6F1}}
AppName=Yagua
AppVersion=2.0.0
AppVerName=Yagua 2.0.0
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
OutputBaseFilename=Yagua_Setup_2.0.0
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Languages]
; El instalador ofrece los mismos dos idiomas que las páginas de agradecimiento.
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
spanish.ThanksURL=https://yagua.bouixdev.workers.dev/es/thanks/
english.ThanksURL=https://yagua.bouixdev.workers.dev/en/thanks/

[Files]
; Copia el directorio one-folder generado por PyInstaller.
Source: "dist\Yagua\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Yagua"; Filename: "{app}\Yagua.exe"
Name: "{commondesktop}\Yagua"; Filename: "{app}\Yagua.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
; La apertura de la app se omite en instalaciones silenciosas.
Filename: "{app}\Yagua.exe"; Description: "Ejecutar Yagua"; Flags: nowait postinstall skipifsilent

[Code]
// Al completar el asistente abre la página correspondiente al idioma elegido.
procedure CurStepChanged(CurStep: TSetupStep);
var
  ErrorCode: Integer;
  ThanksURL: string;
begin
  if (CurStep = ssDone) and not WizardSilent then begin
    ThanksURL := ExpandConstant('{cm:ThanksURL}');
    if ShellExec('', ThanksURL, '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode) then
      Log('Opened thank-you page: ' + ThanksURL)
    else
      Log('Unable to open the thank-you page: ' + SysErrorMessage(ErrorCode));
  end;
end;
