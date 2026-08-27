# Writile 功能与 Bug 清单

> 基于 `md_editor.py`（5315 行）全量代码审查，2026-08-17

---

## 一、功能总览

### 1. 文件操作

| 功能 | 快捷键 | 说明 |
|------|--------|------|
| 新建文件 | Ctrl+N | 清空编辑器，开始新文档 |
| 打开文件 | Ctrl+O | 文件选择对话框，支持 .md/.markdown/.txt |
| 快速打开 | Ctrl+P | 模糊搜索当前文件夹内的文件 |
| 最近打开 | — | 菜单列出最近打开过的文件，点击直接打开 |
| 保存 | Ctrl+S | 保存到当前路径；未命名则弹出另存为 |
| 另存为 | Ctrl+Shift+S | 选择新路径保存 |
| 打开文件夹 | — | 设置当前工作文件夹（侧边栏文件树来源） |
| 在资源管理器中打开 | — | 打开当前文件所在目录 |
| 导出 HTML | — | 将内容渲染为完整 HTML 文件导出 |
| 导出 PDF | — | 通过 QWebEngine 打印功能导出 PDF |
| 退出 | Ctrl+Q | 关闭应用 |
| 启动时恢复上次文件 | — | 设置项，开启后自动打开上次编辑的文件 |

### 2. 编辑模式

| 模式 | 说明 |
|------|------|
| 所见即所得（WYSIWYG） | Typora 风格：块级即时渲染，点击段落进入源码编辑 |
| 源码模式 | 显示原始 Markdown 文本，纯文本编辑 |
| 分栏模式 | 左侧源码 + 右侧预览，各用独立 EditorWidget |
| 预览模式 | 只读渲染预览，不可编辑 |

### 3. 格式插入

| 功能 | 快捷键 | 语法 |
|------|--------|------|
| 粗体 | Ctrl+B | `**文本**` |
| 斜体 | Ctrl+I | `*文本*` |
| 行内代码 | Ctrl+\` | `` `文本` `` |
| 删除线 | — | `~~文本~~` |
| 高亮 | — | `==文本==` |
| 标题 1/2/3 | Ctrl+1/2/3 | `# / ## / ###` |
| 插入图片 | Ctrl+Shift+I | 选择图片文件，自动复制到文档目录并插入 |

### 4. 编辑操作

| 功能 | 快捷键 |
|------|--------|
| 查找 | Ctrl+F |
| 切换源码模式 | Ctrl+/ |
| 全选 | Ctrl+A |
| 复制 | Ctrl+C |
| 剪切 | Ctrl+X |
| 粘贴 | Ctrl+V |

### 5. 视图功能

| 功能 | 快捷键 | 说明 |
|------|--------|------|
| 切换侧边栏 | Ctrl+\ | 显示/隐藏整个侧边栏 |
| 显示文件列表 | — | 侧边栏上半部分，树形文件列表 |
| 显示大纲 | — | 侧边栏下半部分，标题层级大纲 |
| 专注模式 | F8 | 淡化非焦点段落，突出当前编辑位置 |
| 打字机模式 | F9 | 当前行始终保持在屏幕中央区域 |
| 预览模式 | Ctrl+E | 切换只读预览 |

### 6. 主题系统

| 功能 | 说明 |
|------|------|
| 8 种预设主题 | 浅色、深色、护眼黄、Solarized Dark、Dracula、Nord、One Dark、GitHub |
| 浅色/深色一键切换 | 工具栏按钮，在浅色与深色间快速切换 |
| 自定义主题编辑器 | 可视化调整所有颜色（背景、前景、代码块、链接、边框等） |
| 导出/导入主题 | JSON 格式主题文件导入导出 |
| 编辑器字体选择 | 字体对话框选择字体和大小 |

### 7. Markdown 渲染能力

| 元素 | 说明 |
|------|------|
| 标题 | h1-h6，即时渲染 |
| 段落 | 空行分段，行内格式即时渲染 |
| 列表 | 有序/无序列表，支持嵌套 |
| 引用 | `>` 块引用 |
| 代码块 | 围栏代码块（```），支持语法高亮（highlight.js） |
| 表格 | GFM 风格表格 |
| 图片 | 支持本地图片，相对路径解析 |
| 分割线 | `---` / `***` / `___` |
| HTML 围栏块 | `\|\|\|` 开始和结束，中间直接渲染 HTML |
| Mermaid 图表 | ```mermaid 代码块，异步加载 mermaid.js 渲染 |
| 原始 HTML 块 | 直接以 HTML 标签开头的段落 |

### 8. 其他功能

