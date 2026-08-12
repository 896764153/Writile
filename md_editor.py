# -*- coding: utf-8 -*-
"""
Typora 风格 Markdown 编辑器
核心特点：所见即所得、即时渲染、不分屏、专注模式、打字机模式
"""

import os
import sys
import json
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QStatusBar, QToolBar, QSplitter,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QDockWidget, QLineEdit, QPushButton, QLabel, QInputDialog,
    QMenu, QDialog, QColorDialog, QFontDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QSpinBox, QGroupBox,
    QGridLayout, QScrollArea, QFrame, QKeySequenceEdit
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QUrl, QFileInfo, QSettings, pyqtSlot, QObject
)
from PyQt6.QtGui import (
    QAction, QActionGroup, QIcon, QFont, QKeySequence, QShortcut, QColor, QPalette, QPixmap
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
    --fg: #1a1a1a;
    --muted: #6a737d;
    --code-bg: #f6f8fa;
    --border: #e1e4e8;
    --link: #0366d6;
    --accent: #4caf50;
    --selection: #cce5ff;
    --current-line: #fffbea;
    --typewriter-line: #fff8dc;
}

html.dark {
    --bg: #1e1e1e;
    --fg: #d4d4d4;
    --muted: #8b949e;
    --code-bg: #2d2d30;
    --border: #3c3c3c;
    --link: #58a6ff;
    --accent: #4caf50;
    --selection: #264f78;
    --current-line: #3a3a1f;
    --typewriter-line: #3b3520;
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
}

#editor {
    max-width: 860px;
    margin: 0 auto;
    padding: 60px 80px 200px 80px;
    min-height: 100%;
    outline: none;
    overflow-y: auto;
    height: 100vh;
}

#editor:focus { outline: none; }

#editor[data-mode="source"] {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* 标题 */
h1 { font-size: 2em; border-bottom: 1px solid var(--border); padding-bottom: .3em; margin: 1em 0; }
h2 { font-size: 1.5em; border-bottom: 1px solid var(--border); padding-bottom: .3em; margin: 1em 0; }
h3 { font-size: 1.25em; margin: 1em 0; }
h4 { font-size: 1em; margin: 1em 0; }
h5 { font-size: .875em; margin: 1em 0; color: var(--muted); }
h6 { font-size: .85em; margin: 1em 0; color: var(--muted); }

p { margin: 16px 0; }
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
strong { font-weight: 600; }
em { font-style: italic; }
del { text-decoration: line-through; }

blockquote {
    padding: 0 16px;
    color: var(--muted);
    border-left: 4px solid var(--border);
    margin: 16px 0;
}

ul, ol { padding-left: 2em; margin: 16px 0; }
li { margin: 4px 0; }
li > ul, li > ol { margin: 4px 0; }

code {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 0.9em;
    background: var(--code-bg);
    padding: .2em .4em;
    border-radius: 4px;
}

pre {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 0.9em;
    background: var(--code-bg);
    border-radius: 8px;
    padding: 16px;
    overflow: auto;
    line-height: 1.5;
    margin: 16px 0;
}
pre code { background: none; padding: 0; font-size: 100%; }

table {
    border-collapse: collapse;
    margin: 16px 0;
    width: 100%;
}
th, td {
    border: 1px solid var(--border);
    padding: 6px 13px;
}
th { background: var(--code-bg); font-weight: 600; }
tr:nth-child(2n) { background: var(--code-bg); }

