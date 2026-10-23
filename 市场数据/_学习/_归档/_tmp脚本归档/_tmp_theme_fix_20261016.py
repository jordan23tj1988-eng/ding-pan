# -*- coding: utf-8 -*-
import json, os, re
L = r"D:/股票数据/市场数据/_学习"
p = os.path.join(L, "题材生命周期判断_20261016.json")
s = open(p, encoding="utf-8").read()
s = s.replace("机械=lcf 阶段", "机械阶段")
open(p, "w", encoding="utf-8", newline="\n").write(s)
d = json.load(open(p, encoding="utf-8"))
print("逐线数:", len(d["逐线"]), "| 高低切键:", list(d["高低切"].keys()))
print("lcf残留:", "lcf" in s)
# 抽查
print("\n出版传媒定性尾部:", d["逐线"]["出版传媒"]["定性"][-260:])
print("\n出版传媒判据:", d["逐线"]["出版传媒"]["判据"][:200])
print("\n高低切方向:", d["高低切"]["方向"][:200])
t = json.load(open(os.path.join(L,"theme判断_20261016.json"), encoding="utf-8"))
print("\n档位", t["判断"]["档位"], "置信度", t["判断"]["置信度"], "证据", len(t["判断"]["证据"]), "认知迭代", len(t["认知迭代"]), "深挖", len(t["深挖"]))
print("荐票标的", len(t["荐票"]["标的"]), [x["类型"] for x in t["荐票"]["标的"]])
print("\n结论含未替换占位:", "{" in t["判断"]["结论"][:50], t["判断"]["结论"][:120])
