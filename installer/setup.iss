[Setup]
AppName=WhisperAI
AppVersion=1.0
DefaultDirName={autopf}\WhisperAI
DefaultGroupName=WhisperAI
OutputDir=E:\WhisperAI\installer\Output
OutputBaseFilename=WhisperAISetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "E:\WhisperAI\dist\main\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\WhisperAI"; Filename: "{app}\main.exe"
Name: "{autodesktop}\WhisperAI"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked
