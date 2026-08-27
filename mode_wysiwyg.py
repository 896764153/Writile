# -*- coding: utf-8 -*-
"""
写作模式（WYSIWYG - 所见即所得）
"""


class WysiwygModeMixin:
    """写作模式 Mixin：所见即所得编辑

    依赖 MainWindow 属性：editor, mode_combo
    """

    def enter_wysiwyg_mode(self):
        """进入写作模式：所见即所得编辑"""
        # 如果当前在分栏模式，先退出（捕获 RuntimeError 防止反复进入时 C++ 对象失效）
        if hasattr(self, 'split_container') and self.split_container:
            try:
                self.exit_split_mode()
            except RuntimeError:
                return

        # 确保编辑器存在
        if not hasattr(self, 'editor') or self.editor is None:
            return

        # 进入编辑模式（从预览/源码等状态恢复）
        try:
            self.editor.run_js("window.editorAPI.enterEditMode();")
        except RuntimeError:
            return
        except Exception:
            pass

        # 同步模式下拉框
        self._sync_mode_combo('wysiwyg')
        self._editor_mode = 'wysiwyg'