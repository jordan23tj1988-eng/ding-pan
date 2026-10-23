# -*- coding: utf-8 -*-
import json, os, re
L = r"D:/股票数据/市场数据/_学习"
p = os.path.join(L, "theme_body_20261016.html")
s = open(p, encoding="utf-8").read()
op = len(re.findall(r"<div\b", s)); cl = s.count("</div>")
h2 = re.findall(r"<h2[^>]*>(.*?)</h2>", s, re.S)
hint = len(re.findall(r'class="hint"', s))
print("bytes:", len(s.encode()))
print("div open/close:", op, cl, "BALANCED" if op == cl else "!!! UNBALANCED")
print("h2 count:", len(h2))
for i, t in enumerate(h2, 1):
    print("  h2-%d: %s" % (i, re.sub(r"<[^>]+>", "", t)))
print('class="hint":', hint)
for bad in ("<html", "<head", "<body", "<!DOCTYPE", "<style", "<script"):
    if bad in s.lower(): print("!!! FORBIDDEN:", bad)
print("forbidden check done")
# 组件类白名单
cls = set(re.findall(r'class="([^"]+)"', s))
print("classes used:", sorted(cls))
allowed = {"theme-body","hero","card","hint","tl","tli","mut"}
extra = cls - allowed
print("non-whitelist classes:", sorted(extra) if extra else "NONE")
print("LEDGER present:", "<!--LEDGER-->" in s, "| closed:", "<!--/LEDGER-->" in s)
# JSON 全量校验
files = ["theme判断_20261016.json","题材荐票_20261016.json","题材龙头判断_20261016.json",
         "题材生命周期判断_20261016.json","交易计划_theme_20261016.json","能力回执_theme_20261016.json"]
for f in files:
    d = json.load(open(os.path.join(L,f), encoding="utf-8"))
    print("OK %-34s %6d bytes keys=%s" % (f, os.path.getsize(os.path.join(L,f)), list(d.keys())[:8]))
# 荐票标的须 ∈ 61 只涨停池
import csv
pool = {r["代码"] for r in csv.DictReader(open(r"D:/股票数据/市场数据/20261016/zt_pool.csv", encoding="utf-8-sig"))}
t = json.load(open(os.path.join(L,"theme判断_20261016.json"), encoding="utf-8"))
codes = [x["代码"] for x in t["荐票"]["标的"]]
print("\n荐票池大小:", len(pool), "| 标的:", codes, "| 全部∈池:", all(c in pool for c in codes))
print("正式荐票数:", sum(1 for x in t["荐票"]["标的"] if x["类型"]=="荐票"), "观察数:", sum(1 for x in t["荐票"]["标的"] if x["类型"]=="观察"))
tr = json.load(open(os.path.join(L,"交易计划_theme_20261016.json"), encoding="utf-8"))
print("buys:", len(tr["buys"]), "sells:", len(tr["sells"]), "| notes字数:", len(tr["notes"]))
st = json.load(open(os.path.join(L,"_模拟盘/theme/状态.json"), encoding="utf-8"))
print("在持票:", st.get("持仓"), "| 现金:", st.get("现金"))