| 功能 | 说明 |
|------|------|
| 自动保存 | 修改后 2 秒自动保存到当前路径 |
| 字数统计 | 状态栏实时显示字数/字符数/行数 |
| 大纲导航 | 点击大纲中的标题跳转到对应位置 |
| 文件树右键菜单 | 新建文件、删除文件 |
| 自定义快捷键 | 所有菜单快捷键可通过对话框自定义 |
| 窗口状态记忆 | 关闭时保存主题/模式等状态，下次启动恢复 |
| 粘贴图片自动保存 | 粘贴剪贴板图片自动保存到文档目录 |
| Ctrl+点击链接 | 在系统默认浏览器中打开 |

---

## 二、已知 Bug

### 🔴 严重（影响核心功能）

#### Bug-01：分栏模式下多个操作仍直接访问 `self.editor`

**影响范围**：查找、全选、复制、剪切、粘贴、切换源码模式、预览模式、新建文件、打开文件、字数统计、标题更新、默认保存路径

**现象**：在分栏模式下，这些操作作用于已隐藏的主编辑器而非分栏左侧的活跃编辑器，导致操作无效或崩溃。

**涉及方法**（均直接使用 `self.editor` 而非 `self._active_editor()`）：

| 方法 | 行号 | 问题 |
|------|------|------|
| `find_text` | 4432 | `self.editor.run_js(...)` |
| `toggle_source_mode` | 4435 | `self.editor.toggle_source_mode()` |
| `select_all` | 4441 | `self.editor.web_view.page().triggerAction(...)` |
| `copy_selection` | 4449 | 同上 |
| `cut_selection` | 4457 | 同上 |
| `paste_clipboard` | 4465 | 同上 |
| `toggle_preview_mode` | 4512, 4519 | `self.editor.run_js(...)` + `self.editor.web_view.page().runJavaScript(...)` |
| `new_file` | 3919 | `self.editor.new_blank()` |
| `load_file` | 3943 | `self.editor.load_file(path)` |
| `update_title` | 5128 | `self.editor.file_path` |
| `update_word_count` | 5140 | `self.editor.get_word_count_async(...)` |
| `_get_default_save_path` | 3830 | `self.editor.file_path` |
| `open_file` | 3927 | `self.editor.file_path` |

**修复方案**：将这些方法中的 `self.editor` 替换为 `self._active_editor()`。对于 `new_file`/`load_file` 等文件级操作，在分栏模式下应先退出分栏再执行。

---

#### Bug-02：`set_editor_mode` 在分栏模式下操作错误编辑器

**行号**：4534-4541

**现象**：从分栏模式切换到源码/编辑/预览模式时，先退出分栏（正确），但随后对 `self.editor` 执行模式切换。如果 `self.editor` 的内容不是最新的（编辑在 `source_editor` 中进行），模式切换会作用于旧内容。

**修复方案**：退出分栏后，应先将 `source_editor` 的最新内容同步回 `self.editor`，再执行模式切换。

---

### 🟡 中等（功能异常但不崩溃）

#### Bug-03：`_current_mode()` 无法区分预览模式

**行号**：3910-3914

**现象**：`_current_mode()` 只检查是否在分栏模式，否则一律返回 `'wysiwyg'`。当实际处于预览模式时返回错误值。

**修复方案**：通过 JS 查询 `window.editorAPI.isPreviewMode()` 来判断。

---

#### Bug-04：`_on_mode_combo_changed` 信号抑制逻辑顺序错误

**行号**：3879-3886

**现象**：`_suppress_combo_signal` 检查在 `set_editor_mode` 调用之后，不起作用。`set_editor_mode` 内部会调用 `_sync_mode_combo`，后者已经做了 `blockSignals`，但外部的冗余检查反而可能在特定时序下引发问题。

**修复方案**：将 `_suppress_combo_signal` 检查移到 `set_editor_mode` 调用之前，或删除冗余检查（因为 `blockSignals` 已经处理了）。

---

#### Bug-05：分栏模式退出时内容可能丢失

**现象**：在分栏模式中编辑后，直接通过下拉框切换到写作/源码/预览模式，`_exit_split_mode` 被调用，`source_editor` 被销毁。如果用户未手动保存，`source_editor` 中未保存的编辑内容会丢失（主 `editor` 中仍是进入分栏前的旧内容）。

**修复方案**：退出分栏前，先从 `source_editor` 获取最新内容，同步回 `self.editor`，再销毁分栏组件。

---

#### Bug-06：`new_file` 在分栏模式下行为异常

**行号**：3917-3923

**现象**：分栏模式下点新建文件，直接操作 `self.editor`（已隐藏），分栏仍然显示，UI 状态不一致。

**修复方案**：新建文件前检查是否在分栏模式，若是则先退出分栏。

---

#### Bug-07：`load_file` 在分栏模式下行为异常

**行号**：3936-3958

