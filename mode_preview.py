# -*- coding: utf-8 -*-
"""
预览模式（Preview Mode - 只读阅读）
"""


class PreviewModeMixin:
    """预览模式 Mixin：纯阅读，只读，渲染 Markdown

    依赖 MainWindow 属性：editor, preview_action
    """

    def enter_preview_mode(self):
        """进入预览模式：只读阅读"""
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
            self.editor.run_js("window.editorAPI.enterPreviewMode();")
        except RuntimeError:
            return
        except Exception:
            pass

        # 关键修复：切回非分栏模式后，确保主编辑器仍在中央区域可见
        try:
            self._restore_main_editor()
        except Exception:
            pass

        # 同步模式下拉框
        self._sync_mode_combo('preview')
        self._editor_mode = 'preview'

    def toggle_preview_mode(self):
        """切换预览模式（纯阅读，只读）"""
        if not hasattr(self, 'editor') or self.editor is None:
            return

        if self._current_mode() == 'preview':
            # 已在预览模式，退出回到写作模式
            self.set_editor_mode('wysiwyg')
        else:
            self.set_editor_mode('preview')
