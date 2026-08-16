# -*- coding: utf-8 -*-
"""
Typora 风格 Markdown 编辑器
核心特点：所见即所得、即时渲染、不分屏、专注模式、打字机模式
"""

import os
import sys
import json
import configparser

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QStatusBar, QToolBar, QSplitter,
    QListWidget, QListWidgetItem, QButtonGroup,
    QTreeWidget, QTreeWidgetItem,
    QDockWidget, QLineEdit, QPushButton, QLabel, QInputDialog,
    QMenu, QDialog, QColorDialog, QFontDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QSpinBox, QGroupBox,
    QGridLayout, QScrollArea, QFrame, QKeySequenceEdit, QComboBox
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QUrl, QSettings, pyqtSlot, QObject, QStandardPaths
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
    line-height: 1.75;
    color: var(--fg);
    background: var(--bg);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

#editor {
    max-width: 820px;
    margin: 0 auto;
    padding: 48px 64px 200px 64px;
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
h1 { font-size: 2em; font-weight: 700; border-bottom: 1px solid var(--border-light); padding-bottom: .4em; margin: 1.2em 0 .6em; letter-spacing: -0.01em; }
h2 { font-size: 1.5em; font-weight: 700; border-bottom: 1px solid var(--border-light); padding-bottom: .3em; margin: 1.2em 0 .5em; letter-spacing: -0.01em; }
h3 { font-size: 1.25em; font-weight: 600; margin: 1em 0 .4em; }
h4 { font-size: 1em; font-weight: 600; margin: 1em 0 .4em; }
h5 { font-size: .875em; font-weight: 600; margin: 1em 0 .4em; color: var(--muted); }
h6 { font-size: .85em; font-weight: 600; margin: 1em 0 .4em; color: var(--muted); }

p { margin: 0 0 16px 0; }
.empty-line { margin: 0 0 16px 0; min-height: 1em; }
a { color: var(--link); text-decoration: none; transition: opacity 0.15s; }
a:hover { text-decoration: underline; opacity: 0.85; }
strong { font-weight: 600; }
em { font-style: italic; }
del { text-decoration: line-through; color: var(--muted); }

blockquote {
    padding: 12px 20px;
    color: var(--muted);
    border-left: 4px solid var(--accent);
    background: var(--quote-bg);
    border-radius: 0 6px 6px 0;
    margin: 20px 0;
}

ul, ol { padding-left: 2em; margin: 16px 0; }
li { margin: 6px 0; line-height: 1.65; }
li > ul, li > ol { margin: 6px 0; }

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
    padding: 20px 24px;
    overflow: auto;
    line-height: 1.55;
    margin: 20px 0;
    border: 1px solid var(--border-light);
}
pre code { background: none; padding: 0; font-size: 100%; border: none; }

