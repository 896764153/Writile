# -*- coding: utf-8 -*-
"""
Typora 风格 Markdown 编辑器
核心特点：所见即所得、即时渲染、不分屏、专注模式、打字机模式
"""

import os
import sys
import json
import configparser

# 必须在导入 QtWebEngine 之前设置。直接 import editor_common 时也能生效。
if "QTWEBENGINE_CHROMIUM_FLAGS" not in os.environ:
    _flags = [
        "--disable-gpu",
        "--disable-gpu-compositing",
        "--ignore-gpu-blocklist",
        "--in-process-gpu",
        "--disable-dev-shm-usage",
    ]
    if sys.platform.startswith("linux"):
        _flags.extend(["--no-sandbox", "--no-zygote"])
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(_flags)
os.environ.setdefault("QT_OPENGL", "software")

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QFileDialog, QMessageBox, QStatusBar, QToolBar, QSplitter,
    QListWidget, QListWidgetItem, QButtonGroup,
    QTreeWidget, QTreeWidgetItem,
    QDockWidget, QLineEdit, QPushButton, QLabel, QInputDialog,
    QMenu, QDialog, QColorDialog, QFontDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QSpinBox, QGroupBox,
    QGridLayout, QScrollArea, QFrame, QKeySequenceEdit, QComboBox
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QUrl, QSettings, pyqtSlot, pyqtSignal, QObject, QStandardPaths
)
from PyQt6.QtGui import (
    QAction, QActionGroup, QIcon, QFont, QKeySequence, QShortcut, QColor,
    QDesktopServices
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineSettings, QWebEngineProfile
)
from PyQt6.QtWebChannel import QWebChannel


# ============================================================
# 预设主题
# ============================================================

PRESET_THEMES = {
    "light": {
        "name": "浅色",
        "is_dark": False,
        "colors": {
            "bg": "#ffffff",
            "fg": "#1a1a1a",
            "muted": "#6a737d",
            "code_bg": "#f6f8fa",
            "border": "#e1e4e8",
            "link": "#0366d6",
            "accent": "#4caf50",
            "selection": "#cce5ff",
            "current_line": "#fffbea",
            "typewriter_line": "#fff8dc",
        },
        "ui_bg": "#ffffff",
        "ui_fg": "#333333",
        "ui_alt": "#f0f0f0",
        "ui_selection": "#cbe5ff",
    },
    "dark": {
        "name": "深色",
        "is_dark": True,
        "colors": {
            "bg": "#1e1e1e",
            "fg": "#d4d4d4",
            "muted": "#8b949e",
            "code_bg": "#2d2d30",
            "border": "#3c3c3c",
            "link": "#58a6ff",
            "accent": "#4caf50",
            "selection": "#264f78",
            "current_line": "#3a3a1f",
            "typewriter_line": "#3b3520",
        },
        "ui_bg": "#1e1e1e",
        "ui_fg": "#cccccc",
        "ui_alt": "#2d2d30",
        "ui_selection": "#094771",
    },
    "sepia": {
        "name": "护眼黄",
        "is_dark": False,
        "colors": {
            "bg": "#f8f1e3",
            "fg": "#3d3225",
            "muted": "#8a7860",
            "code_bg": "#efe6d3",
            "border": "#d8c9a8",
            "link": "#8b5a2b",
            "accent": "#a0784a",
            "selection": "#e8d8a8",
            "current_line": "#f5e8c8",
            "typewriter_line": "#f0dfb0",
        },
        "ui_bg": "#f8f1e3",
        "ui_fg": "#3d3225",
        "ui_alt": "#efe6d3",
        "ui_selection": "#e8d8a8",
    },
    "solarized_dark": {
        "name": "Solarized Dark",
        "is_dark": True,
        "colors": {
            "bg": "#002b36",
            "fg": "#839496",
            "muted": "#586e75",
            "code_bg": "#073642",
            "border": "#073642",
            "link": "#268bd2",
            "accent": "#2aa198",
            "selection": "#073642",
            "current_line": "#073642",
            "typewriter_line": "#09485a",
        },
        "ui_bg": "#002b36",
        "ui_fg": "#93a1a1",
        "ui_alt": "#073642",
        "ui_selection": "#073642",
    },
    "dracula": {
        "name": "Dracula",
        "is_dark": True,
        "colors": {
            "bg": "#282a36",
            "fg": "#f8f8f2",
            "muted": "#6272a4",
            "code_bg": "#44475a",
            "border": "#44475a",
            "link": "#bd93f9",
            "accent": "#50fa7b",
            "selection": "#44475a",
            "current_line": "#44475a",
            "typewriter_line": "#3a3d4a",
        },
        "ui_bg": "#282a36",
        "ui_fg": "#f8f8f2",
        "ui_alt": "#44475a",
        "ui_selection": "#44475a",
    },
    "nord": {
        "name": "Nord",
        "is_dark": True,
        "colors": {
            "bg": "#2e3440",
            "fg": "#d8dee9",
            "muted": "#616e88",
            "code_bg": "#3b4252",
            "border": "#434c5e",
            "link": "#88c0d0",
            "accent": "#88c0d0",
            "selection": "#434c5e",
            "current_line": "#3b4252",
            "typewriter_line": "#434c5e",
        },
        "ui_bg": "#2e3440",
        "ui_fg": "#d8dee9",
        "ui_alt": "#3b4252",
        "ui_selection": "#434c5e",
    },
    "one_dark": {
        "name": "One Dark",
        "is_dark": True,
        "colors": {
            "bg": "#282c34",
            "fg": "#abb2bf",
            "muted": "#5c6370",
            "code_bg": "#21252b",
            "border": "#21252b",
            "link": "#61afef",
            "accent": "#98c379",
            "selection": "#3d4350",
            "current_line": "#2c313c",
            "typewriter_line": "#323842",
        },
        "ui_bg": "#282c34",
        "ui_fg": "#abb2bf",
        "ui_alt": "#21252b",
        "ui_selection": "#3d4350",
    },
    "github": {
        "name": "GitHub",
        "is_dark": False,
        "colors": {
            "bg": "#ffffff",
            "fg": "#24292e",
            "muted": "#6a737d",
            "code_bg": "#f6f8fa",
            "border": "#e1e4e8",
            "link": "#0366d6",
            "accent": "#28a745",
            "selection": "#f1f8ff",
            "current_line": "#fff8dc",
            "typewriter_line": "#fffacd",
        },
        "ui_bg": "#ffffff",
        "ui_fg": "#24292e",
        "ui_alt": "#f6f8fa",
        "ui_selection": "#f1f8ff",
    },
}


# ============================================================
# 编辑器 HTML/JS/CSS 模板
# ============================================================

EDITOR_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Editor</title>
<style>
:root {
    --bg: #ffffff;
    --fg: #24292f;
    --muted: #656d76;
    --code-bg: #f6f8fa;
    --code-inline-bg: #eff1f3;
    --border: #d0d7de;
    --border-light: #eaeef2;
    --link: #0969da;
    --accent: #1f883d;
    --accent-light: #dafbe1;
    --selection: #b6d4fe;
    --current-line: #fffbea;
    --typewriter-line: #fff8dc;
    --quote-border: #d0d7de;
    --quote-bg: #f6f8fa;
    --table-header-bg: #f6f8fa;
    --table-stripe-bg: #f6f8fa;
    --code-header-bg: #eaeef2;
}

html.dark {
    --bg: #0d1117;
    --fg: #e6edf3;
    --muted: #8b949e;
    --code-bg: #161b22;
    --code-inline-bg: #21262d;
    --border: #30363d;
    --border-light: #21262d;
    --link: #58a6ff;
    --accent: #3fb950;
    --accent-light: #1f6f3f;
    --selection: #264f78;
    --current-line: #3a3a1f;
    --typewriter-line: #3b3520;
    --quote-border: #30363d;
    --quote-bg: #161b22;
    --table-header-bg: #161b22;
    --table-stripe-bg: #161b22;
    --code-header-bg: #21262d;
}

* { box-sizing: border-box; }
html, body {
    margin: 0;
    padding: 0;
    height: 100%;
    overflow: hidden;
}
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
                 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    font-size: 16px;
    line-height: 1.7;
    color: var(--fg);
    background: var(--bg);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

#editor {
    max-width: 820px;
    margin: 0 auto;
    padding: 32px 48px 140px 48px;
    min-height: 100%;
    outline: none;
    overflow-y: auto;
    height: 100vh;
    scroll-behavior: smooth;
}

#editor:focus { outline: none; }

#editor[data-mode="source"] {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    white-space: pre-wrap;
    word-wrap: break-word;
    line-height: 1.6;
}

/* 块级源码模式：光标所在块显示 markdown 源码（Typora 风格卡片） */
#editor [data-source-mode] {
    /* 保持正文排版（不切等宽字体），编辑时更接近最终效果 */
    white-space: pre-wrap;
    word-wrap: break-word;
    background: var(--code-inline-bg);
    border-radius: 8px;
    padding: 4px 14px;
    box-shadow: 0 0 0 1px var(--border-light);
    caret-color: var(--accent);
    outline: none;
    transition: background 0.2s ease, box-shadow 0.2s ease;
}

/* 代码块处于编辑态：等宽字体、独立纯文本编辑区（避免光标乱跳） */
#editor [data-source-mode][data-md="code"] {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    white-space: pre-wrap;
    word-wrap: break-word;
    background: var(--code-bg);
    border-radius: 8px;
    padding: 16px 20px;
    box-shadow: 0 0 0 1px var(--border-light);
    line-height: 1.55;
}

/* 标题 */
h1 { font-size: 2em; font-weight: 700; border-bottom: 1px solid var(--border-light); padding-bottom: .4em; margin: 1em 0 .5em; letter-spacing: -0.01em; }
h2 { font-size: 1.5em; font-weight: 700; border-bottom: 1px solid var(--border-light); padding-bottom: .3em; margin: 1em 0 .4em; letter-spacing: -0.01em; }
h3 { font-size: 1.25em; font-weight: 600; margin: .9em 0 .4em; }
h4 { font-size: 1em; font-weight: 600; margin: .9em 0 .35em; }
h5 { font-size: .875em; font-weight: 600; margin: .9em 0 .35em; color: var(--muted); }
h6 { font-size: .85em; font-weight: 600; margin: .9em 0 .35em; color: var(--muted); }

p { margin: 0 0 12px 0; }
.empty-line { margin: 0 0 12px 0; min-height: 1em; }
a { color: var(--link); text-decoration: none; transition: opacity 0.15s; }
a:hover { text-decoration: underline; opacity: 0.85; }
strong { font-weight: 600; }
em { font-style: italic; }
del { text-decoration: line-through; color: var(--muted); }

blockquote {
    padding: 10px 16px;
    color: var(--muted);
    border-left: 4px solid var(--accent);
    background: var(--quote-bg);
    border-radius: 0 6px 6px 0;
    margin: 14px 0;
}

ul, ol { padding-left: 2em; margin: 10px 0; }
li { margin: 3px 0; line-height: 1.65; }
li > ul, li > ol { margin: 3px 0; }

code {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 0.88em;
    background: var(--code-inline-bg);
    padding: .18em .45em;
    border-radius: 6px;
    color: var(--fg);
    border: 1px solid var(--border-light);
}

pre {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 0.88em;
    background: var(--code-bg);
    border-radius: 10px;
    padding: 16px 18px;
    overflow: auto;
    line-height: 1.55;
    margin: 14px 0;
    border: 1px solid var(--border-light);
}
pre code { background: none; padding: 0; font-size: 100%; border: none; }

table {
    border-collapse: collapse;
    margin: 14px 0;
    width: 100%;
    font-size: 0.95em;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border);
}
th, td {
    border: 1px solid var(--border-light);
    padding: 10px 16px;
    text-align: left;
}
th { background: var(--table-header-bg); font-weight: 600; }
tr:nth-child(2n) { background: var(--table-stripe-bg); }
tr:hover { background: var(--accent-light); }

