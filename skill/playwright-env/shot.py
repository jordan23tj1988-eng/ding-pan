#!/usr/bin/env python3
"""沙箱无头浏览器截图（真渲染，执行JS/Canvas/GSAP——weasyprint盲区的替代目检方案）
用法: LD_LIBRARY_PATH=~/pwlibs/extracted/usr/lib/x86_64-linux-gnu python3 shot.py <html路径或URL> <输出png> [宽] [高] [等待ms]
整页长图: 高度传 full
"""
import sys
from playwright.sync_api import sync_playwright

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "shot.png"
w = int(sys.argv[3]) if len(sys.argv) > 3 else 1440
h_arg = sys.argv[4] if len(sys.argv) > 4 else "900"
wait = int(sys.argv[5]) if len(sys.argv) > 5 else 1500
full = h_arg == "full"
h = 900 if full else int(h_arg)
if "://" not in src:
    src = "file://" + src

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": w, "height": h})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
    pg.goto(src)
    pg.wait_for_timeout(wait)  # 等动画入场完成
    pg.screenshot(path=out, full_page=full)
    b.close()
print(f"截图 -> {out}")
if errors:
    print("⚠️ 页面JS错误:")
    for e in errors[:10]:
        print("  ", e)
