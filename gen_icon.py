# -*- coding: utf-8 -*-
"""
生成 Writile 应用图标 (.ico 格式)
以 W 字母为特色，不依赖网络和 PIL，直接用 Python 生成
"""
import os
import struct
import zlib


def create_w_icon_png_bytes(size=256):
    """生成 PNG 字节数据 (W 字母图标)"""
    width = height = size
    pixels = []

    for y in range(height):
        row = []
        for x in range(width):
            margin = size // 10
            corner_radius = size // 6

            in_corner = False
            if x < margin + corner_radius and y < margin + corner_radius:
                cx = margin + corner_radius
                cy = margin + corner_radius
                dx = x - cx
                dy = y - cy
                if dx * dx + dy * dy > corner_radius * corner_radius:
                    in_corner = True
            elif x >= width - margin - corner_radius and y < margin + corner_radius:
                cx = width - margin - corner_radius - 1
                cy = margin + corner_radius
                dx = x - cx
                dy = y - cy
                if dx * dx + dy * dy > corner_radius * corner_radius:
                    in_corner = True
            elif x < margin + corner_radius and y >= height - margin - corner_radius:
                cx = margin + corner_radius
                cy = height - margin - corner_radius - 1
                dx = x - cx
                dy = y - cy
                if dx * dx + dy * dy > corner_radius * corner_radius:
                    in_corner = True
            elif x >= width - margin - corner_radius and y >= height - margin - corner_radius:
                cx = width - margin - corner_radius - 1
                cy = height - margin - corner_radius - 1
                dx = x - cx
                dy = y - cy
                if dx * dx + dy * dy > corner_radius * corner_radius:
                    in_corner = True

            if x < margin or x >= width - margin or y < margin or y >= height - margin or in_corner:
                row.append((0, 0, 0, 0))
                continue

            # 渐变背景：左上紫色 -> 右下橙红 (Writile 品牌色)
            tx = (x - margin) / (width - 2 * margin)
            ty = (y - margin) / (height - 2 * margin)
            t = (tx + ty) / 2

            # 紫色 #6366f1 (99,102,241) -> 橙红 #f97316 (249,115,22)
            r = int(99 + (249 - 99) * t)
            g = int(102 + (115 - 102) * t)
            b = int(241 + (22 - 241) * t)

            # 绘制 W 字母
            cx = width // 2
            cy = height // 2
            w_size = int(size * 0.45)
            w_height = int(size * 0.45)
            stroke = max(4, w_size // 8)

            in_w = False
            left_x = cx - w_size // 2
            right_x = cx + w_size // 2
            mid_left_x = cx - w_size // 6
            mid_right_x = cx + w_size // 6
            top_y = cy - w_height // 2
            bottom_y = cy + w_height // 2
            mid_y = cy - w_height // 4

            def dist_to_line(px, py, x1, y1, x2, y2):
                dx = x2 - x1
                dy = y2 - y1
                length_sq = dx * dx + dy * dy
                if length_sq == 0:
                    return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
                t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))
                proj_x = x1 + t * dx
                proj_y = y1 + t * dy
                return ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5

            d1 = dist_to_line(x, y, left_x, top_y, mid_left_x, bottom_y)
            d2 = dist_to_line(x, y, mid_left_x, bottom_y, cx, mid_y)
            d3 = dist_to_line(x, y, cx, mid_y, mid_right_x, bottom_y)
            d4 = dist_to_line(x, y, mid_right_x, bottom_y, right_x, top_y)

            if min(d1, d2, d3, d4) <= stroke / 2:
                in_w = True

            if in_w:
                row.append((255, 255, 255, 255))
            else:
                gloss = 1.0
                if ty < 0.3:
                    gloss = 1.0 + (0.3 - ty) * 0.4
                r = min(255, int(r * gloss))
                g = min(255, int(g * gloss))
                b = min(255, int(b * gloss))
                row.append((r, g, b, 255))

        pixels.append(row)

    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)

    signature = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)

    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'
        for x in range(width):
            r, g, b, a = pixels[y][x]
            raw_data += struct.pack('BBBB', r, g, b, a)

    compressed = zlib.compress(raw_data, 9)

    png = signature
    png += make_chunk(b'IHDR', ihdr_data)
    png += make_chunk(b'IDAT', compressed)
    png += make_chunk(b'IEND', b'')
    return png


def create_ico(output_path, sizes=(16, 32, 48, 64, 128, 256)):
    """生成 .ico 文件 (包含多个尺寸)"""
    images = []
    for size in sizes:
        png_data = create_w_icon_png_bytes(size)
        images.append((size, png_data))

    header = struct.pack('<HHH', 0, 1, len(images))

    directory = b''
    offset = 6 + len(images) * 16

    for size, png_data in images:
        w = 0 if size == 256 else size
        h = 0 if size == 256 else size
        entry = struct.pack('<BBBBHHII',
            w, h, 0, 0, 1, 32, len(png_data), offset
        )
        directory += entry
        offset += len(png_data)

    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(directory)
        for size, png_data in images:
            f.write(png_data)

    return os.path.exists(output_path)


if __name__ == '__main__':
    output = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
    if create_ico(output):
        print(f'OK! Icon generated: {output}')
        print(f'Size: {os.path.getsize(output)} bytes')

        png_output = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
        png_data = create_w_icon_png_bytes(256)
        with open(png_output, 'wb') as f:
            f.write(png_data)
        print(f'PNG: {png_output} ({os.path.getsize(png_output)} bytes)')
    else:
        print('FAILED to generate icon')
