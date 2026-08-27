# -*- coding: utf-8 -*-
"""
源码模式（Source Mode - 全局 Markdown 源码编辑）
"""


class SourceModeMixin:
    """源码模式 Mixin：全局 Markdown 源码编辑

    依赖 MainWindow 属性：editor
    """

    def enter_source_mode(self):
        """进入源码模式：全局 Markdown 源码编辑"""
        # 如果当前在分栏模式，先退出（捕获 RuntimeError 防止反复进入时 C++ 对象失效）
        if hasattr(self, 'split_container') and self.split_container:
            try:
                self.exit_split_mode()
            except RuntimeError:
                return

        # 确保编辑器存在
        if not hasattr(self, 'editor') or self.editor is None:
            return

        try:
            # 【修复】用幂等的 setSourceMode(True)，而不是 toggleSourceMode。
            # toggle 依赖 JS 端 sourceMode 的当前值：一旦 JS 状态与 Python 缓存不同步
            # （例如打开文件时 setContent 已把 sourceMode 重置为 false），toggle 会
            # 反向翻转，导致「切源码模式却跳回编辑模式」。
            self.editor.set_source_mode(True)
        except RuntimeError:
            return
        except Exception:
            pass

        # 关键修复：切回非分栏模式后，确保主编辑器仍在中央区域可见
        try:
            self._restore_main_editor()
        except Exception:
            pass

        self._sync_mode_combo('source')
        self._editor_mode = 'source'