img { max-width: 100%; border-radius: 6px; cursor: pointer; }
img:hover { outline: 2px solid var(--accent); outline-offset: 2px; }
hr { border: none; border-top: 1px solid var(--border-light); margin: 20px 0; }
mark { background: #fff3a0; padding: 1px 4px; border-radius: 3px; }

kbd {
    display: inline-block;
    padding: 2px 6px;
    font-size: 11px;
    color: var(--muted);
    background-color: var(--code-bg);
    border: 1px solid var(--border);
    border-bottom-width: 2px;
    border-radius: 4px;
    font-family: 'SFMono-Regular', Consolas, monospace;
}

.task-list-item { list-style-type: none; }
.task-list-item input { margin: 0 .5em .25em -1.4em; }

/* 代码高亮 */
.hljs { display: block; overflow-x: auto; padding: 0; background: transparent; }
.hljs-comment, .hljs-quote { color: #998; font-style: italic; }
.hljs-keyword, .hljs-selector-tag, .hljs-subst { color: #333; font-weight: 600; }
.hljs-number, .hljs-literal, .hljs-variable, .hljs-template-variable, .hljs-tag .hljs-attr { color: #008080; }
.hljs-string, .hljs-doctag { color: #d14; }
.hljs-title, .hljs-section, .hljs-selector-id { color: #900; font-weight: 600; }
.hljs-type, .hljs-class .hljs-title, .hljs-type .hljs-title { color: #458; font-weight: 600; }
.hljs-tag, .hljs-name, .hljs-attribute { color: navy; font-weight: normal; }
.hljs-regexp, .hljs-link { color: #009926; }
.hljs-symbol, .hljs-bullet { color: #990073; }
.hljs-built_in, .hljs-builtin-name { color: #0086b3; }
.hljs-meta { color: #999; font-weight: 600; }
.hljs-deletion { background: #fdd; }
.hljs-addition { background: #dfd; }
.hljs-emphasis { font-style: italic; }
.hljs-strong { font-weight: 600; }

html.dark .hljs { color: #abb2bf; background: transparent; }
html.dark .hljs-comment, html.dark .hljs-quote { color: #7f848e; font-style: italic; }
html.dark .hljs-keyword, html.dark .hljs-selector-tag, html.dark .hljs-subst { color: #c678dd; }
html.dark .hljs-number, html.dark .hljs-literal, html.dark .hljs-variable { color: #d19a66; }
html.dark .hljs-string, html.dark .hljs-doctag { color: #98c379; }
html.dark .hljs-title, html.dark .hljs-section { color: #61afef; }
html.dark .hljs-type, html.dark .hljs-class .hljs-title { color: #e5c07b; }
html.dark .hljs-tag, html.dark .hljs-name { color: #e06c75; }
html.dark .hljs-attribute { color: #d19a66; }
html.dark .hljs-regexp, html.dark .hljs-link { color: #56b6c2; }
html.dark .hljs-symbol, html.dark .hljs-bullet { color: #56b6c2; }
html.dark .hljs-built_in, html.dark .hljs-builtin-name { color: #61afef; }
html.dark .hljs-meta { color: #7f848e; }

/* 专注模式：模糊非当前行 */
body.focus-mode #editor > * { opacity: 0.25; transition: opacity 0.3s ease; }
body.focus-mode #editor > .current-line { opacity: 1; }

/* 打字机模式：当前行高亮 */
body.typewriter-mode #editor > .current-line {
    background: var(--typewriter-line);
}

/* 占位符 */
#editor:empty::before {
    content: attr(data-placeholder);
    color: var(--muted);
    pointer-events: none;
    font-style: italic;
}

/* MathJax */
mjx-container { font-size: 1.1em !important; }

/* Mermaid */
.mermaid { text-align: center; margin: 20px 0; }

/* 原始 HTML 块 */
.html-block { margin: 20px 0; cursor: pointer; }
.html-block:hover { box-shadow: 0 0 0 2px var(--selection); border-radius: 6px; }

/* +++html 交互式 HTML 块 */
.interactive-html-block {
    position: relative;
    margin: 20px 0;
    border-radius: 8px;
    border: 1px solid transparent;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.interactive-html-block:hover {
    border-color: var(--border-light);
    box-shadow: 0 0 0 2px var(--selection);
}
.interactive-html-block iframe {
    width: 100%;
    border: none;
    border-radius: 8px;
    min-height: 60px;
    display: block;
    pointer-events: none;
}
.ihb-edit-hint {
    position: absolute;
    bottom: 6px;
    right: 10px;
    font-size: 12px;
    color: var(--muted);
    opacity: 0;
    transition: opacity 0.2s;
    pointer-events: none;
    background: var(--bg);
    padding: 2px 8px;
    border-radius: 4px;
}
.interactive-html-block:hover .ihb-edit-hint { opacity: 0.7; }
.interactive-html-block.editing { border-color: var(--accent); }
.interactive-html-block.editing iframe { display: none; }
.interactive-html-block.editing .ihb-edit-hint { display: none; }
.interactive-html-block .ihb-edit-area { display: none; }
.interactive-html-block.editing .ihb-edit-area { display: block; }
.interactive-html-block .ihb-toolbar { display: none; }
.interactive-html-block.editing .ihb-toolbar { display: flex; }
.ihb-edit-area textarea {
    width: 100%;
    min-height: 200px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 13px;
    line-height: 1.5;
    padding: 12px 16px;
    border: 1px solid var(--border);
    border-radius: 0 0 8px 8px;
    background: var(--code-bg);
    color: var(--fg);
    resize: vertical;
    outline: none;
    tab-size: 4;
}
.ihb-toolbar {
    display: flex;
    gap: 4px;
    padding: 4px 8px;
    background: var(--code-header-bg);
    border-radius: 8px 8px 0 0;
    border: 1px solid var(--border);
    border-bottom: none;
    align-items: center;
}
.ihb-toolbar button {
    padding: 3px 12px;
    font-size: 12px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--bg);
    color: var(--fg);
    cursor: pointer;
}
.ihb-toolbar button:hover { background: var(--code-bg); }
.ihb-toolbar .ihb-btn-primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.ihb-toolbar .ihb-script-warn {
    margin-left: auto;
    color: #d97706;
    font-size: 12px;
    cursor: pointer;
}
#editor.preview-mode .interactive-html-block:hover {
    border-color: transparent;
    box-shadow: none;
}
#editor.preview-mode .ihb-edit-hint { display: none !important; }

/* 拖拽提示 */
.drag-over { background: var(--selection) !important; }

/* 滚动条 */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; transition: background 0.2s; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* 选区 */
::selection { background: var(--selection); }
::-moz-selection { background: var(--selection); }

/* 预览模式样式 - 只读阅读 */
#editor.preview-mode {
    cursor: default;
}
#editor.preview-mode [data-source-mode] {
    /* 预览模式下不显示源码模式标记 */
    white-space: normal;
    word-wrap: normal;
}
#editor.preview-mode p,
#editor.preview-mode h1,
#editor.preview-mode h2,
#editor.preview-mode h3,
#editor.preview-mode h4,
#editor.preview-mode h5,
#editor.preview-mode h6,
#editor.preview-mode li,
#editor.preview-mode blockquote {
    /* 预览模式下段落/标题等块元素不可编辑 */
    cursor: default;
}
#editor.preview-mode a:hover {
    opacity: 0.7;
}
/* === 自动补全下拉菜单 === */
.autocomplete-dropdown {
    position: fixed;
    z-index: 10000;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    max-height: 240px;
    overflow-y: auto;
    min-width: 200px;
    font-size: 14px;
    padding: 4px 0;
}
.autocomplete-item {
    padding: 6px 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
}
.autocomplete-item:hover,
.autocomplete-item.active {
    background: var(--accent-light);
    color: var(--accent);
}
.autocomplete-item .ac-icon {
    width: 20px;
    text-align: center;
    font-size: 13px;
    opacity: 0.7;
}
.autocomplete-item .ac-label {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.autocomplete-item .ac-desc {
    font-size: 12px;
    color: var(--muted);
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
/* === 查找匹配高亮（Bug-12）=== */
mark.find-match {
    background-color: #fff3a0;
    color: inherit;
    padding: 0;
    border-radius: 2px;
}
mark.find-match.find-current {
    background-color: #ff9800;
    color: #fff;
    font-weight: 600;
}
html.dark mark.find-match {
    background-color: #5a4500;
    color: inherit;
}
html.dark mark.find-match.find-current {
    background-color: #ff9800;
    color: #1e1e1e;
}

/* === CM6 源码编辑器主题 === */
#cm-source-container {
    display: none;
    height: 100vh;
    width: 100%;
}
#cm-source-container.active {
    display: block;
}
#cm-source-container .cm-editor {
    height: 100%;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 15px;
    line-height: 1.6;
    color: var(--fg);
    background: var(--bg);
}
#cm-source-container .cm-editor.cm-focused {
    outline: none;
}
#cm-source-container .cm-gutters {
    background: var(--bg);
    border-right: 1px solid var(--border-light);
    color: var(--muted);
}
#cm-source-container .cm-activeLineGutter {
    background: var(--current-line);
}
#cm-source-container .cm-activeLine {
    background: var(--current-line);
}
#cm-source-container .cm-cursor {
    border-left-color: var(--accent);
}
#cm-source-container .cm-selectionBackground {
    background: var(--selection) !important;
}
#cm-source-container .cm-foldGutter .cm-foldMarker {
    color: var(--muted);
}
</style>
</head>
<body>

<div id="editor" contenteditable="true" data-placeholder="开始写作... (Markdown 格式)"></div>
<div id="cm-source-container"></div>

<!-- CodeMirror 6 打包文件：lib/codemirror-bundle.js 由 build_cm6/build.js 生成
     （步骤：cd build_cm6 && npm install && npm run build）。
     该脚本加载失败不影响其它功能，onerror 让 CodeMirror6 显式置 undefined。 -->
<script src="lib/codemirror-bundle.js" onerror="window.CodeMirror6=undefined"></script>

<!-- Qt WebChannel JS API -->
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>

<!-- Highlight.js (代码高亮) - 占位符将在运行时替换为真实库 -->
<script>
/*! highlight.js v11.9.0 | BSD-3-Clause License | https://highlightjs.org */
__HIGHLIGHT_JS_PLACEHOLDER__
</script>

<!-- Mermaid 采用按需异步加载（避免阻塞页面初始化），见 renderAllMermaid() -->

<!-- 编辑器逻辑 -->
<script>
(function() {
    var editor = document.getElementById('editor');
    var isRendering = false;
    var renderTimer = null;
    var savedMarkdown = '';
    var savedCursor = null; // {blockIndex: n, charOffset: m}

    // ===== 自定义撤销/重做历史（避免 innerHTML 全量重渲染破坏浏览器原生 undo）=====
    var history = [];
    var historyIndex = -1;
    var nextBlockId = 1;

    function getBlockId() {
        return 'block-' + (nextBlockId++);
    }

    // === +++html 交互式 HTML 块 - 内置模板 ===
    var INTERACTIVE_HTML_TEMPLATES = {
        empty: '<div style="padding:16px;border:1px dashed #ccc;border-radius:8px;">\n  <p>\u5728\u6b64\u7f16\u8f91 HTML \u5185\u5bb9</p>\n</div>',
        dashboard: '<div style="padding:20px;background:#f0f4ff;border-radius:8px;">\n'
            + '  <h3 style="color:#2c3e50;">&#128202; \u6570\u636e\u770b\u677f</h3>\n'
            + '  <div style="display:flex;gap:16px;margin-top:12px;">\n'
            + '    <div style="flex:1;padding:16px;background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">\n'
            + '      <div style="font-size:24px;font-weight:700;color:#3498db;">75%</div>\n'
            + '      <div style="color:#666;font-size:13px;">\u5b8c\u6210\u8fdb\u5ea6</div>\n'
            + '      <progress value="75" max="100" style="width:100%;margin-top:8px;"></progress>\n'
            + '    </div>\n'
            + '  </div>\n'
            + '</div>',
        card: '<div style="max-width:360px;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">\n'
            + '  <div style="height:180px;background:#e8e8e8;display:flex;align-items:center;justify-content:center;color:#999;">\u56fe\u7247\u533a\u57df</div>\n'
            + '  <div style="padding:20px;">\n'
            + '    <h3 style="margin:0 0 8px;">\u5361\u7247\u6807\u9898</h3>\n'
            + '    <p style="color:#666;margin:0 0 16px;">\u8fd9\u91cc\u662f\u5361\u7247\u63cf\u8ff0\u5185\u5bb9</p>\n'
            + '    <button style="padding:8px 20px;background:#3498db;color:#fff;border:none;border-radius:6px;cursor:pointer;">\u4e86\u89e3\u66f4\u591a</button>\n'
            + '  </div>\n'
            + '</div>',
        chart: '<div style="padding:20px;border:1px solid #e0e0e0;border-radius:8px;text-align:center;">\n'
            + '  <div id="chart-container" style="width:100%;height:300px;display:flex;align-items:center;justify-content:center;color:#999;">\n'
            + '    \u56fe\u8868\u5bb9\u5668\uff08\u53ef\u96c6\u6210 ECharts\uff09\n'
            + '  </div>\n'
            + '</div>',
        buttons: '<div style="display:flex;gap:12px;flex-wrap:wrap;padding:16px;">\n'
            + '  <button style="padding:10px 24px;background:#3498db;color:#fff;border:none;border-radius:6px;font-size:14px;">\u4e3b\u8981\u6309\u94ae</button>\n'
            + '  <button style="padding:10px 24px;background:#2ecc71;color:#fff;border:none;border-radius:6px;font-size:14px;">\u6210\u529f\u6309\u94ae</button>\n'
            + '  <button style="padding:10px 24px;background:#e74c3c;color:#fff;border:none;border-radius:6px;font-size:14px;">\u5371\u9669\u6309\u94ae</button>\n'
            + '  <button style="padding:10px 24px;background:#fff;color:#333;border:1px solid #ddd;border-radius:6px;font-size:14px;">\u9ed8\u8ba4\u6309\u94ae</button>\n'
            + '</div>',
        form: '<form style="max-width:400px;padding:20px;border:1px solid #e0e0e0;border-radius:8px;">\n'
            + '  <div style="margin-bottom:16px;">\n'
            + '    <label style="display:block;margin-bottom:4px;font-weight:600;">\u59d3\u540d</label>\n'
            + '    <input type="text" style="width:100%;padding:8px 12px;border:1px solid #ddd;border-radius:4px;" placeholder="\u8bf7\u8f93\u5165\u59d3\u540d">\n'
            + '  </div>\n'
            + '  <div style="margin-bottom:16px;">\n'
            + '    <label style="display:block;margin-bottom:4px;font-weight:600;">\u9009\u9879</label>\n'
            + '    <select style="width:100%;padding:8px 12px;border:1px solid #ddd;border-radius:4px;">\n'
            + '      <option>\u9009\u9879\u4e00</option><option>\u9009\u9879\u4e8c</option>\n'
            + '    </select>\n'
            + '  </div>\n'
            + '  <button type="button" style="padding:10px 24px;background:#3498db;color:#fff;border:none;border-radius:6px;">\u63d0\u4ea4</button>\n'
            + '</form>',
        table: '<table style="width:100%;border-collapse:collapse;border:1px solid #ddd;">\n'
            + '  <thead>\n'
            + '    <tr style="background:#f6f8fa;">\n'
            + '      <th style="padding:10px 16px;border:1px solid #ddd;text-align:left;">\u540d\u79f0</th>\n'
            + '      <th style="padding:10px 16px;border:1px solid #ddd;text-align:left;">\u503c</th>\n'
            + '      <th style="padding:10px 16px;border:1px solid #ddd;text-align:left;">\u72b6\u6001</th>\n'
            + '    </tr>\n'
            + '  </thead>\n'
            + '  <tbody>\n'
            + '    <tr><td style="padding:10px 16px;border:1px solid #ddd;">\u9879\u76ee A</td><td style="padding:10px 16px;border:1px solid #ddd;">100</td><td style="padding:10px 16px;border:1px solid #ddd;">\u5b8c\u6210</td></tr>\n'
            + '    <tr style="background:#f9f9f9;"><td style="padding:10px 16px;border:1px solid #ddd;">\u9879\u76ee B</td><td style="padding:10px 16px;border:1px solid #ddd;">75</td><td style="padding:10px 16px;border:1px solid #ddd;">\u8fdb\u884c\u4e2d</td></tr>\n'
            + '  </tbody>\n'
            + '</table>'
    };

    function snapshot() { return collectMarkdown(); }

    function resetHistory(initial) {
        history = [initial != null ? initial : ''];
        historyIndex = 0;
    }

    function recordHistory() {
        var cur = snapshot();
        if (historyIndex >= 0 && history[historyIndex] === cur) return;
        history = history.slice(0, historyIndex + 1);
        history.push(cur);
        if (history.length > 200) history.shift();
        historyIndex = history.length - 1;
    }

    // \u4e3a editor \u5b50\u8282\u70b9\u4e2d\u6240\u6709\u9876\u5c42\u5757\u5206\u914d data-block-id\uff08\u589e\u91cf\u6e32\u67d3\u57fa\u7840\u8bbe\u65bd\uff09
    function assignBlockIds() {
        var blocks = getBlocks();
        for (var i = 0; i < blocks.length; i++) {
            var b = blocks[i];
            if (!b.hasAttribute || !b.hasAttribute('data-block-id')) {
                b.setAttribute('data-block-id', getBlockId());
            }
        }
    }

    // ============================================================
    // \u589e\u91cf\u89e3\u6790\uff08\u4ec5\u91cd\u6e32\u67d3\u53d8\u5316\u7684\u5757\uff0c\u8282\u7701 \uff5e80% CPU\uff09
    // ============================================================
    // \u5c06 markdown \u6587\u672c\u62c6\u6210\u5757\u7ea7\u5355\u5143\uff08\u8fd4\u56de {src, type} \u6570\u7ec4\uff09
    // \u4e0e renderMarkdown \u7684\u5757\u8fb9\u754c\u5224\u65ad\u4fdd\u6301\u4e00\u81f4\uff1a\u7a7a\u884c\u5206\u9694 / \u56f4\u680f / \u5217\u8868 / \u5f15\u7528 \u7b49
    function splitMarkdownToBlocks(text) {
        var lines = String(text || '').split('\n');
        var blocks = [];
        var current = [];
        var inCode = false;
        var inHtmlFenceOpen = false;
        var inInteractiveHtml = false;
        var pendingFenceType = '';
        var blockType = 'p';

        function flush() {
            if (current.length > 0) {
                blocks.push({ src: current.join('\n'), type: blockType });
                current = [];
                blockType = 'p';
            }
        }

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            var trimmed = line.trim();

            // \u8ddf\u8e2a\u591a\u884c\u56f4\u680f\u72b6\u6001
            if (line.match(/^```/)) {
                if (!inCode) { inCode = true; blockType = 'code'; }
                else { inCode = false; }
                current.push(line);
                continue;
            }
            if (line.match(/^\|\|\|/)) {
                if (!inHtmlFenceOpen) {
                    // \u9996\u4e2a ||| = \u56f4\u680f\u5f00\u59cb
                    // \u662f\u5426\u5b8c\u6574\u9700\u7b49\u4e0b\u4e00\u4e2a ||| \u51fa\u73b0\u540e\u624d\u80fd\u786e\u5b9a
                    if (current.length > 0 && !inCode) {
                        // \u6682\u4f5c\u6bb5\u843d\u5904\u7406\uff0c\u7b49 \u300b\u9762\u62ff\u5230\u95ed\u5408 ||| \u65f6\u518d\u5347\u7ea7\u4e3a htmlfence
                    }
                    inHtmlFenceOpen = true;
                    blockType = 'htmlfence-pending';
                } else {
                    inHtmlFenceOpen = false;
                    blockType = 'htmlfence';
                }
                current.push(line);
                continue;
            }
            if (line.match(/^\+\+\+html\s*$/)) {
                inInteractiveHtml = true;
                blockType = 'interactive-html';
                current.push(line);
                continue;
            }
            if (inInteractiveHtml && line.match(/^\+\+\+\s*$/)) {
                inInteractiveHtml = false;
                current.push(line);
                continue;
            }

            if (inCode || inInteractiveHtml || inHtmlFenceOpen) {
                current.push(line);
                continue;
            }

            // \u72ec\u7acb\u56fe\u7247\u5757
            if (line.match(/^!\[.*\]\(.*\)$/)) {
                if (current.length > 0 && blockType !== 'p') flush();
                blockType = 'image';
                current.push(line);
                flush();
                continue;
            }

            // \u539f\u59cb HTML \u5757\uff1a\u4ee5 < \u5f00\u5934\u4e14\u4e0d\u662f\u5217\u8868/\u6807\u9898/\u5f15\u7528 \u7b49
            if (/^\s*<\s*(div|table|html|head|body|p|h[1-6]|ul|ol|li|section|article|header|footer|nav|main|aside|figure|figcaption|form|button|input|select|textarea|blockquote|pre|code|a|span|img|br|hr|tr|td|th|thead|tbody|tfoot|caption)(\s|>|\/)/i.test(line) ||
                /^\s*<!--/.test(line) || /^\s*<!doctype/i.test(line)) {
                if (current.length > 0 && blockType !== 'html') flush();
                blockType = 'html';
                current.push(line);
                continue;
            }

            // \u6807\u9898
            if (line.match(/^#{1,6}\s+/)) {
                if (current.length > 0 && blockType !== 'h') flush();
                blockType = 'h';
                current.push(line);
                flush();
                continue;
            }

            // \u5206\u5272\u7ebf
            if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
                if (current.length > 0) flush();
                blockType = 'hr';
                current.push(line);
                flush();
                continue;
            }

            // \u5f15\u7528
            if (line.match(/^>\s?/)) {
                if (current.length > 0 && blockType !== 'blockquote') flush();
                blockType = 'blockquote';
                current.push(line);
                continue;
            }

            // \u5217\u8868
            if (line.match(/^[-*+]\s+/) || line.match(/^\d+\.\s+/)) {
                if (current.length > 0 && blockType !== 'list') flush();
                blockType = 'list';
                current.push(line);
                continue;
            }

            // \u8868\u683c
            if (line.match(/^\|.+\|$/)) {
                if (current.length > 0 && blockType !== 'table') flush();
                blockType = 'table';
                current.push(line);
                continue;
            }

            // \u7a7a\u884c = \u5757\u5206\u9694
            if (trimmed === '') {
                flush();
                continue;
            }

            // \u666e\u901a\u6bb5\u843d
            if (current.length > 0 && blockType !== 'p') flush();
            blockType = 'p';
            current.push(line);
        }
        flush();
        return blocks;
    }

    // \u589e\u91cf\u6e32\u67d3\uff1a\u8fd4\u56de true \u8868\u793a\u589e\u91cf\u6210\u529f\uff08\u8c03\u7528\u65b9\u8fd8\u9700 setTimout \u8d70\u6bb5\u6027\u9ad8\u4eae\u903b\u8f91\uff09\uff1b
    // \u8fd4\u56de false \u8868\u793a\u9700\u8981\u964d\u7ea7\u5230\u5168\u91cf\u6e32\u67d3
    function renderIncremental(text) {
        try {
            var currentBlocks = getBlocks();
            // \u65e0\u73b0\u6709\u5757\uff1a\u9700\u5168\u91cf\u6e32\u67d3
            if (currentBlocks.length === 0) return false;

            // \u62c6\u5206\u65b0\u6587\u672c\u4e3a\u5757
            var newBlocks = splitMarkdownToBlocks(text);

            // \u5757\u6570\u91cf\u4e0d\u4e00\u81f4 \u2192 \u964d\u7ea7\u5168\u91cf\u6e32\u67d3
            if (newBlocks.length !== currentBlocks.length) {
                return false;
            }

            // \u9010\u5757\u5bf9\u6bd4 src\uff1a\u5168\u90e8\u90fd\u4e00\u81f4 \u2192 \u7eaf\u63d2\u5165\u6587\u672c\uff0c\u4f46 DOM \u672a\u53d8\uff0c\u8df3\u8fc7\u6e32\u67d3
            var changedCount = 0;
            for (var i = 0; i < currentBlocks.length; i++) {
                var cur = currentBlocks[i];
                var curSrc = '';
                if (cur.hasAttribute && cur.hasAttribute('data-src')) {
                    curSrc = cur.getAttribute('data-src') || '';
                } else {
                    // \u6ca1\u6709 data-src \u7684\u5757\uff08\u53ef\u80fd\u662f\u5d4c\u5957\u4e2d\u7684\u5bb9\u5668\uff09\u5408\u5e76\u4e3a\u5176\u4e0b\u6709 data-src \u5b50\u5143\u7d20\u7684 src
                    var inner = cur.querySelector('[data-src]');
                    if (inner) curSrc = inner.getAttribute('data-src') || '';
                    else curSrc = cur.innerText || cur.textContent || '';
                }
                if (curSrc !== newBlocks[i].src) {
                    changedCount++;
                }
            }

            // 0 \u5757\u53d8\u5316 \u2192 \u4ec0\u4e48\u90fd\u4e0d\u505a
            if (changedCount === 0) {
                return true;
            }

            // \u811a\u9ad8\u7c7b\u578b\u4e0d\u4e00\u81f4\uff08\u70b9\u5217\u8868\u9879\u3001\u8de8\u5757\u7c7b\u578b\uff09 \u2192 \u964d\u7ea7\u5168\u91cf\u6e32\u67d3
            if (changedCount > Math.max(3, Math.floor(currentBlocks.length * 0.2))) {
                return false;
            }

            // \u9010\u5757\u66ff\u6362\uff1a\u4ec5\u91cd\u6e32\u67d3\u5b9e\u9645\u53d1\u751f\u53d8\u5316\u7684\u90a3\u51e0\u5757
            for (var i = 0; i < currentBlocks.length; i++) {
                var cur = currentBlocks[i];
                var curSrc = (cur.hasAttribute && cur.hasAttribute('data-src')) ? (cur.getAttribute('data-src') || '') : (cur.innerText || cur.textContent || '');
                if (curSrc !== newBlocks[i].src) {
                    var newHtml = renderMarkdown(newBlocks[i].src);
                    var tpl = document.createElement('template');
                    tpl.innerHTML = newHtml;
                    var parent = cur.parentNode;
                    if (!parent) continue;
                    var newNodes = Array.prototype.slice.call(tpl.content.childNodes).filter(function(n) {
                        return n.nodeType === 1 || (n.nodeType === 3 && n.textContent.trim() !== '');
                    });
                    if (newNodes.length === 0) {
                        var emptyP = document.createElement('p');
                        emptyP.setAttribute('data-md', 'p');
                        emptyP.setAttribute('data-src', '');
                        emptyP.innerHTML = '<br>';
                        newNodes = [emptyP];
                    }
                    // \u4fdd\u7559\u539f\u6709 block-id
                    var oldId = cur.getAttribute('data-block-id');
                    if (oldId) {
                        for (var k = 0; k < newNodes.length; k++) {
                            if (newNodes[k].nodeType === 1) newNodes[k].setAttribute('data-block-id', oldId);
                        }
                    } else {
                        for (var k = 0; k < newNodes.length; k++) {
                            if (newNodes[k].nodeType === 1) newNodes[k].setAttribute('data-block-id', getBlockId());
                        }
                    }
                    // \u63d2\u5165\u65b0\u8282\u70b9\u3001\u5220\u9664\u65e7\u8282\u70b9
                    for (var j = 0; j < newNodes.length; j++) {
                        parent.insertBefore(newNodes[j], cur);
                    }
                    parent.removeChild(cur);
                }
            }
            return true;
        } catch (e) {
            // \u4efb\u4f55\u5f02\u5e38\u90fd\u964d\u7ea7\u5230\u5168\u91cf\u6e32\u67d3
            try { console.warn('renderIncremental failed:', e); } catch(_e) {}
            return false;
        }
    }

    function setContentDirect(text) {
        activeBlock = null;
        savedMarkdown = text || '';
        editor.innerHTML = renderMarkdown(savedMarkdown);
        assignBlockIds();
        // 【性能优化】推迟高亮 / Mermaid / Iframe 到下一帧——这些是耗时操作
        // （hljs 逐块高亮、Mermaid 走 CDN、Iframe 拼接 srcdoc），推迟后 setContentDirect
        // 从「几秒+」降到「几十毫秒」，源→预览 切换不卡。
        setTimeout(function() {
            try {
                var codeBlocks = editor.querySelectorAll('pre code');
                for (var i = 0; i < codeBlocks.length; i++) {
                    try { if (window.hljs) hljs.highlightElement(codeBlocks[i]); } catch(e) {}
                }
            } catch(e) {}
            try { renderAllMermaid(); } catch(e) {}
            try { renderAllInteractiveBlocks(); } catch(e) {}
        }, 0);
    }

    function undo() {
        if (historyIndex <= 0) return;
        historyIndex--;
        setContentDirect(history[historyIndex]);
    }

    function redo() {
        if (historyIndex >= history.length - 1) return;
        historyIndex++;
        setContentDirect(history[historyIndex]);
    }

    function getBlocks() {
        var kids = editor.childNodes;
        var out = [];
        for (var i = 0; i < kids.length; i++) {
            var n = kids[i];
            if (n.nodeType === 1 && n.tagName === 'SCRIPT') continue;
            if (n.nodeType === 3 && n.textContent.trim() === '') continue;
            out.push(n);
        }
        return out;
    }

    function escapeHtml(text) {
        // 使用数字字符引用，避免实体被二次处理（也避免源码转义映射损坏）
        return String(text)
            .replace(/&/g, '&#38;')
            .replace(/</g, '&#60;')
            .replace(/>/g, '&#62;')
            .replace(/"/g, '&#34;')
            .replace(/'/g, '&#39;');
    }

    // 保护 HTML 标签：让用户输入的 HTML（如 <a href="...">）原样渲染，其余内容仍被转义
    var htmlTagCache = [];
    function protectHtmlTags(text) {
        htmlTagCache = [];
        return text.replace(/<\/?[a-zA-Z][^>]*>/g, function(tag) {
            htmlTagCache.push(tag);
            return '\x01' + (htmlTagCache.length - 1) + '\x01';
        });
    }
    function restoreHtmlTags(text) {
        return text.replace(/\x01(\d+)\x01/g, function(_m, idx) {
            var i = parseInt(idx, 10);
            return htmlTagCache[i] != null ? htmlTagCache[i] : '';
        });
    }

    // 常见语言关键字表（用于轻量代码高亮）
    function getKeywordSet(lang) {
        var map = {
            'java': 'abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for goto if implements import instanceof int interface long native new package private protected public return short static strictfp super switch synchronized this throw throws transient try void volatile while var record sealed permits yield true false null',
            'python': 'and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield True False None self',
            'javascript': 'var let const function return if else for while do switch case break continue new delete typeof instanceof in of class extends super import export default try catch finally throw this null undefined true false',
            'js': 'var let const function return if else for while do switch case break continue new delete typeof instanceof in of class extends super import export default try catch finally throw this null undefined true false',
            'ts': 'var let const function return if else for while do switch case break continue new delete typeof instanceof in of class extends super import export default try catch finally throw null undefined true false interface type enum implements namespace readonly',
            'typescript': 'var let const function return if else for while do switch case break continue new delete typeof instanceof in of class extends super import export default try catch finally throw null undefined true false interface type enum implements namespace readonly',
            'c': 'auto break case char const continue default do double else enum extern float for goto if inline int long register restrict return short signed sizeof static struct switch typedef union unsigned void volatile while',
            'cpp': 'auto bool break case catch char class const constexpr continue default delete do double else enum explicit extern false float for friend goto if inline int long namespace new noexcept nullptr operator private protected public register reinterpret_cast return short signed sizeof static static_cast struct switch template this throw true try typedef typename union unsigned using virtual void volatile while',
            'c++': 'auto bool break case catch char class const constexpr continue default delete do double else enum explicit extern false float for friend goto if inline int long namespace new noexcept nullptr operator private protected public register reinterpret_cast return short signed sizeof static static_cast struct switch template this throw true try typedef typename union unsigned using virtual void volatile while',
            'csharp': 'abstract as base bool break byte case catch char checked class const continue decimal default delegate do double else enum event explicit extern false finally fixed float for foreach goto if implicit in int interface internal is lock long namespace new null object operator out override params private protected public readonly ref return sbyte sealed short sizeof stackalloc static string struct switch this throw true try typeof uint ulong unchecked unsafe ushort using virtual void volatile while',
            'go': 'break case chan const continue default defer else fallthrough for func go goto if import interface map package range return select struct switch type var',
            'rust': 'as async await break const continue crate dyn else enum extern false fn for if impl in let loop match mod move mut pub ref return self Self static struct super trait true type unsafe use where while',
            'sql': 'select from where insert into values update set delete create table alter drop index view and or not null primary key foreign references join left right inner outer on as distinct count sum avg min max group by order having limit',
            'html': 'DOCTYPE html head body title meta link script style div span p a img table tr td th ul ol li form input button h1 h2 h3 h4 h5 h6',
            'css': 'color background font margin padding border width height display position top left right bottom flex grid align justify content items',
            'bash': 'if then else fi for while do done case esac function echo export source set unset read exit return',
            'shell': 'if then else fi for while do done case esac function echo export source set unset read exit return',
            'sh': 'if then else fi for while do done case esac function echo export source set unset read exit return'
        };
        lang = (lang || '').toLowerCase();
        return (map[lang] || '').split(/\s+/).filter(Boolean);
    }

    // 轻量代码高亮：对注释、字符串、关键字、数字着色
    function highlightCode(code, lang) {
        if (!code) return '';
        var keywords = getKeywordSet(lang);
        var out = '';
        var last = 0;
        var kw = keywords.length ? keywords.join('|') : null;
        var pattern;
        if (kw) {
            pattern = new RegExp('(\\/\\/[^\\n]*|\\/\\*[\\s\\S]*?\\*\\/|"(?:[^"\\\\\\n]|\\\\.)*"|\'(?:[^\'\\\\\\n]|\\\\.)*\'|`(?:[^`\\\\]|\\\\.)*`|\\b(?:' + kw + ')\\b|\\b\\d+(?:\\.\\d+)?\\b)', 'g');
        } else {
            pattern = /(\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|`(?:[^`\\]|\\.)*`|\b\d+(?:\.\d+)?\b)/g;
        }
        code.replace(pattern, function(m) {
            var idx = arguments[arguments.length - 2];
            out += escapeHtml(code.slice(last, idx));
            var cls = 'hljs-keyword';
            if (m.charAt(0) === '/' && (m.charAt(1) === '/' || m.charAt(1) === '*')) {
                cls = 'hljs-comment';
            } else if (m.charAt(0) === '"' || m.charAt(0) === "'" || m.charAt(0) === '`') {
                cls = 'hljs-string';
            } else if (/^\d/.test(m)) {
                cls = 'hljs-number';
            }
            out += '<span class="' + cls + '">' + escapeHtml(m) + '</span>';
            last = idx + m.length;
        });
        out += escapeHtml(code.slice(last));
        return out;
    }

    // 判断一行是否是原始 HTML 块的起始（块级标签/注释/DOCTYPE）
    function isHtmlBlockStart(line) {
        return /^\s*<\s*(div|table|html|head|body|p|h[1-6]|ul|ol|li|section|article|header|footer|nav|main|aside|figure|figcaption|form|button|input|select|textarea|blockquote|pre|code|a|span|img|br|hr|tr|td|th|thead|tbody|tfoot|caption)(\s|>|\/)/i.test(line) ||
               /^\s*<!--/.test(line) ||
               /^\s*<!doctype/i.test(line);
    }

    // 判断一行文本是否应触发结构渲染（标题/分割线/列表/引用/代码围栏/HTML 围栏等）
    function lineTriggersBlock(line) {
        if (!line) return false;
        var t = String(line).trim();
        if (!t) return false;
        if (/^(#{1,6}\s|>\s?|[-*+]\s+|\d+\.\s+|```|\|\|\||\+\+\+html)/.test(line)) return true;
        if (/^(-{3,}|\*{3,}|_{3,})$/.test(t)) return true;
        if (/^!\[[^\]]*\]\([^)]*\)$/.test(t)) return true;
        if (/^\|.+\|$/.test(t)) return true;
        return isHtmlBlockStart(line);
    }

    // 去掉 ||| HTML 围栏标记，取出内部 HTML 源码
    function stripHtmlFence(src) {
        var s = (src || '');
        s = s.replace(/^\s*\|\|\|\s*[\r\n]+/, '');
        s = s.replace(/[\r\n]+\s*\|\|\|\s*$/, '');
        return s;
    }

    // 判断 HTML 围栏块是否已经包含完整的开始/结束标记（即已输入两个 `|||`）
    function isCompleteHtmlFence(text) {
        return /^\s*\|\|\|[\s\S]*\|\|\|\s*$/.test(text || '');
    }

    // 判断整篇文档中是否已存在一个完整闭合的 `|||` 与 `|||` 围栏
    function hasCompleteHtmlFence(text) {
        return /(^|\n)\s*\|\|\|[\r\n]+[\s\S]*?[\r\n]+\s*\|\|\|\s*(\n|$)/.test(text || '');
    }

    // === +++html 交互式 HTML 块 - 辅助函数 ===

    // 轻量 HTML 净化（移除危险标签和属性）
    function sanitizeHtml(html) {
        var dangerous = /<\s*(script|object|embed|applet|form|input|select|textarea|link|meta|base)\b[^>]*>/gi;
        var cleaned = html.replace(dangerous, '');
        cleaned = cleaned.replace(/\s(on\w+)\s*=\s*("[^"]*"|'[^']*'|[^\s>]*)/gi, '');
        cleaned = cleaned.replace(/javascript\s*:/gi, 'removed:');
        return cleaned;
    }

    // 检测 HTML 中是否包含脚本
    function detectScripts(html) {
        return /<\s*script\b/i.test(html) || /\son\w+\s*=/i.test(html) || /javascript\s*:/i.test(html);
    }

    // 解析 +++html 围栏，提取内部 HTML 内容
    function stripInteractiveHtmlFence(src) {
        var s = (src || '');
        s = s.replace(/^\s*\+\+\+html\s*[\r\n]+/, '');
        s = s.replace(/[\r\n]+\s*\+\+\+\s*$/, '');
        return s;
    }

    // 判断 +++html 围栏是否完整闭合
    function isCompleteInteractiveFence(text) {
        return /^\s*\+\+\+html[\s\S]*\+\+\+\s*$/.test(text || '');
    }

    // === +++html 交互式 HTML 块 - iframe 渲染 ===

    // 渲染所有交互 HTML 块的 iframe
    function renderAllInteractiveBlocks() {
        var blocks = editor.querySelectorAll('.interactive-html-block');
        for (var i = 0; i < blocks.length; i++) {
            renderInteractiveBlock(blocks[i]);
        }
    }

    // 渲染单个交互块
    function renderInteractiveBlock(block) {
        if (!block || block.classList.contains('editing')) return;
        var rawHtml = block.getAttribute('data-ihsrc') || '';
        var iframe = block.querySelector('iframe');
        if (!iframe) return;
        var hasScript = detectScripts(rawHtml);
        var scriptWarn = block.querySelector('.ihb-script-warn');
        var safe = sanitizeHtml(rawHtml);
        writeIframeContent(iframe, safe);
        if (scriptWarn) scriptWarn.style.display = hasScript ? '' : 'none';
        // 自适应 iframe 高度
        iframe.onload = function() {
            try {
                var h = iframe.contentDocument.body.scrollHeight;
                iframe.style.height = Math.max(60, h + 20) + 'px';
            } catch(e) {}
        };
    }

    // 向 iframe 写入内容（含暗色模式适配）
    function writeIframeContent(iframe, html) {
        var isDark = document.documentElement.classList.contains('dark');
        var bg = isDark ? '#0d1117' : '#ffffff';
        var fg = isDark ? '#e6edf3' : '#24292f';
        var doc = '<!DOCTYPE html><html><head><meta charset="UTF-8">'
            + '<style>body{margin:8px 12px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;'
            + 'font-size:15px;line-height:1.6;color:' + fg + ';background:' + bg + ';}'
            + 'img{max-width:100%;}table{border-collapse:collapse;width:100%;}'
            + 'th,td{border:1px solid #d0d7de;padding:6px 12px;text-align:left;}'
            + 'th{background:#f6f8fa;font-weight:600;}</style></head>'
            + '<body>' + html + '</body></html>';
        iframe.srcdoc = doc;
    }

    // === +++html 交互式 HTML 块 - 编辑交互 ===

    // 进入编辑模式
    function enterInteractiveHtmlEdit(block) {
        if (!block || block.classList.contains('editing')) return;
        if (activeBlock) exitSourceMode();
        block.classList.add('editing');
        var textarea = block.querySelector('.ihb-edit-area textarea');
        if (textarea) {
            var rawHtml = block.getAttribute('data-ihsrc') || '';
            textarea.value = rawHtml;
            textarea.focus();
        }
        block.setAttribute('data-ihbackup', block.getAttribute('data-ihsrc') || '');
    }

    // 保存编辑（预览/保存按钮）
    window._ihbSave = function(btn) {
        var block = btn.closest('.interactive-html-block');
        if (!block) return;
        var textarea = block.querySelector('.ihb-edit-area textarea');
        if (!textarea) return;
        var newHtml = textarea.value;
        if (newHtml.length > 1048576) { alert('HTML \u5757\u5185\u5bb9\u8d85\u8fc7 1MB \u9650\u5236'); return; }
        var fullSrc = '+++html\n' + newHtml + '\n+++';
        block.setAttribute('data-src', fullSrc);
        block.setAttribute('data-ihsrc', newHtml);
        block.removeAttribute('data-ihbackup');
        block.classList.remove('editing');
        renderInteractiveBlock(block);
        recordHistory();
        notifyContentChanged();
    };

    // 取消编辑
    window._ihbCancel = function(btn) {
        var block = btn.closest('.interactive-html-block');
        if (!block) return;
        var backup = block.getAttribute('data-ihbackup') || '';
        block.setAttribute('data-ihsrc', backup);
        block.removeAttribute('data-ihbackup');
        block.classList.remove('editing');
        renderInteractiveBlock(block);
    };

    // 执行脚本
    window._ihbRunScripts = function(span) {
        var block = span.closest('.interactive-html-block');
        if (!block) return;
        if (!confirm('\u6b64 HTML \u5757\u5305\u542b\u811a\u672c\uff0c\u786e\u8ba4\u6267\u884c\uff1f')) return;
        var rawHtml = block.getAttribute('data-ihsrc') || '';
        var iframe = block.querySelector('iframe');
        if (!iframe) return;
        iframe.removeAttribute('sandbox');
        iframe.srcdoc = '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>' + rawHtml + '</body></html>';
        span.style.display = 'none';
    };

    // 仅重渲染当前块，并把光标定位到新块末尾，避免回车时全文 innerHTML 重建丢失光标
    function renderLocalAndFocus(block) {
        if (!block || !block.parentNode) return;
        var src = block.getAttribute('data-src') || '';
        var wrapper = document.createElement('div');
        wrapper.innerHTML = renderMarkdown(src);
        var nodes = [];
        while (wrapper.firstChild) nodes.push(wrapper.firstChild);
        if (!nodes.length) {
            var emptyP = document.createElement('p');
            emptyP.setAttribute('data-md', 'p');
            emptyP.setAttribute('data-src', '');
            emptyP.innerHTML = '<br>';
            nodes.push(emptyP);
        }
        var parent = block.parentNode;
        var anchor = block;
        for (var n = 0; n < nodes.length; n++) {
            parent.insertBefore(nodes[n], anchor);
        }
        parent.removeChild(block);
        activeBlock = null;

        var newCodeBlocks = parent.querySelectorAll('pre code');
        newCodeBlocks.forEach(function(cb) {
            try { if (window.hljs) hljs.highlightElement(cb); } catch(e) {}
        });
        renderAllMermaid();

        var last = nodes[nodes.length - 1];
        var range = document.createRange();
        var walker = document.createTreeWalker(last, NodeFilter.SHOW_TEXT, null, false);
        var textNode = null;
        var t = walker.nextNode();
        while (t) { textNode = t; t = walker.nextNode(); }
        if (textNode) {
            range.setStart(textNode, textNode.textContent.length);
            range.collapse(true);
        } else {
            range.selectNodeContents(last);
            range.collapse(false);
        }
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        recordHistory();
        notifyContentChanged();
    }

    // Mermaid 渲染（流程图、甘特图等）
    function renderMermaidBlock(el) {
        if (!window.mermaid) return false;
        try {
            var txt = el.getAttribute('data-src') || el.textContent || '';
            el.removeAttribute('data-processed');
            el.innerHTML = escapeHtml(txt);
            window.mermaid.run({ nodes: [el] }).catch(function(e) {
                el.removeAttribute('data-processed');
                el.innerHTML = '<pre style="color:#c0392b; text-align:left;">Mermaid 渲染失败: ' + escapeHtml(String(e && e.message || e)) + '\n\n' + escapeHtml(txt) + '</pre>';
            });
            return true;
        } catch(e) {
            return false;
        }
    }

    function renderAllMermaid() {
        var els = editor.querySelectorAll('.mermaid');
        if (!els || !els.length) return;
        if (!window.mermaid) {
            // 离线/未加载时尝试动态加载 Mermaid
            var s = document.createElement('script');
            s.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
            s.onload = function() {
                try {
                    window.mermaid.initialize({ startOnLoad: false, securityLevel: 'loose', theme: document.documentElement.classList.contains('dark') ? 'dark' : 'default' });
                } catch(e) {}
                var els2 = editor.querySelectorAll('.mermaid');
                for (var i = 0; i < els2.length; i++) renderMermaidBlock(els2[i]);
            };
            document.head.appendChild(s);
            return;
        }
        for (var i = 0; i < els.length; i++) renderMermaidBlock(els[i]);
    }

    // 把生成的 HTML 字符串解析为 DOM 节点数组
    function parseBlocksHtml(html) {
        var tpl = document.createElement('template');
        tpl.innerHTML = html;
        return Array.prototype.slice.call(tpl.content.childNodes).filter(function(n) {
            return n.nodeType === 1 || (n.nodeType === 3 && n.textContent.trim() !== '');
        });
    }

    function renderMarkdown(text) {
        if (!text) return '<p data-md="p" data-src=""><br></p>';

        var lines = text.split('\n');
        var html = [];
        var i = 0;
        var inList = false;
        var listType = '';
        var inBlockquote = false;
        var codeLang = '';

        while (i < lines.length) {
            var line = lines[i];

            // 围栏代码块：作为普通代码块展示源码（含 html 语言）。
            // 仅 mermaid 特殊处理为图表。
            if (line.match(/^```/)) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                codeLang = line.replace(/^```/, '').trim();
                var codeLines = [];
                i++;
                while (i < lines.length && !lines[i].match(/^```/)) {
                    codeLines.push(lines[i]);
                    i++;
                }
                i++; // 跳过闭合 ```
                var codeText = codeLines.join('\n');
                var codeSrc = '```' + (codeLang || '') + '\n' + codeText + '\n```';
                var langLower = (codeLang || '').toLowerCase();
                if (langLower === 'mermaid') {
                    // Mermaid 图表：可点击编辑源码，渲染后展示图形
                    html.push('<div class="mermaid" data-md="mermaid" data-src="' + escapeHtml(codeText) + '">' + escapeHtml(codeText) + '</div>');
                } else {
                    // 代码内容用 highlightCode 做语法高亮（关键字/字符串/注释/数字着色）
                    html.push('<pre data-md="code" data-src="' + escapeHtml(codeSrc) + '"><code class="language-' + escapeHtml(codeLang) + '">' + highlightCode(codeText, codeLang) + '</code></pre>');
                }
                continue;
            }

            // `|||` HTML 围栏：必须同时存在开始与结束标记才视为完整块。
            // 若尚未闭合，则把 `|||` 当作普通文本段落处理，等补全结束符后再渲染。
            if (line.match(/^\|\|\|/)) {
                var closingIdx = -1;
                for (var k = i + 1; k < lines.length; k++) {
                    if (lines[k].match(/^\|\|\|/)) { closingIdx = k; break; }
                }
                if (closingIdx > i) {
                    if (inList) { html.push('</' + listType + '>'); inList = false; }
                    if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                    var htmlFenceLines = lines.slice(i + 1, closingIdx);
                    var htmlFenceText = htmlFenceLines.join('\n');
                    var htmlFenceSrc = lines.slice(i, closingIdx + 1).join('\n');
                    html.push('<div class="html-block" data-md="htmlfence" data-src="' + escapeHtml(htmlFenceSrc) + '">' + htmlFenceText + '</div>');
                    i = closingIdx + 1;
                    continue;
                }
                // 未闭合：落入下方普通段落处理
            }

            // +++html 交互式 HTML 围栏
            if (line.match(/^\+\+\+html\s*$/)) {
                var closingIdx2 = -1;
                for (var k2 = i + 1; k2 < lines.length; k2++) {
                    if (lines[k2].match(/^\+\+\+\s*$/)) { closingIdx2 = k2; break; }
                }
                if (closingIdx2 > i) {
                    if (inList) { html.push('</' + listType + '>'); inList = false; }
                    if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                    var ihLines = lines.slice(i + 1, closingIdx2);
                    var ihContent = ihLines.join('\n');
                    var ihSrc = lines.slice(i, closingIdx2 + 1).join('\n');
                    html.push('<div class="interactive-html-block" data-md="interactive-html" data-src="' + escapeHtml(ihSrc) + '" data-ihsrc="' + escapeHtml(ihContent) + '">'
                        + '<div class="ihb-toolbar">'
                        + '<button class="ihb-btn-primary" onclick="window._ihbSave(this)">\u9884\u89c8</button>'
                        + '<button onclick="window._ihbSave(this)">\u4fdd\u5b58</button>'
                        + '<button onclick="window._ihbCancel(this)">\u53d6\u6d88</button>'
                        + '<span class="ihb-script-warn" style="display:none" onclick="window._ihbRunScripts(this)">&#9888; \u6267\u884c\u811a\u672c</span>'
                        + '</div>'
                        + '<iframe sandbox="allow-same-origin" scrolling="no"></iframe>'
                        + '<div class="ihb-edit-area"><textarea spellcheck="false"></textarea></div>'
                        + '<span class="ihb-edit-hint">\u70b9\u51fb\u7f16\u8f91\u6b64 HTML \u5757</span>'
                        + '</div>');
                    i = closingIdx2 + 1;
                    continue;
                }
            }

            // 空行：每个空行生成一个占位块，保留多个连续空行（支持多次回车换行）
            if (line.trim() === '') {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                html.push('<p class="empty-line" data-md="p" data-src=""><br></p>');
                i++;
                continue;
            }

            // 独立图片块：整张图可点击编辑图片地址/alt
            var imgMatch = line.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
            if (imgMatch) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                var imgAlt = imgMatch[1];
                var imgSrc = imgMatch[2];
                html.push('<p class="image-block" data-md="image" data-src="' + escapeHtml(line) + '"><img alt="' + escapeHtml(imgAlt) + '" src="' + resolveImageUrl(imgSrc) + '"></p>');
                i++;
                continue;
            }

            // 原始 HTML 块：直接渲染 HTML，可点击整体进入源码编辑（与图片点击逻辑一致）
            if (isHtmlBlockStart(line)) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                var htmlLines = [line];
                i++;
                while (i < lines.length && lines[i].trim() !== '' && !lines[i].match(/^```/)) {
                    htmlLines.push(lines[i]);
                    i++;
                }
                var htmlSrc = htmlLines.join('\n');
                html.push('<div class="html-block" data-md="html" data-src="' + escapeHtml(htmlSrc) + '">' + htmlSrc + '</div>');
                continue;
            }

            // 标题
            var headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
            if (headingMatch) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                var level = headingMatch[1].length;
                html.push('<h' + level + ' data-md="h' + level + '" data-src="' + escapeHtml(line) + '">' + renderInline(headingMatch[2]) + '</h' + level + '>');
                i++;
                continue;
            }

            // 分割线
            if (line.match(/^(-{3,}|\*{3,}|_{3,})$/)) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                html.push('<hr data-md="hr" data-src="' + escapeHtml(line) + '">');
                i++;
                continue;
            }

            // 引用
            if (line.match(/^>/)) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (!inBlockquote) { html.push('<blockquote data-md="blockquote">'); inBlockquote = true; }
                html.push('<p data-md="quote" data-src="' + escapeHtml(line) + '">' + renderInline(line.replace(/^>\s*/, '')) + '</p>');
                i++;
                continue;
            } else if (inBlockquote) {
                html.push('</blockquote>');
                inBlockquote = false;
            }

            // 无序列表
            if (line.match(/^[-*+]\s+/)) {
                if (!inList) { html.push('<ul data-md="ul">'); inList = true; listType = 'ul'; }
                html.push('<li data-md="li" data-src="' + escapeHtml(line) + '">' + renderInline(line.replace(/^[-*+]\s+/, '')) + '</li>');
                i++;
                continue;
            }

            // 有序列表
            if (line.match(/^\d+\.\s+/)) {
                if (!inList) { html.push('<ol data-md="ol">'); inList = true; listType = 'ol'; }
                html.push('<li data-md="li" data-src="' + escapeHtml(line) + '">' + renderInline(line.replace(/^\d+\.\s+/, '')) + '</li>');
                i++;
                continue;
            }

            // 表格（简单判断，收集完整源码写入 data-src 便于点击编辑）
            if (line.match(/^\|.+\|$/) && i + 1 < lines.length && lines[i+1].match(/^[\|: -]+$/)) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                var tableLines = [line];
                i++;
                while (i < lines.length && lines[i].match(/^\|.+\|$/)) {
                    tableLines.push(lines[i]);
                    i++;
                }
                var tableSrc = tableLines.join('\n');
                html.push('<table data-md="table" data-src="' + escapeHtml(tableSrc) + '"><thead><tr>');
                // 【修复表格列数翻倍】拆分时去掉首尾空字符串（边界 `|` 产生的），
                // 例如 `| a | b |` split 后是 ['', ' a ', ' b ', '']，filter 保留了首尾空串导致列数 ×2 +2。
                function parseTableCells(line) {
                    var cs = line.split('|');
                    if (cs.length && cs[0].trim() === '') cs.shift();
                    if (cs.length && cs[cs.length - 1].trim() === '') cs.pop();
                    return cs;
                }
                var headers = parseTableCells(tableLines[0]);
                headers.forEach(function(h) {
                    html.push('<th>' + renderInline(h.trim()) + '</th>');
                });
                html.push('</tr></thead><tbody>');
                for (var ti = 2; ti < tableLines.length; ti++) {
                    html.push('<tr>');
                    var cells = parseTableCells(tableLines[ti]);
                    cells.forEach(function(c) {
                        html.push('<td>' + renderInline(c.trim()) + '</td>');
                    });
                    html.push('</tr>');
                }
                html.push('</tbody></table>');
                continue;
            }

            // 普通段落：每一行单独成块，光标不在该行时自动显示渲染后的样式
            if (inList) { html.push('</' + listType + '>'); inList = false; }
            html.push('<p data-md="p" data-src="' + escapeHtml(line) + '">' + renderInline(line) + '</p>');
            i++;
        }

        if (inList) html.push('</' + listType + '>');
        if (inBlockquote) html.push('</blockquote>');

        return html.join('');
    }

    // 把 markdown 源码渲染成 DOM 节点数组（每个块一个节点）
    function renderNodes(text) {
        var wrapper = document.createElement('div');
        wrapper.innerHTML = renderMarkdown(text);
        var nodes = [];
        while (wrapper.firstChild) nodes.push(wrapper.firstChild);
        if (!nodes.length) {
            var emptyP = document.createElement('p');
            emptyP.setAttribute('data-md', 'p');
            emptyP.setAttribute('data-src', '');
            emptyP.innerHTML = '<br>';
            nodes.push(emptyP);
        }
        return nodes;
    }

    // 在源码模式中按光标位置拆分当前块：光标前内容渲染为样式块，
    // 光标后内容成为新的源码编辑块（保证“光标不在的行自动显示样式”）
    function splitCurrentBlock() {
        if (!activeBlock || !activeBlock.parentNode) return false;
        var sel = window.getSelection();
        if (sel.rangeCount === 0) return false;
        var range = sel.getRangeAt(0);
        if (!activeBlock.contains(range.startContainer)) return false;
        if (!range.collapsed) range.deleteContents();

        var pre = document.createRange();
        pre.selectNodeContents(activeBlock);
        pre.setEnd(range.startContainer, range.startOffset);
        var offset = pre.toString().length;

        var src = activeBlock.textContent || '';
        var beforeText = src.slice(0, offset);
        var afterText = src.slice(offset);

        var parent = activeBlock.parentNode;
        var nextSibling = activeBlock.nextSibling;
        var beforeNodes = renderNodes(beforeText);
        var afterNodes = renderNodes(afterText);

        // 移除旧块（保留 nextSibling 作为插入锚点，避免 removeChild 后 anchor 失效）
        parent.removeChild(activeBlock);
        activeBlock = null;

        function insertAtAnchor(node) {
            if (nextSibling) {
                parent.insertBefore(node, nextSibling);
            } else {
                parent.appendChild(node);
            }
        }

        // 前部内容作为渲染显示（已按行拆分）
        for (var i = 0; i < beforeNodes.length; i++) {
            insertAtAnchor(beforeNodes[i]);
        }
        // 后部内容插入，第一块作为新的源码编辑块
        var newCurrent = null;
        for (var j = 0; j < afterNodes.length; j++) {
            insertAtAnchor(afterNodes[j]);
            if (!newCurrent) newCurrent = afterNodes[j];
        }

        // 代码高亮与 mermaid
        var scopedCode = parent.querySelectorAll('pre code');
        scopedCode.forEach(function(cb) {
            try { if (window.hljs) hljs.highlightElement(cb); } catch(e) {}
        });
        renderAllMermaid();

        if (newCurrent && newCurrent.nodeType === 1 &&
            newCurrent.hasAttribute && newCurrent.hasAttribute('data-src')) {
            enterSourceMode(newCurrent);
            // 光标定位到新块起点（紧贴换行后第一行起始）
            var r2 = document.createRange();
            var walker2 = document.createTreeWalker(newCurrent, NodeFilter.SHOW_TEXT, null, false);
            var tn2 = walker2.nextNode();
            if (tn2) {
                r2.setStart(tn2, 0);
                r2.collapse(true);
            } else {
                r2.selectNodeContents(newCurrent);
                r2.collapse(true);
            }
            var s2 = window.getSelection();
            s2.removeAllRanges();
            s2.addRange(r2);
        }

        recordHistory();
        notifyContentChanged();
        return true;
    }

    // 当前 markdown 文件所在目录（相对路径图片的解析基础，file:/// 前缀）
    var baseDir = '';
    function resolveImageUrl(src) {
        if (!src) return src;
        // 已经是 http(s)/data/file 协议：不处理
        if (/^(https?:|data:|file:)/i.test(src)) return src;
        // 反斜杠转正斜杠（Windows 路径）
        src = src.replace(/\\/g, '/');
        // 绝对路径：Windows 盘符 (C:/...) 或 POSIX (/...) 都要补 file:// 前缀
        if (/^[a-zA-Z]:\//.test(src)) {
            // Windows 盘符路径 → file:///C:/...
            src = 'file:///' + src;
        } else if (src.startsWith('/')) {
            // POSIX 绝对路径 → file:///...
            src = 'file://' + src;
        } else if (baseDir) {
            // 相对路径：拼上当前文件目录
            var sep = baseDir.endsWith('/') ? '' : '/';
            src = baseDir + sep + src;
        }
        // 统一编码（保留 : / 等，编码中文、空格、引号）
        return encodeURI(src).replace(/'/g, "%27").replace(/"/g, "%22");
    }

    function renderInline(text) {
        if (!text) return '';
        // 先保护 HTML 标签，再对剩余文本转义（让 HTML 直通生效）
        text = protectHtmlTags(text);
        text = escapeHtml(text);

        // 图片（路径需经 resolveImageUrl 补全，解决 about:blank 下相对路径无法加载）
        text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, function(_m, alt, src) {
            return '<img alt="' + alt + '" src="' + resolveImageUrl(src) + '">';
        });

        // 链接
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

        // 加粗 + 斜体
        text = text.replace(/\*\*\*([^*]+)\*\*\*/g, '<strong><em>$1</em></strong>');
        text = text.replace(/___([^_]+)___/g, '<strong><em>$1</em></strong>');

        // 加粗
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/__([^_]+)__/g, '<strong>$1</strong>');

        // 斜体
        text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        text = text.replace(/_([^_]+)_/g, '<em>$1</em>');

        // 删除线
        text = text.replace(/~~([^~]+)~~/g, '<del>$1</del>');

        // 行内代码
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

        // 高亮标记
        text = text.replace(/==([^=]+)==/g, '<mark>$1</mark>');

        // 恢复 HTML 标签（原样输出，不转义）
        text = restoreHtmlTags(text);

        return text;
    }

    // 保存光标：编辑器全局字符偏移（简单可靠，不受 DOM 结构影响）
    function saveCursor() {
        var sel = window.getSelection();
        if (sel.rangeCount === 0 || !editor.contains(sel.anchorNode)) {
            savedCursor = null;
            return;
        }
        try {
            var range = document.createRange();
            range.selectNodeContents(editor);
            range.setEnd(sel.anchorNode, sel.anchorOffset);
            savedCursor = range.toString().length;
        } catch(e) {
            savedCursor = null;
        }
    }

    // 恢复光标：用 TreeWalker 在编辑器全局找对应字符位置
    function restoreCursor() {
        if (savedCursor == null) return;
        try {
            var offset = Math.max(0, savedCursor);
            var range = document.createRange();
            var walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT, null, false);
            var node;
            var count = 0;
            var found = false;
            while ((node = walker.nextNode())) {
                var len = node.textContent.length;
                if (count + len >= offset) {
                    range.setStart(node, Math.max(0, offset - count));
                    range.collapse(true);
                    found = true;
                    break;
                }
                count += len;
            }
            if (!found) {
                // 光标位于文本末尾之后的空行：定位到最后一个块的末尾（空段落内）
                var lastBlocks = getBlocks();
                var target = lastBlocks.length ? lastBlocks[lastBlocks.length - 1] : editor;
                range.selectNodeContents(target);
                range.collapse(false);
            }
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        } catch(e) {}
    }

    // ===== 块级源码/预览切换（Typora 风格）=====
    // 光标进入块 → 显示 markdown 源码（带 #、** 等标记）
    // 光标移出块 → 恢复为渲染后的效果
    var activeBlock = null;      // 当前处于源码编辑模式的块
    var activeBlockCursor = 0;   // 进入源码模式时保存的字符偏移
    var editorMode = 'edit';     // 'edit' | 'preview' - 编辑模式和预览模式

    // 获取光标所在的块级元素（editor 的直接子元素）
    function getCurrentBlock() {
        var sel = window.getSelection();
        if (sel.rangeCount === 0) return null;
        var node = sel.anchorNode;
        if (!node || !editor.contains(node)) return null;
        // 找到 editor 直接子元素（块容器）
        var container = node;
        while (container && container.parentNode !== editor) container = container.parentNode;
        if (!container || container === editor) return null;
        // 容器本身有 data-src → 用容器（标题/段落/列表项）
        if (container.nodeType === 1 && container.hasAttribute && container.hasAttribute('data-src')) {
            return container;
        }
        // 否则在容器内找光标所在的带 data-src 子元素（引用内 p、列表内 li）
        var inner = node;
        while (inner && inner !== container) {
            if (inner.nodeType === 1 && inner.hasAttribute && inner.hasAttribute('data-src')) {
                return inner;
            }
            inner = inner.parentNode;
        }
        // 容器是 HR/PRE/空行等
        return container;
    }

    // 保存块内光标偏移（渲染文本中的字符位置）
    function saveBlockCursor(block) {
        var sel = window.getSelection();
        if (sel.rangeCount === 0 || !block.contains(sel.anchorNode)) {
            activeBlockCursor = 0;
            return;
        }
        try {
            var range = document.createRange();
            range.selectNodeContents(block);
            range.setEnd(sel.anchorNode, sel.anchorOffset);
            activeBlockCursor = range.toString().length;
        } catch(e) {
            activeBlockCursor = 0;
        }
    }

    // 恢复块内光标（在源码纯文本中找对应位置）
    function restoreBlockCursor(block) {
        var offset = Math.max(0, activeBlockCursor);
        try {
            var range = document.createRange();
            var walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, null, false);
            var node, count = 0, found = false;
            while ((node = walker.nextNode())) {
                var len = node.textContent.length;
                if (count + len >= offset) {
                    range.setStart(node, Math.max(0, offset - count));
                    range.collapse(true);
                    found = true;
                    break;
                }
                count += len;
            }
            if (!found) {
                range.selectNodeContents(block);
                range.collapse(false);
            }
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        } catch(e) {}
    }

    // 进入块的源码模式：把块显示内容替换为 markdown 源码纯文本
    function enterSourceMode(block) {
        if (!block || block === activeBlock) return;
        // 先退出旧块（恢复渲染）
        if (activeBlock) exitSourceMode();
        // 只对带 data-src 的块生效（标题/段落/列表项/引用段落）
        if (!block.hasAttribute || !block.hasAttribute('data-src')) {
            activeBlock = null;
            return;
        }
        // 保存点击位置的光标（进入源码模式后需要恢复）
        var sel = window.getSelection();
        var clickOffset = 0;
        if (sel.rangeCount > 0) {
            var clickRange = sel.getRangeAt(0);
            if (block.contains(clickRange.startContainer)) {
                try {
                    var pre = document.createRange();
                    pre.selectNodeContents(block);
                    pre.setEnd(clickRange.startContainer, clickRange.startOffset);
                    clickOffset = pre.toString().length;
                } catch(e) { clickOffset = 0; }
            }
        }
        activeBlock = block;
        var src = block.getAttribute('data-src') || '';
        // 切换为纯文本源码（保留换行：textContent + white-space:pre-wrap）
        block.textContent = src;
        block.setAttribute('data-source-mode', '1');
        // 先设置好光标范围（恢复用户点击的位置）
        // 【修复】总是创建 range，即使 src 为空也必须重置选区到块起点，
        // 否则对于刚由回车产生的新空块，光标在 DOM 修改后会指向不存在的位置，
        // 导致回车后写作模式下光标消失（看起来卡死）。
        var range = document.createRange();
        if (src.length > 0) {
            var walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, null, false);
            var node, count = 0, found = false;
            while ((node = walker.nextNode())) {
                var len = node.textContent.length;
                if (count + len >= clickOffset) {
                    range.setStart(node, Math.max(0, clickOffset - count));
                    range.collapse(true);
                    found = true;
                    break;
                }
                count += len;
            }
            if (!found) {
                // 如果没找到，回退到末尾
                var textNode = block.lastChild;
                while (textNode && textNode.nodeType !== 3) textNode = textNode.lastChild;
                if (textNode && textNode.nodeType === 3) {
                    range.setStart(textNode, textNode.textContent.length);
                } else {
                    range.selectNodeContents(block);
                    range.collapse(false);
                }
                range.collapse(true);
            }
        } else {
            // src 为空：明确将光标放在块起点（offset 0），避免 selection 落在已删除的节点上
            range.setStart(block, 0);
            range.collapse(true);
        }
        // 最后确保编辑器获得焦点并设置光标（顺序很重要！）
        editor.focus();
        sel.removeAllRanges();
        sel.addRange(range);
    }


    // 源码模式下：在当前光标位置插入一个纯文本 \n 字符（不触发浏览器生成 <br>/新段落）
    function sourceModeInsertNewline() {
        if (!activeBlock) return false;
        var sel = window.getSelection();
        if (sel.rangeCount === 0) return false;
        var range = sel.getRangeAt(0);
        if (!activeBlock.contains(range.startContainer)) return false;
        // 删除选区
        if (!range.collapsed) {
            range.deleteContents();
        }
        // 插入换行字符
        var newline = document.createTextNode('\n');
        range.insertNode(newline);

        // 重新定位光标：放到换行符后面的文本节点开头，保证在 pre-wrap 下
        // 光标显示在下一行起始位置，而不是停留在上一行末尾。
        var caretRange = document.createRange();
        var afterText = newline.nextSibling;
        if (afterText && afterText.nodeType === 3) {
            caretRange.setStart(afterText, 0);
        } else {
            caretRange.setStartAfter(newline);
        }
        caretRange.collapse(true);
        
        // 先移除所有范围，然后设置新范围，最后确保编辑器获得焦点
        sel.removeAllRanges();
        sel.addRange(caretRange);
        editor.focus();
        
        // 确保焦点设置后光标仍在正确位置
        if (sel.rangeCount > 0) {
            var currentRange = sel.getRangeAt(0);
            // 验证光标是否在正确位置，如不在则重新设置
            var startContainer = currentRange.startContainer;
            if (startContainer !== caretRange.startContainer || 
                currentRange.startOffset !== caretRange.startOffset) {
                sel.removeAllRanges();
                sel.addRange(caretRange);
            }
        }
        
        // 同步 data-src
        activeBlock.setAttribute('data-src', activeBlock.textContent || '');
        recordHistory();
        notifyContentChanged();
        return true;
    }

    // 退出块的源码模式：恢复为渲染后的格式
    function exitSourceMode() {
        if (!activeBlock) return;
        var block = activeBlock;
        activeBlock = null;
        block.removeAttribute('data-source-mode');
        // 用 textContent 取源码（源码模式下保证纯文本，避免 innerText 把 <br>/<img> 吃空）
        var src = block.textContent || '';
        block.setAttribute('data-src', src);
        // 块级元素（代码块/表格/分割线）需整体重构；行内元素用 renderInline
        var mdType = block.getAttribute('data-md') || '';

        if (mdType === 'mermaid') {
            block.innerHTML = escapeHtml(src);
            renderMermaidBlock(block);
        } else if (mdType === 'html') {
            block.innerHTML = src;
        } else if (mdType === 'htmlfence') {
            block.innerHTML = stripHtmlFence(src);
            block.setAttribute('data-src', src || '');
        } else if (mdType === 'interactive-html') {
            var ihHtml = stripInteractiveHtmlFence(src);
            block.setAttribute('data-ihsrc', ihHtml);
            block.setAttribute('data-src', src || '');
            renderInteractiveBlock(block);
        } else if (/^h[1-6]$/.test(mdType)) {
            // 标题：去掉 # 标记后再渲染，并按当前 # 数量修正标题级别
            var hm = src.match(/^(#{1,6})\s+([\s\S]*)$/);
            if (hm) {
                var level = hm[1].length;
                var headingText = hm[2];
                var tag = 'h' + level;
                if (block.tagName.toLowerCase() !== tag) {
                    var hNode = document.createElement(tag);
                    hNode.setAttribute('data-md', tag);
                    hNode.setAttribute('data-src', src);
                    hNode.innerHTML = renderInline(headingText).replace(/\n/g, '<br>');
                    if (block.parentNode) block.parentNode.replaceChild(hNode, block);
                } else {
                    block.setAttribute('data-md', tag);
                    block.innerHTML = renderInline(headingText).replace(/\n/g, '<br>');
                }
            } else {
                // 已不再是标题 → 转为普通段落
                var pNode = document.createElement('p');
                pNode.setAttribute('data-md', 'p');
                pNode.setAttribute('data-src', src);
                pNode.innerHTML = renderInline(src).replace(/\n/g, '<br>');
                if (block.parentNode) block.parentNode.replaceChild(pNode, block);
            }
        } else if (mdType === 'quote') {
            // 引用段落：去掉 > 标记后渲染行内样式
            block.innerHTML = renderInline(src.replace(/^>\s?/, '')).replace(/\n/g, '<br>');
            block.setAttribute('data-src', src);
        } else if (block.tagName === 'LI') {
            // 列表项：去掉 -/*/+ 或数字标记后渲染行内样式，避免出现双重符号
            block.innerHTML = renderInline(src.replace(/^\s*(?:[-*+]\s+|\d+\.\s+)/, '')).replace(/\n/g, '<br>');
            block.setAttribute('data-src', src);
        } else if (mdType === 'code' || mdType === 'table' || mdType === 'hr') {
            var rendered = renderMarkdown(src);
            var wrapper = document.createElement('div');
            wrapper.innerHTML = rendered;
            var newNode = wrapper.firstChild;
            if (newNode && block.parentNode) {
                block.parentNode.replaceChild(newNode, block);
            }
        } else {
            block.innerHTML = renderInline(src).replace(/\n/g, '<br>');
        }
        // 同步全局缓存，避免下次全量 render 时回退
        savedMarkdown = collectMarkdown();
        notifyContentChanged();
    }

    // 从编辑器当前 DOM 收集 markdown 文本（按块拼接，处理嵌套结构）
    function collectMarkdown() {
        var lines = [];
        function pushBlock(b) {
            if (b.nodeType !== 1) {
                lines.push(b.textContent || '');
                return;
            }
            // 源码模式块：读当前显示文本（用户可能正在编辑）
            if (b.hasAttribute && b.hasAttribute('data-source-mode')) {
                var sm = b.getAttribute('data-md') || '';
                if (sm === 'mermaid') {
                    lines.push('```mermaid');
                    lines.push(b.textContent || '');
                    lines.push('```');
                } else {
                    lines.push(b.textContent || '');
                }
            } else if (b.hasAttribute && b.hasAttribute('data-md') && b.getAttribute('data-md') === 'mermaid') {
                lines.push('```mermaid');
                lines.push(b.getAttribute('data-src') || '');
                lines.push('```');
            } else if (b.hasAttribute && b.hasAttribute('data-md') && b.getAttribute('data-md') === 'htmlfence') {
                lines.push(b.getAttribute('data-src') || '');
            } else if (b.hasAttribute && b.hasAttribute('data-md') && b.getAttribute('data-md') === 'interactive-html') {
                lines.push(b.getAttribute('data-src') || '');
            } else if (b.hasAttribute && b.hasAttribute('data-md') && b.getAttribute('data-md') === 'html') {
                lines.push(b.getAttribute('data-src') || '');
            } else if (b.hasAttribute && b.hasAttribute('data-src')) {
                lines.push(b.getAttribute('data-src') || '');
            } else if (b.tagName === 'HR') {
                lines.push('---');
            } else if (b.tagName === 'PRE') {
                var code = b.querySelector('code');
                lines.push('```');
                if (code) lines.push(code.innerText);
                lines.push('```');
            } else if (b.tagName === 'BLOCKQUOTE' || b.tagName === 'UL' || b.tagName === 'OL') {
                // 嵌套结构：遍历内部带 data-src 的子元素
                var kids = b.querySelectorAll('[data-src]');
                if (kids.length === 0) {
                    lines.push(b.innerText || '');
                } else {
                    for (var j = 0; j < kids.length; j++) pushBlock(kids[j]);
                }
            } else if (b.classList && b.classList.contains('empty-line')) {
                lines.push('');
            } else {
                lines.push(b.innerText || '');
            }
        }
        var blocks = getBlocks();
        for (var i = 0; i < blocks.length; i++) pushBlock(blocks[i]);
        return lines.join('\n');
    }

    // 检测光标所在块变化，按需切换源码/预览
    function syncActiveBlock() {
        if (isComposing) return;
        var block = getCurrentBlock();
        if (block === activeBlock) return;
        // 【修复】跳过刚由回车产生的新空块（仅含 <br>）。这种块进入源码模式后，
        // 输入框没东西可点，用户会认为写作模式卡死。空块保持渲染状态，光标在 <br> 后定位即可。
        if (block && isEmptyBlock(block)) {
            if (activeBlock) exitSourceMode();
            return;
        }
        // 光标移到了另一个块（或移出）→ 旧块恢复渲染，新块进入源码
        enterSourceMode(block);
    }


    // IME 输入法组合状态标记（中文输入法不打断渲染，组合结束后立即重排）
    var isComposing = false;
    editor.addEventListener('compositionstart', function() { isComposing = true; });
    editor.addEventListener('compositionend', function() {
        isComposing = false;
        // 组合结束：同步当前源码块的 data-src，不强制全量渲染
        if (activeBlock) {
            activeBlock.setAttribute('data-src', activeBlock.innerText || '');
            savedMarkdown = collectMarkdown();
        }
        notifyContentChanged();
    });

    // 内容变化通知（防抖，避免每个按键都跨 JS/Python 边界）
    var bridgeNotifyTimer = null;
    function notifyContentChanged() {
        if (bridgeNotifyTimer) clearTimeout(bridgeNotifyTimer);
        bridgeNotifyTimer = setTimeout(function() {
            if (window.bridge && window.bridge.onContentChanged) {
                try { window.bridge.onContentChanged(); } catch(e) {}
            }
        }, 500);
    }

    // 渲染内容
    function render() {
        if (isRendering) return;
        // 用 collectMarkdown 获取最新内容（源码模式块的编辑也能纳入）
        // 保留所有连续换行，不再把多个空行折叠成一个
        var text = collectMarkdown();
        if (text === savedMarkdown && !activeBlock) return;
        isRendering = true;
        try {
            savedMarkdown = text;
            saveCursor();
            var html = renderMarkdown(text);
            editor.innerHTML = html;
            activeBlock = null; // innerHTML 已重建，旧引用失效
            recordHistory();
            restoreCursor();
            // 【性能优化】推迟高亮 / Mermaid / Iframe 到下一帧——这些是耗时操作
            // （hljs 逐块高亮、Mermaid 走 CDN、Iframe 拼接 srcdoc），推迟后从「几秒」
            // 降到「几十毫秒」，预览/写作 切换不卡。
            setTimeout(function() {
                try {
                    var codeBlocks = editor.querySelectorAll('pre code');
                    for (var i = 0; i < codeBlocks.length; i++) {
                        try { if (window.hljs) hljs.highlightElement(codeBlocks[i]); } catch(e) {}
                    }
                } catch(e) {}
                try { renderAllMermaid(); } catch(e) {}
                try { renderAllInteractiveBlocks(); } catch(e) {}
            }, 0);
            updateCurrentLine();
        } finally {
            isRendering = false;
        }
    }

    // 防抖渲染：仅 force=true 时触发（Enter/paste 等结构变化）
    // 普通输入不渲染，由块级源码/预览切换负责显示
    function scheduleRender(force) {
        if (isComposing) return;
        if (renderTimer) clearTimeout(renderTimer);
        if (force) {
            renderTimer = setTimeout(render, 100);
        }
        // 非 force：不渲染（Typora 风格，手动换行才生效）
    }

    // 监听输入：仅同步当前源码块的 data-src，不触发渲染（手动换行才生效）
    editor.addEventListener('input', function() {
        if (isComposing) return;
        if (!activeBlock) {
            // 渲染态直接输入：接管光标所在的任意带 data-src 块并进入源码模式，
            // 保证语法/标签/图片等块无需先点击也可编辑。
            // 用当前显示文本接管，避免覆盖用户刚输入的内容。
            var cur = getCurrentBlock();
            if (cur && cur.nodeType === 1 && cur.hasAttribute && cur.hasAttribute('data-src')) {
                cur.setAttribute('data-src', cur.textContent || '');
                // 【关键】跳过刚由回车产生的新空块（仅含 <br>），否则用户继续输入时
                // 光标在源码卡片里，字符看不见、看似卡死。新空块保持渲染模式，光标在 <br> 后即可正常输入。
                if (cur && isEmptyBlock(cur)) {
                    if (activeBlock) exitSourceMode();
                } else {
                    cur.setAttribute('data-src', cur.textContent || '');
                    cur.setAttribute('data-source-mode', '1');
                    activeBlock = cur;
                }
            }
        }
        if (activeBlock) {
            // 源码模式下用 textContent（保证纯文本无 DOM 元素）
            activeBlock.setAttribute('data-src', activeBlock.textContent || '');
        }

        recordHistory();
        notifyContentChanged();
    });

    // 判断块是否为「空」：仅包含 <br> 或零内容（刚由回车产生的空块）
    function isEmptyBlock(block) {
        if (!block || !block.hasAttribute || !block.hasAttribute('data-src')) return false;
        var srcText = (block.textContent || '').replace(/\u200b/g, '').trim();
        if (srcText !== '') return false;
        // 只包含零个子节点，或唯一子节点是 <br>
        if (block.children.length === 0) return true;
        return block.children.length === 1 && block.children[0].tagName === 'BR';
    }


    // 监听键盘事件 - 自动配对 + 结构变更时强制重排
    editor.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Z 撤销，Ctrl/Cmd + Y / Ctrl+Shift+Z 重做
        if ((e.ctrlKey || e.metaKey) && !e.shiftKey && (e.key === 'z' || e.key === 'Z')) {
            e.preventDefault();
            undo();
            return;
        }
        if ((e.ctrlKey || e.metaKey) &&
            ((e.key === 'y' || e.key === 'Y') || (e.shiftKey && (e.key === 'z' || e.key === 'Z')))) {
            e.preventDefault();
            redo();
            return;
        }

        // 源码模式下 Enter：插入纯文本换行（不生成 <br> DOM，不触发新段落）
        // Shift+Enter 同样只插换行；普通 Enter 按"手动换行触发结构渲染"
        if ((e.key === 'Enter' || e.key === 'NumpadEnter') && activeBlock && !e.ctrlKey && !e.metaKey) {
            if (e.shiftKey) {
                e.preventDefault();
                sourceModeInsertNewline();
                return;
            }
            // 代码块 / 原始 HTML 块内 Enter：只插入换行，不触发全量渲染（避免光标丢失）。
            // 但若此时全文已形成完整 `||| ... |||` 围栏，则全量渲染为 HTML 块。
            var mdTypeEnter = activeBlock.getAttribute('data-md') || '';
            if (mdTypeEnter === 'code' || mdTypeEnter === 'html') {
                e.preventDefault();
                sourceModeInsertNewline();
                if (hasCompleteHtmlFence(snapshot())) {
                    scheduleRender(true);
                }
                return;
            }
            // ||| HTML 围栏：已包含完整结束符时，回车退出编辑块并渲染 HTML；
            // 否则仅插入换行，保持源码编辑状态（光标不丢失）
            if (mdTypeEnter === 'htmlfence') {
                if (isCompleteHtmlFence(activeBlock.textContent || '')) {
                    e.preventDefault();
                    exitSourceMode();
                } else {
                    e.preventDefault();
                    sourceModeInsertNewline();
                }
                return;
            }
            // +++html 交互式围栏：只插入换行，保持编辑状态
            if (mdTypeEnter === 'interactive-html') {
                e.preventDefault();
                sourceModeInsertNewline();
                return;
            }
            // 其他源码块（普通段落/标题/列表项/引用段落等）
            if (activeBlock.tagName === 'LI') {
                e.preventDefault();
                sourceModeInsertNewline();
                scheduleRender(true);
                return;
            }
            // 标题/普通段落/引用段落：按行拆分，令上一行自动渲染样式，
            // 新行保持源码编辑，达到“每一行单独自动显示样式”的效果
            var mdTypeSplit = activeBlock ? (activeBlock.getAttribute('data-md') || '') : '';
            if (mdTypeSplit === 'p' || mdTypeSplit === 'quote' || /^h[1-6]$/.test(mdTypeSplit)) {
                // 【修复】如果当前段落已经是一个完整的 |||...||| 围栏，回车直接退出源码模式并渲染
                // （用户输完 ||| 收尾后再敲一下回车，就该看到 HTML 渲染结果）
                if (mdTypeSplit === 'p') {
                    var enterSrc = activeBlock.textContent || '';
                    if (isCompleteHtmlFence(enterSrc)) {
                        e.preventDefault();
                        exitSourceMode();
                        return;
                    }
                    // 如果当前段落以未闭合的 ||| HTML 围符开头，禁止拆分（会破坏围栏结构），
                    // 改为插一个换行，保持围栏在新行继续编辑
                    if (/^\s*\|\|\|/m.test(enterSrc)) {
                        e.preventDefault();
                        sourceModeInsertNewline();
                        return;
                    }
                }
                e.preventDefault();
                splitCurrentBlock();
                // 【修复】换行后若新块为空（光标在原块末尾），退出源码卡片，
                // 避免反复创建新空源卡片导致"被框框住 / 按回车看不到结果"。
                // 新块仍有内容（光标在原块中间）时，保留源卡片以便继续以原始文本编辑。
                if (activeBlock && !(activeBlock.textContent || '').replace(/​/g, '').trim()) {
                    try { activeBlock.removeAttribute('data-source-mode'); } catch(e) {}
                    activeBlock = null;
                }
                return;
            }
            e.preventDefault();
            sourceModeInsertNewline();

            // 判断当前块是否包含结构语法（标题/列表/分隔线/表格/HTML 围栏/图片等）
            var blockText = activeBlock ? (activeBlock.textContent || '') : '';
            var needStructural = false;
            var blockLines = blockText.split('\n');
            for (var bi = 0; bi < blockLines.length; bi++) {
                if (lineTriggersBlock(blockLines[bi])) { needStructural = true; break; }
            }

            // 只有包含结构语法时才重渲染；普通段落换行保持源码模式，
            // 光标已由 sourceModeInsertNewline 移到新行，不重渲染即可保持光标位置
            if (needStructural) {
                if (hasCompleteHtmlFence(snapshot())) {
                    scheduleRender(true);
                } else {
                    renderLocalAndFocus(activeBlock);
                }
            }
            return;
        }

        // === 自动补全菜单键盘导航拦截 ===
        if (typeof acDropdown !== 'undefined' && acDropdown) {
            if (e.key === 'ArrowUp') { e.preventDefault(); navigateAutocomplete(-1); return; }
            if (e.key === 'ArrowDown') { e.preventDefault(); navigateAutocomplete(1); return; }
            if (e.key === 'Enter') { e.preventDefault(); applyAutocomplete(acDropdown.activeIndex); return; }
            if (e.key === 'Escape') { e.preventDefault(); hideAutocomplete(); return; }
        }

        // === Ctrl+Space 手动触发补全 ===
        if (e.ctrlKey && e.key === ' ') {
            e.preventDefault();
            if (typeof detectAndShowAutocomplete === 'function') detectAndShowAutocomplete();
            return;
        }

        // === Ctrl+Enter 展开 Snippet ===
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            var selS = window.getSelection();
            if (selS.rangeCount > 0) {
                var rangeS = selS.getRangeAt(0);
                var nodeS = rangeS.startContainer;
                if (nodeS.nodeType === 3) {
                    var textS = nodeS.textContent;
                    var offS = rangeS.startOffset;
                    var beforeS = textS.substring(0, offS);
                    var matchS = beforeS.match(/(?:^|\s)(\w+)$/);
                    if (matchS) {
                        var keyword = matchS[1];
                        var allSnippets = (window._builtinSnippets || []).concat(window._userSnippets || []);
                        var found = null;
                        for (var si = 0; si < allSnippets.length; si++) {
                            if (allSnippets[si].prefix === keyword) { found = allSnippets[si]; break; }
                        }
                        if (found) {
                            rangeS.setStart(nodeS, offS - keyword.length);
                            selS.removeAllRanges();
                            selS.addRange(rangeS);
                            document.execCommand('insertText', false, found.body);
                            if (activeBlock) activeBlock.setAttribute('data-src', activeBlock.textContent || '');
                            scheduleRender(true);
                            return;
                        }
                    }
                }
            }
        }

        // === ** 双字符配对 ===
        if (e.key === '*') {
            var starSel = window.getSelection();
            if (starSel.rangeCount > 0 && starSel.isCollapsed) {
                var starRange = starSel.getRangeAt(0);
                var starNode = starRange.startContainer;
                if (starNode.nodeType === 3) {
                    var starText = starNode.textContent;
                    var starOff = starRange.startOffset;
                    if (starOff > 0 && starText[starOff - 1] === '*') {
                        e.preventDefault();
                        starRange.setStart(starNode, starOff - 1);
                        starRange.setEnd(starNode, starOff);
                        starSel.removeAllRanges();
                        starSel.addRange(starRange);
                        document.execCommand('insertText', false, '****');
                        var starSel2 = window.getSelection();
                        var starR2 = starSel2.getRangeAt(0);
                        starR2.setStart(starR2.startContainer, starR2.startOffset - 2);
                        starR2.setEnd(starR2.endContainer, starR2.endOffset - 2);
                        starSel2.removeAllRanges();
                        starSel2.addRange(starR2);
                        return;
                    }
                }
            }
        }

        // === 符号配对 + 选中包裹 ===
        var pairs = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'", '`': '`'};
        var selText = window.getSelection().toString();
        if (pairs[e.key]) {
            if (selText !== '') {
                // 选中包裹：输入配对符号自动包裹选中文本
                e.preventDefault();
                document.execCommand('insertText', false, e.key + selText + pairs[e.key]);
            } else {
                // 空选区配对
                e.preventDefault();
                document.execCommand('insertText', false, e.key + pairs[e.key]);
                var sel = window.getSelection();
                var range = sel.getRangeAt(0);
                range.setStart(range.startContainer, range.startOffset - 1);
                range.setEnd(range.endContainer, range.endOffset - 1);
                sel.removeAllRanges();
                sel.addRange(range);
            }
        }
        if (e.key === 'Tab') {
            e.preventDefault();
            if (activeBlock) {
                // 源码模式：直接插入 4 个空格（避免 contentEditable 产生非文本节点）
                document.execCommand('insertText', false, '    ');
                activeBlock.setAttribute('data-src', activeBlock.textContent || '');
            } else {
                document.execCommand('insertText', false, '    ');
            }
        }
        // 【修复】Ctrl+/ 不再由 JS 侧处理：窗口级 QAction（编辑→切换源码模式，Ctrl+/）
        // 在 WebEngine 持有焦点时同样会触发，两处各 toggle 一次会互相抵消，
        // 表现为「按了快捷键却没切换 / 又跳回编辑模式」。统一交给 Qt 侧幂等处理。
        if ((e.key === 'Enter' || e.key === 'NumpadEnter') && !activeBlock) {
            // 非源码模式：正常段落中按回车不需要任何处理——浏览器已自动创建
            // 新的 <p data-md="p" data-src=""><br></p> 并把光标放入新行。
            // 唯一需要干预的是：空列表项（连续回车退格列表）。这种情况下 DOM 已被我们
            // 实际修改，需要重新渲染。把 scheduleRender 移到 if 内避免触发全量重渲染。
            var sel2 = window.getSelection();
            var node2 = sel2.anchorNode;
            while (node2 && node2.nodeType === 3) node2 = node2.parentNode;
            if (node2 && node2.tagName === 'LI' && node2.textContent.trim() === '') {
                e.preventDefault();
                var parent = node2.parentNode;
                parent.removeChild(node2);
                if (parent.children.length === 0) parent.parentNode.removeChild(parent);
                document.execCommand('insertParagraph', false);
                // 只在空列表项退格时才重渲染（DOM 已被我们改动）
                scheduleRender(true);
            }
            // 【关键修复】普通段落中按回车：不 preventDefault、不 scheduleRender，让浏览器
            // 原生行为（创建新空段 + 放置光标）生效。这样光标永远在用户期望的新行里可见。
        }

        if (e.key === 'Backspace') {
            // === 智能退格：删除配对符号中间的空内容 ===
            var bksel = window.getSelection();
            if (bksel.rangeCount > 0 && bksel.isCollapsed) {
                var bkrange = bksel.getRangeAt(0);
                var bknode = bkrange.startContainer;
                if (bknode.nodeType === 3) {
                    var bktext = bknode.textContent;
                    var bkoff = bkrange.startOffset;
                    var bkPairs = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'", '`': '`', '*': '*'};
                    if (bkoff > 0 && bkoff < bktext.length && bkPairs[bktext[bkoff - 1]] === bktext[bkoff]) {
                        e.preventDefault();
                        bkrange.setStart(bknode, bkoff - 1);
                        bkrange.setEnd(bknode, bkoff + 1);
                        bksel.removeAllRanges();
                        bksel.addRange(bkrange);
                        document.execCommand('delete', false);
                        return;
                    }
                }
            }
            setTimeout(function() {
                // 仅同步 data-src，不触发全量渲染，避免删除时光标乱跳
                if (activeBlock) activeBlock.setAttribute('data-src', activeBlock.textContent || '');
            }, 0);
        }
        if (e.key === 'Delete') {
            setTimeout(function() {
                if (activeBlock) activeBlock.setAttribute('data-src', activeBlock.textContent || '');
            }, 0);
        }
    });

    editor.addEventListener('paste', function(e) {
        // 检测剪贴板中的图片：优先保存为本地文件并插入 markdown 图片语法
        var cd = e.clipboardData;
        var items = cd && cd.items;
        var imageItem = null;
        if (items) {
            for (var k = 0; k < items.length; k++) {
                if (items[k].type && items[k].type.indexOf('image') === 0) {
                    imageItem = items[k];
                    break;
                }
            }
        }
        if (imageItem) {
            e.preventDefault();
            var file = imageItem.getAsFile();
            // 保存粘贴时的光标（异步回调中 selection 可能已失效）
            var sel2 = window.getSelection();
            var savedRange = null;
            if (sel2.rangeCount > 0) {
                savedRange = sel2.getRangeAt(0).cloneRange();
            }
            if (file && window.FileReader) {
                var reader = new FileReader();
                reader.onload = function() {
                    var dataUrl = reader.result;
                    if (!window.bridge || !window.bridge.onPasteImage) {
                        return;
                    }
                    // WebChannel 调用为异步：通过回调接收 markdown 图片片段
                    window.bridge.onPasteImage(dataUrl, function(md) {
                        if (!md) return;
                        // 恢复粘贴时的光标位置（异步回调中 selection 可能已失效）
                        if (savedRange) {
                            var s = window.getSelection();
                            s.removeAllRanges();
                            s.addRange(savedRange);
                        }
                        document.execCommand('insertText', false, md);
                        if (activeBlock) {
                            activeBlock.setAttribute('data-src', activeBlock.textContent || '');
                        } else {
                            var cur = getCurrentBlock();
                            if (cur && cur.nodeType === 1 && cur.hasAttribute && cur.hasAttribute('data-src')) {
                                cur.setAttribute('data-src', cur.textContent || '');
                            }
                        }
                        render();
                        notifyContentChanged();
                    });
                };
                reader.readAsDataURL(file);
            }
            return;
        }
        // 无图片的文本粘贴：插入纯文本并保持源码编辑，不触发全量渲染（避免光标丢失）
        e.preventDefault();
        var text = '';
        try { text = e.clipboardData.getData('text/plain'); } catch (err) {}
        if (text) {
            document.execCommand('insertText', false, text);
        }
        if (!activeBlock) {
            var cur = getCurrentBlock();
            if (cur && cur.nodeType === 1 && cur.hasAttribute && cur.hasAttribute('data-src')) {
                cur.setAttribute('data-src', cur.textContent || '');
                cur.setAttribute('data-source-mode', '1');
                activeBlock = cur;
            }
        }
        if (activeBlock) {
            activeBlock.setAttribute('data-src', activeBlock.textContent || '');
        }
        recordHistory();
        notifyContentChanged();

        // === 自动补全防抖触发 ===
        if (typeof acDebounce !== 'undefined') {
            if (acDebounce) clearTimeout(acDebounce);
            acDebounce = setTimeout(function() { detectAndShowAutocomplete(); }, 200);
        }
    });

    // 失焦：退出源码模式，恢复渲染效果
    editor.addEventListener('blur', function() {
        // 预览模式：纯阅读，没有源码模式可以退出，避免无谓重构 DOM
        if (editorMode === 'preview') return;
        if (!isComposing) exitSourceMode();
    });

    // 源码模式（全局）
    var sourceMode = false;
    function toggleSourceMode() {
        sourceMode = !sourceMode;
        if (sourceMode) {
            exitSourceMode(); // 先退出块级源码模式
            var text = collectMarkdown();
            savedMarkdown = text;
            editor.setAttribute('data-mode', 'source');
            editor.innerText = text;
            // 【修复】源码模式必须可编辑。若从预览模式进入，不恢复 editorMode /
            // contentEditable 的话，页面会停留在 preview 状态：显示源码文本但只读，
            // 且所有事件处理器因 editorMode === 'preview' 提前 return，
            // 表现为「预览切源码后异常停留在预览模式 / 无法编辑」。
            if (editorMode === 'preview') {
                editorMode = 'edit';
                editor.classList.remove('preview-mode');
            }
            editor.contentEditable = 'true';
        } else {
            // 源码 DOM 只有一个纯文本节点，不能调用带“内容未变化”短路的 render()；
            // 否则退出源码模式后仍是纯文本，标题、列表等不会恢复渲染。
            var sourceText = editor.innerText || savedMarkdown || '';
            editor.removeAttribute('data-mode');
            setContentDirect(sourceText);
            editorMode = 'edit';
            editor.contentEditable = 'true';
            editor.classList.remove('preview-mode');
        }
    }

    // 专注模式
    function setFocusMode(enabled) {
        document.body.classList.toggle('focus-mode', enabled);
        updateCurrentLine();
    }

    // 打字机模式
    function setTypewriterMode(enabled) {
        document.body.classList.toggle('typewriter-mode', enabled);
        if (enabled) {
            editor.addEventListener('keyup', scrollToCurrentLine);
            scrollToCurrentLine();
        } else {
            editor.removeEventListener('keyup', scrollToCurrentLine);
        }
    }

    function scrollToCurrentLine() {
        var sel = window.getSelection();
        if (sel.rangeCount === 0) return;
        var node = sel.anchorNode;
        var block = node;
        while (block && block.nodeType !== 1) block = block.parentNode;
        if (block) {
            var rect = block.getBoundingClientRect();
            window.scrollTo(0, rect.top + window.scrollY - window.innerHeight / 2);
        }
    }

    function updateCurrentLine() {
        var sel = window.getSelection();
        if (sel.rangeCount === 0) return;
        var node = sel.anchorNode;
        var block = node;
        while (block && block.nodeType !== 1) block = block.parentNode;
        if (!block || block === editor) return;
        var allBlocks = getBlocks();
        for (var i = 0; i < allBlocks.length; i++) {
            if (allBlocks[i].classList) {
                allBlocks[i].classList.remove('current-line');
                var kids = allBlocks[i].querySelectorAll('.current-line');
                for (var j = 0; j < kids.length; j++) kids[j].classList.remove('current-line');
            }
        }
        if (block !== editor && block.classList) block.classList.add('current-line');
    }

    editor.addEventListener('keyup', function() {
        // 预览模式：纯阅读，键盘事件不影响渲染状态
        if (editorMode === 'preview') return;
        updateCurrentLine();
        syncActiveBlock();
    });

    // Ctrl/Cmd + 鼠标左键点击链接：捕获阶段处理（先于 contenteditable/其他处理器），
    // 直接调用 Python 桥接打开，并保留 acceptNavigationRequest 兜底
    document.addEventListener('click', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.button === 0) {
            var el = e.target;
            var link = null;
            while (el && el !== document) {
                if (el.nodeType === 1 && el.tagName && el.tagName.toLowerCase() === 'a') { link = el; break; }
                el = el.parentNode;
            }
            if (link) {
                var rawHref = link.getAttribute('href') || '';
                if (rawHref) {
                    e.preventDefault();
                    e.stopPropagation();
                    var url = rawHref;
                    if (!/^(https?:|mailto:|ftp:|file:)/i.test(url)) {
                        url = 'http://' + url;
                    }
                    // 主路径：原生 window.open -> createWindow -> acceptNavigationRequest
                    var win = null;
                    try { win = window.open(url, '_blank'); } catch (err) {}
                    if (!win && window.bridge && window.bridge.onOpenExternal) {
                        try { window.bridge.onOpenExternal(url); } catch (err) {}
                    }
                }
            }
        }
    }, true);

    editor.addEventListener('click', function(e) {
        // 预览模式：纯阅读，不响应任何编辑型点击（不切换源码模式、不进入交互式 HTML 编辑、不切换活动块）。
        // 链接跳转仍由 document 级的 capture click 处理（Ctrl+点击），与此处互不冲突。
        if (editorMode === 'preview') return;
        updateCurrentLine();
        // 点击交互式 HTML 块：进入编辑模式
        var ihbTarget = e.target;
        while (ihbTarget && ihbTarget !== editor) {
            if (ihbTarget.classList && ihbTarget.classList.contains('interactive-html-block')) break;
            ihbTarget = ihbTarget.parentNode;
        }
        if (ihbTarget && ihbTarget !== editor && ihbTarget.classList.contains('interactive-html-block') && !ihbTarget.classList.contains('editing')) {
            enterInteractiveHtmlEdit(ihbTarget);
            return;
        }
        // 点击图片：进入其所在块源码模式，方便编辑图片地址/alt
        if (e.target && e.target.tagName === 'IMG') {
            var t = e.target;
            while (t && t !== editor && !(t.hasAttribute && t.hasAttribute('data-src'))) {
                t = t.parentNode;
            }
            if (t && t !== editor && t.hasAttribute && t.hasAttribute('data-src')) {
                enterSourceMode(t);
                updateCurrentLine();
                return;
            }
        }
        syncActiveBlock();
    });
    // 鼠标移开编辑器：退出源码模式显示渲染效果
    editor.addEventListener('mouseleave', function() {
        // 预览模式：纯阅读，没有源码模式可以退出
        if (editorMode === 'preview') return;
        if (!isComposing) exitSourceMode();
    });

    // 主题切换
    function setDarkMode(dark) {
        document.documentElement.classList.toggle('dark', dark);
        if (window.mermaid) {
            try {
                window.mermaid.initialize({ startOnLoad: false, securityLevel: 'loose', theme: dark ? 'dark' : 'default' });
            } catch(e) {}
            renderAllMermaid();
        }
    }

    // 预览模式：纯阅读，只读，渲染 Markdown
    function enterPreviewMode() {
        if (editorMode === 'preview') return;
        // 退出块级/全局源码模式，并保留全局源码编辑器中的纯文本。
        if (activeBlock) exitSourceMode();
        var text;
        if (sourceMode) {
            text = editor.innerText || savedMarkdown || '';
            sourceMode = false;
            editor.removeAttribute('data-mode');
        } else {
            // 兜底：如果 DOM 中收集到空文本（页面刚加载、pending 未应用 等场景），使用 savedMarkdown 作为后备。
            // 否则预览模式会出现空白页。F1/F6 修复后场景不多了，但仍保留这道防线。
            text = collectMarkdown() || savedMarkdown || '';
        }
        editorMode = 'preview';
        // 【性能优化】同步设置主结构（renderMarkdown）让用户立即看到文本；
        // 高亮 / Mermaid / Iframe 推迟到下一帧（这些是耗时操作，能从几秒降到几十毫秒）
        savedMarkdown = text;
        editor.innerHTML = renderMarkdown(text);
        editor.contentEditable = 'false';
        editor.classList.add('preview-mode');
        editor.style.display = 'block';
        editor.style.visibility = 'visible';
        setTimeout(function() {
            try {
                var codeBlocks = editor.querySelectorAll('pre code');
                for (var i = 0; i < codeBlocks.length; i++) {
                    try { if (window.hljs) hljs.highlightElement(codeBlocks[i]); } catch(e) {}
                }
            } catch(e) {}
            try { renderAllMermaid(); } catch(e) {}
            try { renderAllInteractiveBlocks(); } catch(e) {}
        }, 0);
    }

    // 编辑模式：所见即所得
    function enterEditMode() {
        // 全局源码模式与 editorMode 独立；即使 editorMode 已是 edit，也必须重建渲染 DOM。
        if (sourceMode) {
            var sourceText = editor.innerText || savedMarkdown || '';
            sourceMode = false;
            editor.removeAttribute('data-mode');
            setContentDirect(sourceText);
        }
        if (editorMode === 'edit') {
            editor.contentEditable = 'true';
            editor.classList.remove('preview-mode');
            return;
        }
        editorMode = 'edit';
        editor.contentEditable = 'true';
        editor.classList.remove('preview-mode');
        // 退出预览模式时重置 activeBlock，确保回车键正常工作
        activeBlock = null;
        render();
    }

    // 切换预览/编辑模式
    function togglePreviewMode() {
        if (editorMode === 'preview') {
            enterEditMode();
        } else {
            enterPreviewMode();
        }
        return editorMode;
    }

    // ===== 自动补全下拉菜单系统 =====
    var acDropdown = null;
    var acDebounce = null;

    // --- 内置 Snippet 定义 ---
    window._builtinSnippets = [
        { prefix: 'table', desc: '3x3 \u8868\u683c', body: '| \u52171 | \u52172 | \u52173 |\n| --- | --- | --- |\n|  |  |  |\n|  |  |  |\n|  |  |  |' },
        { prefix: 'table5x3', desc: '5\u884c3\u5217\u8868\u683c', body: '| \u52171 | \u52172 | \u52173 |\n| --- | --- | --- |\n|  |  |  |\n|  |  |  |\n|  |  |  |\n|  |  |  |\n|  |  |  |' },
        { prefix: 'mermaid', desc: 'Mermaid \u6d41\u7a0b\u56fe', body: '```mermaid\ngraph TD\n    A[\u5f00\u59cb] --> B{\u5224\u65ad}\n    B -->|\u662f| C[\u6267\u884c]\n    B -->|\u5426| D[\u7ed3\u675f]\n```' },
        { prefix: 'sequence', desc: 'Mermaid \u65f6\u5e8f\u56fe', body: '```mermaid\nsequenceDiagram\n    Alice->>Bob: \u4f60\u597d\n    Bob-->>Alice: \u4f60\u597d\uff01\n```' },
        { prefix: 'html', desc: 'HTML \u4ea4\u4e92\u5757', body: '\n+++html\n\n+++\n' },
        { prefix: 'task', desc: '\u4efb\u52a1\u5217\u8868', body: '- [ ] ' },
        { prefix: 'math', desc: '\u5757\u7ea7\u516c\u5f0f', body: '\n$$\n\n$$\n' },
        { prefix: 'inlinemath', desc: '\u884c\u5185\u516c\u5f0f', body: '$ $' },
        { prefix: 'toc', desc: '\u76ee\u5f55', body: '[TOC]' },
        { prefix: 'cite', desc: '\u811a\u6ce8', body: '[^1]: ' },
    ];
    window._userSnippets = [];
    window._recentLinks = [];
    window._projectImages = [];
    window._fileList = [];

    function showAutocomplete(items, type, prefix) {
        hideAutocomplete();
        if (!items || items.length === 0) return;
        var el = document.createElement('div');
        el.className = 'autocomplete-dropdown';
        var sel = window.getSelection();
        if (sel.rangeCount > 0) {
            var rect = sel.getRangeAt(0).getBoundingClientRect();
            el.style.left = rect.left + 'px';
            el.style.top = (rect.bottom + 4) + 'px';
        }
        acDropdown = { el: el, items: items, activeIndex: 0, type: type, prefix: prefix };
        renderAutocompleteItems();
        document.body.appendChild(el);
    }

    function hideAutocomplete() {
        if (acDropdown && acDropdown.el && acDropdown.el.parentNode) {
            acDropdown.el.parentNode.removeChild(acDropdown.el);
        }
        acDropdown = null;
    }

    function renderAutocompleteItems() {
        if (!acDropdown) return;
        acDropdown.el.innerHTML = '';
        acDropdown.items.forEach(function(item, idx) {
            var div = document.createElement('div');
            div.className = 'autocomplete-item' + (idx === acDropdown.activeIndex ? ' active' : '');
            div.innerHTML = '<span class="ac-icon">' + (item.icon || '') + '</span>'
                + '<span class="ac-label">' + item.label + '</span>'
                + (item.desc ? '<span class="ac-desc">' + item.desc + '</span>' : '');
            div.addEventListener('mousedown', function(ev) {
                ev.preventDefault();
                applyAutocomplete(idx);
            });
            acDropdown.el.appendChild(div);
        });
        var activeEl = acDropdown.el.querySelector('.active');
        if (activeEl) activeEl.scrollIntoView({ block: 'nearest' });
    }

    function applyAutocomplete(idx) {
        if (!acDropdown || idx < 0 || idx >= acDropdown.items.length) return;
        var item = acDropdown.items[idx];
        var type = acDropdown.type;
        hideAutocomplete();
        if (type === 'snippet' || type === 'htmlblock') {
            deletePrefixAndInsert(item.body);
        } else if (type === 'lang') {
            deletePrefixAndInsert(item.label);
        } else if (type === 'link' || type === 'image' || type === 'path') {
            deletePrefixAndInsert(item.value || item.label);
        }
    }

    function deletePrefixAndInsert(text) {
        if (!acDropdown || !acDropdown.prefix || acDropdown.prefix.length === 0) {
            document.execCommand('insertText', false, text);
            if (activeBlock) activeBlock.setAttribute('data-src', activeBlock.textContent || '');
            return;
        }
        var len = acDropdown.prefix.length;
        var sel = window.getSelection();
        if (sel.rangeCount > 0) {
            var range = sel.getRangeAt(0);
            range.setStart(range.startContainer, range.startOffset - len);
            sel.removeAllRanges();
            sel.addRange(range);
        }
        document.execCommand('insertText', false, text);
        if (activeBlock) activeBlock.setAttribute('data-src', activeBlock.textContent || '');
    }

    function navigateAutocomplete(direction) {
        if (!acDropdown) return false;
        acDropdown.activeIndex = (acDropdown.activeIndex + direction + acDropdown.items.length) % acDropdown.items.length;
        renderAutocompleteItems();
        return true;
    }

    // --- 补全检测引擎 ---
    function detectAndShowAutocomplete() {
        if (editorMode === 'preview') return;
        var ctx = getAutocompleteContext();
        if (!ctx) { hideAutocomplete(); return; }
        if (ctx.type === 'lang') {
            showAutocomplete(getLangCompletions(ctx.query), 'lang', ctx.query);
        } else if (ctx.type === 'link') {
            showAutocomplete(getLinkCompletions(ctx.query), 'link', ctx.query);
        } else if (ctx.type === 'image') {
            showAutocomplete(getImageCompletions(ctx.query), 'image', ctx.query);
        } else if (ctx.type === 'path') {
            showAutocomplete(getPathCompletions(ctx.query), 'path', ctx.query);
        } else if (ctx.type === 'htmlblock') {
            showAutocomplete(getHtmlBlockCompletions(ctx.query), 'htmlblock', ctx.query);
        } else if (ctx.type === 'snippet') {
            showAutocomplete(getSnippetCompletions(ctx.query), 'snippet', ctx.query);
        } else {
            hideAutocomplete();
        }
    }

    function getAutocompleteContext() {
        var sel = window.getSelection();
        if (!sel.rangeCount || !sel.isCollapsed) return null;
        var range = sel.getRangeAt(0);
        var node = range.startContainer;
        if (node.nodeType !== 3) return null;
        var text = node.textContent;
        var off = range.startOffset;
        var before = text.substring(0, off);

        // \u4ee3\u7801\u8bed\u8a00\u8865\u5168\uff1a``` \u540e
        var langMatch = before.match(/```(\w*)$/);
        if (langMatch) return { type: 'lang', query: langMatch[1] };

        // \u56fe\u7247\u8865\u5168\uff1a![ \u5f00\u5934
        var imgMatch = before.match(/!\[([^\]]*)$/);
        if (imgMatch) return { type: 'image', query: imgMatch[1] };

        // \u94fe\u63a5\u8865\u5168\uff1a[ \u5f00\u5934\uff08\u4e0d\u662f ![\uff09
        var linkIdx = before.lastIndexOf('[');
        if (linkIdx >= 0 && (linkIdx === 0 || before[linkIdx - 1] !== '!')) {
            var afterBracket = before.substring(linkIdx + 1);
            if (!/\]/.test(afterBracket)) {
                return { type: 'link', query: afterBracket };
            }
        }

        // \u6587\u4ef6\u8def\u5f84\u8865\u5168\uff1a]( \u5185\u90e8
        var pathMatch = before.match(/\]\(([^)]*)$/);
        if (pathMatch) return { type: 'path', query: pathMatch[1] };

        // HTML \u5757\u8865\u5168\uff1a+++h \u7b49
        var htmlMatch = before.match(/^\+\+\+(\w*)$/);
        if (htmlMatch) return { type: 'htmlblock', query: htmlMatch[1] };

        // Snippet \u8865\u5168\uff1a\u884c\u9996\u6216\u7a7a\u683c\u540e\u7684\u5173\u952e\u8bcd
        var snippetMatch = before.match(/(?:^|\s)(\w+)$/);
        if (snippetMatch && snippetMatch[1].length >= 2) {
            return { type: 'snippet', query: snippetMatch[1] };
        }

        return null;
    }

    // --- \u5404\u8865\u5168\u6570\u636e\u6e90 ---
    function getLangCompletions(query) {
        var langs = ['python','javascript','typescript','html','css','java','c','cpp','csharp',
            'go','rust','ruby','php','swift','kotlin','sql','bash','shell','json','yaml','xml',
            'markdown','dockerfile','makefile','toml','mermaid','plaintext'];
        return langs.filter(function(l) { return !query || l.indexOf(query.toLowerCase()) === 0; })
            .map(function(l) { return { label: l, icon: '{}' }; });
    }

    function getLinkCompletions(query) {
        var items = (window._recentLinks || []).filter(function(item) {
            return !query || item.label.toLowerCase().indexOf(query.toLowerCase()) >= 0;
        });
        return items.length ? items : [{ label: '\u8f93\u5165\u94fe\u63a5\u5730\u5740...', icon: '\ud83d\udd17', value: '' }];
    }

    function getImageCompletions(query) {
        return (window._projectImages || []).filter(function(item) {
            return !query || item.label.toLowerCase().indexOf(query.toLowerCase()) >= 0;
        });
    }

    function getPathCompletions(query) {
        return (window._fileList || []).filter(function(item) {
            return !query || item.label.toLowerCase().indexOf(query.toLowerCase()) >= 0;
        });
    }

    function getHtmlBlockCompletions(query) {
        var items = [
            { label: '+++html', desc: 'HTML \u4ea4\u4e92\u5757', body: '\n+++html\n\n+++\n', icon: '<>' },
        ];
        if (typeof INTERACTIVE_HTML_TEMPLATES !== 'undefined') {
            Object.keys(INTERACTIVE_HTML_TEMPLATES).forEach(function(key) {
                items.push({ label: '+++html-' + key, desc: key + ' \u6a21\u677f',
                    body: '\n+++html\n' + INTERACTIVE_HTML_TEMPLATES[key] + '\n+++\n', icon: '<>' });
            });
        }
        return items.filter(function(item) {
            return !query || item.label.toLowerCase().indexOf(query.toLowerCase()) >= 0;
        });
    }

    function getSnippetCompletions(query) {
        var all = (window._builtinSnippets || []).concat(window._userSnippets || []);
        if (!query) return all;
        var q = query.toLowerCase();
        return all.filter(function(s) {
            return s.prefix.toLowerCase().indexOf(q) >= 0 || fuzzyMatch(q, s.prefix.toLowerCase());
        });
    }

    function fuzzyMatch(query, target) {
        var qi = 0;
        for (var ti = 0; ti < target.length && qi < query.length; ti++) {
            if (target[ti] === query[qi]) qi++;
        }
        return qi === query.length;
    }

    // 公开接口

    // ===== 查找/替换 助手（Bug-12 增强）=====
    var _findState = {
        query: '',
        matches: [],          // 所有匹配节点的 DOM 引用（按顺序）
        index: -1,            // 当前选中索引（-1 表示未选中）
        caseSensitive: false,
        wholeWord: false,
        scrollPending: false  // 滚动到当前匹配
    };

    // 清除之前的高亮（恢复原始 innerHTML）
    function findClear() {
        if (!_findState.matches.length) return;
        var editorEl = document.getElementById('editor');
        // 移除所有 <mark class="find-match"> 包装
        var marks = editorEl.querySelectorAll('mark.find-match');
        for (var i = 0; i < marks.length; i++) {
            var m = marks[i];
            var parent = m.parentNode;
            while (m.firstChild) parent.insertBefore(m.firstChild, m);
            parent.removeChild(m);
        }
        // 合并相邻文本节点（normalize）
        editorEl.normalize();
        _findState.matches = [];
        _findState.index = -1;
    }

    // 高亮所有匹配项并返回数量
    function findHighlight(query, caseSensitive, wholeWord) {
        findClear();
        if (!query) return 0;
        _findState.query = query;
        _findState.caseSensitive = !!caseSensitive;
        _findState.wholeWord = !!wholeWord;

        var editorEl = document.getElementById('editor');
        // 收集所有文本节点
        var walker = document.createTreeWalker(editorEl, NodeFilter.SHOW_TEXT, {
            acceptNode: function(node) {
                // 跳过脚本/样式/输入框等非内容节点
                if (!node.parentNode) return NodeFilter.FILTER_REJECT;
                var p = node.parentNode;
                while (p && p !== editorEl) {
                    if (p.tagName === 'SCRIPT' || p.tagName === 'STYLE') {
                        return NodeFilter.FILTER_REJECT;
                    }
                    p = p.parentNode;
                }
                return NodeFilter.FILTER_ACCEPT;
            }
        }, false);

        var textNodes = [];
        var tn;
        while ((tn = walker.nextNode())) {
            // 跳过源码模式块（用户在编辑源码，不应高亮）
            var p = tn.parentNode;
            var inSourceMode = false;
            while (p && p !== editorEl) {
                if (p.hasAttribute && p.hasAttribute('data-source-mode')) {
                    inSourceMode = true;
                    break;
                }
                p = p.parentNode;
            }
            if (inSourceMode) continue;
            // 跳过空文本节点
            if (!tn.nodeValue) continue;
            textNodes.push(tn);
        }

        // 匹配：构造正则
        var escaped = query.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
        var pattern = escaped;
        if (wholeWord) {
            pattern = '\\\\b' + pattern + '\\\\b';
        }
        var flags = caseSensitive ? 'g' : 'gi';
        var regex;
        try {
            regex = new RegExp(pattern, flags);
        } catch (e) {
            return 0;
        }

        // 收集所有匹配位置（避免匹配跨越节点边界）
        var allMatches = [];
        for (var i = 0; i < textNodes.length; i++) {
            var node = textNodes[i];
            var text = node.nodeValue;
            regex.lastIndex = 0;
            var m;
            while ((m = regex.exec(text)) !== null) {
                if (m[0].length === 0) {
                    regex.lastIndex++;
                    continue;
                }
                allMatches.push({
                    node: node,
                    start: m.index,
                    end: m.index + m[0].length
                });
            }
        }

        // 用 <mark> 包裹匹配项（从后往前遍历，避免 offset 失效）
        _findState.matches = [];
        for (var k = allMatches.length - 1; k >= 0; k--) {
            var match = allMatches[k];
            var node = match.node;
            var text = node.nodeValue;
            var before = text.slice(0, match.start);
            var hit = text.slice(match.start, match.end);
            var after = text.slice(match.end);

            var mark = document.createElement('mark');
            mark.className = 'find-match';
            mark.textContent = hit;

            var beforeNode = document.createTextNode(before);
            var afterNode = document.createTextNode(after);

            var parent = node.parentNode;
            parent.insertBefore(beforeNode, node);
            parent.insertBefore(mark, node);
            if (afterNode.nodeValue) {
                parent.insertBefore(afterNode, node);
            }
            parent.removeChild(node);

            _findState.matches.unshift(mark);
        }

        _findState.index = _findState.matches.length > 0 ? 0 : -1;
        if (_findState.index >= 0) {
            _scrollToCurrentMatch();
        }
        return _findState.matches.length;
    }

    function _scrollToCurrentMatch() {
        if (_findState.index < 0 || _findState.index >= _findState.matches.length) return;
        var m = _findState.matches[_findState.index];
        if (!m) return;
        try {
            m.scrollIntoView({ block: 'center', behavior: 'auto' });
        } catch(e) {}
        // 高亮当前匹配（加亮颜色），其他保持暗淡
        for (var i = 0; i < _findState.matches.length; i++) {
            if (i === _findState.index) {
                _findState.matches[i].classList.add('find-current');
            } else {
                _findState.matches[i].classList.remove('find-current');
            }
        }
    }

    function findCurrentIndex() {
        return _findState.index;
    }

    function findTotalCount() {
        return _findState.matches.length;
    }

    function findNext(query, caseSensitive) {
        if (!_findState.matches.length) return false;
        _findState.index = (_findState.index + 1) % _findState.matches.length;
        _scrollToCurrentMatch();
        return true;
    }

    function findPrev(query, caseSensitive) {
        if (!_findState.matches.length) return false;
        _findState.index = (_findState.index - 1 + _findState.matches.length) % _findState.matches.length;
        _scrollToCurrentMatch();
        return true;
    }

    // 替换当前匹配项
    function replaceOne(findText, replaceText, caseSensitive) {
        if (_findState.index < 0 || _findState.index >= _findState.matches.length) {
            // 没有当前匹配，尝试找下一个
            if (_findState.matches.length === 0) {
                // 重新高亮
                findHighlight(findText, caseSensitive, false);
            }
            if (_findState.matches.length === 0) return 0;
            _findState.index = 0;
        }
        var currentMark = _findState.matches[_findState.index];
        if (!currentMark) return 0;
        // 替换文本
        var newText = document.createTextNode(replaceText);
        currentMark.parentNode.insertBefore(newText, currentMark);
        currentMark.parentNode.removeChild(currentMark);
        // 从匹配列表中移除
        _findState.matches.splice(_findState.index, 1);
        if (_findState.index >= _findState.matches.length) {
            _findState.index = _findState.matches.length - 1;
        }
        // 同步 Markdown 源码（通过 collectMarkdown），并触发通知
        if (window.editorAPI && window.editorAPI.notifyContentChangedSync) {
            window.editorAPI.notifyContentChangedSync();
        } else if (typeof notifyContentChanged === 'function') {
            notifyContentChanged();
        }
        // 重新高亮剩余匹配（因为 DOM 变化可能影响匹配位置）
        findHighlight(findText, caseSensitive, false);
        if (_findState.index >= _findState.matches.length && _findState.matches.length > 0) {
            _findState.index = 0;
        }
        _scrollToCurrentMatch();
        return 1;
    }

    // 替换所有匹配项（直接在 Markdown 源码层做替换，避免 DOM 操作复杂）
    function replaceAll(findText, replaceText, caseSensitive) {
        if (!findText) return 0;
        // 取当前 Markdown 源码
        var src = (window.editorAPI && window.editorAPI.getContentSync) ?
            window.editorAPI.getContentSync() :
            (typeof collectMarkdown === 'function' ? collectMarkdown() : '');
        if (!src) return 0;
        var flags = caseSensitive ? 'g' : 'gi';
        var pattern;
        try {
            pattern = new RegExp(findText.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&'), flags);
        } catch(e) {
            return 0;
        }
        var newSrc = src.replace(pattern, function(m) { return replaceText; });
        if (newSrc === src) return 0;
        var matchCount = (src.match(pattern) || []).length;
        // 写回编辑器
        if (window.editorAPI && window.editorAPI.setContentSync) {
            window.editorAPI.setContentSync(newSrc);
        } else if (typeof window.editorAPI !== 'undefined' && window.editorAPI.setContent) {
            window.editorAPI.setContent(newSrc);
        }
        // 重新高亮
        findHighlight(findText, caseSensitive, false);
        return matchCount;
    }


    window.editorAPI = {
        render: render,
        getContent: function() {
            // 优先用 collectMarkdown，确保源码模式块的编辑被纳入
            if (activeBlock) savedMarkdown = collectMarkdown();
            return savedMarkdown || editor.innerText;
        },
        setContent: function(text) {
            activeBlock = null;
            sourceMode = false;
            savedMarkdown = text;
            editor.removeAttribute('data-mode');
            // 【性能优化】先设置文本（同步、必需、让用户马上看到内容），
            // 推迟 highlight / Mermaid / Iframe 到下一帧——这几个是耗时操作
            // （highlight 逐块同步高亮、Mermaid 走 CDN、Iframe 拼接 srcdoc），
            // 推迟后 setContent 总耗时从几秒降到几十毫秒，文件切换不卡。
            editor.innerHTML = renderMarkdown(text);
            assignBlockIds();
            // 【修复】保留之前的模式状态，避免分栏模式右侧预览被 setContent 意外重置为编辑模式
            // （之前会无条件设为 edit，导致右侧预览在源面板编辑后短暂进入可编辑状态、交互
            //  HTML 块出现编辑提示、点击事件也会被切换 → 反复输入看起来像“卡死”）
            if (editorMode !== 'preview') {
                editorMode = 'edit';
                editor.contentEditable = 'true';
                editor.classList.remove('preview-mode');
            }
            resetHistory(text);
            // 延迟执行高亮 / Mermaid / Iframe（不影响主结构）
            setTimeout(function() {
                try {
                    var codeBlocks = editor.querySelectorAll('pre code');
                    for (var i = 0; i < codeBlocks.length; i++) {
                        try { if (window.hljs) hljs.highlightElement(codeBlocks[i]); } catch(e) {}
                    }
                } catch(e) {}
                try { renderAllMermaid(); } catch(e) {}
                try { renderAllInteractiveBlocks(); } catch(e) {}
            }, 0);
        },
        _saveContentDirect: function(text) {
            // 手动重建 DOM 的版本（用于 setContentSync），同步执行所有渲染
            activeBlock = null;
            sourceMode = false;
            savedMarkdown = text;
            editor.removeAttribute('data-mode');
            editor.innerHTML = renderMarkdown(text);
            assignBlockIds();
            editorMode = 'edit';
            editor.contentEditable = 'true';
            editor.classList.remove('preview-mode');
            try {
                var codeBlocks = editor.querySelectorAll('pre code');
                for (var i = 0; i < codeBlocks.length; i++) {
                    try { if (window.hljs) hljs.highlightElement(codeBlocks[i]); } catch(e) {}
                }
            } catch(e) {}
            try { renderAllMermaid(); } catch(e) {}
            try { renderAllInteractiveBlocks(); } catch(e) {}
            resetHistory(text);
        },
        // \u6027\u80fd\u8c03\u4f18\uff1a\u8c03\u8282\u9632\u6296\u6e32\u67d3\u5ef6\u8fdf\uff08ms\uff09
        setRenderDelay: function(ms) {
            var n = parseInt(ms, 10);
            if (isFinite(n) && n >= 50 && n <= 2000) renderDelayMs = n;
        },
        // \u8c03\u8bd5\u7528\uff1a\u8fd4\u56de\u589e\u91cf\u6e32\u67d3\u7edf\u8ba1
        getRenderStats: function() {
            return {
                blockCount: (window._editorBlocks || 0),
                lastRenderMs: (window._lastRenderMs || 0),
                incremental: !!window._lastIncremental
            };
        },
        // \u8c03\u8bd5\u7528\uff1a\u89e6\u53d1\u624b\u52a8\u5168\u91cf\u91cd\u6e32\u67d3
        forceFullRender: function() {
            savedMarkdown = '';
            render();
        },
        // 设置当前 md 文件所在目录（file:/// 前缀绝对路径），用于解析相对图片
        setBaseDir: function(dir) {
            baseDir = dir || '';
        },
        // 在当前光标位置插入文本（用于菜单插入图片/格式等）
        insertTextAtCursor: function(text) {
            if (editorMode === 'preview') return;
            var sel = window.getSelection();
            if (sel.rangeCount > 0) {
                document.execCommand('insertText', false, text);
            }
            // 若处于源码模式，同步 data-src（源码模式为纯文本，用 textContent）
            if (activeBlock) activeBlock.setAttribute('data-src', activeBlock.textContent || '');
            notifyContentChanged();
        },
        setDarkMode: setDarkMode,
        setFocusMode: setFocusMode,
        setTypewriterMode: setTypewriterMode,
        toggleSourceMode: toggleSourceMode,
        isSourceMode: function() { return sourceMode; },
        // 直接设置为源码模式（避免 toggle 误触友友状态）
        setSourceMode: function(enabled) {
                if ( enabled && !sourceMode ) toggleSourceMode();
                else if ( !enabled && sourceMode ) toggleSourceMode();
        },
        // 直接设置为预览/编辑模式
        setPreviewMode: function(enabled) {
                if ( enabled && editorMode !== 'preview' ) enterPreviewMode();
                else if ( !enabled && editorMode === 'preview' ) enterEditMode();
        },
        isEditMode: function() { return editorMode === 'edit'; },
        isPreviewMode: function() { return editorMode === 'preview'; },
        togglePreviewMode: togglePreviewMode,
        enterEditMode: enterEditMode,
        enterPreviewMode: enterPreviewMode,
        insertInteractiveHtmlTemplate: function(templateKey) {
            if (editorMode === 'preview') return;
            var tpl = INTERACTIVE_HTML_TEMPLATES[templateKey];
            if (!tpl) return;
            window.editorAPI.insertTextAtCursor('\n+++html\n' + tpl + '\n+++\n');
            scheduleRender(true);
        },
        getEditorState: function() {
            var scrollLeft = editor.scrollLeft || 0;
            var scrollTop = editor.scrollTop || 0;
            var cursorOffset = null;
            var selectionStart = null;
            var selectionEnd = null;
            try {
                var sel = window.getSelection();
                if (sel.rangeCount > 0 && editor.contains(sel.anchorNode)) {
                    var range = sel.getRangeAt(0);
                    var pre = document.createRange();
                    pre.selectNodeContents(editor);
                    pre.setEnd(range.startContainer, range.startOffset);
                    cursorOffset = pre.toString().length;
                    if (!range.collapsed) {
                        selectionStart = cursorOffset;
                        var pre2 = document.createRange();
                        pre2.selectNodeContents(editor);
                        pre2.setEnd(range.endContainer, range.endOffset);
                        selectionEnd = pre2.toString().length;
                    }
                }
            } catch(e) {}
            return { scrollLeft: scrollLeft, scrollTop: scrollTop, cursorOffset: cursorOffset, selectionStart: selectionStart, selectionEnd: selectionEnd };
        },
        setEditorState: function(state) {
            if (!state) return;
            try {
                editor.scrollTop = state.scrollTop || 0;
                editor.scrollLeft = state.scrollLeft || 0;
                if (state.cursorOffset != null) {
                    var offset = Math.max(0, state.cursorOffset);
                    var range = document.createRange();
                    var walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT, null, false);
                    var count = 0, node;
                    while ((node = walker.nextNode())) {
                        var len = node.textContent.length;
                        if (count + len >= offset) {
                            if (state.selectionStart != null && state.selectionEnd != null && state.selectionEnd > state.selectionStart) {
                                var endOffset = Math.max(0, state.selectionEnd);
                                var walker2 = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT, null, false);
                                var count2 = 0, node2;
                                while ((node2 = walker2.nextNode())) {
                                    var len2 = node2.textContent.length;
                                    if (count2 + len2 >= endOffset) {
                                        var r = document.createRange();
                                        r.setStart(node, Math.max(0, offset - count));
                                        r.setEnd(node2, Math.max(0, endOffset - count2));
                                        var sel = window.getSelection();
                                        sel.removeAllRanges();
                                        sel.addRange(r);
                                        break;
                                    }
                                    count2 += len2;
                                }
                            } else {
                                range.setStart(node, Math.max(0, offset - count));
                                range.collapse(true);
                                var sel2 = window.getSelection();
                                sel2.removeAllRanges();
                                sel2.addRange(range);
                            }
                            break;
                        }
                        count += len;
                    }
                }
            } catch(e) {}
        },
        // ===== 查找/替换 API（Bug-12）=====
        findHighlight: function(query, caseSensitive, wholeWord) {
            return findHighlight(query, caseSensitive, wholeWord);
        },
        findClear: function() {
            return findClear();
        },
        findNext: function(query, caseSensitive) {
            return findNext(query, caseSensitive);
        },
        findPrev: function(query, caseSensitive) {
            return findPrev(query, caseSensitive);
        },
        findCurrentIndex: function() {
            return findCurrentIndex();
        },
        findTotalCount: function() {
            return findTotalCount();
        },
        replaceOne: function(findText, replaceText, caseSensitive) {
            return replaceOne(findText, replaceText, caseSensitive);
        },
        replaceAll: function(findText, replaceText, caseSensitive) {
            return replaceAll(findText, replaceText, caseSensitive);
        },
        getContentSync: function() {
            // 同步获取当前 Markdown 源码（用于 find/replaceAll）
            return typeof collectMarkdown === 'function' ? collectMarkdown() : '';
        },
        setContentSync: function(text) {
            // 同步设置内容（用于 find/replaceAll 完成后更新）
            if (typeof setContentDirect === 'function') {
                setContentDirect(text);
            }
        },
        notifyContentChangedSync: function() {
            // 同步通知内容变化（用于 find/replaceOne 后）
            if (typeof notifyContentChanged === 'function') {
                notifyContentChanged();
            }
        },
        setCompletionData: function(data) {
            if (!data) return;
            if (data.recentLinks) window._recentLinks = data.recentLinks;
            if (data.projectImages) window._projectImages = data.projectImages;
            if (data.fileList) window._fileList = data.fileList;
            if (data.userSnippets) window._userSnippets = data.userSnippets;
        }
    };

    // 初始化
    // QWebChannel：连接 Python bridge
    new QWebChannel(qt.webChannelTransport, function(channel) {
        window.bridge = channel.objects.bridge;
    });
    window.editorAPI.setContent('');

})();
</script>

</body>
</html>"""

# ============================================================
# 编辑器页面/视图类
# ============================================================


class EditorWebView(QWebEngineView):
    """重写 createWindow：拦截新窗口请求，由系统浏览器打开其导航。"""

    def __init__(self, open_url_callback=None, parent=None):
        super().__init__(parent)
        self._open_url_callback = open_url_callback
        self._popups = []

    def createWindow(self, window_type):
        popup = QWebEngineView(self)
        profile = self.page().profile() if self.page() else QWebEngineProfile.defaultProfile()
        page = EditorPage(profile, open_url_callback=self._open_url_callback)
        popup.setPage(page)
        popup.resize(8, 8)
        popup.show()
        popup.hide()
        self._popups.append(popup)
        return popup


class EditorPage(QWebEnginePage):
    """自定义 WebEngine 页面，用于 JS 通信"""
    def __init__(self, parent=None, open_url_callback=None):
        super().__init__(parent)
        self._open_url_callback = open_url_callback

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # 开发时调试用
        pass

    def acceptNavigationRequest(self, url, nav_type, isMainFrame):
        """拦截所有网页类导航，转由系统浏览器打开，避免编辑器页面跳走"""
        try:
            scheme = url.scheme().lower()
            if scheme in ('http', 'https', 'mailto', 'ftp'):
                if self._open_url_callback:
                    self._open_url_callback(url.toString())
                return False
        except Exception:
            pass
        return super().acceptNavigationRequest(url, nav_type, isMainFrame)


# ============================================================
# JS-Python 通信桥接
# ============================================================

class EditorBridge(QObject):
    """JS → Python 通信桥接"""
    contentChanged = pyqtSignal()

    def __init__(self, parent=None, image_save_callback=None, open_url_callback=None,
                 scroll_sync_callback=None):
        super().__init__(parent)
        self._image_save_callback = image_save_callback
        self._open_url_callback = open_url_callback
        self._scroll_sync_callback = scroll_sync_callback

    @pyqtSlot()
    def onContentChanged(self):
        self.contentChanged.emit()

    @pyqtSlot(str, result=str)
    def onPasteImage(self, data_url):
        """JS 粘贴图片：保存到本地并返回可引用的 markdown 路径"""
        if self._image_save_callback:
            try:
                return self._image_save_callback(data_url) or ''
            except Exception:
                return ''
        return ''

    @pyqtSlot(str)
    def onOpenExternal(self, url):
        """JS Ctrl+点击链接：在系统浏览器打开"""
        if self._open_url_callback:
            try:
                self._open_url_callback(url)
            except Exception:
                pass

    @pyqtSlot(float, str)
    def onScrollSync(self, pct, role):
        """分栏模式滚动同步：JS 端把滚动百分比与发起方面板（'src'/'prev'）传过来"""
        if self._scroll_sync_callback and pct is not None:
            try:
                self._scroll_sync_callback(float(pct), str(role))
            except Exception:
                pass


# ============================================================
# 编辑器组件
# ============================================================

class EditorWidget(QWidget):
    """单个编辑器组件（Typora 风格：所见即所得）"""

    def __init__(self, parent=None, file_path=None, default_workdir=None,
                 scroll_sync_callback=None):
        super().__init__(parent)
        self._destroyed = False  # 标记：编辑器是否已被销毁（被销毁后回调应跳过）
        self.file_path = file_path
        self.default_workdir = default_workdir
        self._file_loaded = False
        self.is_modified = False
        self.dark_mode = False
        self.focus_mode = False
        self.typewriter_mode = False
        self._pending_content = None  # 页面未就绪时暂存内容
        self._page_ready = False  # 页面是否已加载完成
        self._scroll_sync_callback = scroll_sync_callback  # 分栏滚动同步回调

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # WebEngine 配置（使用默认 profile，避免每个编辑器实例各自创建 profile 带来的生命周期崩溃）
        self.profile = QWebEngineProfile.defaultProfile()
        self.web_view = EditorWebView(open_url_callback=self._open_external_url)
        self.page = EditorPage(self.profile, open_url_callback=self._open_external_url)
        self.web_view.setPage(self.page)

        # 设置 WebChannel（JS 通信）
        self._bridge = EditorBridge(
            self,
            image_save_callback=self._save_pasted_image,
            open_url_callback=self._open_external_url,
            scroll_sync_callback=scroll_sync_callback,
        )
        self._channel = QWebChannel(self.web_view.page())
        self._channel.registerObject("bridge", self._bridge)
        self.web_view.page().setWebChannel(self._channel)
        self._bridge.contentChanged.connect(self._on_content_changed)

        # 启用所有必要特性
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)

        # 加载 HTML
        # 使用本地 file:// 基地址（而非 about:blank），
        # 否则 about:blank 页面会拒绝加载 file:// 协议的本地图片
        _base_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep

        # 必须先连接信号再启动异步加载，避免极快加载时丢失 loadFinished，
        # 导致暂存的 Markdown 内容永远没有机会写入页面。
        self.web_view.loadFinished.connect(self.on_load_finished)
        self.web_view.setHtml(_build_editor_html(), QUrl.fromLocalFile(_base_dir))

        layout.addWidget(self.web_view)

        # 延迟加载文件（单次兜底，避免重复 load 导致内容闪烁/空白）
        if file_path and os.path.exists(file_path):
            QTimer.singleShot(200, lambda: self._ensure_file_loaded())

    def on_load_finished(self, ok):
        # 页面就绪后尝试加载一次文件（仅当尚未加载且未被销毁时）
        if not getattr(self, '_destroyed', False):  # ← 删除 "ok and "
            self._page_ready = True
            # load_file 可能在页面就绪前执行；此时之前的 JS baseDir 调用会被忽略。
            # 页面就绪后先恢复文件目录，再渲染内容，确保相对图片路径也正常。
            if self.file_path:
                self._set_base_dir_from_path(self.file_path)
            # 若有暂存内容（页面加载期间 set_content 调用时页面尚未就绪），现在应用
            if self._pending_content is not None:
                pending = self._pending_content
                self._pending_content = None
                self._apply_content(pending)
            self._ensure_file_loaded()

    def _open_external_url(self, url):
        """在系统默认浏览器打开链接（供 JS Ctrl+点击调用）"""
        if not url:
            return
        target = self._normalize_external_url(url)
        if not target:
            return
        try:
            print(f"[Writile] open external: {target}", file=sys.stderr, flush=True)
        except Exception:
            pass
        # Windows 上 os.startfile 直接走系统默认浏览器，最可靠，优先使用
        if sys.platform == 'win32':
            try:
                os.startfile(target)  # noqa: B606 - 用户主动点击的链接
                return
            except Exception:
                pass
        try:
            if QDesktopServices.openUrl(QUrl(target)):
                return
        except Exception:
            pass
        try:
            import webbrowser
            webbrowser.open(target)
        except Exception:
            pass

    @staticmethod
    def _normalize_external_url(url):
        """规范化链接：无协议的域名自动补 https://，本地 file 路径保持可用"""
        import re
        u = (url or '').strip()
        if not u:
            return None
        low = u.lower()
        if low.startswith(('http://', 'https://', 'mailto:', 'ftp://', 'file://')):
            return u
        # 形似 host 或域名（含点、端口可选）或 localhost：补 https://
        if re.match(r'^[a-z0-9]([a-z0-9\-]*\.)+[a-z0-9\-]+(:\d+)?(/\S*)?$', low, re.I) or \
           re.match(r'^localhost(:\d+)?(/\S*)?$', low, re.I):
            return 'https://' + u
        # Windows 盘符或 POSIX 绝对路径：转为 file://
        if re.match(r'^[a-zA-Z]:[\\/]', u):
            return QUrl.fromLocalFile(u).toString()
        if u.startswith('/'):
            return QUrl.fromLocalFile(u).toString()
        # 其他情况：保留原值交给 os.startfile / QDesktopServices 处理
        return u

    def _on_content_changed(self):
        """JS 端内容变化回调"""
        self.is_modified = True

    def _auto_save(self):
        """自动保存：修改后 2 秒触发"""
        if self.is_modified and self.file_path:
            self.save_file()
            self.is_modified = False

    def _ensure_file_loaded(self):
        """确保文件只被加载一次"""
        if getattr(self, '_destroyed', False):
            return
        if self._file_loaded:
            return
        if self.file_path and os.path.exists(self.file_path):
            self.load_file(self.file_path)

    def load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.file_path = path
            self._file_loaded = True
            # 先设置 baseDir（用于相对图片路径解析），再设置内容
            self._set_base_dir_from_path(path)
            self.set_content(content)
        except Exception as e:
            try:
                # UTF-8 失败时，尝试系统默认编码（兼容 GBK 中文老文件）
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                self.file_path = path
                self._file_loaded = True
                self._set_base_dir_from_path(path)
                self.set_content(content)
            except Exception as e2:
                QMessageBox.critical(self, "错误", f"无法打开文件:\n{path}\n\n{e2}")

    def _set_base_dir_from_path(self, path):
        """根据当前文件路径设置 JS 端 baseDir（用于相对路径图片解析）"""
        try:
            folder = os.path.dirname(os.path.abspath(path))
            # Windows 下转换为 file:/// URL（如 D:/foo → file:///D:/foo）
            # 用 QUrl 生成规范化的本地 file URL
            url = QUrl.fromLocalFile(folder).toString()
            escaped = url.replace('\\', '\\\\').replace("'", "\\'")
            self.run_js(f"if (window.editorAPI) window.editorAPI.setBaseDir('{escaped}');")
        except Exception:
            pass

    def new_blank(self):
        """新建空白文档：清空内容并重置文件路径（复用同一个 WebEngine 实例）"""
        self.file_path = None
        self._file_loaded = False
        self.run_js("if (window.editorAPI) window.editorAPI.setBaseDir('');")
        self.set_content('')

    def run_js_sync(self, code, timeout=2000):
        """同步执行 JavaScript 并返回结果（默认超时 2 秒）"""
        result_holder = []
        def callback(value):
            result_holder.append(value)
        # 避免无限递归：如果 code 中已经包含同步获取，应直接返回
        self.web_view.page().runJavaScript(code, callback)
        # 简单阻塞等待（事件循环会被处理）
        from PyQt6.QtCore import QEventLoop
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(timeout)
        def check_done():
            if result_holder:
                loop.quit()
        # 轮询检查
        check_timer = QTimer()
        check_timer.timeout.connect(check_done)
        check_timer.start(20)
        loop.exec()
        check_timer.stop()
        return result_holder[0] if result_holder else None

    def run_js(self, code):
        """执行 JavaScript（带防崩溃保护）"""
        if getattr(self, '_destroyed', False):
            return
        try:
            self.web_view.page().runJavaScript(code)
        except RuntimeError:
            pass
        except Exception:
            pass

    def set_scroll_sync_callback(self, callback):
        """重绑定分栏滚动同步回调（同时更新桥接对象持有的引用）。

        【修复】旧代码直接给 widget 赋 `scroll_sync_callback` 属性，
        但 EditorBridge 只认构造时传入的回调，导致复用主编辑器作分栏
        左栏时滚动事件根本传不到 Python，同步失效。
        """
        self._scroll_sync_callback = callback
        try:
            self._bridge._scroll_sync_callback = callback
        except Exception:
            pass

    def set_content(self, text):
        """设置内容"""
        if text is None:
            text = ''
        # 页面未就绪时暂存，等 loadFinished 后再应用
        if not self._page_ready:
            self._pending_content = text
            return
        self._apply_content(text)
        self.is_modified = False

    def _apply_content(self, text):
        """实际执行 JS setContent（页面必须已就绪）。"""
        # JSON 字符串字面量能完整覆盖引号、反斜杠、控制字符及 U+2028/U+2029，
        # 避免手工转义遗漏导致某些已有文档再次触发 JavaScript 语法错误。
        payload = json.dumps(text, ensure_ascii=True)
        self.run_js(
            f"if (window.editorAPI && window.editorAPI.setContent) "
            f"window.editorAPI.setContent({payload});"
        )

    def get_content(self, callback=None):
        """获取内容（异步）
        若在回调执行前编辑器已被销毁，回调会被静默跳过。
        """
        if getattr(self, '_destroyed', False):
            return
        def handle(content):
            try:
                if callback and not getattr(self, '_destroyed', False):
                    callback(content or '')
            except RuntimeError:
                pass
        try:
            self.web_view.page().runJavaScript(
                "(function(){ if (window.editorAPI && window.editorAPI.getContent) "
                "return window.editorAPI.getContent(); return ''; })()",
                handle
            )
        except RuntimeError:
            pass
        except Exception:
            pass

    def set_dark_mode(self, dark):
        self.dark_mode = dark
        self.run_js(f"window.editorAPI.setDarkMode({str(dark).lower()})")

    def set_focus_mode(self, enabled):
        self.focus_mode = enabled
        self.run_js(f"window.editorAPI.setFocusMode({str(enabled).lower()})")

    def set_typewriter_mode(self, enabled):
        self.typewriter_mode = enabled
        self.run_js(f"window.editorAPI.setTypewriterMode({str(enabled).lower()})")

    def toggle_source_mode(self):
        self.run_js("window.editorAPI.toggleSourceMode()")

    def set_source_mode(self, enabled):
        """直接设置为源码模式（不反转）。修复 refresh_state 后被误跳出源码模式的问题。"""
        self.run_js(f"window.editorAPI.setSourceMode({str(bool(enabled)).lower()})")

    def save_file(self, path=None):
        if path:
            self.file_path = path
            # 另存新路径：更新 baseDir 用于相对图片
            self._set_base_dir_from_path(path)
        if not self.file_path:
            return False

        def do_save(content):
            # 防止编辑器已被销毁时回调崩溃
            if getattr(self, '_destroyed', False):
                return
            try:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.is_modified = False
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件:\n{e}")

        self.get_content(do_save)
        return True

    def _save_pasted_image(self, data_url):
        """将粘贴的图片（data URL）保存为本地文件，返回 markdown 可用的引用路径"""
        import base64
        import time
        if not data_url or ',' not in data_url:
            return ''
        header, b64 = data_url.split(',', 1)
        mime = 'image/png'
        if ';' in header and ':' in header.split(';')[0]:
            mime = header.split(';')[0].split(':', 1)[1]
        ext_map = {
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
        }
        ext = ext_map.get(mime, '.png')
        try:
            data = base64.b64decode(b64)
        except Exception:
            return ''
        if not data:
            return ''
        # 保存目录：默认文件夹/file/image/（默认文件夹不存在则回退 md 目录或用户主目录）
        base_root = None
        if getattr(self, 'default_workdir', None):
            base_root = self.default_workdir
        elif self.file_path and os.path.exists(self.file_path):
            base_root = os.path.dirname(os.path.abspath(self.file_path))
        else:
            base_root = os.path.expanduser('~')
        save_dir = os.path.join(base_root, 'file', 'image')
        os.makedirs(save_dir, exist_ok=True)
        # 文件名：image-{毫秒级时间戳}.{ext}
        ms = int(time.time() * 1000)
        full_path = os.path.join(save_dir, f'image-{ms}{ext}')
        i = 1
        while os.path.exists(full_path):
            full_path = os.path.join(save_dir, f'image-{ms}_{i}{ext}')
            i += 1
        try:
            with open(full_path, 'wb') as f:
                f.write(data)
        except Exception:
            return ''
        # 返回 Typora 风格的 markdown 图片片段：![文件名去扩展名](绝对路径)
        alt = os.path.splitext(os.path.basename(full_path))[0]
        return f'![{alt}]({full_path})'

    def insert_image(self):
        """插入本地图片：弹文件选择框，按相对当前文件路径写入 markdown 图片语法"""
        # 起始目录：当前文件目录，否则回退到用户主目录（避免引用不存在的 config 模块）
        start_dir = None
        if self.file_path and os.path.exists(self.file_path):
            start_dir = os.path.dirname(os.path.abspath(self.file_path))
        else:
            start_dir = os.path.expanduser("~")

        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", start_dir,
            "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.svg);;所有文件 (*.*)"
        )
        if not path:
            return
        # 若当前文件已存在：优先使用相对路径写入 markdown（便于仓库迁移）
        if self.file_path and os.path.exists(self.file_path):
            try:
                md_dir = os.path.dirname(os.path.abspath(self.file_path))
                img_abs = os.path.abspath(path)
                # 如果图片在 md 目录或其子目录：用相对路径
                if os.path.commonprefix([md_dir, img_abs]) == md_dir:
                    rel = os.path.relpath(img_abs, md_dir)
                    path = rel.replace('\\', '/')
            except Exception:
                pass

        # 转义引号等，插入 markdown 语法
        def _escape(s):
            return s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')

        alt_text = os.path.splitext(os.path.basename(path))[0] if path else ''
        md_snippet = f"![{alt_text}]({path})"
        self.run_js(
            f"if (window.editorAPI && window.editorAPI.insertTextAtCursor) "
            f"window.editorAPI.insertTextAtCursor('{_escape(md_snippet)}');"
        )
        # 插入后触发一次渲染（图片语法完整）
        QTimer.singleShot(150, lambda: self.run_js("if (window.editorAPI) window.editorAPI.render();"))

    def export_html(self, path):
        """导出 HTML"""
        def do_export(content):
            html = self._render_full_html(content or '')
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(html)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{e}")

        self.get_content(do_export)

    def _py_render_inline(self, text, base_folder=None):
        """Python 端简易行内 markdown→HTML（加粗/斜体/删除线/代码/高亮/链接/图片）"""
        import re
        import html as _html
        if not text:
            return ''
        out = _html.escape(text)

        def _img_sub(m):
            alt, src = m.group(1), m.group(2)
            src = src.replace('\\', '/')
            if base_folder and not re.match(r'^(https?:|data:|file:|/)', src, re.I):
                # 相对路径：生成相对于 base_folder 的路径（导出 HTML 与 md 同目录）
                src = src.replace('\\', '/')
            return f'<img alt="{_html.escape(alt)}" src="{src}">'

        out = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', _img_sub, out)
        out = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                     lambda m: f'<a href="{_html.escape(m.group(2))}">{m.group(1)}</a>', out)
        out = re.sub(r'\*\*\*([^*]+)\*\*\*', r'<strong><em>\1</em></strong>', out)
        out = re.sub(r'___([^_]+)___', r'<strong><em>\1</em></strong>', out)
        out = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', out)
        out = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', out)
        out = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', out)
        out = re.sub(r'_([^_]+)_', r'<em>\1</em>', out)
        out = re.sub(r'~~([^~]+)~~', r'<del>\1</del>', out)
        out = re.sub(r'==([^=]+)==', r'<mark>\1</mark>', out)
        out = re.sub(r'`([^`]+)`', r'<code>\1</code>', out)
        return out

    def _py_markdown_to_html(self, md_text, base_folder=None):
        """Python 端轻量 markdown→HTML（与 JS 端 renderMarkdown 行为对齐，用于导出）"""
        import re
        import html as _html
        lines = (md_text or '').split('\n')
        html = []
        i = 0
        in_code = False
        in_html_fence = False
        in_list = False
        list_type = ''
        in_quote = False

        def _para_render(paras):
            inner = self._py_render_inline('\n'.join(paras), base_folder)
            return inner.replace('\n', '<br>')

        while i < len(lines):
            line = lines[i]
            if re.match(r'^```', line):
                if in_list:
                    html.append('</' + list_type + '>')
                    in_list = False
                if in_quote:
                    html.append('</blockquote>')
                    in_quote = False
                if in_code:
                    html.append('</code></pre>')
                    in_code = False
                else:
                    html.append('<pre><code>')
                    in_code = True
                i += 1
                continue
            if in_code:
                html.append(_html.escape(line) + '\n')
                i += 1
                continue
            if re.match(r'^\|\|\|', line):
                if in_list:
                    html.append('</' + list_type + '>')
                    in_list = False
                if in_quote:
                    html.append('</blockquote>')
                    in_quote = False
                in_html_fence = not in_html_fence
                i += 1
                continue
            if in_html_fence:
                html.append(line)
                i += 1
                continue
            if line.strip() == '':
                if in_list:
                    html.append('</' + list_type + '>')
                    in_list = False
                if in_quote:
                    html.append('</blockquote>')
                    in_quote = False
                html.append('<div class="empty-line"><br></div>')
                i += 1
                continue
            # 原始 HTML 块：直接输出原样（与编辑器一致，不转义），如同 markdown 原生 HTML
            if re.match(r'^\s*<\s*(div|table|html|head|body|p|h[1-6]|ul|ol|li|section|article|header|footer|nav|main|aside|figure|figcaption|form|button|input|select|textarea|blockquote|pre|code|a|span|img|br|hr|tr|td|th|thead|tbody|tfoot|caption)(\s|>|/)', line, re.I) or \
               re.match(r'^\s*<!--', line) or \
               re.match(r'^\s*<!doctype', line, re.I):
                if in_list: html.append('</' + list_type + '>'); in_list = False
                if in_quote: html.append('</blockquote>'); in_quote = False
                html_lines = [line]
                i += 1
                while i < len(lines) and lines[i].strip() != '' and not re.match(r'^```', lines[i]):
                    html_lines.append(lines[i])
                    i += 1
                html.append('\n'.join(html_lines))
                continue

            # 标题
            m = re.match(r'^(#{1,6})\s+(.+)$', line)
            if m:
                if in_list: html.append('</' + list_type + '>'); in_list = False
                if in_quote: html.append('</blockquote>'); in_quote = False
                lv = len(m.group(1))
                html.append(f'<h{lv}>{self._py_render_inline(m.group(2), base_folder)}</h{lv}>')
                i += 1
                continue
            # 分割线
            if re.match(r'^(-{3,}|\*{3,}|_{3,})$', line):
                if in_list: html.append('</' + list_type + '>'); in_list = False
                if in_quote: html.append('</blockquote>'); in_quote = False
                html.append('<hr>')
                i += 1
                continue
            # 引用
            if re.match(r'^>', line):
                if in_list: html.append('</' + list_type + '>'); in_list = False
                if not in_quote:
                    html.append('<blockquote>')
                    in_quote = True
                html.append('<p>' + self._py_render_inline(re.sub(r'^>\s*', '', line), base_folder) + '</p>')
                i += 1
                continue
            elif in_quote:
                html.append('</blockquote>')
                in_quote = False
            # 无序列表
            if re.match(r'^[-*+]\s+', line):
                if not in_list or list_type != 'ul':
                    if in_list: html.append('</' + list_type + '>')
                    html.append('<ul>')
                    in_list = True
                    list_type = 'ul'
                html.append('<li>' + self._py_render_inline(re.sub(r'^[-*+]\s+', '', line), base_folder) + '</li>')
                i += 1
                continue
            # 有序列表
            if re.match(r'^\d+\.\s+', line):
                if not in_list or list_type != 'ol':
                    if in_list: html.append('</' + list_type + '>')
                    html.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                html.append('<li>' + self._py_render_inline(re.sub(r'^\d+\.\s+', '', line), base_folder) + '</li>')
                i += 1
                continue
            # 表格
            if re.match(r'^\|.+\|$', line) and i + 1 < len(lines) and re.match(r'^[\|: -]+$', lines[i+1]):
                if in_list: html.append('</' + list_type + '>'); in_list = False
                headers = [c.strip() for c in line.split('|') if c.strip()]
                html.append('<table><thead><tr>')
                for h in headers:
                    html.append(f'<th>{self._py_render_inline(h, base_folder)}</th>')
                html.append('</tr></thead><tbody>')
                i += 2
                while i < len(lines) and re.match(r'^\|.+\|$', lines[i]):
                    cells = [c for c in lines[i].split('|') if c.strip() or c == '']
                    html.append('<tr>')
                    for c in cells:
                        html.append(f'<td>{self._py_render_inline(c.strip(), base_folder)}</td>')
                    html.append('</tr>')
                    i += 1
                html.append('</tbody></table>')
                continue
            # 普通段落（可能多行）
            if in_list: html.append('</' + list_type + '>'); in_list = False
            para = [line]
            while i + 1 < len(lines) and lines[i+1].strip() != '' and \
                  not re.match(r'^(#{1,6}\s|>|[-*+]\s|\d+\.\s|```|---)', lines[i+1]):
                para.append(lines[i+1])
                i += 1
            html.append('<p>' + _para_render(para) + '</p>')
            i += 1

        if in_list: html.append('</' + list_type + '>')
        if in_quote: html.append('</blockquote>')
        if in_code: html.append('</code></pre>')
        return ''.join(html)

    def _render_full_html(self, md_text):
        """渲染完整 HTML 页面（用于导出）"""
        md_text = md_text or ''
        base_folder = None
        if self.file_path:
            base_folder = os.path.dirname(os.path.abspath(self.file_path))
        body_html = self._py_markdown_to_html(md_text, base_folder)
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Export</title>
<style>
body {{ font-family: -apple-system, 'Segoe UI', sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; line-height: 1.7; color: #1a1a1a; }}
pre {{ background: #f6f8fa; padding: 16px; border-radius: 8px; overflow: auto; white-space: pre-wrap; word-wrap: break-word; }}
code {{ background: #f6f8fa; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; }}
pre code {{ background: transparent; padding: 0; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #dfe2e5; padding: 6px 13px; }}
th {{ background: #f6f8fa; }}
blockquote {{ border-left: 4px solid #e1e4e8; padding-left: 16px; color: #6a737d; margin: 16px 0; background: #f6f8fa; border-radius: 0 6px 6px 0; }}
h1 {{ border-bottom: 1px solid #e1e4e8; padding-bottom: .3em; }}
h2 {{ border-bottom: 1px solid #e1e4e8; padding-bottom: .3em; }}
img {{ max-width: 100%; border-radius: 6px; }}
.empty-line {{ min-height: 1em; }}
hr {{ border: none; border-top: 1px solid #e1e4e8; margin: 24px 0; }}
p {{ margin: 0 0 16px 0; }}
</style>
</head>
<body>
<div id="content">
{body_html}
</div>
</body>
</html>"""

    def mark_destroyed(self):
        """显式标记编辑器为已销毁。

        与依赖 closeEvent 不同，应由调用方（如分栏模式切换）显式调用，
        确保只在真正需要销毁时才设置 _destroyed。closeEvent 在
        分栏切换、widget 重用等场景下也会被调用，不适合作为销毁标志。
        """
        self._destroyed = True

    def get_word_count_async(self, callback):
        """异步获取字数统计"""
        def handle(content):
            import re
            content = content or ''
            chinese = len(re.findall(r'[\u4e00-\u9fff]', content))
            english = len(re.findall(r'[a-zA-Z]+', content))
            chars = len(content)
            lines = content.count('\n') + 1 if content else 0
            callback({'chinese': chinese, 'english': english, 'chars': chars, 'lines': lines})
        self.get_content(handle)


# ============================================================
# 模糊搜索对话框
# ============================================================

class RecentFilesDialog(QDialog):
    """启动时选择最近打开的文件（IDEA 风格）"""
    def __init__(self, file_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("最近打开的文件")
        self.setFixedSize(520, 400)
        self.selected_file = None
        self._launch_blank = False

        layout = QVBoxLayout(self)

        title = QLabel("选择要打开的文件")
        title.setStyleSheet("font-size: 14px; font-weight: 600; color: #555;")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_file_selected)
        self.list_widget.itemClicked.connect(lambda _: self._on_file_selected(self.list_widget.currentItem()))
        layout.addWidget(self.list_widget, 1)

        # 填充现有文件（仅显示仍存在的文件）
        valid = [f for f in file_list if os.path.exists(f)]
        for f in valid:
            item = QListWidgetItem(os.path.basename(f))
            item.setData(Qt.ItemDataRole.UserRole, f)
            item.setToolTip(f)
            self.list_widget.addItem(item)
        if valid:
            self.list_widget.setCurrentRow(0)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        blank_btn = QPushButton("新建空白文档")
        blank_btn.clicked.connect(self._on_blank)
        btn_layout.addWidget(blank_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _on_file_selected(self, item):
        if not item:
            return
        self.selected_file = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _on_blank(self):
        self._launch_blank = True
        self.accept()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(e)


class QuickOpenDialog(QDialog):
    """快速打开文件 (Ctrl+P)"""
    def __init__(self, file_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("快速打开")
        self.setFixedSize(500, 400)
        self.file_list = file_list
        self.selected_file = None

        layout = QVBoxLayout(self)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入文件名模糊搜索...")
        self.search_input.textChanged.connect(self.filter_files)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_select)
        layout.addWidget(self.list_widget)

        self.populate(file_list)
        self.search_input.setFocus()

    def populate(self, files):
        self.list_widget.clear()
        for f in files:
            item = QListWidgetItem(os.path.basename(f))
            item.setData(Qt.ItemDataRole.UserRole, f)
            item.setToolTip(f)
            self.list_widget.addItem(item)

    def filter_files(self, text):
        text = text.lower()
        self.list_widget.clear()
        for f in self.file_list:
            name = os.path.basename(f).lower()
            path = f.lower()
            if text in name or text in path:
                item = QListWidgetItem(os.path.basename(f))
                item.setData(Qt.ItemDataRole.UserRole, f)
                item.setToolTip(f)
                self.list_widget.addItem(item)

    def on_select(self, item):
        self.selected_file = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.reject()
        elif e.key() == Qt.Key.Key_Return:
            items = self.list_widget.selectedItems()
            if items:
                self.on_select(items[0])
        else:
            super().keyPressEvent(e)


# ============================================================
# 主题编辑器对话框
# ============================================================

class FindDialog(QDialog):
    """查找替换对话框（增强版）
    - 实时显示 "n of m" 匹配计数
    - 支持大小写敏感、全词匹配
    - 支持上一个/下一个导航（Enter / Shift+Enter）
    - 支持单个替换和全部替换
    - 通过 web_view 暴露的 JS API 高亮所有匹配
    """

    def __init__(self, editor_widget, parent=None):
        super().__init__(parent)
        self.editor = editor_widget
        self._last_query = ''

        self.setWindowTitle("查找 + 替换")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(420, 200)
        self.resize(480, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # === 查找行 ===
        find_row = QHBoxLayout()
        find_row.addWidget(QLabel("查找:"))
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("输入要查找的文本...")
        self.find_input.textChanged.connect(self._on_query_changed)
        self.find_input.returnPressed.connect(self.find_next)
        find_row.addWidget(self.find_input, 1)

        self.match_label = QLabel("0 / 0")
        self.match_label.setMinimumWidth(60)
        self.match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.match_label.setStyleSheet("color: #666; font-size: 12px;")
        find_row.addWidget(self.match_label)

        layout.addLayout(find_row)

        # === 替换行 ===
        replace_row = QHBoxLayout()
        replace_row.addWidget(QLabel("替换:"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("替换为...")
        self.replace_row = replace_row
        replace_row.addWidget(self.replace_input, 1)

        layout.addLayout(replace_row)

        # === 选项行 ===
        options_row = QHBoxLayout()
        self.case_check = QCheckBox("区分大小写")
        self.whole_word_check = QCheckBox("全词匹配")
        self.case_check.stateChanged.connect(self._on_options_changed)
        self.whole_word_check.stateChanged.connect(self._on_options_changed)
        options_row.addWidget(self.case_check)
        options_row.addWidget(self.whole_word_check)
        options_row.addStretch()
        layout.addLayout(options_row)

        # === 按钮行 ===
        btn_row = QHBoxLayout()
        self.prev_btn = QPushButton("上一个 (Shift+Enter)")
        self.next_btn = QPushButton("下一个 (Enter)")
        self.replace_btn = QPushButton("替换")
        self.replace_all_btn = QPushButton("全部替换")
        self.close_btn = QPushButton("关闭 (Esc)")

        self.prev_btn.clicked.connect(self.find_prev)
        self.next_btn.clicked.connect(self.find_next)
        self.replace_btn.clicked.connect(self.replace_one)
        self.replace_all_btn.clicked.connect(self.replace_all)
        self.close_btn.clicked.connect(self.close)

        btn_row.addWidget(self.prev_btn)
        btn_row.addWidget(self.next_btn)
        btn_row.addWidget(self.replace_btn)
        btn_row.addWidget(self.replace_all_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        # 初始状态：禁用按钮
        self._update_button_state('')

        # 回车键在 replace_input 上：触发 replace_one
        self.replace_input.returnPressed.connect(self.replace_one)

        # 关闭时清理高亮
        # Note: don't override closeEvent to avoid stacking with parent

    def _on_query_changed(self, text):
        """查询文本变化时：重新高亮所有匹配并更新计数"""
        self._last_query = text
        self._highlight_all(text)
        self._update_button_state(text)
        # 自动跳到第一个匹配
        if text:
            self.find_next()

    def _on_options_changed(self):
        """选项变化时：重新搜索"""
        text = self.find_input.text()
        if text:
            self._highlight_all(text)
            self.find_next()

    def _update_button_state(self, query):
        """根据是否有查询字符串更新按钮可用状态"""
        has_query = bool(query)
        self.prev_btn.setEnabled(has_query)
        self.next_btn.setEnabled(has_query)
        self.replace_btn.setEnabled(has_query)
        self.replace_all_btn.setEnabled(has_query)

    def _highlight_all(self, query):
        """让 JS 端高亮所有匹配并返回数量"""
        if not query or not self.editor:
            self.match_label.setText("0 / 0")
            return

        case_sensitive = self.case_check.isChecked()
        whole_word = self.whole_word_check.isChecked()

        # 调用 JS 端的高亮函数（见 editor_common.py 中的 editorAPI.findHighlight）
        # 该函数会：
        # 1. 移除之前的高亮
        # 2. 用 <mark class="find-match"> 包裹所有匹配
        # 3. 返回匹配总数
        js = (
            f'window.editorAPI.findHighlight({_js_str(query)}, {str(case_sensitive).lower()}, {str(whole_word).lower()})'
        )
        count = self.editor.run_js_sync(js)
        try:
            count = int(count) if count is not None else 0
        except (ValueError, TypeError):
            count = 0

        # 同时记录当前匹配索引（从 JS 端获取）
        idx_js = 'window.editorAPI.findCurrentIndex()'
        idx = self.editor.run_js_sync(idx_js)
        try:
            idx = int(idx) if idx is not None else 0
        except (ValueError, TypeError):
            idx = 0

        if count > 0:
            # idx 是 0-based；显示 1-based
            self.match_label.setText(f"{idx + 1} / {count}")
            self.match_label.setStyleSheet("color: #4caf50; font-size: 12px; font-weight: 600;")
        else:
            self.match_label.setText("0 / 0")
            self.match_label.setStyleSheet("color: #999; font-size: 12px;")

    def find_next(self):
        """跳到下一个匹配"""
        if not self.editor:
            return
        case_sensitive = self.case_check.isChecked()
        js = f'window.editorAPI.findNext({_js_str(self.find_input.text())}, {str(case_sensitive).lower()})'
        self.editor.run_js(js)
        # 更新计数
        self._update_match_label()

    def find_prev(self):
        """跳到上一个匹配"""
        if not self.editor:
            return
        case_sensitive = self.case_check.isChecked()
        js = f'window.editorAPI.findPrev({_js_str(self.find_input.text())}, {str(case_sensitive).lower()})'
        self.editor.run_js(js)
        self._update_match_label()

    def _update_match_label(self):
        """从 JS 端读取当前匹配索引并更新标签"""
        idx = self.editor.run_js_sync('window.editorAPI.findCurrentIndex()')
        count = self.editor.run_js_sync('window.editorAPI.findTotalCount()')
        try:
            idx = int(idx) if idx is not None else 0
        except (ValueError, TypeError):
            idx = 0
        try:
            count = int(count) if count is not None else 0
        except (ValueError, TypeError):
            count = 0
        if count > 0:
            self.match_label.setText(f"{idx + 1} / {count}")
            self.match_label.setStyleSheet("color: #4caf50; font-size: 12px; font-weight: 600;")

    def replace_one(self):
        """替换当前匹配（如果有）然后跳到下一个"""
        if not self.editor:
            return
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if not find_text:
            return

        case_sensitive = self.case_check.isChecked()
        js = (
            f'window.editorAPI.replaceOne('
            f'{_js_str(find_text)}, {_js_str(replace_text)}, '
            f'{str(case_sensitive).lower()})'
        )
        self.editor.run_js(js)
        # 重新高亮（因为替换后匹配数变化）并跳到下一个
        self._highlight_all(find_text)
        self.find_next()

    def replace_all(self):
        """替换所有匹配"""
        if not self.editor:
            return
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if not find_text:
            return

        case_sensitive = self.case_check.isChecked()
        js = (
            f'window.editorAPI.replaceAll('
            f'{_js_str(find_text)}, {_js_str(replace_text)}, '
            f'{str(case_sensitive).lower()})'
        )
        count = self.editor.run_js_sync(js)
        try:
            count = int(count) if count is not None else 0
        except (ValueError, TypeError):
            count = 0

        from PyQt6.QtWidgets import QMessageBox
        if count > 0:
            QMessageBox.information(
                self, "替换完成",
                f"已替换 {count} 处匹配。"
            )
        else:
            QMessageBox.information(
                self, "替换完成",
                "未找到匹配项。"
            )
        # 重新高亮（替换后可能匹配数变化）
        self._highlight_all(find_text)

    def keyPressEvent(self, e):
        """键盘事件：Esc 关闭，Shift+Enter 上一个"""
        if e.key() == Qt.Key.Key_Escape:
            self.close()
            return
        elif e.key() == Qt.Key.Key_Return or e.key() == Qt.Key.Key_Enter:
            if e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.find_prev()
            else:
                self.find_next()
            return
        super().keyPressEvent(e)

    def closeEvent(self, e):
        """关闭时清除高亮"""
        if self.editor:
            try:
                self.editor.run_js('window.editorAPI.findClear()')
            except Exception:
                pass
        super().closeEvent(e)

    def showEvent(self, e):
        """显示时聚焦到输入框并全选已有内容"""
        super().showEvent(e)
        self.find_input.setFocus()
        self.find_input.selectAll()


def _js_str(s):
    """把 Python 字符串安全地转为 JS 字符串字面量（单引号包裹）"""
    if s is None:
        return "''"
    return "'" + (
        s.replace('\\', '\\\\')  # 先转义反斜杠
         .replace("\'", "\\'")      # 单引号
         .replace('\n', '\\n')      # 换行
         .replace('\r', '\\r')      # 回车
         .replace('\t', '\\t')      # 制表符
         .replace('\u2028', '\\u2028')
         .replace('\u2029', '\\u2029')
    ) + "'"




class ThemeEditorDialog(QDialog):
    """可视化主题编辑器 - 单窗口 + 实时预览"""

    COLOR_FIELDS = [
        ("bg", "背景色", False),
        ("fg", "文字颜色", False),
        ("muted", "弱化文字", False),
        ("code_bg", "代码块背景", False),
        ("border", "边框", False),
        ("link", "链接颜色", False),
        ("accent", "强调色", False),
        ("selection", "选区颜色", False),
        ("current_line", "当前行高亮", False),
        ("typewriter_line", "打字机行高亮", False),
    ]

    UI_FIELDS = [
        ("ui_bg", "UI 背景", True),
        ("ui_fg", "UI 文字", True),
        ("ui_alt", "UI 次要背景", True),
        ("ui_selection", "UI 选区", True),
    ]

    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自定义主题")
        self.setMinimumSize(720, 620)
        self.resize(800, 650)
        self._theme = json.loads(json.dumps(theme))  # 深拷贝
        self._swatch_buttons = {}

        main_layout = QHBoxLayout(self)

        # 左侧：颜色编辑区
        left = QWidget()
        left_layout = QVBoxLayout(left)

        # 主题名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("主题名称:"))
        self.name_edit = QLineEdit(self._theme.get("name", "我的主题"))
        name_layout.addWidget(self.name_edit)
        left_layout.addLayout(name_layout)

        # 深色/浅色切换
        self.dark_check = QCheckBox("深色主题")
        self.dark_check.setChecked(self._theme.get("is_dark", False))
        left_layout.addWidget(self.dark_check)

        # 编辑器颜色
        edit_group = QGroupBox("编辑器颜色")
        edit_grid = QGridLayout(edit_group)
        for i, (key, label, _) in enumerate(self.COLOR_FIELDS):
            edit_grid.addWidget(QLabel(label), i, 0)
            btn = self._create_color_button(
                self._theme.get("colors", {}).get(key, "#ffffff"),
                key, self._on_color_changed
            )
            self._swatch_buttons[key] = btn
            edit_grid.addWidget(btn, i, 1)
        left_layout.addWidget(edit_group)

        # UI 颜色
        ui_group = QGroupBox("界面颜色")
        ui_grid = QGridLayout(ui_group)
        for i, (key, label, _) in enumerate(self.UI_FIELDS):
            ui_grid.addWidget(QLabel(label), i, 0)
            btn = self._create_color_button(
                self._theme.get(key, "#ffffff"),
                key, self._on_ui_color_changed
            )
            self._swatch_buttons[key] = btn
            ui_grid.addWidget(btn, i, 1)
        left_layout.addWidget(ui_group)

        left_layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self._reset_colors)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        ok_btn = QPushButton("保存主题")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        left_layout.addLayout(btn_layout)

        main_layout.addWidget(left, 3)

        # 右侧：预览区
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("实时预览"))

        self.preview = QFrame()
        self.preview.setFrameShape(QFrame.Shape.StyledPanel)
        self.preview.setMinimumSize(280, 400)
        right_layout.addWidget(self.preview, 1)

        self._update_preview()
        main_layout.addWidget(right, 2)

    def _create_color_button(self, color_str, key, callback):
        btn = QPushButton()
        btn.setFixedSize(80, 28)
        btn.setStyleSheet(f"background-color: {color_str}; border: 1px solid #ccc; border-radius: 4px;")
        btn.clicked.connect(lambda: self._pick_color(key, color_str, callback))
        btn._color = color_str
        return btn

    def _pick_color(self, key, current_color, callback):
        color = QColorDialog.getColor(QColor(current_color), self, "选择颜色")
        if color.isValid():
            callback(key, color.name())

    def _on_color_changed(self, key, color_str):
        self._theme.setdefault("colors", {})[key] = color_str
        btn = self._swatch_buttons.get(key)
        if btn:
            btn._color = color_str
            btn.setStyleSheet(f"background-color: {color_str}; border: 1px solid #ccc; border-radius: 4px;")
        self._update_preview()

    def _on_ui_color_changed(self, key, color_str):
        self._theme[key] = color_str
        btn = self._swatch_buttons.get(key)
        if btn:
            btn._color = color_str
            btn.setStyleSheet(f"background-color: {color_str}; border: 1px solid #ccc; border-radius: 4px;")
        self._update_preview()

    def _reset_colors(self):
        self._theme = json.loads(json.dumps(PRESET_THEMES.get("light", {})))
        self.name_edit.setText(self._theme.get("name", "我的主题"))
        self.dark_check.setChecked(self._theme.get("is_dark", False))
        for key, (_, _, _) in enumerate(self.COLOR_FIELDS):
            pass  # will update below
        # Refresh all buttons
        for key, label, _ in self.COLOR_FIELDS:
            color = self._theme.get("colors", {}).get(key, "#ffffff")
            btn = self._swatch_buttons.get(key)
            if btn:
                btn._color = color
                btn.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc; border-radius: 4px;")
        for key, label, _ in self.UI_FIELDS:
            color = self._theme.get(key, "#ffffff")
            btn = self._swatch_buttons.get(key)
            if btn:
                btn._color = color
                btn.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc; border-radius: 4px;")
        self._update_preview()

    def _update_preview(self):
        colors = self._theme.get("colors", {})
        bg = colors.get("bg", "#ffffff")
        fg = colors.get("fg", "#333333")
        code_bg = colors.get("code_bg", "#f6f8fa")
        border = colors.get("border", "#e1e4e8")
        accent = colors.get("accent", "#4caf50")
        selection = colors.get("selection", "#cce5ff")
        ui_bg = self._theme.get("ui_bg", "#ffffff")
        ui_fg = self._theme.get("ui_fg", "#333333")
        ui_alt = self._theme.get("ui_alt", "#f0f0f0")
        self.preview.setStyleSheet(f"""
            QFrame {{ background-color: {bg}; border: 1px solid {border}; border-radius: 8px; }}
            QLabel {{ color: {fg}; background: transparent; }}
        """)
        # Build preview content
        preview_html = f"""
        <div style="background:{bg};color:{fg};padding:20px;border-radius:8px;font-family:sans-serif;">
            <h2 style="color:{fg};border-bottom:1px solid {border};padding-bottom:8px;">预览标题</h2>
            <p>这是一段 <strong>粗体</strong>、<em>斜体</em>、<code style="background:{code_bg};padding:2px 6px;border-radius:4px;">行内代码</code> 的示例。</p>
            <blockquote style="border-left:4px solid {accent};padding-left:16px;color:{colors.get('muted','#666')};">引用文本 - 强调色 {accent}</blockquote>
            <ul style="color:{fg};">
                <li>列表项 1</li>
                <li>列表项 2</li>
                <li>链接: <a style="color:{colors.get('link','#0366d6')};">示例链接</a></li>
            </ul>
            <pre style="background:{code_bg};padding:12px;border-radius:6px;color:{fg};overflow-x:auto;">代码块示例
print("Hello, Writile!")</pre>
            <p style="color:{colors.get('muted','#666')};font-size:12px;">弱化文字颜色 {colors.get('muted','#666')}</p>
        </div>
        """
        # Use QLabel with rich text for preview
        if hasattr(self, '_preview_label'):
            self._preview_label.setStyleSheet(
                f"background:{bg};color:{fg};border:1px solid {border};border-radius:8px;"
                f"padding:20px;font-family:'Segoe UI','PingFang SC',sans-serif;"
            )
            self._preview_label.setText(preview_html)
        else:
            self._preview_label = QLabel(preview_html)
            self._preview_label.setWordWrap(True)
            self._preview_label.setStyleSheet(
                f"background:{bg};color:{fg};border:1px solid {border};border-radius:8px;"
                f"padding:20px;font-family:'Segoe UI','PingFang SC',sans-serif;"
            )
            layout = self.preview.layout()
            if layout:
                layout.addWidget(self._preview_label)
            else:
                layout = QVBoxLayout(self.preview)
                layout.addWidget(self._preview_label)
            # Add UI preview section
            ui_preview = QFrame()
            ui_preview.setStyleSheet(f"background:{ui_alt};border:1px solid {border};border-radius:6px;padding:8px;")
            ui_label = QLabel(f"UI 预览: 背景 {ui_bg} / 文字 {ui_fg} / 次要 {ui_alt}")
            ui_label.setStyleSheet(f"color:{ui_fg};background:transparent;")
            ui_preview_layout = QHBoxLayout(ui_preview)
            ui_preview_layout.addWidget(ui_label)
            ui_btn = QPushButton("按钮示例")
            ui_btn.setStyleSheet(
                f"background:{ui_alt};color:{ui_fg};border:1px solid {border};"
                f"padding:4px 10px;border-radius:4px;"
            )
            ui_preview_layout.addWidget(ui_btn)
            ui_preview_layout.addStretch()
            layout.addWidget(ui_preview)

    def get_theme(self):
        """获取编辑后的主题数据"""
        self._theme["name"] = self.name_edit.text() or "我的主题"
        self._theme["is_dark"] = self.dark_check.isChecked()
        return self._theme


# ============================================================
# 快捷键自定义对话框
# ============================================================

class ShortcutCustomizerDialog(QDialog):
    """快捷键自定义对话框"""

    def __init__(self, actions_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("快捷键设置")
        self.setMinimumSize(520, 500)
        self.resize(560, 560)
        self._actions_data = actions_data  # list of (category, name, shortcut, action)
        self._original_shortcuts = {}
        for cat, name, shortcut, _action in actions_data:
            self._original_shortcuts[(cat, name)] = shortcut

        layout = QVBoxLayout(self)

        # 表格
        self.table = QTableWidget(len(actions_data), 3)
        self.table.setHorizontalHeaderLabels(["分类", "功能", "快捷键"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        for i, (cat, name, shortcut, _action) in enumerate(actions_data):
            item_cat = QTableWidgetItem(cat)
            item_name = QTableWidgetItem(name)
            item_short = QTableWidgetItem(shortcut)
            self.table.setItem(i, 0, item_cat)
            self.table.setItem(i, 1, item_name)
            # Use QKeySequenceEdit for editing
            key_edit = QKeySequenceEdit(QKeySequence(shortcut))
            key_edit.setMaximumWidth(150)
            self.table.setCellWidget(i, 2, key_edit)

        layout.addWidget(self.table)

        # 提示
        hint = QLabel("点击快捷键列中的输入框，然后按下新的键来修改快捷键。")
        hint.setStyleSheet("color: #666; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # 按钮
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._reset_shortcuts)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        ok_btn = QPushButton("保存")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _reset_shortcuts(self):
        for i, (cat, name, shortcut, _action) in enumerate(self._actions_data):
            original = self._original_shortcuts.get((cat, name), shortcut)
            key_edit = self.table.cellWidget(i, 2)
            if key_edit:
                key_edit.setKeySequence(QKeySequence(original))

    def get_shortcuts(self):
        """返回修改后的快捷键 dict {(cat, name): shortcut_str}"""
        result = {}
        for i, (cat, name, shortcut, _action) in enumerate(self._actions_data):
            key_edit = self.table.cellWidget(i, 2)
            if key_edit:
                new_short = key_edit.keySequence().toString()
                result[(cat, name)] = new_short
        return result

# ============================================================
# 大纲提取
# ============================================================

def extract_outline(text):
    """从 Markdown 中提取大纲"""
    import re
    outline = []
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#'):
            match = re.match(r'^(#{1,6})\s+(.+)', stripped)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                title = re.sub(r'[*_`~\[\]]', '', title)
                outline.append((level, title))
    return outline


# ============================================================
# Highlight.js 库加载
# ============================================================

def _load_highlight_js_lib():
    """从 lib/highlight.min.js 加载真实的 highlight.js 库代码。
    失败时返回空字符串（HTML 中的占位符会被替换为空，避免报错）。
    """
    try:
        lib_path = get_resource_path(os.path.join("lib", "highlight.min.js"))
        if not os.path.exists(lib_path):
            return ""
        with open(lib_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _build_editor_html():
    """构建编辑器 HTML，将 highlight.js 占位符替换为真实库代码。

    返回完整的 HTML 字符串，供 QWebEngineView 加载使用。
    """
    html = EDITOR_HTML
    placeholder = "__HIGHLIGHT_JS_PLACEHOLDER__"
    if placeholder in html:
        lib_code = _load_highlight_js_lib()
        # JS 代码嵌入 <script> 块中：需转义 </script> 防止 HTML 提前闭合
        lib_code_safe = lib_code.replace("</script>", "<\\/script>")
        html = html.replace(placeholder, lib_code_safe)
    return html


# ============================================================
# 入口
# ============================================================

def get_resource_path(relative_path):
    """获取资源路径（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        base = sys._MEIPASS
    else:
        # 开发模式
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def get_app_icon():
    """获取应用图标"""
    icon_path = get_resource_path("icon.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return QIcon()


def get_platform_default_font():
    """获取平台默认字体"""
    if sys.platform == 'darwin':
        return QFont('.AppleSystemUIFont', 14)
    elif sys.platform == 'win32':
        return QFont('Microsoft YaHei UI', 10)
    else:
        return QFont('Noto Sans CJK SC', 11)

