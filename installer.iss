; ============================================================
; Writile - Inno Setup 安装脚本
; 使用 Inno Setup 编译此文件以生成 .exe 安装包
; 下载 Inno Setup: https://jrsoftware.org/isdl.php
; ============================================================

#define MyAppName "Writile"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Writile"
#define MyAppExeName "Writile.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/writile
AppSupportURL=https://github.com/writile
AppUpdatesURL=https://github.com/writile
AppComments=Typora 风格的所见即所得 Markdown 编辑器
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=Writile-Setup-{#MyAppVersion}
Compression=lzma2/ultra
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
PrivilegesRequired=admin
SetupIconFile=icon.ico
; 现代化安装界面
WizardStyle=modern
; 允许卸载时保留用户数据
Uninstallable=yes
; 启动画面
DisableStartupPrompt=no
; 允许自定义安装路径
UsePreviousAppDir=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"
Name: "quicklaunchicon"; Description: "创建快速启动栏图标"; GroupDescription: "附加图标:"
Name: "associate_files"; Description: "关联 .md / .markdown 文件"; GroupDescription: "文件关联:"
Name: "create_themes_dir"; Description: "创建主题目录 (我的文档\Writile\themes)"; GroupDescription: "其他:"

[Files]
; 主程序（单文件模式，所有依赖已内嵌）
Source: "dist\Writile.exe"; DestDir: "{app}"; Flags: ignoreversion
; 图标文件
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[FileAssociations]
.md; "Markdown 文件"; "Writile"; """{app}\{#MyAppExeName}"" ""%1""", 0
.markdown; "Markdown 文件"; "Writile"; """{app}\{#MyAppExeName}"" ""%1""", 0
.mdown; "Markdown 文件"; "Writile"; """{app}\{#MyAppExeName}"" ""%1""", 0
.mkd; "Markdown 文件"; "Writile"; """{app}\{#MyAppExeName}"" ""%1""", 0
.markdown; "Markdown 文件"; "Writile"; """{app}\{#MyAppExeName}"" ""%1""", 0

[Registry]
; 注册文件关联 (仅在勾选任务时)
Root: HKCR; Subkey: ".md"; ValueType: string; ValueName: ""; ValueData: "Writile.md"; Flags: uninsdeletevalue; Tasks: associate_files
Root: HKCR; Subkey: ".markdown"; ValueType: string; ValueName: ""; ValueData: "Writile.md"; Flags: uninsdeletevalue; Tasks: associate_files
Root: HKCR; Subkey: ".mdown"; ValueType: string; ValueName: ""; ValueData: "Writile.md"; Flags: uninsdeletevalue; Tasks: associate_files
Root: HKCR; Subkey: ".mkd"; ValueType: string; ValueName: ""; ValueData: "Writile.md"; Flags: uninsdeletevalue; Tasks: associate_files
Root: HKCR; Subkey: "Writile.md"; ValueType: string; ValueName: ""; ValueData: "Markdown 文件"; Flags: uninsdeletekey; Tasks: associate_files
Root: HKCR; Subkey: "Writile.md\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: associate_files
Root: HKCR; Subkey: "Writile.md\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: associate_files
Root: HKCR; Subkey: "Writile.md\shell\edit\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: associate_files
Root: HKCR; Subkey: "Writile.md\shell\edit"; ValueType: string; ValueName: ""; ValueData: "用 Writile 编辑"; Tasks: associate_files

; 注册到"打开方式"列表
Root: HKCU; Subkey: "Software\Classes\.md\OpenWithList\Writile"; ValueType: string; ValueName: ""; ValueData: ""; Flags: uninsdeletekey; Tasks: associate_files
Root: HKCU; Subkey: "Software\Classes\.markdown\OpenWithList\Writile"; ValueType: string; ValueName: ""; ValueData: ""; Flags: uninsdeletekey; Tasks: associate_files

[Dirs]
; 创建主题目录
Name: "{userdocs}\Writile\themes"; Tasks: create_themes_dir

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "立即启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时询问是否删除用户数据
Type: filesandordirs; Name: "{app}"
; 不删除用户主题目录 ({userdocs}\Writile)，保留用户自定义主题

[Code]
var
  WorkDirPage: TInputDirWizardPage;

function InitializeSetup(): Boolean;
begin
    Result := True;
end;

procedure InitializeWizard();
begin
  // 在选择安装目录之后，添加"选择默认工作目录"页面
  WorkDirPage := CreateInputDirPage(
    wpSelectDir,
    '选择默认工作目录',
    'Writile 将在此目录中保存和打开 Markdown 文件',
    '您可以稍后在程序设置中修改此目录。',
    False, '');
  WorkDirPage.Add('');
  WorkDirPage.Values[0] := ExpandConstant('{userdocs}\Writile');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigFile: String;
  ConfigContent: String;
  WorkDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    ConfigFile := ExpandConstant('{app}\config.ini');
    WorkDir := WorkDirPage.Values[0];
    if WorkDir = '' then
      WorkDir := ExpandConstant('{userdocs}\Writile');
    // 确保目录存在
    CreateDir(WorkDir);
    // 写入 config.ini
    ConfigContent := '[settings]' + #13#10 + 'default_workdir=' + WorkDir + #13#10;
    SaveStringToFile(ConfigFile, ConfigContent, False);
  end;
end;

function InitializeUninstall(): Boolean;
begin
    Result := True;
end;

// 卸载完成后询问是否删除用户数据
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
    ResultCode: Integer;
    UserDataDir: String;
begin
    if CurUninstallStep = usPostUninstall then
    begin
        UserDataDir := ExpandConstant('{userdocs}\Writile');
        if DirExists(UserDataDir) then
        begin
            if MsgBox('是否删除用户数据（包括自定义主题和设置）？' + #13#10 + '目录: ' + UserDataDir,
                      mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
            begin
                DelTree(UserDataDir, True, True, True);
            end;
        end;
    end;
end;
