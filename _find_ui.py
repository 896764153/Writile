
# -*- coding: utf-8 -*-
import io
lines = io.open('md_editor.py', encoding='utf-8').read().splitlines()
out = io.open('_ui_lines.txt', 'w', encoding='utf-8')
targets = ['def create_toolbar', 'def create_sidebar', 'def populate_file_tree',
           'def refresh_filelist_for_current_file', 'def _update_folder_label',
           'def create_editor', 'def toggle_focus_mode', 'def toggle_typewriter_mode',
           'def apply_theme', 'focus_btn', 'typewriter_btn', 'theme_combo', 'theme_btn',
           'min_btn', 'max_btn', 'close_btn', 'title_bar', 'setCentralWidget']
for i, l in enumerate(lines):
    for t in targets:
        if t in l:
            out.write('%d: %s\n' % (i + 1, l.rstrip()))
            break
out.close()
print('done', len(lines))