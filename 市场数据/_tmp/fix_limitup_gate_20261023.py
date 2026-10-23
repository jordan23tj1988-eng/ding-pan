# -*- coding: utf-8 -*-
"""limitup body 两处门禁口径修复（零语义改动，只改写法避免核对器跨格误拼）
① 推荐表 002724 行 `<td>0</td><td>连板≥5×炸≥2` 剥标签后成 "观察0连板≥5" →
   高标口径正则 (\d+)连?板 误读成 "海洋王 0板"（真实 6 板）。加"桶："断开。
② hero 洞察 "温度 11.2→53.2" → 元信息温度引用取第一个数字 11.2 ≠ 温度表 53.2。
   改为 "温度 53.2（昨 11.2）"，信息不丢、今日值在前。
"""
import os, shutil

os.chdir(r"D:\股票数据\市场数据")
p = "_学习/limitup_body_20261023.html"
raw = open(p, encoding="utf-8").read()
shutil.copy2(p, p + ".bak_gate")

pairs = [
    ("<td>0</td><td>连板≥5×炸≥2", "<td>0</td><td>桶：连板≥5×炸≥2"),
    ("温度 11.2→53.2", "温度 53.2（昨 11.2）"),
]
new = raw
for a, b in pairs:
    n = new.count(a)
    print(f"{n} 处: {a[:40]} -> {b[:40]}")
    new = new.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(new)

# 复验：剥标签后不应再出现 "观察0连板"
import re
t = re.sub(r"<[^>]+>", "", new)
print("残留 '观察0连板':", t.count("观察0连板"), "| '温度 11.2→53.2':", new.count("温度 11.2→53.2"))
print("'海洋王观察' 后 20 字:", repr(t[t.find("海洋王观察"):t.find("海洋王观察") + 26]))
print("div", new.count("<div"), new.count("</div>"))
