[Setup]
AppName=WhisperAI
AppVersion=1.0
DefaultDirName={localappdata}\Programs\WhisperAI
PrivilegesRequired=lowest
DefaultGroupName=WhisperAI
OutputDir=Output
OutputBaseFilename=WhisperAISetup
Compression=lzma
SolidCompression=yes
WizardImageFile=assets\wizard_image.bmp
WizardSmallImageFile=assets\wizard_small.bmp

[Files]
Source: "{#SourcePath}\..\dist\WhisperAI.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\WhisperAI"; Filename: "{app}\WhisperAI.exe"
Name: "{autodesktop}\WhisperAI"; Filename: "{app}\WhisperAI.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Response: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    Response := MsgBox('Do you want to keep your custom dictionaries, downloaded AI models, and user preferences?', mbConfirmation, MB_YESNO);
    if Response = IDNO then
    begin
      DelTree(ExpandConstant('{userprofile}\.whisperai'), True, True, True);
    end;
  end;
end;

[Run]
Filename: "{app}\WhisperAI.exe"; Description: "Launch WhisperAI"; Flags: nowait postinstall