**现象**：同 Bug-06，分栏模式下打开新文件直接加载到隐藏的主编辑器，分栏内容不更新。

**修复方案**：同 Bug-06，先退出分栏再加载。

---

### 🟢 轻微（体验问题）

#### Bug-08：分栏模式每次进入都重建 WebEngine 组件

**行号**：4507-4533

**现象**：每次进入分栏模式都创建两个新的 `EditorWidget`（含 WebEngine 页面加载），有约 0.5-1 秒的白屏等待期。频繁切换分栏模式会导致明显的性能开销。

**可能的优化**：缓存分栏组件，退出时仅隐藏不销毁。但需注意 WebEngine 状态同步问题。

---

#### Bug-09：`closeEvent` 未保存分栏模式状态

**行号**：5189-5194

**现象**：关闭应用时不保存当前是否处于分栏模式。下次启动时总是以普通模式打开。

**影响**：较小，因为分栏模式通常不需要持久化。

---

#### Bug-10：文件列表右键删除无确认对话框

**行号**：4355

**现象**：`_delete_filelist_file` 直接删除文件，没有二次确认。误操作风险高。

**修复方案**：删除前弹出 `QMessageBox.question` 确认。

---

#### Bug-11：`highlight.js` 为 stub 实现

**行号**：525

**现象**：内嵌的 `highlight.js` 是一个 stub（空实现），`highlight` 和 `highlightAuto` 方法直接返回原文不做高亮。代码块语法高亮实际依赖自定义的 `highlightCode()` 函数（关键字正则匹配），而非真正的 highlight.js。

**影响**：代码高亮仅支持有限语言（通过自定义正则），不如完整 highlight.js 丰富。

---

#### Bug-12：`find_text` 功能简陋

**行号**：4430-4432

**现象**：查找功能仅调用 `window.find('')`，传入空字符串。没有查找对话框、没有查找/替换、没有高亮匹配项。

---

## 三、已修复的问题（本轮会话）

| 问题 | 修复内容 |
|------|----------|
| `hasCompleteHtmlFence` 正则被破坏 | `\n` 转义被展开为真换行，导致 JS 语法错误，整个 script 块失败 |
| `marked.js` 压缩代码被破坏 | 3079 字符单行被拆成 21 行，所有 `\n` 转义被展开 |
| 分栏模式不显示 | `_exit_split_mode` 使用 `deleteLater` 导致时序问题 + `set_content` 在页面未就绪时调用 |
| `setCentralWidget` 导致 C++ 对象被销毁 | 添加 `setParent(self)` 脱离所有权 |
| 分栏模式保存闪退 | 添加 `_active_editor()` 辅助方法，保存操作感知分栏状态 |
| `|||` HTML 围栏不渲染 | 根因是 `hasCompleteHtmlFence` 正则破坏导致整个 JS 块失败 |

---

## 四、架构概览

```
md_editor.py (单文件应用)
├── PRESET_THEMES          # 8 种预设主题定义
├── EDITOR_HTML            # r"""...""" 包含完整 HTML/CSS/JS 编辑器
│   ├── CSS 样式            # 编辑器、主题、专注模式、打字机模式等
│   ├── marked.js (minified) # Markdown 解析库 (v4.3.0)
│   ├── highlight.js (stub)  # 代码高亮 (stub，实际用自定义 highlightCode)
│   ├── Mermaid 按需加载     # 图表渲染
│   └── editorAPI           # JS 端公开接口
│       ├── setContent / getContent
│       ├── enterEditMode / enterPreviewMode
│       ├── toggleSourceMode
│       ├── render / renderMarkdown
│       └── setDarkMode / setFocusMode / setTypewriterMode
├── EditorWebView           # QWebEngineView 子类（拦截新窗口）
├── EditorPage              # QWebEnginePage 子类（日志、导航拦截）
├── EditorBridge            # QObject（JS↔Python 通信桥接）
├── EditorWidget            # 编辑器组件（WebEngine + WebChannel）
│   ├── set_content / get_content / save_file
│   ├── load_file / new_blank
│   ├── export_html / _py_markdown_to_html
│   └── _page_ready + _pending_content 机制
├── RecentFilesDialog       # 启动时最近文件选择对话框
├── QuickOpenDialog         # Ctrl+P 快速打开对话框
├── ThemeEditorDialog       # 自定义主题颜色编辑器
├── ShortcutCustomizerDialog # 快捷键自定义对话框
└── MainWindow              # 主窗口
    ├── 菜单栏（文件/编辑/格式/视图/设置/帮助）
    ├── 工具栏（专注/打字机/主题切换）
    ├── 侧边栏（文件树 + 大纲）
    ├── 编辑器区域（单编辑器 / 分栏）
    └── 状态栏（字数统计 + 模式下拉框）
```
