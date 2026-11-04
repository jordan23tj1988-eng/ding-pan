# -*- coding: utf-8 -*-
"""临时: 复用 竞价池分桶回填 的零后视镜口径, 重建逐票样本并算今日所需细胞。"""
import os, sys, json, importlib.util
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
spec = importlib.util.spec_from_file_location("bf", os.path.join(BASE, "竞价池分桶回填.py"))
bf = importlib.util.module_from_spec(spec); spec.loader.exec_module(bf)
L = os.path.join(BASE, "_学习")
CACHE = os.path.join(L, "_竞价池样本_auction.json")

if os.path.isfile(CACHE):
    S = json.load(open(CACHE, encoding="utf-8"))
else:
    ths = json.load(open(os.path.join(L, "_ths_zt_pool.json"), encoding="utf-8"))
    wdt = json.load(open(os.path.join(L, "_市场温度表.json"), encoding="utf-8"))
    days = sorted(ths.keys()); S = []; miss = 0; tot = 0
    for di, d in enumerate(days[:-1]):
        dn = days[di + 1]; pool = bf.build_pool(ths[d]); tot += len(pool)
        wd = (wdt.get(d) or {}).get("温度")
        nx = {x["code"] for x in ths.get(dn, [])}
        for t in pool:
            r = bf.settle(t["代码"], d, dn)
            if r is None: miss += 1; continue
            gk, ex, sg, mv = r
            fdb = round(t["封单额亿"] / mv * 100, 2) if (mv and mv > 0) else None
            S.append(dict(日=d, 代码=t["代码"], 名称=t.get("名称"), 信号=t["信号"].split("·")[0],
                          连板=t["连板"], 炸板=t["炸板"], 封单比=fdb, 温度=wd,
                          T1高开=gk, 执行=ex, 信号收益=sg, 次日封板=t["代码"] in nx))
    json.dump(S, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
print("样本", len(S))


def agg(sel, name, verbose=True):
    s = [x for x in S if sel(x)]
    n = len(s)
    if not n:
        if verbose: print("%-58s n=0" % name)
        return None
    ex = [x["执行"] for x in s]
    win = sum(1 for e in ex if e > 0)
    d = dict(n=n, 胜率=round(100 * win / n, 1), 均收=round(sum(ex) / n, 2),
             封板率=round(100 * sum(1 for x in s if x["次日封板"]) / n, 1))
    if verbose:
        print("%-58s n=%-4d 胜%5.1f%% 均%+6.2f%% 封%5.1f%%%s"
              % (name, n, d["胜率"], d["均收"], d["封板率"], "  <小样本" if n < 25 else ""))
    return d


def wt(s):
    v = s.get("温度")
    return -1 if v is None else v


def gkb(g): return "低开≤0" if g <= 0 else ("高开0~5" if g < 5 else "高开≥5")
def fdb(f): return "<0.5" if f < 0.5 else ("0.5~1.5" if f < 1.5 else ("1.5~4" if f < 4 else "≥4"))

print("\n== 池基线 ==")
agg(lambda s: True, "全样本")
agg(lambda s: 40 <= wt(s) < 65, "温度 中40~65")
agg(lambda s: 40 <= wt(s) < 65 and s["信号"] == "秒板", "中40~65 | 秒板")
agg(lambda s: 40 <= wt(s) < 65 and s["信号"] == "一字", "中40~65 | 一字")

print("\n== 今日两票所在格(605577 秒板3板薄封炸4 / 002088 秒板2板薄封炸2) ==")
agg(lambda s: s["信号"] == "秒板" and s["连板"] >= 3 and s["封单比"] is not None and s["封单比"] < 0.5,
    "秒板|3板+|封<0.5")
agg(lambda s: s["信号"] == "秒板" and s["连板"] >= 3 and s["封单比"] is not None and s["封单比"] < 0.5 and s["炸板"] >= 1,
    "秒板|3板+|封<0.5|炸1+")
agg(lambda s: s["信号"] == "秒板" and s["连板"] == 2 and s["封单比"] is not None and s["封单比"] < 0.5,
    "秒板|2板|封<0.5")
agg(lambda s: s["信号"] == "秒板" and s["连板"] == 2 and s["封单比"] is not None and s["封单比"] < 0.5 and s["炸板"] >= 1,
    "秒板|2板|封<0.5|炸1+")
agg(lambda s: s["信号"] == "秒板" and s["封单比"] is not None and s["封单比"] < 0.5 and s["炸板"] >= 3,
    "秒板|封<0.5|炸3+")
agg(lambda s: s["信号"] == "秒板" and s["封单比"] is not None and s["封单比"] < 0.5,
    "秒板|封<0.5")
for cellname, sel in [
    ("秒板3板+薄封", lambda s: s["信号"] == "秒板" and s["连板"] >= 3 and s["封单比"] is not None and s["封单比"] < 0.5),
    ("秒板2板薄封", lambda s: s["信号"] == "秒板" and s["连板"] == 2 and s["封单比"] is not None and s["封单比"] < 0.5),
]:
    print("  -- %s 按 gap 带:" % cellname)
    for band in ("低开≤0", "高开0~5", "高开≥5"):
        agg(lambda s, sel=sel, band=band: sel(s) and gkb(s["T1高开"]) == band, "     %s|%s" % (cellname, band))

print("\n== 温度中40~65 条件化 ==")
for nm, sel in [
    ("中|秒板|封<0.5", lambda s: 40 <= wt(s) < 65 and s["信号"] == "秒板" and s["封单比"] is not None and s["封单比"] < 0.5),
    ("中|秒板|封<0.5|gap0~5", lambda s: 40 <= wt(s) < 65 and s["信号"] == "秒板" and s["封单比"] is not None and s["封单比"] < 0.5 and 0 < s["T1高开"] < 5),
    ("中|秒板|封<0.5|gap≤0", lambda s: 40 <= wt(s) < 65 and s["信号"] == "秒板" and s["封单比"] is not None and s["封单比"] < 0.5 and s["T1高开"] <= 0),
    ("中|秒板|3板+|gap0~5", lambda s: 40 <= wt(s) < 65 and s["信号"] == "秒板" and s["连板"] >= 3 and 0 < s["T1高开"] < 5),
    ("中|一字|gap0~5", lambda s: 40 <= wt(s) < 65 and s["信号"] == "一字" and 0 < s["T1高开"] < 5),
    ("中|一字|封≥4", lambda s: 40 <= wt(s) < 65 and s["信号"] == "一字" and s["封单比"] is not None and s["封单比"] >= 4),
    ("中|炸1+|gap0~5", lambda s: 40 <= wt(s) < 65 and s["炸板"] >= 1 and 0 < s["T1高开"] < 5),
]:
    agg(sel, nm)

print("\n== 今日池 10 只逐票 gap 带期望 ==")
pool = json.load(open(os.path.join(L, "竞价池发出_20261104.json"), encoding="utf-8"))["池"]
for p in pool:
    lb = p["连板"]; f = p["封单比"]; sig = p["信号"].split("·")[0]; zh = p["炸板"]
    base = lambda s, sig=sig, lb=lb: s["信号"] == sig and ((s["连板"] >= 3) if lb >= 3 else (s["连板"] == lb))
    sub = [s for s in S if base(s)]
    n = len(sub); w = sum(1 for s in sub if s["执行"] > 0); m = sum(s["执行"] for s in sub) / n if n else 0
    line = "%s %-6s %-8s 封%.2f%% 炸%d  信号x连板 n=%d 胜%.1f%% 均%+.2f%%" % (
        p["代码"], p["名称"], p["信号"], f, zh, n, 100 * w / n if n else 0, m)
    print(line)
    for band in ("低开≤0", "高开0~5", "高开≥5"):
        sub2 = [s for s in sub if gkb(s["T1高开"]) == band]
        if sub2:
            w2 = sum(1 for s in sub2 if s["执行"] > 0)
            print("      %-8s n=%-4d 胜%5.1f%% 均%+6.2f%%" % (band, len(sub2), 100 * w2 / len(sub2), sum(s["执行"] for s in sub2) / len(sub2)))
        else:
            print("      %-8s n=0" % band)
