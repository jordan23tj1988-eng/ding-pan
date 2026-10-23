# -*- coding: utf-8 -*-
"""20261023 复盘的日历口径修复：20261024（周六，非交易日）→ 20261026（下一交易日）
影响 8 个产物；全部 .bak 备份。理由：周五盘后推演/验证的截止日必须是 20261026。
"""
import os, shutil, glob

os.chdir(r"D:\股票数据\市场数据")
files = glob.glob("_学习/*body_20261023.html") + glob.glob("_学习/*判断_20261023.json") + \
        glob.glob("_学习/交易计划_*_20261023.json")
total = 0
for f in files:
    if "总审" in f or "推演" in f:
        continue
    raw = open(f, encoding="utf-8").read()
    n = raw.count("20261024")
    if not n:
        continue
    shutil.copy2(f, f + ".bak_cal")
    new = raw.replace("20261024", "20261026")
    open(f, "w", encoding="utf-8", newline="\n").write(new)
    print(f"{n:>2} 处 -> {f}")
    total += n
print("合计替换", total, "处")
