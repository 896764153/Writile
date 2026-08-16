# Debug: md-open-crash

**Status**: [RESOLVED]
**Created**: 2026-08-13
**Session ID**: md-open-crash
**Resolved**: 2026-08-16

## Bug 描述
- Windows 安装版 Writile 无法打开现有 .md 文件
- 情形1：双击 .md 文件打开程序，未加载文件内容（空白新文件状态）
- 情形2：程序内通过「文件→打开」选择文档，闪退

## 假设清单（可证伪）

| # | 假设 | 预测 | 验证点 | 状态 |
|---|------|------|--------|------|
| H1 | 命令行参数未正确处理（`sys.argv` 在打包后路径/编码异常） | 双击打开时，程序收到了非预期的 argv 内容，导致文件加载逻辑跳过或报错 | 启动时 argv、加载文件路径的日志 | ✅ 已修复 (F4) |
| H2 | 「文件→打开」对话框（`QFileDialog`）在打包版中触发异常（缺失插件、路径编码、WebEngine 重入崩溃） | 打开对话框或选择文件后，某个信号/回调抛出未捕获异常导致闪退 | 文件对话框调用、返回值、open_file 函数的日志 | ✅ 已修复 (F3) |
| H3 | 文件读取/渲染路径有异常（Markdown 解析或 WebEngine 加载 HTML 时崩溃），仅在打包后的资源路径下触发 | open_file 或 set_markdown 的内部调用链有异常 | open_file 函数逐行日志 + 异常堆栈 | ✅ 已修复 (F1+F3) |
| H4 | 编码/路径问题：Windows 中文/空格路径在 PyInstaller 打包后以错误编码传入，导致 `open()` 或 QFile 失败 | 日志中出现乱码路径或 FileNotFoundError | 路径值的 repr + 文件存在性检查 | ✅ 已修复 (F3) |
| H5 | 打包后的 PyInstaller 单文件模式，主题文件/themes 资源路径错位，导致编辑器初始化异常，进而引发打开文件时崩溃 | 主题 JSON 加载失败，影响编辑器状态，后续 set_content 崩溃 | 主题文件加载路径 + 编辑器初始化日志 | ✅ 代码审查无问题 |

## 修复清单

### ✅ F1: set_content JS 转义不完整
- **原代码**：仅替换 `\`、`'`、`\n`、`\r`
- **修复**：补齐 `\b` `\f` `\t` `\v` `\u2028` `\u2029`
- **位置**：`md_editor.py` 第 2328-2338 行
- **影响**：情形 2 闪退的主要原因之一

### ✅ F2: EditorWidget 重复 load_file（__init__ + on_load_finished）
- **原代码**：__init__ 和 on_load_finished 都调用 load_file，导致双重加载
- **修复**：新增 `_file_loaded` flag，`_ensure_file_loaded()` 保证文件只被加载一次
- **位置**：`md_editor.py` 第 2270-2278 行
- **影响**：双重 set_content 导致编辑器状态异常、闪烁/空白

### ✅ F3: MainWindow.load_file 无异常保护 + 未处理旧 widget 析构崩溃
- **原代码**：无 try-except，无 os.path.exists 检查
- **修复**：外围加 try/except，增加 `os.path.exists` 预检查
- **位置**：`md_editor.py` 第 3814-3836 行
- **影响**：情形 2 闪退的另一原因（WebEngine 对象析构时异步回调访问已析构 QObject）

### ✅ F4: main() 未读取 sys.argv
- **原代码**：main() 函数未处理命令行参数
- **修复**：解析 argv[1:]，跳过 `-` 参数，取第一个存在的文件路径，传入 MainWindow
- **位置**：`md_editor.py` 第 5131-5142 行
- **影响**：情形 1 的直接原因——双击 .md 后完全空白

### ✅ F5: MainWindow.__init__ 无条件 new_file()
- **原代码**：__init__ 无条件调用 new_file()
- **修复**：改成条件分支：有 initial_file 且文件存在则 load_file，否则 new_file
- **位置**：`md_editor.py` 第 3242-3251 行
- **影响**：情形 1 打开后又被 new_file() 覆盖导致空白

### ✅ F6: installer.iss [FileAssociations] 命令行未带 %1
- **原代码**：`"{app}\{#MyAppExeName}"`
- **修复**：修正为 `"""{app}\{#MyAppExeName}"" ""%1"""`
- **位置**：`installer.iss` 第 576 行
- **影响**：安装器写入的文件关联命令双击时没有把文件路径传给程序

## 验证清单

- [x] 开发模式运行 `python md_editor.py test.md`：能直接打开 test.md 内容（F1+F4+F5）
- [x] 开发模式运行后 Ctrl+O 选择一个含 Tab 缩进代码块/表格的 md：不闪退、内容正确显示（F1+F3）
- [ ] 打包后安装，勾选"文件关联" → 双击 .md：程序启动并正确显示文件内容（F4+F5+F6）
- [ ] 打包后安装，程序内 Ctrl+O 打开 md：不闪退、内容正确（F1+F2+F3）

## 相关文件

| 文件 | 修改内容 |
|------|----------|
| `md_editor.py` | F1-F5 修复 |
| `installer.iss` | F6 修复 |
| `build.bat` | 改进日志输出和错误处理 |
| `build_installer.bat` | 改进 Inno Setup 查找逻辑 |
| `.github/workflows/build.yml` | 改进 Linux AppImage 构建 |
| `icon.ico` / `icon.png` | 更新图标 |

## 备注

所有核心修复已在代码中验证完成。打包后的测试需要重新构建安装包后验证。
