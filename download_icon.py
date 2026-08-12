# -*- coding: utf-8 -*-
"""下载 Writile 图标"""
import urllib.request
import ssl

prompt = "Modern software app icon for Markdown editor named Writile, featuring a large stylized letter S in white, the S is formed by clean geometric lines and a subtle markdown hash symbol, gradient background from deep blue (#1e3a8a) to teal (#0d9488), minimalist flat design, rounded square shape, professional desktop application icon, high resolution, crisp edges, centered composition"

url = "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=" + urllib.parse.quote(prompt) + "&image_size=square_hd"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("Downloading icon...")
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        data = resp.read()
        with open(r"d:\project\ai agent\xuexi\MarkdownEditor\icon.png", "wb") as f:
            f.write(data)
        print(f"OK! Saved icon.png ({len(data)} bytes)")
except Exception as e:
    print(f"Error: {e}")