img { max-width: 100%; }
hr { border: none; border-top: 2px solid var(--border); margin: 32px 0; }
mark { background: #fff3a0; padding: 1px 3px; border-radius: 3px; }

kbd {
    display: inline-block;
    padding: 3px 5px;
    font-size: 11px;
    color: var(--muted);
    background-color: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
}

.task-list-item { list-style-type: none; }
.task-list-item input { margin: 0 .5em .25em -1.4em; }

/* 代码高亮 */
.hljs { display: block; overflow-x: auto; padding: 0.5em; }
.hljs-comment, .hljs-quote { color: #998; font-style: italic; }
.hljs-keyword, .hljs-selector-tag, .hljs-subst { color: #333; font-weight: bold; }
.hljs-number, .hljs-literal, .hljs-variable, .hljs-template-variable, .hljs-tag .hljs-attr { color: #008080; }
.hljs-string, .hljs-doctag { color: #d14; }
.hljs-title, .hljs-section, .hljs-selector-id { color: #900; font-weight: bold; }
.hljs-type, .hljs-class .hljs-title, .hljs-type .hljs-title { color: #458; font-weight: bold; }
.hljs-tag, .hljs-name, .hljs-attribute { color: navy; font-weight: normal; }
.hljs-regexp, .hljs-link { color: #009926; }
.hljs-symbol, .hljs-bullet { color: #990073; }
.hljs-built_in, .hljs-builtin-name { color: #0086b3; }
.hljs-meta { color: #999; font-weight: bold; }
.hljs-deletion { background: #fdd; }
.hljs-addition { background: #dfd; }
.hljs-emphasis { font-style: italic; }
.hljs-strong { font-weight: bold; }

html.dark .hljs { color: #abb2bf; background: var(--code-bg); }
html.dark .hljs-comment, html.dark .hljs-quote { color: #5c6370; font-style: italic; }
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
body.focus-mode #editor > * { opacity: 0.3; transition: opacity 0.3s; }
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
}

/* MathJax */
mjx-container { font-size: 1.1em !important; }

/* Mermaid */
.mermaid { text-align: center; margin: 16px 0; }

/* 拖拽提示 */
.drag-over { background: var(--selection) !important; }

/* 滚动条 */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
</style>
</head>
<body>

<div id="editor" contenteditable="true" data-placeholder="开始写作... (Markdown 格式)"></div>

<!-- Marked.js (Markdown 解析) -->
<script>
/*! marked v4.3.0 | (c) 2018- Chenchen Shen and contributors | MIT license */
!function(e,t){"object"==typeof exports&&"undefined"!=typeof module?t(exports):"function"==typeof define&&define.amd?define(["exports"],t):t(e.marked={})}(this,function(e){"use strict";function t(e,t){this.marked=e,this.defaults=t}function n(e){for(var t=1,n=arguments.length;t<n;t++)for(var r in arguments[t])e[r]=arguments[t][r];return e}function r(e,t,n){var r=n.walker||new i(n);r.tokens=n.tokens;var s=r.renderTokens(r.lex(e));return s}function i(e){this.options=e||{},this.renderer=this.options.renderer||new s,this.renderer.options=this.options}function s(e){this.options=e||{}}function a(){}var o={newline:/^\n+/,code:/^( {4}[^\n]+\n*)+/,fences:f,hr:/^ {0,3}((?:- *){3,}|(?:_ *){3,}|(?:\* *){3,})(?:\n+|$)/,heading:l,heading2:/^ {0,3}(#{1,6})(?:\s|$)/,lheading:/^([^\n]+)\n {0,3}(=+|#+) {0,3}\n+/,blockquote:p,bullet:k,list:A,def:x,table:w,paragraph:b,text:/^[^\n]+/,nptable:g};function l(e){this.options=e||{}}function p(e){this.tokens=[],this.token=null,this.options=e||{},this.options.pedantic&&(o.blockquote=/^( {0,3}> ?(paragraph|[^\n]*)(?:\n( {0,3}> ?[^\n]+))*)+/)}function u(e){this.tokens=[],this.token=null,this.options=e||{}}function c(e){this.options=e||{}}function h(e){this.options=e||{}}function d(e){var t=String(e);return t=t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function f(e,t,n){var r=n.tok();return r}function g(){}e.Parser=function(e,t){this.tokens=[],this.token=null,this.options=t||n.defaults},e.parser=function(t,n){var r=new e.Parser(t,n);return r.parse()},e.Lexer=function(e,t){this.tokens=[],this.tokens.links=Object.create(null),this.options=n(this.options,t),this.rules=o.pedantic?n({},o.pedantic):n({},o.normal||o),this.options.pedantic&&(o.blockquote=/^( {0,3}> ?(paragraph|[^\n]*)(?:\n( {0,3}> ?[^\n]+))*)+/),this.options.gfm&&(o.fences=/^ {0,3}(`{3,})(?=[^\s]*$)((?:\s*\n|.)*?)(?:\n {0,3}\1|$)/,o.paragraph=/^([^\n]+(?:\n(?!hr|heading|lheading|blockquote|fences|list|html|table|def|\n{2,}))[^\n]*)*/),this.options.breaks&&(o.inline=/^\\?(`+)(?!`)(\s?[\s\S]*?[^`]\s?)\1(?!`)/),this.token=null},e.lexer=function(t,n){var r=new e.Lexer(n);return r.lex(t)},e.InlineLexer=function(e,t){this.options=n(this.options,t)},e.inlineLexer=function(t,n,r){var i=new e.InlineLexer(n,r);return i.output(t)},e.Slugger=function(){this.seen=Object.create(null)},e.parse=function(t,n){return new e.Parser(n).parse(t)},e.marked=r,n(r,{defaults:{gfm:!0,breaks:!1,pedantic:!1,silent:!1,highlight:null,langPrefix:"language-",smartLists:!1,smartypants:!1,headerIds:!0,headerPrefix:"",xhtml:!1,baseUrl:null,mangle:!0,renderer:null,walkable:!0}}),r.options=function(e){return e?n(r.defaults,e):r.defaults},r.setOptions=function(e){n(r.defaults,e)},r.use=function(){var e,t,i,s,o,l;for(t=0;t<arguments.length;t++)if(e=arguments[t],i=Object.keys(e),o=i.length,0!==o)for(;o--;)l=i[o],s=e[l],"object"==typeof s?r.defaults[l]=r.defaults[l]?n(r.defaults[l],s):s:r.defaults[l]=s},r.walk=function(e,t){return new i(t).walk(e)},r.parseInline=function(e,t){return new i(t).parseInline(e)},e.exports=r});
</script>

<!-- Highlight.js (代码高亮) -->
<script>
/*! highlight.js v11.9.0 | BSD-3-Clause License | https://highlightjs.org */
var hljs=function(){"use strict";var e,t,n=Object.freeze({__proto__:null,registerLanguage:function(t,n){e[t]=n},registerAliases:function(){},highlight:function(e,t){return{value:e}},highlightAuto:function(e){return{value:e}}});return n}();
</script>

<!-- 编辑器逻辑 -->
<script>
(function() {
    var editor = document.getElementById('editor');
    var isRendering = false;
    var renderTimer = null;
    var savedRange = null;
    var savedMarkdown = '';

    // 简易 Markdown 渲染器（避免依赖外部库）
    function escapeHtml(text) {
        var map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'};
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    function renderMarkdown(text) {
        if (!text) return '';

        var lines = text.split('\n');
        var html = [];
        var i = 0;
        var inList = false;
        var listType = '';
        var inBlockquote = false;
        var inCode = false;
        var codeLang = '';

        while (i < lines.length) {
            var line = lines[i];

            // 代码块
            if (line.match(/^```/)) {
                if (inCode) {
                    html.push('</code></pre>');
                    inCode = false;
                } else {
                    codeLang = line.replace(/^```/, '').trim();
                    html.push('<pre><code class="language-' + escapeHtml(codeLang) + '">');
                    inCode = true;
                }
                i++;
                continue;
            }
            if (inCode) {
                html.push(escapeHtml(line) + '\n');
                i++;
                continue;
            }

            // 空行
            if (line.trim() === '') {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                i++;
                continue;
            }

            // 标题
            var headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
            if (headingMatch) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                var level = headingMatch[1].length;
                html.push('<h' + level + '>' + renderInline(headingMatch[2]) + '</h' + level + '>');
                i++;
                continue;
            }

            // 分割线
            if (line.match(/^(-{3,}|\*{3,}|_{3,})$/)) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (inBlockquote) { html.push('</blockquote>'); inBlockquote = false; }
                html.push('<hr>');
                i++;
                continue;
            }

            // 引用
            if (line.match(/^>/)) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                if (!inBlockquote) { html.push('<blockquote>'); inBlockquote = true; }
                html.push('<p>' + renderInline(line.replace(/^>\s*/, '')) + '</p>');
                i++;
                continue;
            } else if (inBlockquote) {
                html.push('</blockquote>');
                inBlockquote = false;
            }

            // 无序列表
            if (line.match(/^[-*+]\s+/)) {
                if (!inList) { html.push('<ul>'); inList = true; listType = 'ul'; }
                html.push('<li>' + renderInline(line.replace(/^[-*+]\s+/, '')) + '</li>');
                i++;
                continue;
            }

            // 有序列表
            if (line.match(/^\d+\.\s+/)) {
                if (!inList) { html.push('<ol>'); inList = true; listType = 'ol'; }
                html.push('<li>' + renderInline(line.replace(/^\d+\.\s+/, '')) + '</li>');
                i++;
                continue;
            }

            // 表格（简单判断）
            if (line.match(/^\|.+\|$/) && i + 1 < lines.length && lines[i+1].match(/^[\|: -]+$/)) {
                if (inList) { html.push('</' + listType + '>'); inList = false; }
                html.push('<table><thead><tr>');
                var headers = line.split('|').filter(function(c) { return c.trim(); });
                headers.forEach(function(h) {
                    html.push('<th>' + renderInline(h.trim()) + '</th>');
                });
                html.push('</tr></thead><tbody>');
                i += 2;
                while (i < lines.length && lines[i].match(/^\|.+\|$/)) {
                    html.push('<tr>');
                    var cells = lines[i].split('|').filter(function(c) { return c.trim() || c === ''; });
                    cells.forEach(function(c) {
                        html.push('<td>' + renderInline(c.trim()) + '</td>');
                    });
                    html.push('</tr>');
                    i++;
                }
                html.push('</tbody></table>');
                continue;
            }

            // 普通段落
            if (inList) { html.push('</' + listType + '>'); inList = false; }
            var para = [line];
            while (i + 1 < lines.length && lines[i+1].trim() !== '' &&
                   !lines[i+1].match(/^(#{1,6}\s|>|[-*+]\s|\d+\.\s|```|---)/)) {
                para.push(lines[i+1]);
                i++;
            }
            html.push('<p>' + renderInline(para.join('\n').replace(/\n/g, '<br>')) + '</p>');
            i++;
        }

        if (inList) html.push('</' + listType + '>');
        if (inBlockquote) html.push('</blockquote>');
        if (inCode) html.push('</code></pre>');

        return html.join('\n');
    }

    function renderInline(text) {
        if (!text) return '';
        text = escapeHtml(text);

        // 图片
        text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img alt="$1" src="$2">');

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

        // 键盘按键
        text = text.replace(/<kbd>([^<]+)<\/kbd>/g, '<kbd>$1</kbd>');

        return text;
    }

    // 保存光标位置
    function saveCursor() {
        var sel = window.getSelection();
        if (sel.rangeCount > 0) {
            var range = sel.getRangeAt(0);
            savedRange = {
                startContainer: range.startContainer,
                startOffset: range.startOffset,
                endContainer: range.endContainer,
                endOffset: range.endOffset
            };
        }
    }

    // 恢复光标位置
    function restoreCursor() {
        if (savedRange) {
            try {
                var sel = window.getSelection();
                sel.removeAllRanges();
                var range = document.createRange();
                range.setStart(savedRange.startContainer, savedRange.startOffset);
                range.setEnd(savedRange.endContainer, savedRange.endOffset);
                sel.addRange(range);
            } catch(e) {}
        }
    }

    // 渲染内容
    function render() {
        if (isRendering) return;
        isRendering = true;

        var text = editor.innerText;
        savedMarkdown = text;

        saveCursor();
        var html = renderMarkdown(text);
        editor.innerHTML = html;
        restoreCursor();

        // 高亮代码块
        var codeBlocks = editor.querySelectorAll('pre code');
        codeBlocks.forEach(function(block) {
            try { if (window.hljs) hljs.highlightElement(block); } catch(e) {}
        });

        isRendering = false;
    }

    // 防抖渲染
    function scheduleRender() {
        if (renderTimer) clearTimeout(renderTimer);
        renderTimer = setTimeout(render, 500);
    }

    // 监听输入
    editor.addEventListener('input', function() {
        scheduleRender();
        // 通知 Python 内容已变化
        if (window.qt && window.qt.onContentChanged) {
            window.qt.onContentChanged();
        }
    });

    // 监听键盘事件 - 自动配对
    editor.addEventListener('keydown', function(e) {
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
        // Tab 缩进
        if (e.key === 'Tab') {
            e.preventDefault();
            document.execCommand('insertText', false, '    ');
        }
        // Ctrl+/ 切换源码模式
        if (e.ctrlKey && e.key === '/') {
            e.preventDefault();
            toggleSourceMode();
        }
        // Enter 在列表中自动延续
        if (e.key === 'Enter') {
            var sel = window.getSelection();
            var node = sel.anchorNode;
            while (node && node.nodeType === 3) node = node.parentNode;
            if (node && node.tagName === 'LI' && node.textContent.trim() === '') {
                e.preventDefault();
                var parent = node.parentNode;
                parent.removeChild(node);
                if (parent.children.length === 0) parent.parentNode.removeChild(parent);
                document.execCommand('insertParagraph', false);
            }
        }
    });

    // 源码模式
    var sourceMode = false;
    function toggleSourceMode() {
        sourceMode = !sourceMode;
        if (sourceMode) {
            editor.setAttribute('data-mode', 'source');
            var text = savedMarkdown || editor.innerText;
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
        var blocks = editor.children;
        for (var i = 0; i < blocks.length; i++) {
            blocks[i].classList.remove('current-line');
        }
        if (block !== editor) block.classList.add('current-line');
    }

    editor.addEventListener('keyup', updateCurrentLine);
    editor.addEventListener('click', updateCurrentLine);

    // 主题切换
    function setDarkMode(dark) {
        document.documentElement.classList.toggle('dark', dark);
    }

    // 公开接口
    window.editorAPI = {
        render: render,
        getContent: function() { return savedMarkdown || editor.innerText; },
        setContent: function(text) {
            savedMarkdown = text;
            editor.innerHTML = renderMarkdown(text);
            var codeBlocks = editor.querySelectorAll('pre code');
            codeBlocks.forEach(function(block) {
                try { if (window.hljs) hljs.highlightElement(block); } catch(e) {}
            });
        },
        setDarkMode: setDarkMode,
        setFocusMode: setFocusMode,
        setTypewriterMode: setTypewriterMode,
        toggleSourceMode: toggleSourceMode,
        isSourceMode: function() { return sourceMode; }
    };

    // 初始化
    window.editorAPI.setContent('');

})();
</script>

</body>
</html>"""


# ============================================================
# 编辑器页面类
# ============================================================

class EditorPage(QWebEnginePage):
    """自定义 WebEngine 页面，用于 JS 通信"""
    def __init__(self, parent=None):
        super().__init__(parent)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # 开发时调试用
        pass


# ============================================================
# 编辑器组件
# ============================================================

class EditorWidget(QWidget):
    """单个编辑器组件（Typora 风格：所见即所得）"""

    def __init__(self, parent=None, file_path=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_modified = False
        self.dark_mode = False
        self.focus_mode = False
        self.typewriter_mode = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # WebEngine 配置
        self.profile = QWebEngineProfile()
        self.web_view = QWebEngineView()
        self.page = EditorPage(self.profile)
        self.web_view.setPage(self.page)

        # 启用所有必要特性
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)

        # 加载 HTML
        self.web_view.setHtml(EDITOR_HTML, QUrl("about:blank"))

        # 等待页面加载完成
        self.web_view.loadFinished.connect(self.on_load_finished)

        layout.addWidget(self.web_view)

        # 加载文件
        if file_path and os.path.exists(file_path):
            QTimer.singleShot(100, lambda: self.load_file(file_path))

    def on_load_finished(self, ok):
        if ok and self.file_path and os.path.exists(self.file_path):
            self.load_file(self.file_path)

    def run_js(self, code):
        """执行 JavaScript"""
        self.web_view.page().runJavaScript(code)

    def set_content(self, text):
        """设置内容"""
        escaped = text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')
        self.run_js(f"window.editorAPI.setContent('{escaped}')")
        self.is_modified = False

    def get_content(self, callback=None):
        """获取内容（异步）"""
        def handle(content):
            if callback:
                callback(content)
        self.web_view.page().runJavaScript("window.editorAPI.getContent()", handle)

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

    def load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.file_path = path
            self.set_content(content)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件:\n{e}")

    def save_file(self, path=None):
        if path:
            self.file_path = path
        if not self.file_path:
            return False

        def do_save(content):
            try:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.is_modified = False
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件:\n{e}")

        self.get_content(do_save)
        return True

    def export_html(self, path):
        """导出 HTML"""
        def do_export(content):
            html = self._render_full_html(content)
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(html)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{e}")

        self.get_content(do_export)

    def _render_full_html(self, md_text):
        """渲染完整 HTML 页面（用于导出）"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Export</title>
<style>
body {{ font-family: -apple-system, 'Segoe UI', sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; line-height: 1.7; color: #1a1a1a; }}
pre {{ background: #f6f8fa; padding: 16px; border-radius: 8px; overflow: auto; }}
code {{ background: #f6f8fa; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #dfe2e5; padding: 6px 13px; }}
th {{ background: #f6f8fa; }}
blockquote {{ border-left: 4px solid #e1e4e8; padding-left: 16px; color: #6a737d; margin: 16px 0; }}
h1 {{ border-bottom: 1px solid #e1e4e8; padding-bottom: .3em; }}
h2 {{ border-bottom: 1px solid #e1e4e8; padding-bottom: .3em; }}
img {{ max-width: 100%; }}
</style>
</head>
<body>
<div id="content"></div>
<script>
var md = {json.dumps(md_text)};
document.getElementById('content').innerHTML = md;
</script>
</body>
</html>"""

    def get_word_count_async(self, callback):
        """异步获取字数统计"""
        def handle(content):
            import re
            chinese = len(re.findall(r'[\u4e00-\u9fff]', content))
            english = len(re.findall(r'[a-zA-Z]+', content))
            chars = len(content)
            lines = content.count('\n') + 1 if content else 0
            callback({'chinese': chinese, 'english': english, 'chars': chars, 'lines': lines})
        self.get_content(handle)


# ============================================================
# 模糊搜索对话框
# ============================================================

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

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Writile - 所见即所得 Markdown 编辑器")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

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
        self.current_folder = self.settings.value("current_folder", "", type=str) or ""
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

        # 快捷键
        self.create_shortcuts()

        # 恢复状态
        self.restore_state()

        # 新建空文档
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

        # 主题子菜单
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
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))

        new_btn = QAction("新建", self)
        new_btn.triggered.connect(self.new_file)
        toolbar.addAction(new_btn)

        open_btn = QAction("打开", self)
        open_btn.triggered.connect(self.open_file)
        toolbar.addAction(open_btn)

        save_btn = QAction("保存", self)
        save_btn.triggered.connect(self.save_file)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        bold_btn = QAction("B", self)
        bold_btn.triggered.connect(lambda: self.insert_format("**", "**"))
        toolbar.addAction(bold_btn)

        italic_btn = QAction("I", self)
        italic_btn.triggered.connect(lambda: self.insert_format("*", "*"))
        toolbar.addAction(italic_btn)

        code_btn = QAction("< >", self)
        code_btn.triggered.connect(lambda: self.insert_format("`", "`"))
        toolbar.addAction(code_btn)

        toolbar.addSeparator()

        focus_btn = QAction("专注", self)
        focus_btn.triggered.connect(self.toggle_focus_mode)
        toolbar.addAction(focus_btn)

        typewriter_btn = QAction("打字机", self)
        typewriter_btn.triggered.connect(self.toggle_typewriter_mode)
        toolbar.addAction(typewriter_btn)

        toolbar.addSeparator()

        theme_btn = QAction("切换主题", self)
        theme_btn.triggered.connect(lambda: self.set_theme(not self.dark_mode))
        toolbar.addAction(theme_btn)

    def create_sidebar(self):
        """创建侧边栏（大纲 + 文件树）"""
        self.dock = QDockWidget("侧边栏", self)
        self.dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # 文件树
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self.on_tree_clicked)
        layout.addWidget(self.tree)

        # 大纲
        outline_label = QLabel("大纲")
        outline_label.setStyleSheet("padding: 8px; font-weight: bold; background: palette(mid);")
        layout.addWidget(outline_label)

        self.outline_widget = QListWidget()
        self.outline_widget.itemClicked.connect(self.outline_clicked)
        layout.addWidget(self.outline_widget)

        self.dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)

    def create_editor(self):
        """创建编辑器"""
        self.editor = EditorWidget()
        self.setCentralWidget(self.editor)

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)

        self.count_label = QLabel("字数: 0 | 字符: 0")
        self.status_bar.addPermanentWidget(self.count_label)

        # 定时更新字数
        self.count_timer = QTimer()
        self.count_timer.timeout.connect(self.update_word_count)
        self.count_timer.start(2000)

    def create_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Shift+1"), self, lambda: self.insert_heading(1))
        QShortcut(QKeySequence("Ctrl+Shift+2"), self, self.toggle_sidebar)

    # ============================================================
    # 文件操作
    # ============================================================

    def new_file(self):
        self.editor = EditorWidget()
        self.editor.set_dark_mode(self.dark_mode)
        self.setCentralWidget(self.editor)
        self.editor.file_path = None
        self.update_title()
        self.status_label.setText("新建文件")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", self.current_folder or "",
            "Markdown 文件 (*.md *.markdown *.txt);;所有文件 (*.*)"
        )
        if path:
            self.load_file(path)

    def load_file(self, path):
        self.editor = EditorWidget(file_path=path)
        self.editor.set_dark_mode(self.dark_mode)
        self.editor.set_focus_mode(self.focus_mode)
        self.editor.set_typewriter_mode(self.typewriter_mode)
        self.setCentralWidget(self.editor)
        self.update_title()

        if path not in self.recent_files:
            self.recent_files.insert(0, path)
            self.recent_files = self.recent_files[:10]
            self.settings.setValue("recent_files", self.recent_files)
            self.update_recent_menu()

        self.status_label.setText(f"已打开: {os.path.basename(path)}")
        QTimer.singleShot(500, self.update_outline_async)

    def save_file(self):
        if not self.editor.file_path:
            self.save_as_file()
        else:
            self.editor.save_file()
            self.update_title()
            self.status_label.setText("已保存")

    def save_as_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为", self.current_folder or "",
            "Markdown 文件 (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        if path:
            if self.editor.save_file(path):
                self.update_title()
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

        if not files:
            QMessageBox.information(self, "提示", "没有可用的文件。\n请先打开文件夹。")
            return

        dialog = QuickOpenDialog(files, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_file:
            self.load_file(dialog.selected_file)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "打开文件夹")
        if folder:
            self.current_folder = folder
            self.settings.setValue("current_folder", folder)
            self.populate_file_tree(folder)
            self.status_label.setText(f"已打开文件夹: {folder}")

    def populate_file_tree(self, folder):
        """填充文件树"""
        self.tree.clear()
        root_item = QTreeWidgetItem(self.tree, [os.path.basename(folder) or folder])
        root_item.setData(0, Qt.ItemDataRole.UserRole, folder)
        self._add_tree_items(root_item, folder)
        root_item.setExpanded(True)

    def _add_tree_items(self, parent_item, path):
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return

        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                # 跳过隐藏目录
                if entry.startswith('.'):
                    continue
                child = QTreeWidgetItem(parent_item, [entry])
                child.setData(0, Qt.ItemDataRole.UserRole, full_path)
                self._add_tree_items(child, full_path)
            elif entry.endswith(('.md', '.markdown', '.txt')):
                child = QTreeWidgetItem(parent_item, [entry])
                child.setData(0, Qt.ItemDataRole.UserRole, full_path)

    def on_tree_clicked(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.isfile(path):
            self.load_file(path)

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

    def find_text(self):
        """查找（使用浏览器原生）"""
        self.editor.run_js("window.find('');")

    def toggle_source_mode(self):
        self.editor.toggle_source_mode()

    # ============================================================
    # 视图控制
    # ============================================================

    def toggle_sidebar(self):
        self.dock.setVisible(not self.dock.isVisible())

    def toggle_focus_mode(self):
        self.focus_mode = not self.focus_mode
        self.focus_action.setChecked(self.focus_mode)
        self.editor.set_focus_mode(self.focus_mode)

    def toggle_typewriter_mode(self):
        self.typewriter_mode = not self.typewriter_mode
        self.typewriter_action.setChecked(self.typewriter_mode)
        self.editor.set_typewriter_mode(self.typewriter_mode)

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
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {bg}; }}
            QMenuBar {{ background-color: {alt}; color: {fg}; }}
            QMenuBar::item:selected {{ background-color: {sel}; }}
            QMenu {{ background-color: {bg}; color: {fg}; border: 1px solid {alt}; }}
            QMenu::item:selected {{ background-color: {sel}; }}
            QToolBar {{ background: {alt}; border: none; spacing: 4px; }}
            QToolBar QToolButton {{ color: {fg}; }}
            QStatusBar {{ background: {accent}; color: #ffffff; }}
            QStatusBar QLabel {{ color: #ffffff; }}
            QDockWidget {{ color: {fg}; }}
            QDockWidget::title {{ background: {alt}; padding: 6px; }}
            QTreeWidget {{ background-color: {alt}; color: {fg}; border: none; }}
            QTreeWidget::item:selected {{ background-color: {sel}; }}
            QListWidget {{ background-color: {alt}; color: {fg}; border: none; }}
            QListWidget::item:selected {{ background-color: {sel}; }}
            QLabel {{ color: {fg}; }}
            QLineEdit {{ background-color: {bg}; color: {fg}; border: 1px solid {alt}; padding: 4px; }}
            QPushButton {{ background-color: {alt}; color: {fg}; border: 1px solid {alt}; padding: 6px 12px; border-radius: 4px; }}
            QPushButton:hover {{ background-color: {sel}; }}
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
        data.append(("文件", "新建", self._get_shortcut("文件", "新建", "Ctrl+N"), self._actions.get("new")))
        data.append(("文件", "打开", self._get_shortcut("文件", "打开", "Ctrl+O"), self._actions.get("open")))
        data.append(("文件", "快速打开", self._get_shortcut("文件", "快速打开", "Ctrl+P"), self._actions.get("quick_open")))
        data.append(("文件", "保存", self._get_shortcut("文件", "保存", "Ctrl+S"), self._actions.get("save")))
        data.append(("文件", "另存为", self._get_shortcut("文件", "另存为", "Ctrl+Shift+S"), self._actions.get("save_as")))
        data.append(("文件", "导出 HTML", self._get_shortcut("文件", "导出 HTML", ""), self._actions.get("export_html")))
        data.append(("文件", "导出 PDF", self._get_shortcut("文件", "导出 PDF", ""), self._actions.get("export_pdf")))
        data.append(("文件", "退出", self._get_shortcut("文件", "退出", "Ctrl+Q"), self._actions.get("quit")))

        # 编辑菜单
        data.append(("编辑", "查找", self._get_shortcut("编辑", "查找", "Ctrl+F"), self._actions.get("find")))
        data.append(("编辑", "切换源码模式", self._get_shortcut("编辑", "切换源码模式", "Ctrl+/"), self._actions.get("source_mode")))

        # 格式菜单
        data.append(("格式", "粗体", self._get_shortcut("格式", "粗体", "Ctrl+B"), self._actions.get("bold")))
        data.append(("格式", "斜体", self._get_shortcut("格式", "斜体", "Ctrl+I"), self._actions.get("italic")))
        data.append(("格式", "行内代码", self._get_shortcut("格式", "行内代码", "Ctrl+`"), self._actions.get("code")))
        data.append(("格式", "标题 1", self._get_shortcut("格式", "标题 1", "Ctrl+1"), self._actions.get("h1")))
        data.append(("格式", "标题 2", self._get_shortcut("格式", "标题 2", "Ctrl+2"), self._actions.get("h2")))
        data.append(("格式", "标题 3", self._get_shortcut("格式", "标题 3", "Ctrl+3"), self._actions.get("h3")))

        # 视图菜单
        data.append(("视图", "切换侧边栏", self._get_shortcut("视图", "切换侧边栏", "Ctrl+\\"), self._actions.get("toggle_sidebar")))
        data.append(("视图", "专注模式", self._get_shortcut("视图", "专注模式", "F8"), self._actions.get("focus")))
        data.append(("视图", "打字机模式", self._get_shortcut("视图", "打字机模式", "F9"), self._actions.get("typewriter")))
        data.append(("视图", "切换主题", self._get_shortcut("视图", "切换主题", ""), self._actions.get("theme_toggle")))

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
            outline = extract_outline(content)
            self.outline_widget.clear()
            for level, title in outline:
                indent = "  " * (level - 1)
                item = QListWidgetItem(f"{indent}{title}")
                item.setData(Qt.ItemDataRole.UserRole, title)
                self.outline_widget.addItem(item)

        self.editor.get_content(handle)

    def outline_clicked(self, item):
        """点击大纲项，滚动到对应位置"""
        title = item.data(Qt.ItemDataRole.UserRole)
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

    def update_recent_menu(self):
        self.recent_menu.clear()
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
        if self.current_folder and os.path.isdir(self.current_folder):
            self.populate_file_tree(self.current_folder)

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
            "<p>Ctrl+\\\\: 侧边栏 | Ctrl+Q: 退出</p>"
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
            "  Ctrl+\\\\       切换侧边栏\n"
            "  Ctrl+Shift+1  切换文件树\n"
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

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
