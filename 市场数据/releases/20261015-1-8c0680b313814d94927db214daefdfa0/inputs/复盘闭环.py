# -*- coding: utf-8 -*-
"""复盘闭环检查：扫描 日记.md，报告每块「六、复盘总结（T+1 回顾）」区块状态。
- 已回填：T+1 当日已填写复盘总结 + 验证
- 待 T+1 复盘：仍为占位，需 T+1 当日回填，完成「记录 → 次日验证」闭环
用法: python 复盘闭环.py
"""
import os, re

BASE = r"D:\股票数据\市场数据"
dp = os.path.join(BASE, "_学习", "日记.md")
if not os.path.isfile(dp):
    print("无日记"); raise SystemExit

txt = open(dp, encoding="utf-8").read().replace("\r\n", "\n")
blocks = re.split(r"(?=^## )", txt, flags=re.M)
day_blocks = [b for b in blocks if re.match(r"^##\s+\d{4}-\d{2}-\d{2}\b", b.strip())]

print("复盘闭环状态：")
pending = 0
no_block = 0
for b in day_blocks:
    m = re.match(r"^##\s+(\d{4}-\d{2}-\d{2})", b.strip())
    date = m.group(1) if m else "?"
    sec = re.search(r"###\s*六、复盘总结.*?(?=\n### |\Z)", b, re.S)
    if not sec:
        print("  · %s: 无复盘总结区块（旧块，待补）" % date)
        no_block += 1
        continue
    body = sec.group(0)
    if "待 T+1" in body:
        mm = re.search(r"待 T\+1（(\d{4}-\d{2}-\d{2})）", body)
        tgt = mm.group(1) if mm else "?"
        print("  ⏳ %s: 待 %s 复盘" % (date, tgt))
        pending += 1
    else:
        print("  ✓ %s: 已回填" % date)

print("\n共 %d 个日期块 | 已回填 %d | 待复盘 %d | 缺区块 %d"
      % (len(day_blocks), len(day_blocks) - pending - no_block, pending, no_block))
print("待复盘块请在 T+1 当日用 bash python 读 日记.md → 替换占位 → 整体写回（勿用 Edit/Write 直改中文长行）。")