table {
    border-collapse: collapse;
    margin: 20px 0;
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
hr { border: none; border-top: 1px solid var(--border-light); margin: 32px 0; }
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
</style>
</head>
<body>

<div id="editor" contenteditable="true" data-placeholder="开始写作... (Markdown 格式)"></div>

<!-- Qt WebChannel JS API -->
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>

<!-- Marked.js (Markdown 解析) -->
<script>
/*! marked v4.3.0 | (c) 2018- Chenchen Shen and contributors | MIT license */
!function(e,t){"object"==typeof exports&&"undefined"!=typeof module?t(exports):"function"==typeof define&&define.amd?define(["exports"],t):t(e.marked={})}(this,function(e){"use strict";function t(e,t){this.marked=e,this.defaults=t}function n(e){for(var t=1,n=arguments.length;t<n;t++)for(var r in arguments[t])e[r]=arguments[t][r];return e}function r(e,t,n){var r=n.walker||new i(n);r.tokens=n.tokens;var s=r.renderTokens(r.lex(e));return s}function i(e){this.options=e||{},this.renderer=this.options.renderer||new s,this.renderer.options=this.options}function s(e){this.options=e||{}}function a(){}var o={newline:/^\n+/,code:/^( {4}[^\n]+\n*)+/,fences:f,hr:/^ {0,3}((?:- *){3,}|(?:_ *){3,}|(?:\* *){3,})(?:\n+|$)/,heading:l,heading2:/^ {0,3}(#{1,6})(?:\s|$)/,lheading:/^([^\n]+)\n {0,3}(=+|#+) {0,3}\n+/,blockquote:p,bullet:k,list:A,def:x,table:w,paragraph:b,text:/^[^\n]+/,nptable:g};function l(e){this.options=e||{}}function p(e){this.tokens=[],this.token=null,this.options=e||{},this.options.pedantic&&(o.blockquote=/^( {0,3}> ?(paragraph|[^\n]*)(?:\n( {0,3}> ?[^\n]+))*)+/)}function u(e){this.tokens=[],this.token=null,this.options=e||{}}function c(e){this.options=e||{}}function h(e){this.options=e||{}}function d(e){var t=String(e);return t=t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function f(e,t,n){var r=n.tok();return r}function g(){}e.Parser=function(e,t){this.tokens=[],this.token=null,this.options=t||n.defaults},e.parser=function(t,n){var r=new e.Parser(t,n);return r.parse()},e.Lexer=function(e,t){this.tokens=[],this.tokens.links=Object.create(null),this.options=n(this.options,t),this.rules=o.pedantic?n({},o.pedantic):n({},o.normal||o),this.options.pedantic&&(o.blockquote=/^( {0,3}> ?(paragraph|[^\n]*)(?:\n( {0,3}> ?[^\n]+))*)+/),this.options.gfm&&(o.fences=/^ {0,3}(`{3,})(?=[^\s]*$)((?:\s*\n|.)*?)(?:\n {0,3}\1|$)/,o.paragraph=/^([^\n]+(?:\n(?!hr|heading|lheading|blockquote|fences|list|html|table|def|\n{2,}))[^\n]*)*/),this.options.breaks&&(o.inline=/^\\?(`+)(?!`)(\s?[\s\S]*?[^`]\s?)\1(?!`)/),this.token=null},e.lexer=function(t,n){var r=new e.Lexer(n);return r.lex(t)},e.InlineLexer=function(e,t){this.options=n(this.options,t)},e.inlineLexer=function(t,n,r){var i=new e.InlineLexer(n,r);return i.output(t)},e.Slugger=function(){this.seen=Object.create(null)},e.parse=function(t,n){return new e.Parser(n).parse(t)},e.marked=r,n(r,{defaults:{gfm:!0,breaks:!1,pedantic:!1,silent:!1,highlight:null,langPrefix:"language-",smartLists:!1,smartypants:!1,headerIds:!0,headerPrefix:"",xhtml:!1,baseUrl:null,mangle:!0,renderer:null,walkable:!0}}),r.options=function(e){return e?n(r.defaults,e):r.defaults},r.setOptions=function(e){n(r.defaults,e)},r.use=function(){var e,t,i,s,o,l;for(t=0;t<arguments.length;t++)if(e=arguments[t],i=Object.keys(e),o=i.length,0!==o)for(;o--;)l=i[o],s=e[l],"object"==typeof s?r.defaults[l]=r.defaults[l]?n(r.defaults[l],s):s:r.defaults[l]=s},r.walk=function(e,t){return new i(t).walk(e)},r.parseInline=function(e,t){return new i(t).parseInline(e)},e.exports=r});
</script>

<!-- Highlight.js (代码高亮) -->
<script>
/*! highlight.js v11.9.0 | BSD-3-Clause License | https://highlightjs.org */
var hljs=function(){"use strict";var e,t,n=Object.freeze({__proto__:null,registerLanguage:function(t,n){e[t]=n},registerAliases:function(){},highlight:function(e,t){return{value:e}},highlightAuto:function(e){return{value:e}},highlightElement:function(){}});return n}();
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

    function setContentDirect(text) {
        activeBlock = null;
        savedMarkdown = text || '';
        editor.innerHTML = renderMarkdown(savedMarkdown);
        var codeBlocks = editor.querySelectorAll('pre code');
        codeBlocks.forEach(function(block) {
            try { if (window.hljs) hljs.highlightElement(block); } catch(e) {}
        });
        renderAllMermaid();
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
        if (/^(#{1,6}\s|>\s?|[-*+]\s+|\d+\.\s+|```|\|\|\|)/.test(line)) return true;
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
                var headers = tableLines[0].split('|').filter(function(c) { return c.trim(); });
                headers.forEach(function(h) {
                    html.push('<th>' + renderInline(h.trim()) + '</th>');
                });
                html.push('</tr></thead><tbody>');
                for (var ti = 2; ti < tableLines.length; ti++) {
                    html.push('<tr>');
                    var cells = tableLines[ti].split('|').filter(function(c) { return c.trim() || c === ''; });
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
        var range = null;
        if (src.length > 0) {
            range = document.createRange();
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
        }
        // 最后确保编辑器获得焦点并设置光标（顺序很重要！）
        editor.focus();
        if (range) {
            sel.removeAllRanges();
            sel.addRange(range);
        }
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
            var codeBlocks = editor.querySelectorAll('pre code');
            codeBlocks.forEach(function(block) {
                try { if (window.hljs) hljs.highlightElement(block); } catch(e) {}
            });
            renderAllMermaid();
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
                cur.setAttribute('data-source-mode', '1');
                activeBlock = cur;
            }
        }
        if (activeBlock) {
            // 源码模式下用 textContent（保证纯文本无 DOM 元素）
            activeBlock.setAttribute('data-src', activeBlock.textContent || '');
        }
        recordHistory();
        notifyContentChanged();
    });

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
                e.preventDefault();
                splitCurrentBlock();
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

        var pairs = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'", '`': '`'};
        if (pairs[e.key] && window.getSelection().toString() === '') {
            e.preventDefault();
            document.execCommand('insertText', false, e.key + pairs[e.key]);
            var sel = window.getSelection();
            var range = sel.getRangeAt(0);
            range.setStart(range.startContainer, range.startOffset - 1);
            range.setEnd(range.endContainer, range.endOffset - 1);
            sel.removeAllRanges();
            sel.addRange(range);
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
        if (e.ctrlKey && e.key === '/') {
            e.preventDefault();
            toggleSourceMode();
        }
        if ((e.key === 'Enter' || e.key === 'NumpadEnter') && !activeBlock) {
            // 非源码模式：列表空项退格 + 结构渲染
            var sel2 = window.getSelection();
            var node2 = sel2.anchorNode;
            while (node2 && node2.nodeType === 3) node2 = node2.parentNode;
            if (node2 && node2.tagName === 'LI' && node2.textContent.trim() === '') {
                e.preventDefault();
                var parent = node2.parentNode;
                parent.removeChild(node2);
                if (parent.children.length === 0) parent.parentNode.removeChild(parent);
                document.execCommand('insertParagraph', false);
            }
            scheduleRender(true);
        }
        if (e.key === 'Backspace' || e.key === 'Delete') {
            setTimeout(function() {
                // 仅同步 data-src，不触发全量渲染，避免删除时光标乱跳
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
    });

    // 失焦：退出源码模式，恢复渲染效果
    editor.addEventListener('blur', function() {
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
        } else {
            editor.removeAttribute('data-mode');
            render();
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
        updateCurrentLine();
        // 点击图片：进入其所在块的源码模式，方便编辑图片地址/alt
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
        // 退出源码模式
        if (activeBlock) exitSourceMode();
        editorMode = 'preview';
        // 收集内容并全量渲染
        var text = collectMarkdown();
        savedMarkdown = text;
        editor.innerHTML = renderMarkdown(text);
        editor.contentEditable = 'false';
        // 添加预览模式样式
        editor.classList.add('preview-mode');
        var codeBlocks = editor.querySelectorAll('pre code');
        codeBlocks.forEach(function(block) {
            try { if (window.hljs) hljs.highlightElement(block); } catch(e) {}
        });
        renderAllMermaid();
    }

    // 编辑模式：所见即所得
    function enterEditMode() {
        if (editorMode === 'edit') return;
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

    // 公开接口
    window.editorAPI = {
        render: render,
        getContent: function() {
            // 优先用 collectMarkdown，确保源码模式块的编辑被纳入
            if (activeBlock) savedMarkdown = collectMarkdown();
            return savedMarkdown || editor.innerText;
        },
        setContent: function(text) {
            activeBlock = null;
            savedMarkdown = text;
            editor.innerHTML = renderMarkdown(text);
            editorMode = 'edit';
            editor.contentEditable = 'true';
            editor.classList.remove('preview-mode');
            var codeBlocks = editor.querySelectorAll('pre code');
            codeBlocks.forEach(function(block) {
                try { if (window.hljs) hljs.highlightElement(block); } catch(e) {}
            });
            renderAllMermaid();
            resetHistory(text);
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
        isPreviewMode: function() { return editorMode === 'preview'; },
        togglePreviewMode: togglePreviewMode,
        enterEditMode: enterEditMode,
        enterPreviewMode: enterPreviewMode
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
from PyQt6.QtCore import pyqtSignal

class EditorBridge(QObject):
    """JS → Python 通信桥接"""
    contentChanged = pyqtSignal()

    def __init__(self, parent=None, image_save_callback=None, open_url_callback=None):
        super().__init__(parent)
        self._image_save_callback = image_save_callback
        self._open_url_callback = open_url_callback

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


# ============================================================
# 编辑器组件
# ============================================================

class EditorWidget(QWidget):
    """单个编辑器组件（Typora 风格：所见即所得）"""

    def __init__(self, parent=None, file_path=None, default_workdir=None):
        super().__init__(parent)
        self.file_path = file_path
        self.default_workdir = default_workdir
        self._file_loaded = False
        self.is_modified = False
        self.dark_mode = False
        self.focus_mode = False
        self.typewriter_mode = False

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
        self.web_view.setHtml(EDITOR_HTML, QUrl.fromLocalFile(_base_dir))

        # 等待页面加载完成（只在有文件且 __init__ 里的 singleShot 还没生效时兜底加载）
        self.web_view.loadFinished.connect(self.on_load_finished)

        layout.addWidget(self.web_view)

        # 延迟加载文件（单次兜底，避免重复 load 导致内容闪烁/空白）
        if file_path and os.path.exists(file_path):
            QTimer.singleShot(200, lambda: self._ensure_file_loaded())

    def on_load_finished(self, ok):
        # 页面就绪后尝试加载一次文件（仅当尚未加载且未被销毁时）
        if ok and not getattr(self, '_destroyed', False):
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

    def run_js(self, code):
        """执行 JavaScript"""
        self.web_view.page().runJavaScript(code)

    def set_content(self, text):
        """设置内容"""
        # 完整的 JS 字符串转义，防止包含 Tab、\u2028 等字符时 JS 语法错误
        if text is None:
            text = ''
        escaped = (
            text.replace('\\', '\\\\')
                .replace('\b', '\\b')
                .replace('\f', '\\f')
                .replace('\n', '\\n')
                .replace('\r', '\\r')
                .replace('\t', '\\t')
                .replace('\v', '\\v')
                .replace("'", "\\'")
                .replace('\u2028', '\\u2028')
                .replace('\u2029', '\\u2029')
        )
        self.run_js(f"window.editorAPI.setContent('{escaped}')")
        self.is_modified = False

    def get_content(self, callback=None):
        """获取内容（异步）"""
        def handle(content):
            if callback:
                callback(content or '')
        # 页面尚未就绪或 editorAPI 异常时返回空字符串，避免拿到 None
        self.web_view.page().runJavaScript(
            "(function(){ if (window.editorAPI && window.editorAPI.getContent) "
            "return window.editorAPI.getContent(); return ''; })()",
            handle
        )

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
# 主窗口
# ============================================================

class MainWindow(QMainWindow):
    """主窗口 - Typora 风格"""

    def __init__(self, initial_file=None):
        super().__init__()
        self.setWindowTitle("Writile - 所见即所得 Markdown 编辑器")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        self._initial_file = initial_file  # 启动时要打开的文件（双击 .md 传入）

        # 设置窗口图标
        icon_path = get_resource_path("icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 状态
        self.dark_mode = False
        self.focus_mode = False
        self.typewriter_mode = False
        self.current_theme = "light"  # 当前主题 key
        self.custom_theme = None       # 自定义主题数据
        self.settings = QSettings("Writile", "Editor")
        self.recent_files = self.settings.value("recent_files", [], type=list) or []
        # 去重（Windows 下路径不区分大小写）
        self.recent_files = self._dedupe_paths(self.recent_files)
        self.current_folder = self.settings.value("current_folder", "", type=str) or ""
        # 默认工作目录：从 config.ini 读取（安装时设置，不在注册表中）
        self.default_workdir = self._read_default_workdir()
        # 确保默认目录存在
        os.makedirs(self.default_workdir, exist_ok=True)
        # 加载保存的主题
        saved_theme = self.settings.value("current_theme", "light", type=str) or "light"
        self.custom_theme = self.settings.value("custom_theme", None, type=dict)

        # 加载自定义主题文件
        self.custom_themes = {}
        self.load_custom_themes()

        # UI
        self._actions = {}  # 存储所有 action 用于快捷键自定义
        self.create_menu_bar()
        self.create_toolbar()
        self.create_sidebar()
        self.create_editor()
        self.create_status_bar()

        # 主题
        self.apply_theme()

        # 恢复状态
        self.restore_state()

        # 决定初始内容：若有命令行传入的文件则打开它
        if self._initial_file and os.path.exists(self._initial_file):
            self.load_file(self._initial_file)
        else:
            # 检查是否启用"启动时恢复上次文件"
            reopen_last = self.settings.value("reopen_last_file", True, type=bool)
            last_file = self.settings.value("last_open_file", "", type=str) or ""
            if reopen_last and last_file and os.path.exists(last_file):
                self.load_file(last_file)
            else:
                self._choose_startup_file()

    def _choose_startup_file(self):
        """启动时选择文件：若有最近文件则弹出选择窗口，否则新建空白文档（IDEA 风格）"""
        # 使用 QTimer 延迟弹出，确保主窗口已显示
        valid_recent = [p for p in self.recent_files if os.path.exists(p)]
        if valid_recent:
            QTimer.singleShot(0, lambda: self._show_recent_dialog(valid_recent))
        else:
            self.new_file()

    def _show_recent_dialog(self, files):
        dialog = RecentFilesDialog(files, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.selected_file:
                self.load_file(dialog.selected_file)
            elif dialog._launch_blank:
                self.new_file()
        else:
            # 用户取消：新建空白文档
            self.new_file()

    def create_menu_bar(self):
        menubar = self.menuBar()
        saved_shortcuts = self.settings.value("shortcuts", {}, type=dict) or {}

        def _action(name, default_shortcut, callback, category=None):
            """辅助方法：创建 action 并注册"""
            a = QAction(name, self)
            shortcut = saved_shortcuts.get(f"{category}|{name}", default_shortcut) if category else default_shortcut
            if shortcut:
                a.setShortcut(shortcut)
            a.triggered.connect(callback)
            if category:
                self._actions[name] = a
            return a

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        new_action = _action("新建", "Ctrl+N", self.new_file, "文件")
        file_menu.addAction(new_action)

        open_action = _action("打开", "Ctrl+O", self.open_file, "文件")
        file_menu.addAction(open_action)

        quick_open_action = _action("快速打开", "Ctrl+P", self.quick_open, "文件")
        file_menu.addAction(quick_open_action)

        self.recent_menu = file_menu.addMenu("最近打开")
        self.update_recent_menu()

        file_menu.addSeparator()

        save_action = _action("保存", "Ctrl+S", self.save_file, "文件")
        file_menu.addAction(save_action)

        save_as_action = _action("另存为", "Ctrl+Shift+S", self.save_as_file, "文件")
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        open_folder_action = _action("打开文件夹", "", self.open_folder)
        file_menu.addAction(open_folder_action)

        open_in_explorer_action = _action("在资源管理器中打开", "", self.open_current_folder_in_explorer)
        file_menu.addAction(open_in_explorer_action)

        file_menu.addSeparator()

        export_html = _action("导出 HTML", "", self.export_html, "文件")
        file_menu.addAction(export_html)

        export_pdf = _action("导出 PDF", "", self.export_pdf, "文件")
        file_menu.addAction(export_pdf)

        file_menu.addSeparator()

        quit_action = _action("退出", "Ctrl+Q", self.close, "文件")
        file_menu.addAction(quit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")

        find_action = _action("查找", "Ctrl+F", self.find_text, "编辑")
        edit_menu.addAction(find_action)

        source_mode_action = _action("切换源码模式", "Ctrl+/", self.toggle_source_mode, "编辑")
        edit_menu.addAction(source_mode_action)

        edit_menu.addSeparator()

        select_all_action = _action("全选", "Ctrl+A", self.select_all, "编辑")
        edit_menu.addAction(select_all_action)

        copy_action = _action("复制", "Ctrl+C", self.copy_selection, "编辑")
        edit_menu.addAction(copy_action)

        cut_action = _action("剪切", "Ctrl+X", self.cut_selection, "编辑")
        edit_menu.addAction(cut_action)

        paste_action = _action("粘贴", "Ctrl+V", self.paste_clipboard, "编辑")
        edit_menu.addAction(paste_action)

        # 格式菜单
        fmt_menu = menubar.addMenu("格式(&M)")

        bold_action = _action("粗体", "Ctrl+B", lambda: self.insert_format("**", "**"), "格式")
        fmt_menu.addAction(bold_action)

        italic_action = _action("斜体", "Ctrl+I", lambda: self.insert_format("*", "*"), "格式")
        fmt_menu.addAction(italic_action)

        code_action = _action("行内代码", "Ctrl+`", lambda: self.insert_format("`", "`"), "格式")
        fmt_menu.addAction(code_action)

        strike_action = _action("删除线", "", lambda: self.insert_format("~~", "~~"), "格式")
        fmt_menu.addAction(strike_action)

        mark_action = _action("高亮", "", lambda: self.insert_format("==", "=="), "格式")
        fmt_menu.addAction(mark_action)

        fmt_menu.addSeparator()

        image_action = _action("插入图片...", "Ctrl+Shift+I", self.insert_image, "格式")
        fmt_menu.addAction(image_action)

        fmt_menu.addSeparator()

        h1_action = _action("标题 1", "Ctrl+1", lambda: self.insert_heading(1), "格式")
        fmt_menu.addAction(h1_action)

        h2_action = _action("标题 2", "Ctrl+2", lambda: self.insert_heading(2), "格式")
        fmt_menu.addAction(h2_action)

        h3_action = _action("标题 3", "Ctrl+3", lambda: self.insert_heading(3), "格式")
        fmt_menu.addAction(h3_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        toggle_sidebar = _action("切换侧边栏", "Ctrl+\\", self.toggle_sidebar, "视图")
        view_menu.addAction(toggle_sidebar)

        # 文件列表和大纲独立开关
        self.toggle_filelist_action = QAction("显示文件列表", self, checkable=True)
        self.toggle_filelist_action.setChecked(True)
        self.toggle_filelist_action.triggered.connect(self.toggle_filelist)
        view_menu.addAction(self.toggle_filelist_action)
        self._actions["显示文件列表"] = self.toggle_filelist_action

        self.toggle_outline_action = QAction("显示大纲", self, checkable=True)
        self.toggle_outline_action.setChecked(True)
        self.toggle_outline_action.triggered.connect(self.toggle_outline)
        view_menu.addAction(self.toggle_outline_action)
        self._actions["显示大纲"] = self.toggle_outline_action

        view_menu.addSeparator()

        self.focus_action = QAction("专注模式", self, checkable=True)
        focus_shortcut = saved_shortcuts.get("视图|专注模式", "F8")
        self.focus_action.setShortcut(focus_shortcut)
        self.focus_action.triggered.connect(self.toggle_focus_mode)
        view_menu.addAction(self.focus_action)
        self._actions["专注模式"] = self.focus_action

        self.typewriter_action = QAction("打字机模式", self, checkable=True)
        tw_shortcut = saved_shortcuts.get("视图|打字机模式", "F9")
        self.typewriter_action.setShortcut(tw_shortcut)
        self.typewriter_action.triggered.connect(self.toggle_typewriter_mode)
        view_menu.addAction(self.typewriter_action)
        self._actions["打字机模式"] = self.typewriter_action

        view_menu.addSeparator()

        # 预览模式
        self.preview_action = QAction("预览模式", self, checkable=True)
        preview_shortcut = saved_shortcuts.get("视图|预览模式", "Ctrl+E")
        self.preview_action.setShortcut(preview_shortcut)
        self.preview_action.triggered.connect(self.toggle_preview_mode)
        view_menu.addAction(self.preview_action)
        self._actions["预览模式"] = self.preview_action

        view_menu.addSeparator()

        # 切换主题（浅色/深色一键切换）
        self.theme_toggle_action = QAction("切换浅色/深色", self)
        self.theme_toggle_action.triggered.connect(lambda: self.set_theme(not self.dark_mode))
        view_menu.addAction(self.theme_toggle_action)
        self._actions["切换主题"] = self.theme_toggle_action

        view_menu.addSeparator()
        theme_menu = view_menu.addMenu("主题(&T)")

        # 预设主题
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        self.theme_actions = {}

        for key, theme in PRESET_THEMES.items():
            action = QAction(theme["name"], self, checkable=True)
            action.setActionGroup(theme_group)
            action.triggered.connect(lambda checked, k=key: self.apply_theme_by_key(k))
            theme_menu.addAction(action)
            self.theme_actions[key] = action

        # 自定义主题
        if self.custom_themes:
            theme_menu.addSeparator()
            custom_label = theme_menu.addAction("自定义主题")
            custom_label.setEnabled(False)
            for key, theme in self.custom_themes.items():
                action = QAction(theme.get("name", key), self, checkable=True)
                action.setActionGroup(theme_group)
                action.triggered.connect(lambda checked, k=key: self.apply_theme_by_key(k))
                theme_menu.addAction(action)
                self.theme_actions["custom:" + key] = action

        theme_menu.addSeparator()

        # 自定义主题编辑器
        custom_theme_action = QAction("自定义主题颜色...", self)
        custom_theme_action.triggered.connect(self.open_custom_theme_dialog)
        theme_menu.addAction(custom_theme_action)

        # 导入/导出主题
        export_theme_action = QAction("导出当前主题...", self)
        export_theme_action.triggered.connect(self.export_theme)
        theme_menu.addAction(export_theme_action)

        import_theme_action = QAction("导入主题...", self)
        import_theme_action.triggered.connect(self.import_theme)
        theme_menu.addAction(import_theme_action)

        theme_menu.addSeparator()

        # 字体设置
        font_action = QAction("编辑器字体...", self)
        font_action.triggered.connect(self.choose_editor_font)
        theme_menu.addAction(font_action)

        # 设置菜单
        settings_menu = menubar.addMenu("设置(&S)")

        # 修改默认文件夹
        workdir_action = QAction("修改默认文件夹...", self)
        workdir_action.triggered.connect(self.change_default_workdir)
        settings_menu.addAction(workdir_action)

        # 启动时恢复上次文件
        reopen_action = QAction("启动时恢复上次打开的文件", self)
        reopen_action.setCheckable(True)
        reopen_action.setChecked(self.settings.value("reopen_last_file", True, type=bool))
        reopen_action.triggered.connect(self._toggle_reopen_last_file)
        settings_menu.addAction(reopen_action)

        settings_menu.addSeparator()

        shortcut_setting_action = QAction("自定义快捷键...", self)
        shortcut_setting_action.triggered.connect(self.open_shortcut_customizer)
        settings_menu.addAction(shortcut_setting_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        shortcuts_action = QAction("快捷键", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)

    def create_toolbar(self):
        """创建工具栏（简化版，仅保留常用功能）"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 专注模式按钮
        btn_style = """
            QPushButton {
                background-color: palette(window);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: 500;
                min-width: 50px;
            }
            QPushButton:hover {
                background-color: palette(mid);
            }
        """
        self.focus_btn = QPushButton("专注")
        self.focus_btn.setCheckable(True)
        self.focus_btn.setToolTip("专注模式 (F8)")
        self.focus_btn.clicked.connect(self.toggle_focus_mode)
        self.focus_btn.setStyleSheet(btn_style)
        toolbar.addWidget(self.focus_btn)
        
        # 打字机模式按钮
        self.typewriter_btn = QPushButton("打字机")
        self.typewriter_btn.setCheckable(True)
        self.typewriter_btn.setToolTip("打字机模式 (F9)")
        self.typewriter_btn.clicked.connect(self.toggle_typewriter_mode)
        self.typewriter_btn.setStyleSheet(btn_style)
        toolbar.addWidget(self.typewriter_btn)
        
        toolbar.addSeparator()
        
        # 主题切换按钮
        theme_btn = QPushButton("主题")
        theme_btn.setToolTip("切换浅色/深色主题")
        theme_btn.clicked.connect(lambda: self.apply_theme_by_key("dark" if not self.dark_mode else "light"))
        theme_btn.setStyleSheet(btn_style)
        toolbar.addWidget(theme_btn)

    def update_toolbar_buttons(self):
        """更新工具栏按钮状态"""
        # 异步获取预览模式状态
        def update_preview_state(result):
            if hasattr(self, 'preview_btn'):
                self.preview_btn.setChecked(result)
        if hasattr(self, 'editor') and self.editor:
            self.editor.web_view.page().runJavaScript(
                "(function(){ if (window.editorAPI && window.editorAPI.isPreviewMode) return window.editorAPI.isPreviewMode(); return false; })()",
                update_preview_state
            )
        # 更新专注模式按钮
        if hasattr(self, 'focus_btn'):
            self.focus_btn.setChecked(self.focus_mode)
        # 更新打字机模式按钮
        if hasattr(self, 'typewriter_btn'):
            self.typewriter_btn.setChecked(self.typewriter_mode)

    def create_sidebar(self):
        """创建侧边栏（文件列表 + 大纲，可独立或同时展示）"""
        self.dock = QDockWidget("", self)
        self.dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        # 隐藏标题栏
        self.dock.setTitleBarWidget(QWidget())

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 用 QSplitter 替代 QVBoxLayout，允许拖拽调整两个面板比例
        self.sidebar_splitter = QSplitter(Qt.Orientation.Vertical)

        # === 文件列表面板（当前文件同目录的 .md 文件）===
        self.filelist_panel = QWidget()
        filelist_layout = QVBoxLayout(self.filelist_panel)
        filelist_layout.setContentsMargins(0, 0, 0, 0)
        filelist_layout.setSpacing(0)

        # 文件列表头部栏
        filelist_header = QWidget()
        filelist_header.setFixedHeight(24)
        filelist_header.setStyleSheet(
            "QWidget { background-color: palette(alternate-base); border: none; border-radius: 4px; margin: 4px 6px 0px 6px; }"
        )
        header_layout = QHBoxLayout(filelist_header)
        header_layout.setContentsMargins(10, 2, 4, 2)

        self.folder_label = QLabel("📁 文件夹")
        self.folder_label.setStyleSheet(
            "font-weight: 500; font-size: 11px; color: palette(muted);"
        )
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch()

        filelist_layout.addWidget(filelist_header)

        self.filelist_widget = QTreeWidget()
        self.filelist_widget.setHeaderHidden(True)
        self.filelist_widget.setIndentation(16)
        self.filelist_widget.setStyleSheet("""
            QTreeWidget {
                background: transparent;
                border: none;
                outline: none;
                padding: 4px 0px;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 4px 8px;
                border-radius: 6px;
                margin: 1px 6px;
            }
            QTreeWidget::item:hover {
                background: palette(mid);
            }
            QTreeWidget::item:selected {
                background: palette(highlight);
                color: palette(highlighted-text);
                border: 1px solid palette(link);
                font-weight: 600;
            }
        """)
        self.filelist_widget.itemClicked.connect(self.on_filelist_clicked)
        self.filelist_widget.itemDoubleClicked.connect(self.on_filelist_clicked)
        self.filelist_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.filelist_widget.customContextMenuRequested.connect(self._show_filelist_context_menu)
        filelist_layout.addWidget(self.filelist_widget)

        # === 大纲面板 ===
        self.outline_panel = QWidget()
        outline_layout = QVBoxLayout(self.outline_panel)
        outline_layout.setContentsMargins(0, 0, 0, 0)
        outline_layout.setSpacing(0)

        outline_header = QLabel("  大纲")
        outline_header.setStyleSheet(
            "padding: 4px 10px; font-weight: 500; font-size: 11px; "
            "background: transparent; border: none; color: palette(muted);"
        )
        outline_layout.addWidget(outline_header)

        self.outline_widget = QListWidget()
        self.outline_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                padding: 4px 0px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px 12px;
                border-radius: 6px;
                margin: 1px 6px;
            }
            QListWidget::item:hover {
                background: palette(mid);
            }
            QListWidget::item:selected {
                background: palette(highlight);
                color: palette(highlighted-text);
                font-weight: 600;
            }
            QListWidget::item:disabled {
                color: palette(mid);
                font-style: italic;
            }
        """)
        self.outline_widget.itemClicked.connect(self.outline_clicked)
        outline_layout.addWidget(self.outline_widget)

        self.sidebar_splitter.addWidget(self.filelist_panel)
        self.sidebar_splitter.addWidget(self.outline_panel)
        # 初始比例：文件列表占 35%，大纲占 65%
        self.sidebar_splitter.setSizes([350, 650])

        layout.addWidget(self.sidebar_splitter)

        self.dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)

    def create_editor(self):
        """创建编辑器（单实例复用，避免 WebEngine 频繁重建导致闪退）"""
        editor = EditorWidget(default_workdir=self.default_workdir)
        editor.set_dark_mode(self.dark_mode)
        editor.set_focus_mode(self.focus_mode)
        editor.set_typewriter_mode(self.typewriter_mode)
        editor._bridge.contentChanged.connect(self._on_editor_content_changed)
        self.editor = editor
        self.setCentralWidget(editor)

    def _ensure_editor(self):
        """确保编辑器已创建（首次打开文件时调用）"""
        if not hasattr(self, 'editor') or self.editor is None:
            self.create_editor()

    def _on_editor_content_changed(self):
        """编辑器内容变化时标记修改状态，并防抖刷新大纲"""
        if self.editor:
            self.editor.is_modified = True
            self.update_title()
            # 停止输入 1.5 秒后刷新大纲，避免每次按键都跨 JS 边界
            if hasattr(self, '_outline_timer'):
                self._outline_timer.start()
            # 停止输入后更新字数统计（防抖，降低 JS/Python 往返开销）
            if hasattr(self, '_wordcount_timer'):
                self._wordcount_timer.start()

    def _get_default_save_path(self):
        """获取默认保存路径（当前文件目录或默认工作目录）"""
        if self.editor and self.editor.file_path:
            return os.path.dirname(self.editor.file_path)
        if not self.default_workdir:
            return None
        os.makedirs(self.default_workdir, exist_ok=True)
        return self.default_workdir

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 左侧：状态标签（用于显示文件路径等状态信息）
        self.status_label = QLabel("")
        self.status_bar.addWidget(self.status_label)

        # 右侧：模式下拉框 + 字数统计
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # 模式下拉框
        self.mode_combo = QComboBox()
        self.mode_combo.setFixedWidth(80)
        self.mode_combo.addItems(["编辑", "源码", "预览"])
        self.mode_combo.setToolTip("切换编辑模式")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_combo_changed)
        right_layout.addWidget(self.mode_combo)

        # 字数统计
        self.count_label = QLabel("字数: 0 | 字符: 0")
        right_layout.addWidget(self.count_label)

        self.status_bar.addPermanentWidget(right_widget)

        # 字数统计：内容停止变化后更新（防抖），减少高频轮询
        self._wordcount_timer = QTimer(self)
        self._wordcount_timer.setSingleShot(True)
        self._wordcount_timer.setInterval(1200)
        self._wordcount_timer.timeout.connect(self.update_word_count)
        QTimer.singleShot(600, self.update_word_count)

        # 大纲防抖刷新定时器（内容变化后延迟更新）
        self._outline_timer = QTimer(self)
        self._outline_timer.setSingleShot(True)
        self._outline_timer.setInterval(1500)
        self._outline_timer.timeout.connect(self.update_outline_async)

    def _on_mode_combo_changed(self, index):
        """状态下拉框切换处理"""
        modes = ["edit", "source", "preview"]
        mode = modes[index] if index < len(modes) else "edit"
        self.set_editor_mode(mode)

    def new_file(self):
        self._ensure_editor()
        self.editor.new_blank()
        self.editor.file_path = None
        self.update_title()
        self.status_label.setText("新建文件")
        self.refresh_filelist_for_current_file()

    def open_file(self):
        start_dir = self.default_workdir or ""
        if self.editor and self.editor.file_path:
            start_dir = os.path.dirname(self.editor.file_path)
        path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", start_dir,
            "Markdown 文件 (*.md *.markdown *.txt);;所有文件 (*.*)"
        )
        if path:
            self.load_file(path)

    def load_file(self, path):
        try:
            if not os.path.exists(path):
                QMessageBox.warning(self, "提示", f"文件不存在:\n{path}")
                return
            # 复用单实例编辑器：仅更新内容，不重建 WebEngine（避免闪退）
            self._ensure_editor()
            self.editor.load_file(path)
            self.update_title()

            self._add_recent_file(path)

            # 刷新同目录文件列表（高亮当前文件）和大纲
            self.refresh_filelist_for_current_file()
            self.status_label.setText(f"已打开: {os.path.basename(path)}")
            QTimer.singleShot(800, self.update_outline_async)
            # 记住上次打开的文件
            self.settings.setValue("last_open_file", path)
        except Exception as e:
            try:
                QMessageBox.critical(self, "错误", f"打开文件失败:\n{path}\n\n{e}")
            except Exception:
                pass

    def save_file(self):
        if not self.editor.file_path:
            # 未命名文件：弹对话框让用户填写文件名
            # 默认文件名取编辑器第一行内容
            default_name = self._get_first_line_as_filename()
            save_dir = self._get_default_save_path() or ""
            default_path = os.path.join(save_dir, default_name) if save_dir else default_name
            path, _ = QFileDialog.getSaveFileName(
                self, "保存文件", default_path,
                "Markdown 文件 (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
            )
            if path:
                if self.editor.save_file(path):
                    self.update_title()
                    self.refresh_filelist_for_current_file()
                    self.status_label.setText("已保存")
        else:
            self.editor.save_file()
            self.update_title()
            self.refresh_filelist_for_current_file()
            self.status_label.setText("已保存")

    def _get_first_line_as_filename(self):
        """从编辑器内容第一行生成默认文件名"""
        first_line = ""
        if hasattr(self.editor, 'web_view'):
            from PyQt6.QtCore import QEventLoop
            result = [None]
            loop = QEventLoop()
            def on_content(text):
                result[0] = text
                loop.quit()
            self.editor.web_view.page().runJavaScript(
                "(function(){ var c = window.editorAPI.getContent() || ''; return c.split('\\n')[0] || ''; })()",
                on_content
            )
            loop.exec()
            if result[0]:
                first_line = result[0].strip()
        # 清理文件名：去掉不合法字符
        if first_line:
            for ch in '\\/:*?"<>|#&':
                first_line = first_line.replace(ch, '')
            first_line = first_line.strip()
            if first_line:
                if not first_line.endswith('.md'):
                    first_line += '.md'
                return first_line
        return "未命名.md"

    def save_as_file(self):
        start_dir = self.default_workdir or ""
        if self.editor and self.editor.file_path:
            start_dir = os.path.dirname(self.editor.file_path)
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为", start_dir,
            "Markdown 文件 (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        if path:
            if self.editor.save_file(path):
                self.update_title()
                self.refresh_filelist_for_current_file()
                self.status_label.setText("已保存")

    def quick_open(self):
        """快速打开 (Ctrl+P) 模糊搜索"""
        files = []
        if self.current_folder and os.path.isdir(self.current_folder):
            for root, dirs, filenames in os.walk(self.current_folder):
                for f in filenames:
                    if f.endswith(('.md', '.markdown', '.txt')):
                        files.append(os.path.join(root, f))
        files.extend(self.recent_files)
        files = self._dedupe_paths(files)

        if not files:
            QMessageBox.information(self, "提示", "没有可用的文件。\n请先打开文件夹。")
            return

        dialog = QuickOpenDialog(files, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_file:
            self.load_file(dialog.selected_file)

    def open_folder(self):
        start_dir = self.default_workdir or ""
        if self.editor and self.editor.file_path:
            start_dir = os.path.dirname(self.editor.file_path)
        folder = QFileDialog.getExistingDirectory(self, "打开文件夹", start_dir)
        if folder:
            self.current_folder = folder
            self.settings.setValue("current_folder", folder)
            self.populate_file_tree(folder)
            self._update_folder_label(folder)
            self.status_label.setText(f"已打开文件夹: {folder}")

    def open_current_folder_in_explorer(self):
        """在系统文件管理器中打开当前文件夹"""
        folder = self.current_folder or self.default_workdir
        if not folder or not os.path.isdir(folder):
            QMessageBox.information(self, "提示", "当前没有可打开的文件夹。")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(folder)))

    def _update_folder_label(self, folder):
        """更新文件夹标签显示（只显示最后一级目录名）"""
        if folder:
            name = os.path.basename(folder.rstrip(os.sep))
            self.folder_label.setText(f"📁 {name}")
            self.folder_label.setToolTip(folder)
        else:
            self.folder_label.setText("📁 文件夹")
            self.folder_label.setToolTip("")

    def _get_config_paths(self):
        """返回 config.ini 的候选路径列表（优先级从高到低）"""
        paths = []
        # 1. 用户可写目录（安装后修改保存在这里）
        local_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
        if local_dir:
            paths.append(os.path.join(local_dir, "config.ini"))
        # 2. 程序安装目录（安装时写入）
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        paths.append(os.path.join(app_dir, "config.ini"))
        return paths

    def _read_default_workdir(self):
        """从 config.ini 读取默认工作目录"""
        for config_path in self._get_config_paths():
            if os.path.exists(config_path):
                try:
                    cp = configparser.ConfigParser()
                    cp.read(config_path, encoding='utf-8')
                    if cp.has_option('settings', 'default_workdir'):
                        workdir = cp.get('settings', 'default_workdir').strip()
                        if workdir:
                            return workdir
                except Exception:
                    pass
        # 回退：程序目录可写则用程序目录，否则用文档/Writile
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        test_file = os.path.join(app_dir, ".writile_test_write")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return app_dir
        except (PermissionError, OSError):
            doc_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            if doc_dir:
                return os.path.join(doc_dir, "Writile")
            return os.path.expanduser("~/Writile")

    def _write_default_workdir(self, workdir):
        """将默认工作目录写入 config.ini（用户可写目录优先）"""
        config_path = self._get_config_paths()[0]  # 用户可写目录
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        try:
            cp = configparser.ConfigParser()
            cp['settings'] = {'default_workdir': workdir}
            with open(config_path, 'w', encoding='utf-8') as f:
                cp.write(f)
        except Exception:
            # 回退到程序目录
            config_path = self._get_config_paths()[1]
            try:
                cp = configparser.ConfigParser()
                cp['settings'] = {'default_workdir': workdir}
                with open(config_path, 'w', encoding='utf-8') as f:
                    cp.write(f)
            except Exception:
                pass

    def _toggle_reopen_last_file(self, checked):
        """切换启动时是否恢复上次打开的文件"""
        self.settings.setValue("reopen_last_file", bool(checked))

    def change_default_workdir(self):
        """修改默认工作目录（写入 config.ini，并立即同步到编辑器）"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择默认工作目录", self.default_workdir or ""
        )
        if folder:
            self.default_workdir = folder
            self._write_default_workdir(folder)
            os.makedirs(folder, exist_ok=True)
            # 立即同步到编辑器实例（粘贴图片等依赖此目录）
            if getattr(self, 'editor', None):
                self.editor.default_workdir = folder
            QMessageBox.information(
                self, "设置已更新",
                f"默认工作目录已改为:\n{folder}\n\n"
                f"已立即生效。"
            )
            self.status_label.setText(f"默认工作目录: {folder} (已生效)")

    def populate_file_tree(self, folder):
        """填充文件树：展示 .md 文件、图片等附件，并以目录树形式呈现"""
        self._update_folder_label(folder)
        self.filelist_widget.clear()
        if not os.path.isdir(folder):
            return

        # 展示的扩展名：markdown 文件 + 常见图片附件
        doc_exts = ('.md', '.markdown', '.txt')
        img_exts = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg')

        current_path = self.editor.file_path if self.editor else None

        folder_item = QTreeWidgetItem([os.path.basename(folder) or folder])
        folder_item.setData(0, Qt.ItemDataRole.UserRole, folder)
        folder_item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
        self.filelist_widget.addTopLevelItem(folder_item)
        folder_item.setExpanded(True)

        # 收集当前目录及其子目录下的所有文档和图片（限制层级与数量，避免过深/过大）
        _scanned_count = {'n': 0}
        MAX_NODES = 2000
        MAX_DEPTH = 6

        def scandir(base, top_item, depth=0):
            if depth > MAX_DEPTH or _scanned_count['n'] >= MAX_NODES:
                return
            try:
                entries = sorted(os.listdir(base))
            except (PermissionError, OSError):
                return
            dirs = []
            files = []
            for entry in entries:
                full = os.path.join(base, entry)
                if os.path.isdir(full):
                    dirs.append(entry)
                elif os.path.isfile(full):
                    ext = os.path.splitext(entry)[1].lower()
                    if ext in doc_exts or ext in img_exts:
                        files.append(entry)

            for name in files:
                full = os.path.join(base, name)
                _scanned_count['n'] += 1
                child = QTreeWidgetItem([name])
                child.setData(0, Qt.ItemDataRole.UserRole, full)
                child.setToolTip(0, full)
                child.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
                if current_path and full == current_path:
                    child.setFont(0, QFont("", -1, QFont.Weight.Bold))
                    child.setForeground(0, QColor(0, 120, 215))
                top_item.addChild(child)

            for d in dirs:
                full = os.path.join(base, d)
                child = QTreeWidgetItem([d])
                child.setData(0, Qt.ItemDataRole.UserRole, full)
                child.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
                top_item.addChild(child)
                scandir(full, child, depth + 1)

        scandir(folder, folder_item)

        # 折叠所有子目录，仅展开包含当前文件的目录路径
        if current_path:
            def expand_to(path):
                rel = os.path.relpath(path, folder)
                parts = rel.split(os.sep)
                item = folder_item
                for part in parts[:-1]:
                    for i in range(item.childCount()):
                        if item.child(i).text(0) == part:
                            item = item.child(i)
                            item.setExpanded(True)
                            break
            expand_to(current_path)

        self._adjust_sidebar_panels()

    def refresh_filelist_for_current_file(self):
        """根据当前打开的文件，刷新文件树"""
        if self.editor and self.editor.file_path:
            folder = os.path.dirname(self.editor.file_path)
            self.populate_file_tree(folder)
        elif self.default_workdir and os.path.isdir(self.default_workdir):
            self.populate_file_tree(self.default_workdir)
        else:
            self._update_folder_label("")
            self.filelist_widget.clear()
            item = QTreeWidgetItem(["点击此处打开文件或文件夹"])
            item.setData(0, Qt.ItemDataRole.UserRole, "__open_prompt__")
            item.setForeground(0, QColor(0, 120, 215))
            item.setFont(0, QFont("", -1, QFont.Weight.DemiBold))
            self.filelist_widget.addTopLevelItem(item)
        self._adjust_sidebar_panels()

    def _adjust_sidebar_panels(self):
        """根据内容量自动调整侧边栏两个面板的比例"""
        if not hasattr(self, 'sidebar_splitter'):
            return
        filelist_count = self.filelist_widget.topLevelItemCount()
        outline_count = self.outline_widget.count()

        # 文件列表只有占位符时，收缩到 1 行高度
        if filelist_count <= 1:
            filelist_size = 36  # 约一行高度
        else:
            filelist_size = min(filelist_count * 28 + 12, 300)

        # 大纲为空时，收缩到只剩标题
        if outline_count == 0:
            outline_size = 32  # 只有"大纲"标题高度
        else:
            outline_size = min(outline_count * 26 + 40, 500)

        total = filelist_size + outline_size
        if total > 0:
            self.sidebar_splitter.setSizes([filelist_size, outline_size])

    def on_filelist_clicked(self, item, column=0):
        """点击文件树节点，打开对应文件或触发打开对话框"""
        if not item:
            return
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path == "__open_prompt__":
            self.open_folder()
        elif path and os.path.isfile(path):
            self.load_file(path)

    def _show_filelist_context_menu(self, pos):
        """文件列表右键菜单"""
        menu = QMenu(self)
        new_action = menu.addAction("新建文件")

        item = self.filelist_widget.itemAt(pos)
        if item:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and os.path.isfile(path):
                menu.addSeparator()
                open_action = menu.addAction("打开")
                open_action.triggered.connect(lambda: self.load_file(path))
                menu.addSeparator()
                del_action = menu.addAction("删除")
                del_action.triggered.connect(lambda: self._delete_filelist_file(path))

        action = menu.exec(self.filelist_widget.mapToGlobal(pos))
        if action == new_action:
            self._new_file_in_current_dir()

    def _new_file_in_current_dir(self):
        """在当前文件列表所在目录新建文件"""
        # 确定目标目录
        target_dir = ""
        if self.editor and self.editor.file_path:
            target_dir = os.path.dirname(self.editor.file_path)
        elif self.current_folder and os.path.isdir(self.current_folder):
            target_dir = self.current_folder
        elif self.default_workdir and os.path.isdir(self.default_workdir):
            target_dir = self.default_workdir

        if not target_dir:
            QMessageBox.information(self, "提示", "请先打开一个文件夹。")
            return

        # 让用户输入文件名
        name, ok = QInputDialog.getText(
            self, "新建文件", "文件名:", text="新建文档.md"
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        if not name.endswith(('.md', '.markdown', '.txt')):
            name += '.md'
        file_path = os.path.join(target_dir, name)
        if os.path.exists(file_path):
            QMessageBox.warning(self, "提示", f"文件已存在:\n{file_path}")
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("")
            self.load_file(file_path)
            self.status_label.setText(f"已创建: {name}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建文件失败:\n{e}")

    def _delete_filelist_file(self, path):
        """删除文件列表中的文件"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除以下文件吗？\n{os.path.basename(path)}\n\n{path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(path)
                self.refresh_filelist_for_current_file()
                self.status_label.setText(f"已删除: {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败:\n{e}")

    # ============================================================
    # 导出
    # ============================================================

    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 HTML", "", "HTML 文件 (*.html)")
        if path:
            self.editor.export_html(path)
            self.status_label.setText(f"已导出到 {path}")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 PDF", "", "PDF 文件 (*.pdf)")
        if path:
            self.editor.web_view.page().printToPdf(path)
            self.status_label.setText(f"正在导出 PDF 到 {path}")

    # ============================================================
    # 编辑功能
    # ============================================================

    def insert_format(self, before, after):
        """插入格式标记"""
        js = f"""
        var sel = window.getSelection();
        if (sel.rangeCount > 0 && sel.toString()) {{
            var text = sel.toString();
            document.execCommand('insertText', false, '{before}' + text + '{after}');
        }} else {{
            document.execCommand('insertText', false, '{before}{after}');
            var range = sel.getRangeAt(0);
            range.setStart(range.startContainer, range.startOffset - {len(after)});
            range.setEnd(range.endContainer, range.endOffset - {len(after)});
            sel.removeAllRanges();
            sel.addRange(range);
        }}
        window.editorAPI.render();
        """
        self.editor.run_js(js)

    def insert_heading(self, level):
        """插入标题"""
        js = f"""
        var sel = window.getSelection();
        var node = sel.anchorNode;
        while (node && node.nodeType === 3) node = node.parentNode;
        if (node) {{
            var text = node.textContent;
            text = text.replace(/^#+\\s*/, '');
            node.textContent = '{"#" * level} ' + text;
            window.editorAPI.render();
        }}
        """
        self.editor.run_js(js)

    def insert_image(self):
        """插入图片：代理给 EditorWidget（需要弹文件选择框）"""
        if self.editor and hasattr(self.editor, "insert_image"):
            self.editor.insert_image()

    def find_text(self):
        """查找（使用浏览器原生）"""
        self.editor.run_js("window.find('');")

    def toggle_source_mode(self):
        self.editor.toggle_source_mode()

    def select_all(self):
        """全选编辑器内容"""
        if self.editor:
            try:
                self.editor.web_view.page().triggerAction(QWebEnginePage.WebAction.SelectAll)
            except Exception:
                pass

    def copy_selection(self):
        """复制选中内容"""
        if self.editor:
            try:
                self.editor.web_view.page().triggerAction(QWebEnginePage.WebAction.Copy)
            except Exception:
                pass

    def cut_selection(self):
        """剪切选中内容"""
        if self.editor:
            try:
                self.editor.web_view.page().triggerAction(QWebEnginePage.WebAction.Cut)
            except Exception:
                pass

    def paste_clipboard(self):
        """粘贴剪贴板内容"""
        if self.editor:
            try:
                self.editor.web_view.page().triggerAction(QWebEnginePage.WebAction.Paste)
            except Exception:
                pass

    # ============================================================
    # 视图控制
    # ============================================================

    def toggle_sidebar(self):
        """切换整个侧边栏（文件列表 + 大纲）"""
        visible = not self.dock.isVisible()
        self.dock.setVisible(visible)
        self.toggle_filelist_action.setChecked(visible)
        self.toggle_outline_action.setChecked(visible)
        self.filelist_panel.setVisible(visible)
        self.outline_panel.setVisible(visible)

    def toggle_filelist(self):
        """切换文件列表面板"""
        visible = self.toggle_filelist_action.isChecked()
        self.filelist_panel.setVisible(visible)
        if not visible and not self.outline_panel.isVisible():
            self.dock.setVisible(False)
        elif visible or self.outline_panel.isVisible():
            self.dock.setVisible(True)

    def toggle_outline(self):
        """切换大纲面板"""
        visible = self.toggle_outline_action.isChecked()
        self.outline_panel.setVisible(visible)
        if not visible and not self.filelist_panel.isVisible():
            self.dock.setVisible(False)
        elif visible or self.filelist_panel.isVisible():
            self.dock.setVisible(True)

    def toggle_focus_mode(self):
        self.focus_mode = not self.focus_mode
        self.focus_action.setChecked(self.focus_mode)
        self.editor.set_focus_mode(self.focus_mode)

    def toggle_typewriter_mode(self):
        self.typewriter_mode = not self.typewriter_mode
        self.typewriter_action.setChecked(self.typewriter_mode)
        self.editor.set_typewriter_mode(self.typewriter_mode)

    def toggle_preview_mode(self):
        """切换预览模式（纯阅读，只读）"""
        self.editor.run_js("window.editorAPI.togglePreviewMode();")
        # 异步获取当前预览状态并更新菜单和工具栏按钮状态
        def update_preview_state(result):
            if result:
                self.preview_action.setChecked(True)
                if hasattr(self, 'preview_btn'):
                    self.preview_btn.setChecked(True)
            else:
                self.preview_action.setChecked(False)
                if hasattr(self, 'preview_btn'):
                    self.preview_btn.setChecked(False)
        self.editor.web_view.page().runJavaScript(
            "(function(){ if (window.editorAPI && window.editorAPI.isPreviewMode) return window.editorAPI.isPreviewMode(); return false; })()",
            update_preview_state
        )

    def set_editor_mode(self, mode):
        """设置编辑器模式"""
        # 确保编辑器存在且可用
        if not hasattr(self, 'editor') or self.editor is None:
            return
        
        try:
            if mode == 'source':
                # 源代码模式：全屏显示源码
                self.editor.toggle_source_mode()
            elif mode == 'edit':
                # 编辑模式：正常编辑（所见即所得）
                self.editor.run_js("window.editorAPI.enterEditMode();")
            elif mode == 'wysiwyg':
                # 所见即所得模式：正常编辑
                self.editor.run_js("window.editorAPI.enterEditMode();")
            elif mode == 'split':
                # 分栏模式：左边源码 | 右边预览
                self._show_split_mode()
            elif mode == 'preview':
                # 纯预览模式：只读
                self.editor.run_js("window.editorAPI.enterPreviewMode();")
        except Exception as e:
            print(f"set_editor_mode error: {e}")

    def _show_split_mode(self):
        """显示分栏模式：左边源码编辑器，右边预览"""
        # 获取当前编辑器的内容
        def handle_content(content):
            # 切换到分栏布局
            self._switch_to_split_layout(content)
        
        self.editor.get_content(handle_content)

    def _switch_to_split_layout(self, content):
        """切换到分栏布局"""
        # 隐藏原来的编辑器
        if hasattr(self, 'editor'):
            self.editor.setVisible(False)
        
        # 创建分栏容器（如果不存在）
        if not hasattr(self, 'split_container'):
            self.split_container = QWidget()
            split_layout = QHBoxLayout(self.split_container)
            split_layout.setContentsMargins(0, 0, 0, 0)
            split_layout.setSpacing(0)
            
            # 左边：源码编辑器
            self.source_editor = EditorWidget(default_workdir=self.default_workdir)
            self.source_editor.set_dark_mode(self.dark_mode)
            split_layout.addWidget(self.source_editor, 1)
            
            # 分隔条
            self.split_splitter = QSplitter(Qt.Orientation.Horizontal)
            self.split_splitter.addWidget(self.source_editor)
            
            # 右边：预览视图
            self.preview_view = QWebEngineView()
            self.preview_view.setHtml(EDITOR_HTML)
            self.split_splitter.addWidget(self.preview_view)
            
            # 设置分隔条位置（50%）
            self.split_splitter.setStretchFactor(0, 1)
            self.split_splitter.setStretchFactor(1, 1)
            
            split_layout.addWidget(self.split_splitter)
        
        # 设置源码编辑器内容
        self.source_editor.set_content(content)
        self.source_editor.set_dark_mode(self.dark_mode)
        
        # 设置预览视图内容
        def set_preview():
            escaped = (
                content.replace('\\', '\\\\')
                .replace('\b', '\\b')
                .replace('\f', '\\f')
                .replace('\n', '\\n')
                .replace('\r', '\\r')
                .replace('\t', '\\t')
                .replace('\v', '\\v')
                .replace("'", "\\'")
            )
            self.preview_view.page().runJavaScript(f"window.editorAPI.setContent('{escaped}');")
            self.preview_view.page().runJavaScript(f"window.editorAPI.enterPreviewMode();")
        
        # 等待预览页面加载完成后设置内容
        self.preview_view.loadFinished.connect(lambda ok: set_preview() if ok else None)
        
        # 设置为中心部件
        self.setCentralWidget(self.split_container)
        self.split_container.show()

    def _exit_split_mode(self):
        """退出分栏模式"""
        if hasattr(self, 'split_container'):
            self.split_container.setVisible(False)
        if hasattr(self, 'editor'):
            self.editor.setVisible(True)
            self.setCentralWidget(self.editor)

    def set_theme(self, dark):
        """兼容旧接口：切换深/浅色主题"""
        self.apply_theme_by_key("dark" if dark else "light")

    def get_theme(self, key=None):
        """获取指定主题的数据"""
        if key is None:
            key = self.current_theme
        if key.startswith("custom:"):
            ck = key[7:]
            return self.custom_themes.get(ck, PRESET_THEMES["light"])
        return PRESET_THEMES.get(key, PRESET_THEMES["light"])

    def apply_theme_by_key(self, key):
        """根据主题 key 应用主题"""
        self.current_theme = key
        theme = self.get_theme(key)
        self.dark_mode = theme.get("is_dark", False)
        self.apply_theme()
        # 同步编辑器主题色
        self.apply_editor_theme(theme)
        # 更新菜单选中状态
        for k, action in self.theme_actions.items():
            action.setChecked(k == key)

    def apply_editor_theme(self, theme):
        """将主题色注入编辑器 (WebEngine)"""
        colors = theme.get("colors", {})
        js_vars = "; ".join(f"--{k}: {v}" for k, v in colors.items())
        js = f"""
        var root = document.documentElement;
        var editor = document.getElementById('editor');
        if (root) {{
            {"; ".join(f"root.style.setProperty('--{k}', '{v}')" for k, v in colors.items())};
            if ({str(theme.get('is_dark', False)).lower()}) {{
                root.classList.add('dark');
            }} else {{
                root.classList.remove('dark');
            }}
        }}
        """
        try:
            self.editor.page.runJavaScript(js)
        except Exception:
            pass

    def apply_theme(self):
        """应用 Qt UI 主题样式"""
        theme = self.get_theme()
        bg = theme.get("ui_bg", "#ffffff")
        fg = theme.get("ui_fg", "#333333")
        alt = theme.get("ui_alt", "#f0f0f0")
        sel = theme.get("ui_selection", "#cbe5ff")
        accent = theme.get("colors", {}).get("accent", "#4caf50")
        border = theme.get("colors", {}).get("border", "#e1e4e8")
        muted = theme.get("colors", {}).get("muted", "#6a737d")

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {bg}; }}
            QMenuBar {{
                background-color: {alt};
                color: {fg};
                border-bottom: 1px solid {border};
                padding: 2px;
            }}
            QMenuBar::item {{
                padding: 6px 12px;
                border-radius: 4px;
                spacing: 6px;
            }}
            QMenuBar::item:selected {{ background-color: {sel}; }}
            QMenu {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 6px 28px 6px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{ background-color: {sel}; }}
            QMenu::separator {{ height: 1px; background: {border}; margin: 4px 8px; }}
            QToolBar {{
                background: {bg};
                border: none;
                border-bottom: 1px solid {border};
                spacing: 2px;
                padding: 4px 6px;
            }}
            QToolBar QToolButton {{
                color: {fg};
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                background: transparent;
                min-width: 28px;
            }}
            QToolBar QToolButton:hover {{ background: {sel}; }}
            QToolBar QToolButton:pressed {{ background: {accent}; color: white; }}
            QStatusBar {{
                background: {alt};
                color: {muted};
                border-top: 1px solid {border};
            }}
            QStatusBar QLabel {{ color: {muted}; padding: 0 8px; }}
            QDockWidget {{
                color: {fg};
                titlebar-close-icon: none;
                titlebar-normal-icon: none;
            }}
            QDockWidget::title {{
                background: {alt};
                color: {fg};
                padding: 8px 10px;
                border-bottom: 1px solid {border};
                font-weight: 600;
            }}
            QDockWidget::close-button, QDockWidget::float-button {{
                background: transparent;
                border: none;
                padding: 2px;
                border-radius: 3px;
            }}
            QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
                background: {sel};
            }}
            QListWidget {{
                background-color: {bg};
                color: {fg};
                border: none;
                outline: none;
                padding: 4px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-radius: 5px;
                margin: 1px 4px;
            }}
            QListWidget::item:hover {{
                background-color: {sel};
            }}
            QListWidget::item:selected {{
                background-color: {sel};
                color: {fg};
                border: 1px solid {accent};
                font-weight: 600;
            }}
            QListWidget::item:disabled {{
                color: {muted};
                font-style: italic;
            }}
            QLabel {{ color: {fg}; }}
            QLineEdit {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 5px;
                padding: 5px 10px;
                selection-background-color: {sel};
            }}
            QLineEdit:focus {{ border-color: {accent}; }}
            QPushButton {{
                background-color: {alt};
                color: {fg};
                border: 1px solid {border};
                border-radius: 5px;
                padding: 6px 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {sel};
                border-color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {accent};
                color: white;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {border};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {muted}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: transparent;
                height: 8px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {border};
                border-radius: 4px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{ background: {muted}; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
        """)

    # ============================================================
    # 自定义主题
    # ============================================================

    def get_themes_dir(self):
        """获取自定义主题存放目录（跨平台）"""
        if getattr(sys, 'frozen', False):
            # 打包后：用户主题目录（按平台标准路径）
            if sys.platform == 'darwin':
                # macOS: ~/Documents/Writile/themes
                base = os.path.expanduser("~/Documents/Writile/themes")
            elif sys.platform == 'win32':
                # Windows: ~/Documents/Writile/themes
                base = os.path.expanduser("~/Documents/Writile/themes")
            else:
                # Linux: ~/.local/share/Writile/themes
                xdg_data = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
                base = os.path.join(xdg_data, 'Writile', 'themes')
        else:
            # 开发模式：项目目录下
            base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "themes")
        os.makedirs(base, exist_ok=True)
        return base

    def get_builtin_themes_dir(self):
        """获取内置主题目录 (打包后)"""
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, "themes")
        else:
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), "themes")

    def load_custom_themes(self):
        """加载自定义主题文件 (从用户目录和内置目录)"""
        # 加载用户主题
        themes_dir = self.get_themes_dir()
        for fname in os.listdir(themes_dir):
            if fname.endswith(".json"):
                path = os.path.join(themes_dir, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        theme = json.load(f)
                    key = fname[:-5]
                    self.custom_themes[key] = theme
                except Exception:
                    pass
        # 加载内置主题 (打包后)
        builtin_dir = self.get_builtin_themes_dir()
        if builtin_dir != themes_dir and os.path.isdir(builtin_dir):
            for fname in os.listdir(builtin_dir):
                if fname.endswith(".json"):
                    path = os.path.join(builtin_dir, fname)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            theme = json.load(f)
                        key = fname[:-5]
                        if key not in self.custom_themes:
                            self.custom_themes[key] = theme
                    except Exception:
                        pass

    def open_custom_theme_dialog(self):
        """打开可视化主题编辑器"""
        theme = self.get_theme()
        dlg = ThemeEditorDialog(theme, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_theme = dlg.get_theme()
            name = new_theme.get("name", "我的主题")
            key = name.lower().replace(" ", "_")
            # 保存到文件
            path = os.path.join(self.get_themes_dir(), f"{key}.json")
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(new_theme, f, ensure_ascii=False, indent=2)
            except Exception as e:
                QMessageBox.warning(self, "保存失败", f"无法保存主题文件:\n{e}")
                return
            self.custom_themes[key] = new_theme
            # 重建菜单
            self.create_menu_bar()
            # 应用
            self.apply_theme_by_key("custom:" + key)
            QMessageBox.information(self, "主题已保存", f"主题 '{name}' 已保存，并已应用。")

    # ============================================================
    # 快捷键自定义
    # ============================================================

    def collect_actions_data(self):
        """收集所有可自定义快捷键的 action"""
        data = []
        shortcuts = self.settings.value("shortcuts", {}, type=dict) or {}

        # 文件菜单
        data.append(("文件", "新建", self._get_shortcut("文件", "新建", "Ctrl+N"), self._actions.get("新建")))
        data.append(("文件", "打开", self._get_shortcut("文件", "打开", "Ctrl+O"), self._actions.get("打开")))
        data.append(("文件", "快速打开", self._get_shortcut("文件", "快速打开", "Ctrl+P"), self._actions.get("快速打开")))
        data.append(("文件", "保存", self._get_shortcut("文件", "保存", "Ctrl+S"), self._actions.get("保存")))
        data.append(("文件", "另存为", self._get_shortcut("文件", "另存为", "Ctrl+Shift+S"), self._actions.get("另存为")))
        data.append(("文件", "导出 HTML", self._get_shortcut("文件", "导出 HTML", ""), self._actions.get("导出 HTML")))
        data.append(("文件", "导出 PDF", self._get_shortcut("文件", "导出 PDF", ""), self._actions.get("导出 PDF")))
        data.append(("文件", "退出", self._get_shortcut("文件", "退出", "Ctrl+Q"), self._actions.get("退出")))

        # 编辑菜单
        data.append(("编辑", "查找", self._get_shortcut("编辑", "查找", "Ctrl+F"), self._actions.get("查找")))
        data.append(("编辑", "切换源码模式", self._get_shortcut("编辑", "切换源码模式", "Ctrl+/"), self._actions.get("切换源码模式")))

        # 格式菜单
        data.append(("格式", "粗体", self._get_shortcut("格式", "粗体", "Ctrl+B"), self._actions.get("粗体")))
        data.append(("格式", "斜体", self._get_shortcut("格式", "斜体", "Ctrl+I"), self._actions.get("斜体")))
        data.append(("格式", "行内代码", self._get_shortcut("格式", "行内代码", "Ctrl+`"), self._actions.get("行内代码")))
        data.append(("格式", "标题 1", self._get_shortcut("格式", "标题 1", "Ctrl+1"), self._actions.get("标题 1")))
        data.append(("格式", "标题 2", self._get_shortcut("格式", "标题 2", "Ctrl+2"), self._actions.get("标题 2")))
        data.append(("格式", "标题 3", self._get_shortcut("格式", "标题 3", "Ctrl+3"), self._actions.get("标题 3")))

        # 视图菜单
        data.append(("视图", "切换侧边栏", self._get_shortcut("视图", "切换侧边栏", "Ctrl+\\"), self._actions.get("切换侧边栏")))
        data.append(("视图", "显示文件列表", self._get_shortcut("视图", "显示文件列表", ""), self._actions.get("显示文件列表")))
        data.append(("视图", "显示大纲", self._get_shortcut("视图", "显示大纲", ""), self._actions.get("显示大纲")))
        data.append(("视图", "专注模式", self._get_shortcut("视图", "专注模式", "F8"), self._actions.get("专注模式")))
        data.append(("视图", "打字机模式", self._get_shortcut("视图", "打字机模式", "F9"), self._actions.get("打字机模式")))
        data.append(("视图", "切换主题", self._get_shortcut("视图", "切换主题", ""), self._actions.get("切换主题")))

        return data

    def _get_shortcut(self, cat, name, default):
        """获取保存的或默认的快捷键"""
        shortcuts = self.settings.value("shortcuts", {}, type=dict) or {}
        return shortcuts.get(f"{cat}|{name}", default)

    def open_shortcut_customizer(self):
        """打开快捷键自定义对话框"""
        actions_data = self.collect_actions_data()
        dlg = ShortcutCustomizerDialog(actions_data, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_shortcuts = dlg.get_shortcuts()
            # 保存
            self.settings.setValue("shortcuts", new_shortcuts)
            # 应用到 actions
            for (cat, name), shortcut in new_shortcuts.items():
                action = self._actions.get(name)
                if action:
                    action.setShortcut(QKeySequence(shortcut))
            QMessageBox.information(self, "快捷键已更新", "快捷键设置已保存。")

    def export_theme(self):
        """导出当前主题到文件"""
        theme = self.get_theme()
        default_name = theme.get("name", "my_theme").lower().replace(" ", "_") + ".json"
        path, _ = QFileDialog.getSaveFileName(self, "导出主题", default_name, "JSON 主题文件 (*.json)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(theme, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "导出成功", f"主题已导出到:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"无法导出主题:\n{e}")

    def import_theme(self):
        """导入主题文件"""
        path, _ = QFileDialog.getOpenFileName(self, "导入主题", "", "JSON 主题文件 (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                theme = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"无法读取主题文件:\n{e}")
            return
        name = theme.get("name", os.path.basename(path)[:-5])
        key = name.lower().replace(" ", "_")
        # 复制到 themes 目录
        dest = os.path.join(self.get_themes_dir(), f"{key}.json")
        try:
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(theme, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"无法保存主题:\n{e}")
            return
        self.custom_themes[key] = theme
        self.create_menu_bar()
        self.apply_theme_by_key("custom:" + key)
        QMessageBox.information(self, "导入成功", f"主题 '{name}' 已导入并应用。")

    def choose_editor_font(self):
        """选择编辑器字体"""
        current_font = self.editor.web_view.font() if hasattr(self.editor, 'web_view') else QFont()
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            # 通过 JS 设置编辑器字体
            family = font.family()
            size = font.pointSize()
            js = f"""
            var editor = document.getElementById('editor');
            if (editor) {{
                editor.style.fontFamily = '{family}';
                editor.style.fontSize = '{size}px';
            }}
            """
            try:
                self.editor.page.runJavaScript(js)
            except Exception:
                pass
            self.settings.setValue("editor_font_family", family)
            self.settings.setValue("editor_font_size", size)

    # ============================================================
    # 大纲
    # ============================================================

    def update_outline_async(self):
        """异步更新大纲"""
        def handle(content):
            outline = extract_outline(content or '')
            self.outline_widget.clear()
            for level, title in outline:
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, title)
                if level == 1:
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                    item.setForeground(QColor(0, 120, 215))
                elif level == 2:
                    item.setFont(QFont("", -1, QFont.Weight.DemiBold))
                elif level == 3:
                    item.setFont(QFont("", -1, QFont.Weight.Normal))
                else:
                    item.setForeground(QColor(128, 128, 128))
                indent = "  " * (level - 1)
                item.setText(indent + title)
                self.outline_widget.addItem(item)
            self._adjust_sidebar_panels()

        self.editor.get_content(handle)

    def outline_clicked(self, item):
        """点击大纲项，滚动到对应位置"""
        title = item.data(Qt.ItemDataRole.UserRole)
        if not title:
            return
        escaped = title.replace("'", "\\'")
        js = f"""
        var headers = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        for (var i = 0; i < headers.length; i++) {{
            if (headers[i].textContent.trim() === '{escaped}') {{
                headers[i].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                break;
            }}
        }}
        """
        self.editor.run_js(js)

    # ============================================================
    # 工具方法
    # ============================================================

    def update_title(self):
        if self.editor.file_path:
            title = os.path.basename(self.editor.file_path)
        else:
            title = "未命名.md"
        self.setWindowTitle(f"{title} - Writile")

    def update_word_count(self):
        def handle(stats):
            self.count_label.setText(
                f"字数: {stats['chinese'] + stats['english']} | "
                f"字符: {stats['chars']} | 行: {stats['lines']}"
            )
        if hasattr(self, 'editor') and self.editor:
            self.editor.get_word_count_async(handle)

    @staticmethod
    def _path_key(p):
        """路径比较键：统一大小写与绝对路径（Windows 不区分大小写）"""
        try:
            return os.path.normcase(os.path.abspath(p))
        except Exception:
            return p

    def _dedupe_paths(self, paths):
        """去重并保持顺序（按 path key 判重）"""
        seen = set()
        out = []
        for p in paths or []:
            key = self._path_key(p)
            if key in seen:
                continue
            seen.add(key)
            out.append(p)
        return out

    def _add_recent_file(self, path):
        """把 path 加入最近打开列表（去重、限量、持久化、刷新菜单）"""
        self.recent_files = self._dedupe_paths([path] + list(self.recent_files))[:10]
        self.settings.setValue("recent_files", self.recent_files)
        self.update_recent_menu()

    def update_recent_menu(self):
        self.recent_menu.clear()
        self.recent_files = self._dedupe_paths(self.recent_files)
        for path in self.recent_files:
            if os.path.exists(path):
                action = QAction(os.path.basename(path), self)
                action.setData(path)
                action.triggered.connect(lambda checked, p=path: self.load_file(p))
                self.recent_menu.addAction(action)

    def restore_state(self):
        dark = self.settings.value("dark_mode", False, type=bool)
        self.dark_mode = dark
        # 应用保存的主题
        saved_theme = self.settings.value("current_theme", "light", type=str) or "light"
        if saved_theme in PRESET_THEMES or saved_theme in self.custom_themes:
            self.apply_theme_by_key(saved_theme)
        else:
            self.apply_theme_by_key("light")

    def closeEvent(self, event):
        self.settings.setValue("dark_mode", self.dark_mode)
        self.settings.setValue("focus_mode", self.focus_mode)
        self.settings.setValue("typewriter_mode", self.typewriter_mode)
        self.settings.setValue("current_theme", self.current_theme)
        event.accept()

    def show_about(self):
        QMessageBox.about(self, "关于 Writile",
            "<h2>Writile</h2>"
            "<p>Typora 风格的所见即所得 Markdown 编辑器</p>"
            "<p>功能：即时渲染、专注模式、打字机模式、代码高亮、大纲、文件树</p>"
            "<p>技术栈：Python + PyQt6 + WebEngine</p>"
            "<hr>"
            "<p><b>快捷键:</b></p>"
            "<p>Ctrl+N: 新建 | Ctrl+O: 打开 | Ctrl+S: 保存</p>"
            "<p>Ctrl+P: 快速打开 | Ctrl+/: 源码模式</p>"
            "<p>Ctrl+B: 粗体 | Ctrl+I: 斜体 | Ctrl+`: 代码</p>"
            "<p>Ctrl+1/2/3: 标题 | F8: 专注模式 | F9: 打字机模式</p>"
            "<p>Ctrl+\\: 侧边栏 | Ctrl+Q: 退出</p>"
            "<p>视图菜单可单独切换文件列表/大纲</p>"
            "<hr>"
            "<p><b>编辑模式切换:</b></p>"
            "<p>工具栏按钮：源码 / 写作 / 分栏 / 预览</p>"
            "<p>Ctrl+/: 源码模式 | Ctrl+E: 预览模式</p>"
        )

    def show_shortcuts(self):
        shortcuts = (
            "快捷键列表:\n\n"
            "文件操作:\n"
            "  Ctrl+N        新建文件\n"
            "  Ctrl+O        打开文件\n"
            "  Ctrl+P        快速打开（模糊搜索）\n"
            "  Ctrl+S        保存\n"
            "  Ctrl+Shift+S  另存为\n"
            "  Ctrl+Q        退出\n\n"
            "编辑:\n"
            "  Ctrl+/        切换源码模式\n"
            "  Ctrl+F        查找\n\n"
            "格式:\n"
            "  Ctrl+B        粗体\n"
            "  Ctrl+I        斜体\n"
            "  Ctrl+`        行内代码\n"
            "  Ctrl+1/2/3    标题1/2/3\n\n"
            "视图:\n"
            "  F8            专注模式\n"
            "  F9            打字机模式\n"
            "  Ctrl+\\\\       切换侧边栏（文件列表+大纲）\n"
            "  视图菜单     单独切换文件列表/大纲\n"
        )
        QMessageBox.information(self, "快捷键", shortcuts)


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


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Writile")
    app.setOrganizationName("Writile")
    app.setStyle("Fusion")

    # 设置跨平台默认字体
    app.setFont(get_platform_default_font())

    # macOS: 使用原生菜单栏
    if sys.platform == 'darwin':
        app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, False)

    # 设置应用图标
    app_icon = get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # 解析命令行参数：若传入了文件路径（双击 .md），启动时直接打开
    initial_file = None
    args = sys.argv[1:]  # 跳过 argv[0]（程序自身路径）
    for arg in args:
        # 跳过常见 flag / DDE 参数
        if arg.startswith('-'):
            continue
        # PyInstaller 打包后在 Windows 双击 .md 文件时，文件路径会是唯一的非 flag 参数
        possible_path = arg.strip().strip('"')
        if os.path.isabs(possible_path) or os.path.exists(possible_path):
            initial_file = os.path.abspath(possible_path)
            break

    window = MainWindow(initial_file=initial_file)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
