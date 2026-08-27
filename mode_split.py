# -*- coding: utf-8 -*-
"""
分栏模式（Split Mode - 左源码右预览）
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QSplitter

from editor_common import EditorWidget


# 分栏滚动同步注入脚本（每个面板各注入一次，__ROLE__ 替换为 'src'/'prev'）。
# 要点：
#   - el.style.scrollBehavior = 'auto'：覆盖全局 CSS 的 smooth，否则程序化
#     设置 scrollTop 会变成平滑动画，动画期间不断发 scroll 事件造成反馈回环；
#   - applying 回声抑制：被 Python 程序化滚动的一方忽略自身随之产生的
#     scroll 事件，避免「滚过去又被弹回来」；
#   - requestAnimationFrame 节流：高频滚动事件每帧最多上报一次。
_SPLIT_SCROLL_SYNC_JS = r"""
(function() {
    var el = document.getElementById('editor');
    if (!el || el._writileScrollSync) return;
    el._writileScrollSync = true;
    el.style.scrollBehavior = 'auto';
    var role = '__ROLE__';
    var applying = false;
    var applyTimer = null;
    var lastPct = -1;
    var pendingPct = null;
    var rafScheduled = false;

    // 接收侧入口：Python 只把百分比写给「非发起方」面板
    window._writileSyncApply = function(pct) {
        var sh = el.scrollHeight - el.clientHeight;
        if (sh <= 0) return;
        var target = Math.round(pct * sh);
        if (Math.abs(el.scrollTop - target) <= 1) return;
        applying = true;
        if (applyTimer) clearTimeout(applyTimer);
        // 连续同步期间持续抑制自身回声事件
        applyTimer = setTimeout(function() { applying = false; }, 150);
        el.scrollTop = target;
        lastPct = pct;
    };

    function send() {
        rafScheduled = false;
        if (pendingPct === null) return;
        var pct = pendingPct;
        pendingPct = null;
        lastPct = pct;
        if (window.bridge && window.bridge.onScrollSync) {
            try { window.bridge.onScrollSync(pct, role); } catch(e) {}
        }
    }

    el.addEventListener('scroll', function() {
        // 程序化同步引发的回声：忽略，否则会形成来回反弹
        if (applying) return;
        var sh = el.scrollHeight - el.clientHeight;
        if (sh <= 0) return;
        var pct = el.scrollTop / sh;
        if (Math.abs(pct - lastPct) < 0.002) return;
        pendingPct = pct;
        if (!rafScheduled) {
            rafScheduled = true;
            requestAnimationFrame(send);
        }
    }, { passive: true });
})();
"""


class SplitModeMixin:
    """分栏模式 Mixin：左边源码编辑器，右边只读预览

    依赖 MainWindow 属性：
      - editor, default_workdir, dark_mode, focus_mode, typewriter_mode
      - _active_editor(), _sync_mode_combo(), update_title()
    """

    def enter_split_mode(self):
        """显示分栏模式：左边源码编辑器，右边预览"""
        # 获取当前编辑器的内容（若主编辑器不可用，直接使用上次缓存）
        ed = self._active_editor()
        if ed is None:
            self._switch_to_split_layout("")
            return

        def handle_content(content):
            self._switch_to_split_layout(content or "")

        try:
            ed.get_content(handle_content)
        except Exception:
            self._switch_to_split_layout("")

    def _switch_to_split_layout(self, content):
        """切换到分栏布局：左源码编辑器，右只读预览，两侧同步滚动与内容。

        架构：
          - 左（source_editor）：保持 contenteditable，进入「全局源码模式」（toggleSourceMode）
            优点是 源码渲染 在编辑过程中能够提供语法高亮、行号、未闭合括号提示，
            而且可以直接复用现有 EDITOR_HTML，无需打包外部资源（WebEngine 加载远程
            CDN 在某些环境会被防火墙阻断）。
          - 右（preview_view）：保持 contenteditable，进入「只读预览模式」（enterPreviewMode）
            完全只读，不接收编辑信号。
          - 两面板 content_changed + scroll 事件互连：
              • 左→右：源面板内容变化后防抖 300ms，把全文同步写入预览面板
              • 右→左：预览面板滚动时按行号比例反推源面板应滚动位置（scrolling user-not-active
                期间避免循环反弹）

        修复（重复进入 split 模式 bug）：
          1. 每次进入前无条件调用 _cleanup_split_widgets() 彻底清理旧实例。
          2. 使用 _wait_for_editor_ready() 通过 polling 机制等待编辑器页面真正就绪
             （不依赖 page_ready 标志，因为 GPU 错误可能导致该标志不更新）。
          3. 使用多次重试机制调用 setContent/toggleSourceMode，确保在 GPU 错误、
             渲染异常等情况下仍能正确显示。
          4. 主动触发大纲与字数刷新，避免依赖用户在 split 中编辑。
        """
        # 关键：每次进入都先彻底清理旧实例（防止信号/loadFinished 互相干扰）。
        self._cleanup_split_widgets()

        # 备份主编辑器当前状态（光标偏移、滚动位置），退出分栏时恢复
        self._backup_main_editor_state()
        # 同步 file_path（如果有）使预览面板能解析相对路径图片
        file_path = getattr(self.editor, 'file_path', None) if getattr(self, 'editor', None) else None

        # 【根本性修复】复用主编辑器 self.editor 作为左侧，不再创建新的 source_editor。
        # 原因：每次分栏模式切换都创建 2 个新的 QWebEngineView，多次切换后 GPU 共享上下文
        # 创建失败（"Failed to create GLES3 context" / "Failed to create shared context"），
        # 进而导致 web_view 渲染异常，最终表现为"主体内容框消失"。
        # 复用 self.editor 可彻底避免在分栏切换中创建额外的 WebEngine 实例。
        # 主编辑器需要进入「全局源码模式」(toggleSourceMode) 以提供行号 / 语法高亮。
        if hasattr(self, 'editor') and self.editor and not getattr(self.editor, '_destroyed', False):
            try:
                # 关键：先从 QMainWindow 中央 widget 解父子关系，
                # 否则 Qt 会因"widget 已有父对象"而拒绝 addWidget 到 splitter
                if self.centralWidget() is self.editor:
                    self.takeCentralWidget()
                self.editor.setParent(None)
                # 接入滚动同步回调（必须同时更新桥接对象，否则滚动事件传不到 Python）
                self.editor.set_scroll_sync_callback(self._on_split_scroll_sync)
                # 把左侧修改信号接到主窗口
                try:
                    self.editor._bridge.contentChanged.connect(self._on_split_source_changed)
                except Exception:
                    pass
                self.source_editor = self.editor  # 别名保留，避免 _active_editor 错乱
            except RuntimeError:
                self.source_editor = None

        # 创建分栏控件
        self.split_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.split_splitter.setChildrenCollapsible(False)
        self.split_splitter.setHandleWidth(4)

        # 左侧：复用 self.editor（避免重复创建 WebEngine）
        if getattr(self, 'source_editor', None) is not None:
            self.split_splitter.addWidget(self.source_editor)

        # 右侧：仍然创建一个新的只读预览面板（必须有预览）
        self.preview_view = EditorWidget(
            default_workdir=self.default_workdir,
            scroll_sync_callback=self._on_split_scroll_sync,
        )
        self.preview_view.set_dark_mode(self.dark_mode)
        self.preview_view.set_focus_mode(self.focus_mode)
        self.preview_view.set_typewriter_mode(self.typewriter_mode)
        if file_path:
            self.preview_view.file_path = file_path
        self.split_splitter.addWidget(self.preview_view)

        # 50% 平分
        self.split_splitter.setStretchFactor(0, 1)
        self.split_splitter.setStretchFactor(1, 1)
        self.split_splitter.setSizes([10**6, 10**6])

        self.split_container = self.split_splitter
        self.setCentralWidget(self.split_splitter)
        self.split_splitter.show()

        # 内容同步设置（初始装载使用防抖 300ms）
        self.split_sync_timer = QTimer(self)
        self.split_sync_timer.setSingleShot(True)
        self.split_sync_timer.setInterval(300)
        self.split_sync_timer.timeout.connect(self._sync_split_content)

        # 滚动互相同步设置
        self._setup_split_scroll_sync()

        # 加载内容（先设源面板，再设预览面板）
        # 关键修复：即使编辑器在创建后立即可见，也要等页面真正可交互后才执行模式切换。
        # 使用 polling + 重试机制，确保 setContent / toggleSourceMode / enterPreviewMode
        # 都能在页面真正可用时被调用，避免 GPU 错误导致的初始化异常。
        self._split_initial_content = content
        self._wait_and_init_split_editors()

        # 同步模式下拉框与焦点
        self._sync_mode_combo('split')
        self._editor_mode = 'split'

    def _wait_and_init_split_editors(self):
        """轮询等待两个 split 编辑器真正就绪后初始化内容与模式。

        修复：在多 WebEngine 实例环境下（split 模式有 2 个实例），第二次进入时
        Chromium 经常出现 "Failed to create shared context" 的 GPU 错误，
        导致 page_ready 标志可能不准确。本方法使用 JS 探测（runJavaScript 返回值）
        而非 page_ready 标志判断页面是否真正可用，最多等待 5 秒。
        """
        if not (hasattr(self, 'source_editor') and self.source_editor and
                hasattr(self, 'preview_view') and self.preview_view):
            return
        content = getattr(self, '_split_initial_content', '') or ''

        state = {'attempts': 0, 'src_ready': False, 'prev_ready': False}

        def _check():
            # 编辑器已被销毁/切换出 split 模式：停止轮询
            if (getattr(self, '_destroyed', False) or
                    getattr(self, '_editor_mode', None) != 'split' or
                    not hasattr(self, 'source_editor') or not self.source_editor or
                    not hasattr(self, 'preview_view') or not self.preview_view or
                    getattr(self.source_editor, '_destroyed', False) or
                    getattr(self.preview_view, '_destroyed', False)):
                return

            state['attempts'] += 1

            # 通过探测 editorAPI 是否真的存在，判断页面是否真正就绪
            # （page_ready 标志在 GPU 错误时可能不准确，但 JS 探测更可靠）
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

            try:
                if not state['src_ready'] and self.source_editor and not getattr(self.source_editor, '_destroyed', False):
                    self.source_editor.web_view.page().runJavaScript(
                        "!!(window.editorAPI && window.editorAPI.setContent)",
                        _probe_src
                    )
            except Exception:
                pass

            try:
                if not state['prev_ready'] and self.preview_view and not getattr(self.preview_view, '_destroyed', False):
                    self.preview_view.web_view.page().runJavaScript(
                        "!!(window.editorAPI && window.editorAPI.setContent)",
                        _probe_prev
                    )
            except Exception:
                pass

            # 兜底：如果 polling 探测 JS 没回调（同步阻塞），基于 _page_ready 标志判断
            def _try_finish():
                # 主循环兜底将在下一次轮询中执行，这里不强求
                pass

            # 兜底：基于 page_ready 标志和探测结果判断
            if (state['src_ready'] or getattr(self.source_editor, '_page_ready', False)) and \
               (state['prev_ready'] or getattr(self.preview_view, '_page_ready', False)):
                _do_init()
                return

            if state['attempts'] >= 50:  # 5 秒超时（每 100ms 检查一次）
                # 超时后强制初始化（即使页面还没就绪，setContent 也会被排队）
                _do_init()
                return

            QTimer.singleShot(100, _check)

        def _do_init():
            """执行真正的初始化：setContent + toggleSourceMode / enterPreviewMode"""
            src = getattr(self, 'source_editor', None)
            prv = getattr(self, 'preview_view', None)
            if not src or not prv:
                return
            if getattr(src, '_destroyed', False) or getattr(prv, '_destroyed', False):
                return
            try:
                # 1) 设置内容
                src._apply_content(content)
                prv._apply_content(content)

                # 2) 进入源码模式（左）和只读预览模式（右）
                # 用幂等 setSourceMode(true)，避免 toggle 依赖 JS 端当前状态
                src.run_js("window.editorAPI.setSourceMode(true);")
                prv.run_js("window.editorAPI.enterPreviewMode();")

                # 3) 200ms 后再次执行一次（防止 JS 队列延迟导致初始化失败）
                def _retry_init():
                    if (getattr(self, '_destroyed', False) or
                            getattr(self, '_editor_mode', None) != 'split' or
                            not hasattr(self, 'source_editor') or not self.source_editor or
                            not hasattr(self, 'preview_view') or not self.preview_view):
                        return
                    try:
                        if not getattr(self.source_editor, '_destroyed', False):
                            self.source_editor._apply_content(content)
                            self.source_editor.run_js("window.editorAPI.setSourceMode(true);")
                        if not getattr(self.preview_view, '_destroyed', False):
                            self.preview_view._apply_content(content)
                            self.preview_view.run_js("window.editorAPI.enterPreviewMode();")
                    except Exception:
                        pass
                    # 触发大纲和字数刷新
                    _refresh_outline_wordcount()
                QTimer.singleShot(200, _retry_init)

                # 4) 1.5 秒后最后一次保险
                def _final_retry():
                    if (getattr(self, '_destroyed', False) or
                            getattr(self, '_editor_mode', None) != 'split' or
                            not hasattr(self, 'source_editor') or not self.source_editor):
                        return
                    try:
                        if not getattr(self.source_editor, '_destroyed', False):
                            self.source_editor._apply_content(content)
                            self.source_editor.run_js("window.editorAPI.setSourceMode(true);")
                    except Exception:
                        pass
                    # 最后触发一次大纲/字数刷新
                    _refresh_outline_wordcount()
                QTimer.singleShot(1500, _final_retry)

                # 立即触发一次大纲/字数刷新
                _refresh_outline_wordcount()

            except Exception:
                pass

        def _refresh_outline_wordcount():
            """主动触发大纲与字数统计刷新。"""
            try:
                if hasattr(self, '_outline_timer'):
                    self._outline_timer.start()
            except Exception:
                pass
            try:
                if hasattr(self, '_wordcount_timer'):
                    self._wordcount_timer.start()
            except Exception:
                pass

        # 启动轮询
        QTimer.singleShot(50, _check)

    def _setup_split_scroll_sync(self):
        """为分栏模式配置滚动同步：单向传播 + 回声抑制。

        旧实现的缺陷（表现为滚动不灵敏、不跟手、有时往回收）：
          1. Python 回写时的防回环条件写死为 splitSyncSuspend !== 'src'，
             当预览面板发起滚动时回写会打到预览面板自己，与用户操作对抗；
          2. #editor 的 CSS scroll-behavior: smooth 使程序化 scrollTop 赋值
             变成平滑动画，动画期间持续产生 scroll 事件，形成反馈风暴；
          3. Python 不区分发起方，对两个面板无差别回写。

        新设计：
          - 面板滚动事件携带 role 标识（'src'/'prev'）上报，Python 只写另一侧；
          - 接收方面板用 applying 标志抑制自身被程序化滚动引发的回声事件；
          - 分栏面板内禁用 smooth 滚动，程序化同步即时精确生效；
          - 发起侧用 requestAnimationFrame 节流，每帧最多上报一次。

        同步采用「滚动百分比 = scrollTop / (scrollHeight - clientHeight)」，
        同一份文档在源码/预览两种视图中的高度比例基本一致。
        """
        if not (hasattr(self, 'source_editor') and self.source_editor and
                hasattr(self, 'preview_view') and self.preview_view):
            return

        def _inject(ed, role):
            try:
                ed.run_js(_SPLIT_SCROLL_SYNC_JS.replace('__ROLE__', role))
            except Exception as e:
                print(f"setup scroll sync ({role}): {e}")

        def _setup():
            """注入同步脚本；页面尚未就绪时每 200ms 重试（最多约 4 秒）。
            注入脚本自带幂等守卫（_writileScrollSync），重复注入无副作用。"""
            if getattr(self, '_destroyed', False):
                return
            if getattr(self, '_editor_mode', None) != 'split':
                return
            src = getattr(self, 'source_editor', None)
            prv = getattr(self, 'preview_view', None)
            if not src or not prv:
                return
            if getattr(src, '_destroyed', False) or getattr(prv, '_destroyed', False):
                return
            _inject(src, 'src')
            _inject(prv, 'prev')
            self._scroll_sync_attempts = getattr(self, '_scroll_sync_attempts', 0) + 1

            def _check(ok):
                try:
                    if ok or getattr(self, '_scroll_sync_attempts', 0) >= 20:
                        return
                except Exception:
                    return
                QTimer.singleShot(200, _setup)

            try:
                prv.web_view.page().runJavaScript(
                    "!!(document.getElementById('editor') && "
                    "document.getElementById('editor')._writileScrollSync)",
                    _check
                )
            except Exception:
                if getattr(self, '_scroll_sync_attempts', 0) < 20:
                    QTimer.singleShot(200, _setup)

        # 等面板加载完成后再注入脚本
        self._scroll_sync_attempts = 0
        QTimer.singleShot(200, _setup)

    def _on_split_source_changed(self):
        """源面板内容变化时：刷新大纲/字数，并把内容防抖同步到预览面板。"""
        ed = self._active_editor()
        if ed:
            ed.is_modified = True
        self.update_title()
        if hasattr(self, '_outline_timer'):
            self._outline_timer.start()
        if hasattr(self, '_wordcount_timer'):
            self._wordcount_timer.start()
        # 防抖 300ms 后同步内容到预览
        if hasattr(self, 'split_sync_timer') and self.split_sync_timer:
            self.split_sync_timer.start()

    def _sync_split_content(self):
        """源 → 预览 内容同步：取源面板文本，应用到预览面板并重新渲染。"""
        if not (hasattr(self, 'source_editor') and self.source_editor and
                hasattr(self, 'preview_view') and self.preview_view):
            return
        try:
            def handle(content):
                if content is None:
                    return
                # 把源面板文本同步到预览面板（预览面板会自动渲染）
                try:
                    self.preview_view._apply_content(content)
                except Exception as e:
                    print(f"preview set_content: {e}")

            self.source_editor.get_content(handle)
        except Exception as e:
            print(f"sync split content: {e}")

    def _backup_main_editor_state(self):
        """进入分栏模式前备份主编辑器的光标偏移与滚动位置，退出分栏时恢复。"""
        self._main_state_backup = {
            'content': '',
            'cursor': 0,
            'scroll': 0,
            'file_path': None,
            'is_modified': False,
        }
        ed = getattr(self, 'editor', None)
        if not ed:
            return
        try:
            # 内容（同步快照）
            ed.get_content(lambda c: self._main_state_backup.update({'content': c or ''}))
            self._main_state_backup['file_path'] = ed.file_path
            self._main_state_backup['is_modified'] = ed.is_modified
            # 滚动位置（像素）
            try:
                self._main_state_backup['scroll'] = ed.web_view.page().scrollPosition().y()
            except Exception:
                self._main_state_backup['scroll'] = 0
            # 光标位置（编辑器全局字符偏移，通过 JS 获取）
            # 注意：cb_cursor 在异步回调里被调用，期间编辑器可能已被销毁
            # （例如用户立即切换模式）。必须检查 _destroyed 标志并捕获 RuntimeError，
            # 否则会出现 "wrapped C/C++ object of type EditorWebView has been deleted"。
            def cb_cursor(text):
                if text is None:
                    return
                if getattr(ed, '_destroyed', False):
                    return
                js = (
                    "var sel = window.getSelection();"
                    "if (sel && sel.rangeCount > 0) {"
                    "  var range = sel.getRangeAt(0);"
                    "  var pre = document.createRange();"
                    "  pre.selectNodeContents(document.getElementById('editor'));"
                    "  try { pre.setEnd(range.startContainer, range.startOffset); } catch(e) {}"
                    "  pre.toString().length;"
                    "} else { 0; }"
                )
                try:
                    ed.web_view.page().runJavaScript(
                        f"window.editorAPI.getContent() ? ({js}) : 0",
                        lambda offset: self._main_state_backup.update({'cursor': offset or 0})
                    )
                except RuntimeError:
                    pass
                except Exception:
                    pass
            ed.get_content(cb_cursor)
        except Exception as e:
            print(f"backup main editor: {e}")

    def _restore_main_editor_state(self):
        """退出分栏模式时恢复主编辑器之前的光标和滚动位置。"""
        backup = getattr(self, '_main_state_backup', None)
        if not backup:
            return
        ed = getattr(self, 'editor', None)
        if not ed:
            return
        try:
            # 恢复滚动位置（延迟到页面准备好后）
            scroll_y = backup.get('scroll', 0) or 0
            def _do_restore():
                try:
                    if scroll_y and scroll_y > 0:
                        ed.web_view.page().runJavaScript(
                            f"window.scrollTo(0, {int(scroll_y)});"
                        )
                    # 恢复光标位置：在编辑器容器里找对应字符偏移
                    cursor = backup.get('cursor', 0) or 0
                    if cursor > 0:
                        ed.web_view.page().runJavaScript(f"""
                            (function() {{
                                var ed = document.getElementById('editor');
                                if (!ed) return;
                                var walker = document.createTreeWalker(ed, NodeFilter.SHOW_TEXT, null, false);
                                var count = 0;
                                var node;
                                while ((node = walker.nextNode())) {{
                                    var len = node.textContent.length;
                                    if (count + len >= {int(cursor)}) {{
                                        var range = document.createRange();
                                        range.setStart(node, Math.max(0, {int(cursor)} - count));
                                        range.collapse(true);
                                        var sel = window.getSelection();
                                        if (sel) {{ sel.removeAllRanges(); sel.addRange(range); }}
                                        ed.focus();
                                        return;
                                    }}
                                    count += len;
                                }}
                            }})();
                        """)
                except Exception as e:
                    print(f"restore scroll/cursor: {e}")
            QTimer.singleShot(150, _do_restore)
        except Exception as e:
            print(f"restore main editor: {e}")

    def _cleanup_split_widgets(self):
        """清理分栏模式的 widget（彻底删除旧实例 + 释放资源）。

        修复（重复进入 split 模式 bug）：
          旧实现只 hide 编辑器并保留 self.source_editor / self.preview_view 引用，
          注释声称「为重用优化」，但实际上 _switch_to_split_layout 每次都创建新
          EditorWidget 实例，导致旧实例残留：
            • 旧 _bridge.contentChanged 信号仍连接到 _on_split_source_changed
            • 旧 web_view.loadFinished 可能再次触发
            • 旧 WebEngine 进程持续占用内存（资源泄漏）
          本函数现在彻底释放旧实例（包括 deleteLater 和 delattr Python 引用）。
        """
        # 1. 断开两个编辑器的所有 loadFinished / contentChanged 连接（避免后续误触发）
        for attr in ('source_editor', 'preview_view'):
            ed = getattr(self, attr, None)
            if ed and getattr(ed, 'web_view', None):
                try:
                    ed.web_view.loadFinished.disconnect()
                except Exception:
                    pass
            if ed and getattr(ed, '_bridge', None):
                try:
                    ed._bridge.contentChanged.disconnect()
                except Exception:
                    pass

        # 2. 隐藏并彻底释放旧编辑器（不再「重用」，避免重复进入时的状态冲突）
        #    【关键保护】source_editor 可能是 self.editor（复用主编辑器），
        #    这种情况下绝不能 deleteLater 主编辑器，否则主体内容框永久消失。
        for attr in ('source_editor', 'preview_view'):
            ed = getattr(self, attr, None)
            if ed is None:
                continue
            # 关键保护：主编辑器永远不能被 deleteLater
            if ed is getattr(self, 'editor', None):
                # 解除父子关系 + 解除信号连接，但不 deleteLater 也不永久 hide
                try:
                    ed.setParent(None)
                except Exception:
                    pass
                continue
            try:
                # 非主编辑器：彻底释放（这是 split 模式独有实例）
                ed._destroyed = True
                try:
                    ed.setParent(None)
                except Exception:
                    pass
                try:
                    ed.hide()
                except Exception:
                    pass
                ed.deleteLater()
            except Exception:
                pass

        # 3. 清除 Python 属性引用（source_editor 若就是 editor，则跳过避免删引用）
        for attr in ('source_editor', 'preview_view'):
            if not hasattr(self, attr):
                continue
            ed = getattr(self, attr, None)
            if ed is getattr(self, 'editor', None):
                # 主编辑器被复用为 source_editor，保留对它的引用
                continue
            try:
                delattr(self, attr)
            except AttributeError:
                pass

        # 4. 删除 splitter
        if hasattr(self, 'split_splitter') and self.split_splitter:
            try:
                self.split_splitter.setParent(None)
            except Exception:
                pass
            try:
                self.split_splitter.deleteLater()
            except Exception:
                pass

        # 5. 清除容器引用
        for attr in ('split_container', 'split_splitter'):
            if hasattr(self, attr):
                try:
                    delattr(self, attr)
                except AttributeError:
                    pass

        # 6. 清理 split 初始化临时状态
        if hasattr(self, '_split_initial_content'):
            try:
                delattr(self, '_split_initial_content')
            except AttributeError:
                pass

    def exit_split_mode(self):
        """退出分栏模式：释放 split 资源 + 恢复主编辑器状态（光标/滚动/内容）。

        增强（修复多次切换后主编辑器消失）：
          - 重新设置主编辑器为中央 widget 前，先 setParent(self) 避免被 dock / split 占用布局。
          - 主动 show() + raise_() 确保 WebEngine 在隐藏后能被重新显示。
        """
        if hasattr(self, 'split_container') and self.split_container:
            # 脱离 splitter 所有权，避免 setCentralWidget 替换时销毁 C++ 对象
            try:
                self.split_splitter.setParent(None)
            except Exception:
                pass
            self._cleanup_split_widgets()
        # 恢复主编辑器（如果存在）
        if hasattr(self, 'editor') and self.editor and not getattr(self.editor, '_destroyed', False):
            try:
                # 关键：如果主编辑器还在 splitter 里，先从 splitter 移除
                # （_switch_to_split_layout 中我们把它加入 splitter 作为左侧）
                if hasattr(self, 'split_splitter') and self.split_splitter is not None:
                    if self.editor.parent() is self.split_splitter:
                        try:
                            self.split_splitter.removeWidget(self.editor)
                        except Exception:
                            pass
                # 关键：先重新设定父对象（可能在 split 期间被调整过）
                try:
                    self.editor.setParent(self)
                except RuntimeError:
                    return
                # 显式设置最小尺寸和大小策略，确保中央 widget 有正确的 layout
                try:
                    from PyQt6.QtWidgets import QSizePolicy
                    self.editor.setMinimumSize(0, 0)
                    self.editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                except Exception:
                    pass
                self.editor.setVisible(True)
                # 把 split 源面板的最终内容同步回主编辑器（用户在 split 里改了东西）
                # 使用同步等待，确保内容完全同步后再进行后续操作
                try:
                    if hasattr(self, 'source_editor') and self.source_editor \
                            and not getattr(self.source_editor, '_destroyed', False):
                        from PyQt6.QtCore import QEventLoop, QTimer
                        content_result = [None]
                        sync_loop = QEventLoop()

                        def _sync_back(content):
                            content_result[0] = content
                            sync_loop.quit()

                        # 【修复卡顿】加超时兜底：页面无响应时回调可能永不触发，
                        # 无超时的嵌套事件循环会把主线程永久挂起（表现为切模式卡死）。
                        sync_timeout = QTimer()
                        sync_timeout.setSingleShot(True)
                        sync_timeout.timeout.connect(sync_loop.quit)
                        sync_timeout.start(2000)

                        self.source_editor.get_content(_sync_back)
                        sync_loop.exec()
                        sync_timeout.stop()

                        # 在内容同步完成后再恢复状态
                        if content_result[0] is not None:
                            try:
                                self.editor.set_content(content_result[0])
                            except Exception:
                                pass
                except Exception:
                    pass
                # 恢复主编辑器之前的光标和滚动位置
                self._restore_main_editor_state()
                # 重新设为中央 widget（只在当前不是它时）
                if self.centralWidget() is not self.editor:
                    self.setCentralWidget(self.editor)
                self.editor.show()
                self.editor.raise_()
                self._sync_mode_combo('wysiwyg')
                self._editor_mode = 'wysiwyg'
            except RuntimeError:
                # wrapped C/C++ object ... has been deleted：静默忽略
                pass
        # 清理备份状态
        if hasattr(self, '_main_state_backup'):
            try:
                delattr(self, '_main_state_backup')
            except AttributeError:
                pass
        # 清理同步定时器
        if hasattr(self, 'split_sync_timer'):
            try:
                self.split_sync_timer.stop()
                delattr(self, 'split_sync_timer')
            except (AttributeError, RuntimeError):
                pass

    def _on_split_scroll_sync(self, pct, role=''):
        """分栏模式滚动同步桥接：把百分比只写给发起方的另一侧面板。

        role='src'  → 源面板发起，写预览面板；
        role='prev' → 预览面板发起，写源面板。
        接收方通过 _writileSyncApply 设置 scrollTop 并抑制回声事件，
        因此不会反弹回发起方，用户滚动始终跟手。
        """
        if not (hasattr(self, 'source_editor') and self.source_editor and
                hasattr(self, 'preview_view') and self.preview_view):
            return
        try:
            pct = max(0.0, min(1.0, float(pct)))
        except Exception:
            return
        if role == 'src':
            target = self.preview_view
        elif role == 'prev':
            target = self.source_editor
        else:
            return
        try:
            if not getattr(target, '_destroyed', False):
                target.web_view.page().runJavaScript(
                    f"window._writileSyncApply && window._writileSyncApply({pct});"
                )
        except Exception as e:
            print(f"scroll sync: {e}")