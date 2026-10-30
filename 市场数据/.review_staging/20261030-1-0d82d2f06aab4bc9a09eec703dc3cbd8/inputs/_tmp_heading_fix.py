# -*- coding: utf-8 -*-
"""按 review_pages.HEADING_MAP 关键词重命名 route body 的 h2"""
import io

D = "20261029"
L = r"D:\股票数据\市场数据\_学习"

FIX = {
 "auction": [
   ("一 竞价核心判断", "一 竞价选股池 · 核心判断"),
   ("二 证据与闸门对账", "二 当日证据与闸门对账"),
   ("四 明日竞价预案", "四 明日竞价预案 · 当日池处置"),
 ],
 "lhb": [
   ("一 席位核心判断", "一 席位综合判断"),
   ("三 游资量化扫描", "三 席位训练库 · 游资量化扫描"),
   ("四 明日席位预案", "四 席位荐票与明日预案"),
 ],
 "limitup": [
   ("二 连板梯队与断层", "二 连板梯队与温度断层"),
   ("三 炸板与虚胖检测", "三 炸板与虚胖检测 · 质量库"),
 ],
}

for r, pairs in FIX.items():
    p = "%s\\%s_body_%s.html" % (L, r, D)
    s = io.open(p, encoding="utf-8").read()
    for old, new in pairs:
        if old not in s:
            print("MISS", r, old)
            continue
        s = s.replace(old, new, 1)
    io.open(p, "w", encoding="utf-8").write(s)
    print("patched", r)
