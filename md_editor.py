# -*- coding: utf-8 -*-
"""
Typora 风格 Markdown 编辑器
核心特点：所见即所得、即时渲染、不分屏、专注模式、打字机模式

重构后结构：
  - editor_common.py: 共享基础（常量、HTML模板、编辑器组件类、对话框）
  - mode_wysiwyg.py:  写作模式 Mixin
  - mode_source.py:   源码模式 Mixin
  - mode_split.py:    分栏模式 Mixin
  - mode_preview.py:  预览模式 Mixin
  - md_editor.py:     主入口（MainWindow + main）
"""

import os

import sys
import json
import configparser

# Chromium / OpenGL 必须在导入任何 QtWebEngine 模块之前设置。
# 旧组合 --disable-gpu + --disable-software-rasterizer + --single-process
# 会让 Windows 上既没有硬件 GL，也没有软件回退，启动即闪退。
def _configure_webengine_env():
    if "QTWEBENGINE_CHROMIUM_FLAGS" not in os.environ:
        flags = [
            "--use-angle=swiftshader",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(flags)
    os.environ.setdefault("QT_OPENGL", "software")
    os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
    # if "QTWEBENGINE_CHROMIUM_FLAGS" not in os.environ:
    #     flags = [
    #         "--disable-gpu",
    #         "--disable-gpu-compositing",
    #         "--ignore-gpu-blocklist",
    #         "--in-process-gpu",
    #         "--disable-dev-shm-usage",
    #     ]
    #     if sys.platform.startswith("linux"):
    #         flags.extend(["--no-sandbox", "--no-zygote"])
    #     os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(flags)
    # os.environ.setdefault("QT_OPENGL", "software")


_configure_webengine_env()

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QFileDialog, QMessageBox, QStatusBar, QToolBar, QSplitter, QTabWidget,
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

# 从共享模块导入
from editor_common import (
    PRESET_THEMES, EDITOR_HTML,
    EditorWebView, EditorPage, EditorBridge, EditorWidget,
    FindDialog,
    RecentFilesDialog, QuickOpenDialog, ThemeEditorDialog, ShortcutCustomizerDialog,
    extract_outline,
    get_resource_path, get_app_icon, get_platform_default_font,
)

# 从模式模块导入 Mixin
from mode_wysiwyg import WysiwygModeMixin
from mode_source import SourceModeMixin
from mode_split import SplitModeMixin
from mode_preview import PreviewModeMixin


class MainWindow(WysiwygModeMixin, SourceModeMixin, SplitModeMixin, PreviewModeMixin, QMainWindow):
    """主窗口 - Typora 风格"""
    def __init__(self, initial_file=None):
        super().__init__()
        # 关键：立即读取并清除启动模式标记，避免重启死循环
        # （每个新进程都会读取这个值，然后立刻清掉，确保 switch_to_top_mode 只触发一次）
        try:
            from PyQt6.QtCore import QSettings
            _boot_settings = QSettings("Writile", "Editor")
            _boot_mode = _boot_settings.value("startup_top_mode", "", type=str) or ""
            _boot_file = _boot_settings.value("startup_open_file", "", type=str) or ""
            if _boot_mode:
                _boot_settings.remove("startup_top_mode")
            if _boot_file:
                _boot_settings.remove("startup_open_file")
            _boot_settings.sync()
        except Exception:
            _boot_mode = ""
            _boot_file = ""
        self._startup_pending_mode = _boot_mode
        self._startup_pending_file = _boot_file

        self.setWindowTitle("Writile - 编辑模式 Markdown 编辑器")
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
        self._editor_mode = 'wysiwyg'  # 当前模式状态缓存
        self.create_menu_bar()
        self.create_toolbar()
        self.create_sidebar()
        self.create_editor()
        self.create_status_bar()

        # 主题
        self.apply_theme()

        # 延迟推送补全数据到 JS 端（等待页面就绪）
        QTimer.singleShot(500, self._push_completion_data)

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

        # 处理启动时的大模式切换（从 __init__ 头部读取并清除的标记）
        try:
            if self._startup_pending_mode == 'split':
                # 延迟进入分栏模式（等文件加载完成 + JS 页面就绪）
                startup_file = self._startup_pending_file

                def _enter_split_after_init():
                    try:
                        # 关键：不调用 switch_to_top_mode（它会再写 startup_top_mode 并触发重启），
                        # 而是直接调用 _rebuild_split_layout 重建分栏布局。
                        # 这样 _editor_mode 变为 'split'，下次启动 switch_to_top_mode('split')
                        # 时 self._current_mode()=='split'，直接 return 不重启。
                        # 销毁主编辑器（如果是 split 模式要重建）
                        try:
                            if getattr(self, 'editor', None) and not getattr(self.editor, '_destroyed', False):
                                self.editor._destroyed = True
                                old_cw = self.takeCentralWidget()
                                if old_cw is not None and old_cw is not self.editor:
                                    try:
                                        old_cw.deleteLater()
                                    except RuntimeError:
                                        pass
                                self.editor.setParent(None)
                                self.editor.deleteLater()
                                self.editor = None
                        except RuntimeError:
                            pass
                        except Exception:
                            pass
                        # 直接重建分栏布局，并传入要打开的文件（self.editor 已销毁，必须传）
                        self._rebuild_split_layout(current_file=startup_file)
                        # 同步状态
                        self._editor_mode = 'split'
                        if hasattr(self, 'action_split_mode'):
                            self.action_split_mode.setChecked(True)
                        self._sync_mode_combo('split')
                    except Exception:
                        pass
                QTimer.singleShot(800, _enter_split_after_init)
            # 清除保存的临时变量
            self._startup_pending_mode = ""
            self._startup_pending_file = ""
        except Exception:
            pass

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

        # ===== 顶层「模式」菜单（独立顶级菜单，子模式嵌套在编辑下）=====
        # 顶层模式：编辑（含 3 个子模式） vs 分栏编辑（直接切换 = 重载）
        view_menu.addSeparator()

        # 顶级「模式(&M)」菜单：清晰分组主模式 + 子模式
        mode_menu = view_menu.addMenu("模式(&M)")

        # 主模式 1：编辑 → 包含 3 个子模式（写作/源码/预览）
        wysiwyg_menu = mode_menu.addMenu("编辑")
        sub_mode_group = QActionGroup(self)
        sub_mode_group.setExclusive(True)
        sub_mode_items = [
            ("写作", "Ctrl+Alt+1", "wysiwyg_sub"),
            ("源码", "Ctrl+Alt+2", "source_sub"),
            ("预览", "Ctrl+Alt+3", "preview_sub"),
        ]
        self.sub_mode_actions = {}
        for label, shortcut, mode_key in sub_mode_items:
            action = QAction(label, self, checkable=True)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked, m=mode_key: self.set_sub_mode(m))
            sub_mode_group.addAction(action)
            wysiwyg_menu.addAction(action)
            self.sub_mode_actions[mode_key] = action
        self.sub_mode_actions['wysiwyg_sub'].setChecked(True)
        self._actions["所见即所得/写作"] = self.sub_mode_actions['wysiwyg_sub']
        self._actions["所见即所得/源码"] = self.sub_mode_actions['source_sub']
        self._actions["所见即所得/预览"] = self.sub_mode_actions['preview_sub']

        # 主模式 2：分栏编辑（直接切换 = 重载所有 web_view 实例）
        mode_menu.addSeparator()
        self.action_split_mode = QAction("分栏编辑", self, checkable=True)
        self.action_split_mode.setShortcut("Alt+2")
        self.action_split_mode.triggered.connect(lambda: self.switch_to_top_mode("split"))
        mode_menu.addAction(self.action_split_mode)
        self._actions["分栏编辑"] = self.action_split_mode

        # 顶层模式同步（用于 checkbox 状态显示）：所见即所得 = 选中
        self._top_mode_group = QActionGroup(self)
        self._top_mode_group.setExclusive(True)
        self._top_mode_group.addAction(self.sub_mode_actions['wysiwyg_sub'])
        self._top_mode_group.addAction(self.action_split_mode)
        self.action_wysiwyg_mode = self.sub_mode_actions['wysiwyg_sub']  # 别名，保持兼容

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

        snippet_action = QAction("Snippet 管理...", self)
        snippet_action.triggered.connect(self.manage_snippets)
        settings_menu.addAction(snippet_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        shortcuts_action = QAction("快捷键", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)

    def create_toolbar(self):
        """创建工具栏（已彻底移除：专注/打字机/主题按钮移至菜单，工具栏本体也不再创建）。

        避免顶部出现空白 toolbar 区域，专注于显示侧边栏 / 编辑区 / 状态栏。
        按钮事件仍由菜单项 / 快捷键触发，功能不受影响。
        """
        # 保留一个安全引用避免其他代码访问 self.focus_btn 报错
        self.focus_btn = None
        self.typewriter_btn = None

    def update_toolbar_buttons(self):
        """兼容保留：原本更新工具栏按钮状态，现已无按钮，仅作为安全占位。"""
        return

    def create_sidebar(self):
        """创建侧边栏（文件列表 + 大纲 作为 tab 切换，不同时显示）"""
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

        # 【重构】使用 QTabWidget 代替 QSplitter，文件列表/大纲作为 tab 切换。
        # 一次只显示一个，更聚焦；同时节省屏幕空间（侧边栏更窄）。
        self.sidebar_tabs = QTabWidget()
        self.sidebar_tabs.setDocumentMode(True)
        self.sidebar_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.sidebar_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                padding: 6px 18px;
                min-width: 80px;
                font-size: 12px;
                border: 1px solid transparent;
                border-bottom: 2px solid transparent;
                background: transparent;
            }
            QTabBar::tab:selected {
                color: palette(highlighted-text);
                background: palette(highlight);
                border-bottom: 2px solid palette(highlight);
                font-weight: 600;
            }
            QTabBar::tab:!selected:hover {
                background: palette(mid);
            }
        """)

        # === 文件列表面板（当前文件同目录的 .md 文件，扁平列表）===
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

        # 使用 QListWidget 扁平展示当前文件夹下的所有 .md 文件（不再用树形结构）
        self.filelist_widget = QListWidget()
        self.filelist_widget.setStyleSheet("""
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

        # 把两个面板作为 tab 加入 QTabWidget
        self.sidebar_tabs.addTab(self.filelist_panel, "📁 文件")
        self.sidebar_tabs.addTab(self.outline_panel, "📑 大纲")
        # 默认显示文件列表
        self.sidebar_tabs.setCurrentIndex(0)
        # 切换 tab 时记录当前 index
        self.sidebar_tabs.currentChanged.connect(self._on_sidebar_tab_changed)

        layout.addWidget(self.sidebar_tabs)

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

    # 已移除重复的 _active_editor() 和 _iter_editors() 方法
    # 这些方法已在前面实现（行1029-1056）

    def _on_editor_content_changed(self):
        """编辑器内容变化时标记修改状态，并防抖刷新大纲"""
        ed = self._active_editor()
        if ed:
            ed.is_modified = True
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

        # 右侧：主模式 + 子模式级联下拉框 + 字数统计
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # ===== 主模式（单选下拉）：所见即所得 / 分栏 =====
        self.top_mode_combo = QComboBox()
        self.top_mode_combo.setFixedWidth(110)
        self.top_mode_combo.addItems(["编辑", "分栏"])
        self.top_mode_combo.setToolTip("主模式：编辑（可切子模式） vs 分栏（顶层重载）")
        self.top_mode_combo.currentIndexChanged.connect(self._on_top_mode_combo_changed)
        right_layout.addWidget(self.top_mode_combo)

        # ===== 子模式（单选下拉）：编辑 / 源码 / 预览（仅在主模式=编辑时显示）=====
        self.sub_mode_combo = QComboBox()
        self.sub_mode_combo.setFixedWidth(90)
        self.sub_mode_combo.addItems(["编辑", "源码", "预览"])
        self.sub_mode_combo.setToolTip("子模式：编辑下的二级模式（切换仅切 JS，不销毁 widget）")
        self.sub_mode_combo.currentIndexChanged.connect(self._on_sub_mode_combo_changed)
        right_layout.addWidget(self.sub_mode_combo)

        # 字数统计
        self.count_label = QLabel("字数: 0 | 字符: 0")
        right_layout.addWidget(self.count_label)

        self.status_bar.addPermanentWidget(right_widget)

        # 默认：所见即所得 + 编辑
        self.top_mode_combo.setCurrentIndex(0)
        self.sub_mode_combo.setCurrentIndex(0)

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

    def _on_top_mode_combo_changed(self, index):
        """主模式下拉框切换：0=所见即所得 / 1=分栏。"""
        # 0=所见即所得 / 1=分栏
        if index == 1:
            # 分栏：隐藏子模式切换，并触发顶层切换 = 重载
            if hasattr(self, 'sub_mode_combo'):
                self.sub_mode_combo.setVisible(False)
            self.switch_to_top_mode('split')
        else:
            # 所见即所得：显示子模式切换
            if hasattr(self, 'sub_mode_combo'):
                self.sub_mode_combo.setVisible(True)
            # 如果当前在 split 模式，需要切回 wysiwyg
            if getattr(self, '_editor_mode', 'wysiwyg') == 'split':
                self.switch_to_top_mode('wysiwyg')

    def _on_sub_mode_combo_changed(self, index):
        """子模式下拉框切换：0=编辑 / 1=源码 / 2=预览。"""
        # 仅在所见即所得模式下有效
        if getattr(self, '_editor_mode', 'wysiwyg') == 'split':
            return
        sub_map = {0: 'wysiwyg_sub', 1: 'source_sub', 2: 'preview_sub'}
        sub = sub_map.get(index, 'wysiwyg_sub')
        self.set_sub_mode(sub)

    def _sync_statusbar_mode_buttons(self, mode):
        """根据当前模式同步状态栏级联下拉框的选中状态。"""
        if not hasattr(self, 'top_mode_combo'):
            return
        try:
            # 1. 同步主模式下拉框
            if mode == 'split':
                if self.top_mode_combo.currentIndex() != 1:
                    self.top_mode_combo.blockSignals(True)
                    self.top_mode_combo.setCurrentIndex(1)
                    self.top_mode_combo.blockSignals(False)
                # 分栏模式下隐藏子模式
                if hasattr(self, 'sub_mode_combo'):
                    self.sub_mode_combo.setVisible(False)
            else:
                if self.top_mode_combo.currentIndex() != 0:
                    self.top_mode_combo.blockSignals(True)
                    self.top_mode_combo.setCurrentIndex(0)
                    self.top_mode_combo.blockSignals(False)
                # 所见即所得模式下显示子模式
                if hasattr(self, 'sub_mode_combo'):
                    self.sub_mode_combo.setVisible(True)
            # 2. 同步子模式下拉框
            if mode in ('wysiwyg', 'wysiwyg_sub', 'edit'):
                target = 0  # 编辑
            elif mode in ('source', 'source_sub'):
                target = 1  # 源码
            elif mode in ('preview', 'preview_sub'):
                target = 2  # 预览
            else:
                target = None
            if target is not None and hasattr(self, 'sub_mode_combo'):
                if self.sub_mode_combo.currentIndex() != target:
                    self.sub_mode_combo.blockSignals(True)
                    self.sub_mode_combo.setCurrentIndex(target)
                    self.sub_mode_combo.blockSignals(False)
        except RuntimeError:
            pass
        except Exception:
            pass

    def _on_mode_combo_changed(self, index):
        """状态下拉框切换处理：保留兼容（实际已不再使用下拉框）。""" 

    def _on_mode_combo_changed(self, index):
        """状态下拉框切换处理：只用于子模式切换。"""
        if hasattr(self, '_suppress_combo_signal') and self._suppress_combo_signal:
            return
        # 0=写作 / 1=源码 / 2=分栏（顶层重载）/ 3=预览
        # 但用户已要求简化，这里只用于 wysiwyg 内部子模式
        if index == 2:  # 分栏
            self.switch_to_top_mode('split')
            return
        sub_map = {0: 'wysiwyg_sub', 1: 'source_sub', 3: 'preview_sub'}
        sub = sub_map.get(index, 'wysiwyg_sub')
        self.set_sub_mode(sub)

    def _sync_mode_combo(self, mode):
        """同步状态下拉框 / 顶层模式菜单 checkbox / 状态栏按钮。"""
        if hasattr(self, 'mode_combo'):
            try:
                # index: 0=写作 / 1=源码 / 2=分栏 / 3=预览
                mapping = {
                    'wysiwyg': 0, 'edit': 0, 'wysiwyg_sub': 0,
                    'source': 1, 'source_sub': 1,
                    'split': 2,
                    'preview': 3, 'preview_sub': 3,
                }
                target_index = mapping.get(mode, 0)
                if self.mode_combo.currentIndex() != target_index:
                    self._suppress_combo_signal = True
                    self.mode_combo.blockSignals(True)
                    self.mode_combo.setCurrentIndex(target_index)
                    self.mode_combo.blockSignals(False)
                    self._suppress_combo_signal = False
            except Exception:
                self._suppress_combo_signal = False
        # 同步子模式 checkbox
        if hasattr(self, 'sub_mode_actions'):
            target_sub = {'wysiwyg': 'wysiwyg_sub', 'edit': 'wysiwyg_sub',
                          'wysiwyg_sub': 'wysiwyg_sub',
                          'source': 'source_sub', 'source_sub': 'source_sub',
                          'preview': 'preview_sub', 'preview_sub': 'preview_sub'}.get(mode, 'wysiwyg_sub')
            for key, action in self.sub_mode_actions.items():
                action.setChecked(key == target_sub)
        # 同步顶层模式 checkbox
        if hasattr(self, '_top_mode_group') and hasattr(self, 'action_wysiwyg_mode'):
            if mode == 'split':
                self.action_split_mode.setChecked(True)
            else:
                self.action_wysiwyg_mode.setChecked(True)
        # 同步状态栏右下角按钮
        self._sync_statusbar_mode_buttons(mode)

    def _is_editor_valid(self):
        """检查主编辑器（self.editor）是否仍然有效。

        异步回调（如 runJavaScript / QTimer）执行时，窗口可能已关闭、
        C++ 对象已被销毁。访问已删除的 Python 包装对象会抛出
        ``wrapped C/C++ object of type EditorWidget has been deleted`` RuntimeError。
        本方法统一拦截这类问题：先看自身 _destroyed 标记，再看 editor._destroyed，
        最后回退到 sip.isdeleted()。
        """
        # 窗口已关闭：所有后续操作都应跳过
        if getattr(self, '_destroyed', False):
            return False
        ed = getattr(self, 'editor', None)
        if ed is None:
            return False
        # Python 包装对象本身可能已被析构（访问属性会触发 RuntimeError）
        try:
            if getattr(ed, '_destroyed', False):
                return False
        except RuntimeError:
            return False
        # 补充检查：sip.isdeleted() 检测底层 C++ 对象是否已被 delete
        try:
            import sip  # PyQt6 自带的绑定层
            return not sip.isdeleted(ed)
        except Exception:
            return True

    def _current_mode(self):
        """返回当前模式（以 Python 端 _editor_mode 缓存为唯一事实来源）。

        【修复卡顿/异常切换】旧实现在缓存为 wysiwyg 时会用嵌套 QEventLoop
        同步阻塞地向 JS 查询 isPreviewMode()，且没有任何超时：
          - 渲染器繁忙（大文档渲染、高亮）时回调迟迟不返回 → 主线程卡死；
          - 嵌套事件循环期间会继续派发其它事件（重复点击、延迟定时器），
            引发模式切换重入，导致「莫名跳到编辑/预览模式」。
        现在所有模式切换入口（enter_*_mode / set_sub_mode / load_file /
        new_file / exit_split_mode）都负责维护 _editor_mode，
        这里直接返回缓存，不再阻塞主线程。
        """
        return getattr(self, '_editor_mode', 'wysiwyg')


    def new_file(self):
        # 如果在分栏模式下，先退出分栏模式
        if hasattr(self, '_editor_mode') and self._editor_mode == 'split':
            self.exit_split_mode()
        self._ensure_editor()
        ed = self._active_editor()
        if ed:
            ed.new_blank()
            ed.file_path = None
        self.update_title()
        # 【修复模式错乱】同 load_file：setContent 会重置 JS 源码态，缓存需同步
        if getattr(self, '_editor_mode', 'wysiwyg') not in ('preview', 'split'):
            self._editor_mode = 'wysiwyg'
            self._sync_mode_combo('wysiwyg')
        self.status_label.setText("新建文件")
        self.refresh_filelist_for_current_file()

    def open_file(self):
        start_dir = self.default_workdir or ""
        if self.editor and self.editor.file_path:
            start_dir = os.path.dirname(self.editor.file_path)
        path, _ = QFileDialog.getOpenFileName(
            self, "打开 Markdown 文件", start_dir,
            "Markdown 文件 (*.md *.markdown);;所有文件 (*.*)"
        )
        if not path:
            return
        # 严格限制：只接受 .md / .markdown 文件
        if os.path.splitext(path)[1].lower() not in ('.md', '.markdown'):
            QMessageBox.warning(
                self, "仅支持 Markdown 文件",
                f"Writile 只支持打开 .md / .markdown 文件。\n\n文件：{path}"
            )
            return
        self.load_file(path)

    def load_file(self, path):
        try:
            if not os.path.exists(path):
                QMessageBox.warning(self, "提示", f"文件不存在:\n{path}")
                return
            # 限制只加载 Markdown 文件
            if os.path.splitext(path)[1].lower() not in ('.md', '.markdown'):
                QMessageBox.warning(
                    self, "仅支持 Markdown 文件",
                    f"Writile 只支持打开 .md / .markdown 文件。\n\n文件：{path}"
                )
                return
            # 复用单实例编辑器：仅更新内容，不重建 WebEngine（避免闪退）
            self._ensure_editor()
            self.editor.load_file(path)
            self.update_title()

            # 【修复模式错乱】JS 端 setContent 会把 sourceMode 重置为 false、
            # 回到编辑态（预览模式除外）。Python 端缓存必须同步，否则后续
            # 子模式切换会基于过期状态做判断，出现「切源码却跳到编辑模式」。
            if getattr(self, '_editor_mode', 'wysiwyg') not in ('preview', 'split'):
                self._editor_mode = 'wysiwyg'
                self._sync_mode_combo('wysiwyg')

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
        ed = self._active_editor()
        if not ed.file_path:
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
                if ed.save_file(path):
                    # 同步路径回主 editor（退出分栏后仍需记住文件）
                    if hasattr(self, 'editor') and self.editor:
                        self.editor.file_path = ed.file_path
                    self.update_title()
                    self.refresh_filelist_for_current_file()
                    self.status_label.setText("已保存")
        else:
            ed.save_file()
            self.update_title()
            self.refresh_filelist_for_current_file()
            self.status_label.setText("已保存")

    def _get_first_line_as_filename(self):
        """从编辑器内容第一行生成默认文件名"""
        first_line = ""
        ed = self._active_editor()
        if hasattr(ed, 'web_view'):
            from PyQt6.QtCore import QEventLoop, QTimer
            result = [None]
            loop = QEventLoop()
            def on_content(text):
                result[0] = text
                loop.quit()
            # 【修复卡顿】超时兜底，避免页面无响应时嵌套事件循环永久阻塞主线程
            timeout = QTimer()
            timeout.setSingleShot(True)
            timeout.timeout.connect(loop.quit)
            timeout.start(2000)
            ed.web_view.page().runJavaScript(
                "(function(){ var c = window.editorAPI.getContent() || ''; return c.split('\\n')[0] || ''; })()",
                on_content
            )
            loop.exec()
            timeout.stop()
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
        ed = self._active_editor()
        start_dir = self.default_workdir or ""
        if ed and ed.file_path:
            start_dir = os.path.dirname(ed.file_path)
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为", start_dir,
            "Markdown 文件 (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        if path:
            if ed.save_file(path):
                if hasattr(self, 'editor') and self.editor:
                    self.editor.file_path = ed.file_path
                self.update_title()
                self.refresh_filelist_for_current_file()
                self.status_label.setText("已保存")

    def quick_open(self):
        """快速打开 (Ctrl+P) 模糊搜索：只列出 .md / .markdown 文件"""
        files = []
        if self.current_folder and os.path.isdir(self.current_folder):
            for root, dirs, filenames in os.walk(self.current_folder):
                for f in filenames:
                    if f.lower().endswith(('.md', '.markdown')):
                        files.append(os.path.join(root, f))
        # 仅添加扩展名合法的最近文件
        for f in self.recent_files:
            if isinstance(f, str) and f.lower().endswith(('.md', '.markdown')):
                files.append(f)
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
            self.populate_file_list(folder)
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
        """\u5207\u6362\u542f\u52a8\u65f6\u662f\u5426\u6062\u590d\u4e0a\u6b21\u6253\u5f00\u7684\u6587\u4ef6"""
        self.settings.setValue("reopen_last_file", bool(checked))

    def _set_render_delay(self, ms):
        """\u8bbe\u7f6e\u5927\u6587\u6863\u6e32\u67d3\u9632\u6296\u5ef6\u8fdf\uff08100-2000ms\uff09"""
        try:
            ms = max(50, min(2000, int(ms)))
        except Exception:
            return
        self.settings.setValue("render_delay_ms", ms)
        # \u540c\u6b65\u5230\u6240\u6709\u6d3b\u8dc3\u7f16\u8f91\u5668
        for ed in self._iter_editors():
            try:
                if hasattr(ed, 'set_render_delay'):
                    ed.set_render_delay(ms)
            except Exception:
                pass
        self.status_label.setText(f"\u6e32\u67d3\u5ef6\u8fdf\u5df2\u8bbe\u7f6e\u4e3a {ms}ms")

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

    def populate_file_list(self, folder):
        """填充文件列表：扁平展示 folder 下的所有 .md / .markdown 文件。"""
        self._update_folder_label(folder)
        self.filelist_widget.clear()
        if not os.path.isdir(folder):
            return

        current_path = self.editor.file_path if self.editor else None

        # 只收集 markdown 文件，不再扫描子目录，不再包含 .txt / 图片附件
        md_files = []
        try:
            for entry in sorted(os.listdir(folder)):
                full = os.path.join(folder, entry)
                if not os.path.isfile(full):
                    continue
                ext = os.path.splitext(entry)[1].lower()
                if ext in ('.md', '.markdown'):
                    md_files.append(entry)
        except (PermissionError, OSError):
            pass

        for name in md_files:
            full = os.path.join(folder, name)
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, full)
            item.setToolTip(full)
            item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
            if current_path and os.path.normcase(os.path.abspath(full)) == os.path.normcase(os.path.abspath(current_path)):
                # 高亮当前打开的文件
                f = item.font()
                f.setBold(True)
                item.setFont(f)
                item.setForeground(QColor(0, 120, 215))
            self.filelist_widget.addItem(item)

        # 如果什么都没有，给个提示项
        if self.filelist_widget.count() == 0:
            placeholder = QListWidgetItem("（该文件夹下暂无 Markdown 文件）")
            placeholder.setData(Qt.ItemDataRole.UserRole, "__empty__")
            placeholder.setForeground(QColor(128, 128, 128))
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self.filelist_widget.addItem(placeholder)

        self._adjust_sidebar_panels()

    def refresh_filelist_for_current_file(self):
        """根据当前打开的文件，刷新文件列表。

        优先级：
          1. 若已打开文件 -> 显示该文件所在父目录中的 .md 文件列表
          2. 若已打开文件夹 -> 显示该文件夹下的 .md 文件列表
          3. 否则退回到默认工作目录 / 显示提示
        """
        target_folder = ""
        if self.editor and self.editor.file_path:
            target_folder = os.path.dirname(self.editor.file_path) or self.default_workdir
        elif self.current_folder and os.path.isdir(self.current_folder):
            target_folder = self.current_folder
        elif self.default_workdir and os.path.isdir(self.default_workdir):
            target_folder = self.default_workdir

        if target_folder:
            self.populate_file_list(target_folder)
        else:
            self._update_folder_label("")
            self.filelist_widget.clear()
            placeholder = QListWidgetItem("点击此处打开文件夹")
            placeholder.setData(Qt.ItemDataRole.UserRole, "__open_prompt__")
            placeholder.setForeground(QColor(0, 120, 215))
            f = placeholder.font()
            f.setBold(True)
            placeholder.setFont(f)
            self.filelist_widget.addItem(placeholder)
        self._adjust_sidebar_panels()

    def _adjust_sidebar_panels(self):
        """根据内容量调整侧边栏 tab 标题——加上项目数提示。"""
        if not hasattr(self, 'sidebar_tabs'):
            return
        filelist_count = self.filelist_widget.count()
        outline_count = self.outline_widget.count()
        # 文件列表 tab：有项目才显示数字
        if filelist_count > 0:
            self.sidebar_tabs.setTabText(0, f"📁 文件 ({filelist_count})")
        else:
            self.sidebar_tabs.setTabText(0, "📁 文件")
        # 大纲 tab：有项目才显示数字
        if outline_count > 0:
            self.sidebar_tabs.setTabText(1, f"📑 大纲 ({outline_count})")
        else:
            self.sidebar_tabs.setTabText(1, "📑 大纲")

    def _on_sidebar_tab_changed(self, index):
        """侧边栏 tab 切换回调：同步菜单 checkbox。"""
        if not hasattr(self, 'toggle_filelist_action'):
            return
        if index == 0:
            self.toggle_filelist_action.setChecked(True)
        elif index == 1 and hasattr(self, 'toggle_outline_action'):
            self.toggle_outline_action.setChecked(True)

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
        """删除文件列表中的文件（带确认对话框）"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除以下文件吗？\n\n{os.path.basename(path)}\n{path}\n\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(path)
                self.refresh_filelist_for_current_file()
                self.status_label.setText(f"已删除: {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "删除失败", f"无法删除文件:\n{e}")

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
        """插入格式标记（使用活跃编辑器）"""
        ed = self._active_editor()
        if not ed:
            return
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
        ed.run_js(js)

    def insert_heading(self, level):
        """插入标题（使用活跃编辑器）"""
        ed = self._active_editor()
        if not ed:
            return
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
        ed.run_js(js)

    def insert_image(self):
        """插入图片：代理给活跃编辑器（需要弹文件选择框）"""
        ed = self._active_editor()
        if ed and hasattr(ed, "insert_image"):
            ed.insert_image()

    def find_text(self):
        """查找 + 替换（Bug-12 增强）"""
        ed = self._active_editor()
        if ed:
            # 打开增强的查找 + 替换对话框
            self._show_find_dialog(ed)
            return
        # 没有任何编辑器时给出提示
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "查找", "当前没有可用的编辑器。")
        except Exception:
            pass

    def _show_find_dialog(self, editor_widget):
        """打开查找替换对话框（Bug-12 增强版）"""
        # 复用已有对话框（避免重复打开）
        if self._find_dialog is None or not self._find_dialog.isVisible():
            self._find_dialog = FindDialog(editor_widget, self)
        else:
            # 复用现有对话框：切换编辑器
            self._find_dialog.editor = editor_widget
            self._find_dialog.find_input.setFocus()
            self._find_dialog.find_input.selectAll()
            return

        # 定位到主窗口右上角（避免遮挡当前光标所在行）
        try:
            parent_geo = self.geometry()
            dlg_w, dlg_h = 480, 220
            x = parent_geo.x() + parent_geo.width() - dlg_w - 20
            y = parent_geo.y() + 60
            self._find_dialog.move(x, y)
        except Exception:
            pass

        self._find_dialog.show()
        self._find_dialog.raise_()
        self._find_dialog.activateWindow()


    def select_all(self):
        """全选编辑器内容"""
        ed = self._active_editor()
        if ed and hasattr(ed, 'web_view'):
            try:
                ed.web_view.page().triggerAction(QWebEnginePage.WebAction.SelectAll)
            except Exception:
                pass

    def copy_selection(self):
        """复制选中内容"""
        ed = self._active_editor()
        if ed and hasattr(ed, 'web_view'):
            try:
                ed.web_view.page().triggerAction(QWebEnginePage.WebAction.Copy)
            except Exception:
                pass

    def cut_selection(self):
        """剪切选中内容"""
        ed = self._active_editor()
        if ed and hasattr(ed, 'web_view'):
            try:
                ed.web_view.page().triggerAction(QWebEnginePage.WebAction.Cut)
            except Exception:
                pass

    def paste_clipboard(self):
        """粘贴剪贴板内容"""
        ed = self._active_editor()
        if ed and hasattr(ed, 'web_view'):
            try:
                ed.web_view.page().triggerAction(QWebEnginePage.WebAction.Paste)
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

    def _on_sidebar_filelist_toggled(self, visible):
        """显示/隐藏文件列表 tab：同时控制 dock 可见性 + 同步切到该 tab。"""
        if visible:
            # 切到文件列表 tab（index 0）
            if hasattr(self, 'sidebar_tabs'):
                self.sidebar_tabs.setCurrentIndex(0)
            # 至少一个 tab 可见，确保 dock 显示
            self.dock.setVisible(True)
        else:
            # 关闭文件列表：检查大纲 tab 状态
            other_visible = (
                self.toggle_outline_action.isChecked()
                if hasattr(self, 'toggle_outline_action') else False
            )
            if not other_visible:
                self.dock.setVisible(False)
            # 切到大纲 tab（如果大纲可见）
            elif hasattr(self, 'sidebar_tabs'):
                self.sidebar_tabs.setCurrentIndex(1)

    def _on_sidebar_outline_toggled(self, visible):
        """显示/隐藏大纲 tab：同时控制 dock 可见性 + 同步切到该 tab。"""
        if visible:
            if hasattr(self, 'sidebar_tabs'):
                self.sidebar_tabs.setCurrentIndex(1)
            self.dock.setVisible(True)
        else:
            other_visible = (
                self.toggle_filelist_action.isChecked()
                if hasattr(self, 'toggle_filelist_action') else False
            )
            if not other_visible:
                self.dock.setVisible(False)
            elif hasattr(self, 'sidebar_tabs'):
                self.sidebar_tabs.setCurrentIndex(0)

    def toggle_filelist(self):
        """切换文件列表面板（tab 形式）"""
        self._on_sidebar_filelist_toggled(self.toggle_filelist_action.isChecked())

    def toggle_outline(self):
        """切换大纲面板（tab 形式）"""
        self._on_sidebar_outline_toggled(self.toggle_outline_action.isChecked())

    def toggle_focus_mode(self):
        self.focus_mode = not self.focus_mode
        self.focus_action.setChecked(self.focus_mode)
        # 同时同步到分栏下的所有面板
        for ed in self._iter_editors():
            try:
                ed.set_focus_mode(self.focus_mode)
            except Exception:
                pass

    def toggle_typewriter_mode(self):
        self.typewriter_mode = not self.typewriter_mode
        self.typewriter_action.setChecked(self.typewriter_mode)
        # 同时同步到分栏下的所有面板
        for ed in self._iter_editors():
            try:
                ed.set_typewriter_mode(self.typewriter_mode)
            except Exception:
                pass



    def _restore_main_editor(self):
        """保证主编辑器 self.editor 在中央区域且可见。

        背景：重复进出分栏 / 切换模式多次后，self.editor 可能仍为非可见状态
        或未重新占据中央布局，导致中央文本框"消失"。这里统一重新设置为中央 widget，
        作为所有非分栏模式的最后一个保险。

        关键：必须在主线程事件循环中处理 layout，否则 setCentralWidget 不会立即生效。
        这里使用 QTimer.singleShot(0) 把恢复操作推迟到下一个事件循环迭代，
        保证 setCentralWidget 真正生效、centralWidget() 拿到的是主编辑器。
        """
        if getattr(self, '_destroyed', False):
            return
        ed = getattr(self, 'editor', None)
        if not ed or getattr(ed, '_destroyed', False):
            return
        try:
            # 脱离可能的多余父对象，避免被 split / dock 抢占布局
            try:
                ed.setParent(self)
            except RuntimeError:
                return
            ed.setVisible(True)
            # 如果当前中央 widget 不是主编辑器，重新设回去
            if self.centralWidget() is not ed:
                self.setCentralWidget(ed)
            # 立即 + 延迟 双保险：Qt 布局必须等事件循环才会生效
            ed.show()
            ed.raise_()
            self.centralWidget().updateGeometry()
            ed.updateGeometry()
            self.updateGeometry()
            # 延迟 0ms 在事件循环末尾再强制一次，确保多次切换后不会留下 0×0 中央 widget
            QTimer.singleShot(0, self._finalize_main_editor_visibility)
        except RuntimeError:
            pass
        except Exception:
            pass

    def _finalize_main_editor_visibility(self):
        """延迟到下一个事件循环：用 takeCentralWidget + setCentralWidget 强制恢复。

        关键修复（模式切换多次后主体内容框消失）：
          在快速重复切换模式下，Qt 的 setCentralWidget 在某些情况下会保留
          旧的中央 widget 引用而不真正替换。这里先显式 takeCentralWidget 释放旧
          widget 引用，再 setCentralWidget 强制替换，最大限度保证中央区域
          显示的是 self.editor 而非旧的 split_splitter 等。
        """
        if getattr(self, '_destroyed', False):
            return
        ed = getattr(self, 'editor', None)
        if not ed or getattr(ed, '_destroyed', False):
            return
        try:
            # 仅在主编辑器未挂载在中央时才强制 take+set，避免不必要的销毁
            if self.centralWidget() is not ed:
                old = self.takeCentralWidget()
                if old is not None and old is not ed:
                    # 旧 widget（split_splitter 等）不立即销毁，
                    # 仅从 QMainWindow 解除父子关系，由 Qt 自行 deleteLater
                    try:
                        old.setParent(None)
                    except RuntimeError:
                        pass
                self.setCentralWidget(ed)
            ed.setVisible(True)
            ed.show()
            ed.raise_()
            self.centralWidget().updateGeometry()
            ed.updateGeometry()
            self.updateGeometry()
        except RuntimeError:
            pass
        except Exception:
            pass

    def switch_to_top_mode(self, top_mode):
        """切换顶层模式：编辑 ↔ 分栏编辑。

        顶层模式之间切换 = 直接重启整个程序进程（彻底避免 GPU 共享上下文冲突、
        widget 树状态错乱、模式间状态泄漏等所有问题）。
        启动时读取 self.settings 中的 'startup_top_mode' 来决定使用哪种模式。
        """
        if getattr(self, '_destroyed', False):
            return
        current = self._current_mode()
        # 判断是否需要切换（在同一模式内就不重启）
        if top_mode == 'wysiwyg' and current in ('wysiwyg', 'source', 'preview'):
            return
        if top_mode == 'split' and current == 'split':
            return

        # 保存当前打开的文件路径 + 要切换的目标模式
        current_file = None
        for attr in ('editor', 'source_editor', 'preview_view'):
            ed_obj = getattr(self, attr, None)
            if ed_obj and getattr(ed_obj, 'file_path', None):
                current_file = ed_obj.file_path
                break

        # 把要切换的目标模式保存到 settings，让重启后的程序读取
        try:
            self.settings.setValue('startup_top_mode', top_mode)
            if current_file:
                self.settings.setValue('startup_open_file', current_file)
        except Exception:
            pass
        self.settings.sync()  # 立即写入磁盘

        # 直接重启整个程序进程
        self._restart_application()

    def _restart_application(self):
        """完全重启 Writile 程序进程以切换大模式。

        关键：使用 subprocess.Popen() 启动新进程 + os._exit() 终止当前进程。
        不要使用 os.execv()，因为它在 Windows 上会立即替换进程，导致 Qt 状态泄漏、
        启动后立刻闪退。subprocess + os._exit 是更稳健的方案。
        """
        import sys
        import os as _os
        import subprocess
        try:
            # 保存当前 QSettings 中的状态
            if hasattr(self, 'settings'):
                try:
                    self.settings.sync()
                except Exception:
                    pass

            # 启动新进程的命令
            python = _os.path.abspath(sys.executable)
            script = _os.path.abspath(sys.argv[0]) if sys.argv else python
            args = [python, script] + sys.argv[1:]

            # 使用 Popen 启动新进程
            # CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS 让新进程独立运行
            creationflags = 0
            if sys.platform == 'win32':
                # Windows: 0x00000008 = DETACHED_PROCESS, 0x00000200 = CREATE_NEW_PROCESS_GROUP
                creationflags = 0x00000008 | 0x00000200
            try:
                subprocess.Popen(
                    args,
                    creationflags=creationflags,
                    close_fds=True,
                )
            except Exception as e:
                print(f"Popen 启动失败: {e}")
                # 退化为 execv
                _os.execv(python, args)

            # 关闭当前 Qt 应用
            try:
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
                if app is not None:
                    app.quit()
                    app.processEvents()
            except Exception:
                pass

            # 终止当前进程（0 表示正常退出）
            _os._exit(0)
        except Exception as e:
            print(f"重启失败: {e}")
            import _os
            _os._exit(0)

    def _rebuild_wysiwyg_layout(self):
        """重建所见即所得模式：创建新的主编辑器并设为中心 widget。"""
        from editor_common import EditorWidget
        ed = EditorWidget(default_workdir=self.default_workdir)
        ed.set_dark_mode(self.dark_mode)
        ed.set_focus_mode(self.focus_mode)
        ed.set_typewriter_mode(self.typewriter_mode)
        try:
            ed._bridge.contentChanged.connect(self._on_editor_content_changed)
        except Exception:
            pass
        self.editor = ed
        self.setCentralWidget(ed)
        # 触发补全数据推送
        try:
            QTimer.singleShot(500, self._push_completion_data)
        except Exception:
            pass

    def _rebuild_split_layout(self, current_file=None):
        """重建分栏模式：创建新的 source_editor + preview_view，并使用 polling 等待页面就绪。

        current_file: 可选参数。启动时 self.editor 不存在，需要从 _startup_pending_file
        传入。默认从 self.editor / self.source_editor 自动取。
        """
        from editor_common import EditorWidget
        from PyQt6.QtWidgets import QSplitter
        from PyQt6.QtCore import Qt
        # 先取当前中央 widget 引用（如果存在），避免被自动 deleteLater
        try:
            old_cw = self.takeCentralWidget()
            if old_cw is not None:
                try:
                    old_cw.setParent(None)
                except RuntimeError:
                    pass
                try:
                    old_cw.deleteLater()
                except RuntimeError:
                    pass
        except Exception:
            pass

        self.split_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.split_splitter.setChildrenCollapsible(False)
        self.split_splitter.setHandleWidth(4)

        # 创建 source_editor
        self.source_editor = EditorWidget(
            default_workdir=self.default_workdir,
            scroll_sync_callback=self._on_split_scroll_sync,
        )
        self.source_editor.set_dark_mode(self.dark_mode)
        self.source_editor.set_focus_mode(self.focus_mode)
        self.source_editor.set_typewriter_mode(self.typewriter_mode)
        try:
            self.source_editor._bridge.contentChanged.connect(self._on_split_source_changed)
        except Exception:
            pass
        self.split_splitter.addWidget(self.source_editor)

        # 创建 preview_view
        self.preview_view = EditorWidget(
            default_workdir=self.default_workdir,
            scroll_sync_callback=self._on_split_scroll_sync,
        )
        self.preview_view.set_dark_mode(self.dark_mode)
        self.preview_view.set_focus_mode(self.focus_mode)
        self.preview_view.set_typewriter_mode(self.typewriter_mode)
        self.split_splitter.addWidget(self.preview_view)

        self.split_splitter.setStretchFactor(0, 1)
        self.split_splitter.setStretchFactor(1, 1)
        self.split_splitter.setSizes([10**6, 10**6])
        self.split_container = self.split_splitter

        # 关键：setCentralWidget 后立即强制 show，避免 splitter 不显示
        self.setCentralWidget(self.split_splitter)
        self.split_splitter.show()
        self.source_editor.show()
        self.preview_view.show()
        # 强制布局重算
        self.split_splitter.updateGeometry()
        self.split_splitter.repaint()
        self.updateGeometry()

        # 内容同步 timer
        self.split_sync_timer = QTimer(self)
        self.split_sync_timer.setSingleShot(True)
        self.split_sync_timer.setInterval(300)
        self.split_sync_timer.timeout.connect(self._sync_split_content)
        self._setup_split_scroll_sync()

        # 设置左右内容：优先用参数 current_file，否则自动从 web_view 中取
        if current_file is None:
            for attr in ('editor', 'source_editor'):
                ed = getattr(self, attr, None)
                if ed and getattr(ed, 'file_path', None):
                    current_file = ed.file_path
                    break
        content = ''
        if current_file and os.path.exists(current_file):
            try:
                with open(current_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                pass
            try:
                self.source_editor.file_path = current_file
                self.preview_view.file_path = current_file
            except Exception:
                pass

        self._split_initial_content = content

        # 使用 polling 等待 web_view 页面真正就绪后再设置内容与模式
        self._wait_split_editors_ready(content)

    def _wait_split_editors_ready(self, content):
        """轮询等待 source_editor / preview_view 的 web_view 页面真正可交互。

        修复"切到分栏就不显示"bug：
          创建新 QWebEngineView 后，页面 HTML/JS 需要时间加载。
          如果直接 _apply_content + run_js，页面可能还没就绪导致 JS 调用失败、内容显示空白。
          这里用 JS 探测 (window.editorAPI) 来判断页面是否就绪，最多等待 5 秒。
        """
        if not (hasattr(self, 'source_editor') and self.source_editor and
                hasattr(self, 'preview_view') and self.preview_view):
            return
        # 安全保护：窗口已销毁
        if getattr(self, '_destroyed', False):
            return

        state = {'attempts': 0, 'src_ready': False, 'prev_ready': False}

        def _probe_src(ready):
            try:
                state['src_ready'] = bool(ready)
            except Exception:
                pass
            _try_finish()

        def _probe_prev(ready):
            try:
                state['prev_ready'] = bool(ready)
            except Exception:
                pass
            _try_finish()

        def _try_finish():
            pass  # 主循环兜底将在下一次轮询中执行

        def _do_init():
            src = getattr(self, 'source_editor', None)
            prv = getattr(self, 'preview_view', None)
            if not src or not prv:
                return
            if getattr(src, '_destroyed', False) or getattr(prv, '_destroyed', False):
                return
            try:
                # 关键：先设置内容，等内容渲染完成（200ms）后再切换模式
                # 否则 setContent 内部会重置 sourceMode = false，toggleSourceMode 失效
                src._apply_content(content)
                prv._apply_content(content)
                def _apply_modes():
                    if getattr(self, '_destroyed', False):
                        return
                    # 【修复】已退出分栏模式则不再对编辑器发模式指令
                    if getattr(self, '_editor_mode', None) != 'split':
                        return
                    try:
                        # 2) 进入源码模式（左）和只读预览模式（右）
                        # 用幂等 setSourceMode(true)，避免 toggle 在已处于源码态时反向退出
                        if not getattr(src, '_destroyed', False):
                            src.run_js("window.editorAPI.setSourceMode(true);")
                        if not getattr(prv, '_destroyed', False):
                            prv.run_js("window.editorAPI.enterPreviewMode();")
                    except RuntimeError:
                        pass
                    except Exception:
                        pass
                # 延迟 250ms 让 setContent 的 renderMarkdown 完成
                QTimer.singleShot(250, _apply_modes)
                # 再次重试（防 setContent 异步覆盖）
                def _retry():
                    if getattr(self, '_destroyed', False):
                        return
                    if getattr(self, '_editor_mode', None) != 'split':
                        return
                    try:
                        if not getattr(src, '_destroyed', False):
                            # 重新 setContent（确保是源码）+ 幂等进入源码模式
                            src._apply_content(content)
                            src.run_js("window.editorAPI.setSourceMode(true);")
                        if not getattr(prv, '_destroyed', False):
                            prv._apply_content(content)
                            prv.run_js("window.editorAPI.enterPreviewMode();")
                    except RuntimeError:
                        pass
                    except Exception:
                        pass
                QTimer.singleShot(600, _retry)
                # 1.5 秒后最终保险
                def _final():
                    if getattr(self, '_destroyed', False):
                        return
                    if getattr(self, '_editor_mode', None) != 'split':
                        return
                    try:
                        # 【修复】旧代码这里盲调 toggleSourceMode()：若左栏已在源码态，
                        # 会被反向切回编辑态（进入分栏 1.5 秒后左栏突然变成渲染视图）。
                        if not getattr(src, '_destroyed', False):
                            src.run_js("window.editorAPI.setSourceMode(true);")
                        if not getattr(prv, '_destroyed', False):
                            prv.run_js("window.editorAPI.enterPreviewMode();")
                    except RuntimeError:
                        pass
                    except Exception:
                        pass
                QTimer.singleShot(1500, _final)
            except RuntimeError:
                pass
            except Exception:
                pass

        def _check():
            # 编辑器已被销毁：停止轮询
            if (getattr(self, '_destroyed', False) or
                    not hasattr(self, 'source_editor') or not self.source_editor or
                    not hasattr(self, 'preview_view') or not self.preview_view):
                return
            if (getattr(self.source_editor, '_destroyed', False) or
                    getattr(self.preview_view, '_destroyed', False)):
                return
            state['attempts'] += 1
            try:
                if not state['src_ready']:
                    self.source_editor.web_view.page().runJavaScript(
                        "!!(window.editorAPI && window.editorAPI.setContent)",
                        _probe_src
                    )
            except RuntimeError:
                pass
            except Exception:
                pass
            try:
                if not state['prev_ready']:
                    self.preview_view.web_view.page().runJavaScript(
                        "!!(window.editorAPI && window.editorAPI.setContent)",
                        _probe_prev
                    )
            except RuntimeError:
                pass
            except Exception:
                pass
            # 两个都就绪 或 超时
            if (state['src_ready'] and state['prev_ready']) or state['attempts'] >= 50:
                _do_init()
                return
            QTimer.singleShot(100, _check)

        # 启动轮询
        QTimer.singleShot(50, _check)

    def set_sub_mode(self, sub):
        """切换编辑内的子模式：写作 / 源码 / 预览（只切 JS，不销毁 widget）。"""
        if getattr(self, '_destroyed', False):
            return
        if getattr(self, '_editor_mode', 'wysiwyg') == 'split':
            # 分栏模式下不允许切子模式（应切回所见即所得）
            return
        if not self._is_editor_valid():
            return
        try:
            # sub 形如 wysiwyg_sub / source_sub / preview_sub
            # 直接调用对应的 enter_*_mode 方法，只切换 JS 模式
            if sub == 'wysiwyg_sub':
                self.enter_wysiwyg_mode()
            elif sub == 'source_sub':
                self.enter_source_mode()
            elif sub == 'preview_sub':
                self.enter_preview_mode()
            # 确保主编辑器仍可见
            self._restore_main_editor()
            # 同步下拉框显示
            self._sync_mode_combo(sub)
        except RuntimeError:
            pass
        except Exception:
            pass

    def set_editor_mode(self, mode):
        """兼容旧调用：在 wysiwyg 内部切换 JS 模式（不销毁 widget）。""" 
        # 窗口已关闭或编辑器已销毁 → 直接跳过，避免延迟回调触发
        # "wrapped C/C++ object of type EditorWidget has been deleted" 错误。
        if not self._is_editor_valid():
            return

        current = self._current_mode()
        if current == mode:
            return  # 已在目标模式

        def do_switch(state_data):
            # 异步回调（runJavaScript / QTimer）在执行时窗口可能已被关闭。
            # 再次检查有效性，避免访问已销毁的 C++ 对象。
            if not self._is_editor_valid():
                return
            try:
                self._last_mode_state = state_data
                # 退出当前模式
                if current == 'split':
                    try:
                        self.exit_split_mode()
                    except RuntimeError:
                        return
                elif current == 'preview':
                    try:
                        if getattr(self, 'editor', None):
                            self.editor.run_js("window.editorAPI.enterEditMode();")
                    except RuntimeError:
                        return

                # 进入目标模式
                if mode == 'wysiwyg':
                    self.enter_wysiwyg_mode()
                elif mode == 'source':
                    self.enter_source_mode()
                elif mode == 'split':
                    self.enter_split_mode()
                elif mode == 'preview':
                    self.enter_preview_mode()

                # 修复：多次切换模式后主体文本框消失的 bug。
                # 非 split 模式都要强制把主编辑器设回中央并可见。
                # 使用两层延迟保险：立即一次 + 事件循环末尾再一次。
                if mode != 'split':
                    self._restore_main_editor()
                    QTimer.singleShot(0, self._finalize_main_editor_visibility)

                # 恢复状态（延迟执行，等待模式切换完成）
                if state_data and mode != 'split':
                    QTimer.singleShot(200, lambda: self._restore_mode_state(state_data))
            except RuntimeError:
                # wrapped C/C++ object ... has been deleted：静默忽略
                pass
            except Exception as e:
                print(f"set_editor_mode error: {e}")

        # 异步获取状态后执行切换
        def on_state(s):
            do_switch(s)

        try:
            ed = self._active_editor()
            if ed and not getattr(ed, '_destroyed', False) and hasattr(ed, 'web_view'):
                ed.web_view.page().runJavaScript(
                    "(function(){ return window.editorAPI.getEditorState(); })()",
                    on_state
                )
            else:
                do_switch(None)
        except RuntimeError:
            pass
        except Exception:
            do_switch(None)

    def _restore_mode_state(self, state=None):
        """恢复编辑器状态（光标/滚动/选区）。QTimer 回调、窗口可能已关闭。"""
        if getattr(self, '_destroyed', False):
            return
        if state is None:
            state = getattr(self, '_last_mode_state', None)
        if not state:
            return
        try:
            ed = self._active_editor()
            if not ed or not hasattr(ed, 'web_view'):
                return
            ed.web_view.page().runJavaScript(
                "window.editorAPI.setEditorState(" + json.dumps(state) + ")"
            )
        except RuntimeError:
            pass
        except Exception:
            pass

    def toggle_source_mode(self):
        """切换源码模式（菜单/快捷键兼容入口）。

        方向由 Python 端模式缓存决定，底层走幂等的 setSourceMode：
          - 缓存为 source → 回到写作模式
          - 其他（写作/预览）→ 进入源码模式
        这样即使 JS 端状态短暂不同步，结果也确定，不会出现
        「切源码却跳回编辑/预览」的异常。
        """
        if getattr(self, '_editor_mode', 'wysiwyg') == 'split':
            return
        if getattr(self, '_editor_mode', 'wysiwyg') == 'source':
            self.set_sub_mode('wysiwyg_sub')
        else:
            self.set_sub_mode('source_sub')

    def toggle_preview_mode(self):
        """切换预览模式（菜单/快捷键兼容入口）。

        旧实现只发 JS 不更新 _editor_mode / 下拉框，会造成缓存与实际状态脱节。
        统一走 enter_preview_mode，保证模式缓存、菜单勾选、状态栏同步。
        """
        self.enter_preview_mode()

    def _show_split_mode(self):
        """显示分栏模式（兼容旧调用）"""
        self.enter_split_mode()

    def _exit_split_mode(self):
        """退出分栏模式（兼容旧调用）"""
        self.exit_split_mode()



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
        # 同步编辑器主题色（分栏模式下同步到两个面板）
        self.apply_editor_theme(theme)
        # 更新菜单选中状态
        for k, action in self.theme_actions.items():
            action.setChecked(k == key)

    def apply_editor_theme(self, theme):
        """将主题色注入编辑器 (WebEngine)，同时应用到分栏模式下的所有面板"""
        colors = theme.get("colors", {})
        is_dark = str(theme.get("is_dark", False)).lower()
        props_js = "; ".join(f"root.style.setProperty('--{k}', '{v}')" for k, v in colors.items())
        js = f"""
        var root = document.documentElement;
        var editor = document.getElementById('editor');
        if (root) {{
            {props_js};
            if ({is_dark}) {{
                root.classList.add('dark');
            }} else {{
                root.classList.remove('dark');
            }}
        }}
        """
        # 同时推送到所有活跃的编辑器面板（分栏时为 2 个）
        for ed in self._iter_editors():
            try:
                ed.set_dark_mode(bool(theme.get("is_dark", False)))
                ed.page.runJavaScript(js)
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
    # 工具方法
    # ============================================================

    def _active_editor(self):
        """获取当前活跃的编辑器实例

        在分栏模式下返回 source_editor（用户真正编辑的地方）
        否则返回主编辑器 self.editor。
        如果窗口已关闭或该编辑器 C++ 对象已销毁，返回 None。
        """
        if hasattr(self, '_editor_mode') and self._editor_mode == 'split':
            # 分栏模式：返回源码编辑器（用户实际编辑的地方）
            if hasattr(self, 'source_editor') and self.source_editor:
                try:
                    if not getattr(self.source_editor, '_destroyed', False):
                        return self.source_editor
                except RuntimeError:
                    pass
                return None
        ed = self.editor if hasattr(self, 'editor') else None
        if ed is None:
            return None
        # 检查 C++ 对象是否已被销毁
        try:
            if getattr(ed, '_destroyed', False):
                return None
            return ed
        except RuntimeError:
            return None

    def _iter_editors(self):
        """迭代所有编辑器实例（用于同步操作）"""
        if hasattr(self, '_editor_mode') and self._editor_mode == 'split':
            if hasattr(self, 'source_editor') and self.source_editor:
                yield self.source_editor
            if hasattr(self, 'preview_view') and self.preview_view:
                yield self.preview_view
        elif hasattr(self, 'editor') and self.editor:
            yield self.editor

    # ============================================================
    # 大纲
    # ============================================================

    def update_outline_async(self):
        """异步更新大纲（使用当前活跃编辑器，分栏时为源码面板））"""
        def handle(content):
            # 异步回调：窗口可能已关闭
            if getattr(self, '_destroyed', False):
                return
            try:
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
            except RuntimeError:
                pass
            except Exception:
                pass

        ed = self._active_editor()
        if ed:
            try:
                ed.get_content(handle)
            except RuntimeError:
                pass
            except Exception:
                pass

    def outline_clicked(self, item):
        """点击大纲项，滚动到对应位置（使用活跃编辑器）"""
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
        ed = self._active_editor()
        if ed:
            ed.run_js(js)

    # ============================================================
    # 工具方法
    # ============================================================

    def update_title(self):
        ed = self._active_editor()
        if ed and ed.file_path:
            title = os.path.basename(ed.file_path)
        else:
            title = "未命名.md"
        # 显示修改标记
        if ed and hasattr(ed, 'is_modified') and ed.is_modified:
            title = "● " + title
        self.setWindowTitle(f"{title} - Writile")

    def update_word_count(self):
        """更新字数统计（使用活跃编辑器）"""
        def handle(stats):
            # 异步回调：窗口可能已关闭
            if getattr(self, '_destroyed', False):
                return
            try:
                self.count_label.setText(
                    f"字数: {stats['chinese'] + stats['english']} | "
                    f"字符: {stats['chars']} | 行: {stats['lines']}"
                )
            except RuntimeError:
                pass
            except Exception:
                pass
        ed = self._active_editor()
        if ed and hasattr(ed, 'get_word_count_async'):
            try:
                ed.get_word_count_async(handle)
            except RuntimeError:
                pass
            except Exception:
                pass

    def _path_key(self, p):
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

        # 【修复闪退问题】不要自动恢复非 wysiwyg 模式。
        # 原代码在启动后 300ms 调度 set_editor_mode(saved_mode)，
        # 如果上次关闭时是 split/source/preview，会调用：
        #   - enter_split_mode：把主编辑器 setVisible(False)，创建新 WebEngine。
        #     主编辑器中刚加载的文件内容（on_load_finished 之后才设置）
        #     还没被用户看到就被隐藏了，而且新创建的 split WebEngine 需要
        #     重新加载 HTML、JS、apply content，整个过渡期用户看到的是空窗口。
        #   - enter_source_mode / enter_preview_mode：调 toggle JS，
        #     而状态保存依赖于 toggle反转，不一定与上次状态一致。
        # 修复后仅记住上次模式，强制回到 wysiwyg，避免冷启动时主编辑器隐藏/内容丢失。
        saved_mode = self.settings.value("editor_mode", "wysiwyg", type=str) or "wysiwyg"
        # 不自动调用 set_editor_mode，只记录到 self._saved_mode 供其它逻辑使用
        self._saved_mode = saved_mode

    def closeEvent(self, event):
        # 标记窗口已开始销毁：所有后续异步回调（runJavaScript / QTimer / 延迟回调）
        # 应立即跳过，避免访问已销毁的 EditorWidget C++ 对象触发
        # "wrapped C/C++ object of type EditorWidget has been deleted" RuntimeError。
        # 该标志必须设置在 event.accept() 之前——一旦接受关闭，Qt 会立即销毁子 widget。
        self._destroyed = True
        try:
            self.settings.setValue("dark_mode", self.dark_mode)
            self.settings.setValue("focus_mode", self.focus_mode)
            self.settings.setValue("typewriter_mode", self.typewriter_mode)
            self.settings.setValue("current_theme", self.current_theme)
            # 保存分栏模式状态
            if hasattr(self, '_editor_mode'):
                self.settings.setValue("editor_mode", self._editor_mode)
        except Exception:
            pass
        event.accept()

    # ============================================================
    # Snippet 管理 + 补全数据
    # ============================================================

    def _get_snippets_path(self):
        """获取 snippets.json 路径（用户配置目录）"""
        config_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppConfigLocation)
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'snippets.json')

    def _load_user_snippets(self):
        """加载用户自定义 snippets"""
        path = self._get_snippets_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            except Exception:
                pass
        return []

    def _push_completion_data(self):
        """推送补全数据到 JS 端"""
        if not hasattr(self, 'editor') or self.editor is None:
            return
        try:
            # 最近链接
            links = []
            for f in (self.recent_files or []):
                name = os.path.basename(f)
                links.append({
                    'label': name, 'desc': f,
                    'value': f'[{name}]({f})', 'icon': '\U0001f4c4'
                })
            # 用户 snippets
            snippets = self._load_user_snippets()
            data = {
                'recentLinks': links,
                'userSnippets': snippets,
            }
            data_json = json.dumps(data, ensure_ascii=False)
            self.editor.run_js(
                f"if (window.editorAPI) window.editorAPI.setCompletionData({data_json});")
            # 项目文件列表
            self._scan_project_files()
        except Exception as e:
            print(f"_push_completion_data error: {e}")

    def _scan_project_files(self):
        """扫描当前文件夹的图片/文件列表（依赖 self.editor，需提前检查有效性）"""
        if not self._is_editor_valid():
            return
        folder = getattr(self, 'current_folder', '') or self.default_workdir
        if not folder or not os.path.isdir(folder):
            return
        try:
            images = []
            files = []
            img_ext = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp'}
            for f in os.listdir(folder):
                fp = os.path.join(folder, f)
                if os.path.isfile(fp):
                    _, ext = os.path.splitext(f)
                    if ext.lower() in img_ext:
                        images.append({
                            'label': f, 'desc': '\u56fe\u7247',
                            'value': f, 'icon': '\U0001f5bc'
                        })
                    files.append({
                        'label': f, 'desc': '\u6587\u4ef6',
                        'value': f, 'icon': '\U0001f4c4'
                    })
            self.editor.run_js(
                f"window._projectImages = {json.dumps(images, ensure_ascii=False)};")
            self.editor.run_js(
                f"window._fileList = {json.dumps(files, ensure_ascii=False)};")
        except RuntimeError:
            pass
        except Exception:
            pass

    def manage_snippets(self):
        """打开 Snippet 管理（用系统默认编辑器打开 snippets.json）"""
        path = self._get_snippets_path()
        # 若文件不存在，先创建默认模板
        if not os.path.exists(path):
            template = [
                {"prefix": "mytemplate", "desc": "\u81ea\u5b9a\u4e49\u6a21\u677f",
                 "body": "\u8fd9\u91cc\u662f\u6a21\u677f\u5185\u5bb9"}
            ]
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)
            except Exception as e:
                QMessageBox.warning(self, "\u9519\u8bef", f"\u65e0\u6cd5\u521b\u5efa snippets.json: {e}")
                return
        # 用系统默认编辑器打开
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(path)))
        QMessageBox.information(
            self, "Snippet \u7ba1\u7406",
            f"\u5df2\u6253\u5f00 snippets.json\n\n"
            f"\u6587\u4ef6\u4f4d\u7f6e: {path}\n\n"
            f"\u683c\u5f0f\u8bf4\u660e:\n"
            f'  prefix: \u89e6\u53d1\u8bcd\n'
            f'  desc: \u63cf\u8ff0\n'
            f'  body: \u5c55\u5f00\u5185\u5bb9\n\n'
            f"\u4fdd\u5b58\u540e\u91cd\u542f\u5e94\u7528\u3002"
        )

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
            "<p>Alt+1/2/3/4: 模式切换 | Ctrl+\\: 侧边栏 | Ctrl+Q: 退出</p>"
            "<p>Ctrl+Space: 补全菜单 | Ctrl+Enter: 展开 Snippet</p>"
            "<p>视图菜单可单独切换文件列表/大纲</p>"
            "<hr>"
            "<p><b>编辑模式切换:</b></p>"
            "<p>Alt+1: 写作 | Alt+2: 源码 | Alt+3: 分栏 | Alt+4: 预览</p>"
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
            "  Alt+1         写作模式\n"
            "  Alt+2         源码模式\n"
            "  Alt+3         分栏模式\n"
            "  Alt+4         预览模式\n"
            "  Ctrl+\\\\       切换侧边栏（文件列表+大纲）\n"
            "  视图菜单     单独切换文件列表/大纲\n\n"
            "自动补全:\n"
            "  Ctrl+Space    手动触发补全菜单\n"
            "  Ctrl+Enter    展开 Snippet\n"
            "  ↑/↓          导航补全列表\n"
            "  Enter         确认补全\n"
            "  Esc           关闭补全菜单\n"
        )
        QMessageBox.information(self, "快捷键", shortcuts)



# ============================================================
# 入口
# ============================================================


def main():
    # Chromium 标志已在模块导入前由 _configure_webengine_env() 设置。
    # 这里绝不能再覆盖成 --single-process + --disable-software-rasterizer，
    # 否则 Windows 上既没有硬件 GL 也没有软件回退，启动即闪退。
    _configure_webengine_env()
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)

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

    # 主窗口创建失败时（极少发生，如 WebEngine 初始化异常）退化为简易文本编辑器。
    try:
        window = MainWindow(initial_file=initial_file)
    except Exception as exc:
        from PyQt6.QtWidgets import QPlainTextEdit
        fallback = QPlainTextEdit()
        if initial_file and os.path.exists(initial_file):
            try:
                with open(initial_file, "r", encoding="utf-8") as handle:
                    fallback.setPlainText(handle.read())
            except Exception:
                pass
        fallback.setWindowTitle("Writile (简易模式)")
        fallback.resize(900, 600)
        fallback.show()
        print(f"[Writile] 主窗口初始化失败：{exc}", file=sys.stderr)
        return app.exec()

    window.show()

    try:
        return app.exec()
    except Exception as exc:
        print(f"[Writile] 主事件循环异常退出：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    main()
