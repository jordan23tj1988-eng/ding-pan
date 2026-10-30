# -*- coding: utf-8 -*-
"""概览页(index)正文自检：结构 + 长度 + 配平 + 禁字面量 + class 白名单"""
import re
import sys

P = r"D:\股票数据\市场数据\_学习\_wip_index_body_20261030.html"
TITLES = [
    "一 总判断 · 今日一句话",
    "二 五路裁决",
    "三 题材树 · 主线与结构",
    "四 总裁决 · 荐票与仓位",
    "五 指派与线索",
    "六 分歧与盲区 · 风险",
]
ALLOWED = {"card", "hint", "trow", "tbl", "tct", "tnm", "tds", "tjd", "tjd tj-main", "tr1", "sub"}

s = open(P, encoding="utf-8").read()
errs = []

# 1 存在且非空
if len(s) < 1000:
    errs.append("文件为空或过短")

# 2 h2 数=6 且标题逐字
h2 = re.findall(r"<h2>(.*?)</h2>", s, re.S)
if len(h2) != 6:
    errs.append("h2 数=%d（应为 6）" % len(h2))
for i, t in enumerate(h2[:6]):
    core = re.sub(r'<span class="hint">.*?</span>', "", t, flags=re.S).strip()
    if core != TITLES[i]:
        errs.append("h2#%d 标题不符：%r" % (i + 1, core))

# 3 纯文本长度
txt = re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", s))
if len(txt) < 3200:
    errs.append("纯文本长度=%d（<3200）" % len(txt))

# 4 div 配平
if len(re.findall(r"<div\b", s)) != len(re.findall(r"</div>", s)):
    errs.append("div 不配平")
if len(re.findall(r"<section\b", s)) != len(re.findall(r"</section>", s)):
    errs.append("section 不配平")

# 5 禁裸 null/None
if re.search(r"\bnull\b|\bNone\b", s):
    errs.append("出现裸 null/None")

# 6 class 白名单
cls = set(re.findall(r'class="([^"]*)"', s))
bad = cls - ALLOWED
if bad:
    errs.append("越界 class：%s" % sorted(bad))

# 7 片段约束：不得含 html/head/body/h1
for tag in ("<html", "<head", "<body", "<h1"):
    if tag in s.lower():
        errs.append("出现了 %s" % tag)

# 8 关键读数抽检（当日值在前）
for k in ("15.2（昨 11.0", "47（昨 39", "82（昨 41", "39.7%", "16745 亿（昨 15565", "5 板（001219"):
    if k not in s:
        errs.append("缺关键读数：%s" % k)

if errs:
    print("FAIL")
    for e in errs:
        print(" -", e)
    sys.exit(1)

print("h2=6 标题逐字匹配")
print("纯文本长度=%d（>=3200）" % len(txt))
print("div/section 配平；class 白名单通过；无 null/None；无 html/head/body/h1")
print("OK")
