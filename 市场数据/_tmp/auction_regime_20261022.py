# -*- coding: utf-8 -*-
"""auction 20261022: regime 桶(崩盘日/跌停数/温度极寒)x高开档 —— 明日是否出手的A档依据。"""
import os, sys, json, importlib.util
BASE = r"D:\股票数据\市场数据"; L = os.path.join(BASE, "_学习")
spec = importlib.util.spec_from_file_location("bf", os.path.join(BASE, "竞价池分桶回填.py"))
bf = importlib.util.module_from_spec(spec); spec.loader.exec_module(bf)
ths = json.load(open(os.path.join(L, "_ths_zt_pool.json"), encoding="utf-8"))
wdt = json.load(open(os.path.join(L, "_市场温度表.json"), encoding="utf-8"))
days = sorted(ths.keys())
S = []
for di, d in enumerate(days[:-1]):
    dn = days[di+1]
    pool = bf.build_pool(ths[d])
    w = wdt.get(d) or {}
    nx = {x["code"] for x in ths.get(dn, [])}
    for t in pool:
        r = bf.settle(t["代码"], d, dn)
        if r is None: continue
        gk, ex, sg, mv = r
        fdb = round(t["封单额亿"]/mv*100, 2) if (mv and mv > 0) else None
        S.append(dict(d=d, code=t["代码"], lb=t["连板"], sig=t["信号"].split("·")[0], zha=t["炸板"],
                      fdb=fdb, wd=w.get("温度"), zt=w.get("涨停数"), dt=w.get("跌停数"),
                      gk=gk, ex=ex, sg=sg, seal=t["代码"] in nx))

def agg(rows):
    n = len(rows)
    if n == 0: return None
    ex = [r["ex"] for r in rows]
    return dict(n=n, 胜率=round(sum(1 for e in ex if e > 0)/n*100, 1), 均收=round(sum(ex)/n, 2),
                封板率=round(sum(1 for r in rows if r["seal"])/n*100, 1), 注=("小样本" if n < 25 else None))
def gk(r): return "低开≤0" if r["gk"] <= 0 else ("高开0~5" if r["gk"] < 5 else "高开≥5")

out = {}
# 崩盘日定义:T日 跌停数 >= 涨停数
crash = [r for r in S if r["dt"] is not None and r["zt"] is not None and r["dt"] >= r["zt"]]
out["A崩溃日_跌停≥涨停"] = dict(全桶=agg(crash), 天数=len({r["d"] for r in crash}),
    **{g: agg([r for r in crash if gk(r) == g]) for g in ("低开≤0", "高开0~5", "高开≥5")})
out["A崩溃日_按信号"] = {s: agg([r for r in crash if r["sig"] == s]) for s in ("一字", "秒板")}
out["A崩溃日_炸板二分"] = {"未炸": agg([r for r in crash if r["zha"] == 0]), "炸1+": agg([r for r in crash if r["zha"] >= 1])}
out["A崩溃日_薄封<0.5%"] = agg([r for r in crash if r["fdb"] is not None and r["fdb"] < 0.5])
out["A崩溃日_薄封<1.5%"] = agg([r for r in crash if r["fdb"] is not None and r["fdb"] < 1.5])
out["A崩溃日_薄封<1.5%x高开档"] = {g: agg([r for r in crash if r["fdb"] is not None and r["fdb"] < 1.5 and gk(r) == g]) for g in ("低开≤0", "高开0~5", "高开≥5")}
# 跌停数分档
def dtb(r):
    dt = r["dt"]
    if dt is None: return None
    return "dt<10" if dt < 10 else ("dt10~29" if dt < 30 else "dt≥30")
out["B跌停数分档"] = {b: agg([r for r in S if dtb(r) == b]) for b in ("dt<10", "dt10~29", "dt≥30")}
out["B跌停≥30x高开档"] = {g: agg([r for r in S if dtb(r) == "dt≥30" and gk(r) == g]) for g in ("低开≤0", "高开0~5", "高开≥5")}
out["B跌停≥30_天数列"] = sorted({r["d"] for r in S if dtb(r) == "dt≥30"})
out["B跌停10~29x高开档"] = {g: agg([r for r in S if dtb(r) == "dt10~29" and gk(r) == g]) for g in ("低开≤0", "高开0~5", "高开≥5")}
# 极寒<20 按信号/连板
hz = [r for r in S if r["wd"] is not None and r["wd"] < 20]
out["C极寒<20_按信号"] = {s: agg([r for r in hz if r["sig"] == s]) for s in ("一字", "秒板")}
out["C极寒<20_按连板"] = {b: agg([r for r in hz if (("首板" if r["lb"] == 1 else ("2板" if r["lb"] == 2 else "3板+"))) == b]) for b in ("首板", "2板", "3板+")}
out["极寒天数"] = len({r["d"] for r in hz})
json.dump(out, open(os.path.join(L, "子agent增强", "auction_regime_20261022.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in out.items():
    if isinstance(v, dict) and "n" not in v:
        print("##", k)
        for kk, vv in v.items():
            print("   ", kk, "=", (("n=%d 胜%.1f%% 均%.2f%% 封%.1f%%" % (vv["n"], vv["胜率"], vv["均收"], vv["封板率"])) if isinstance(vv, dict) and "n" in vv else vv))
    else:
        print("##", k, "=", (("n=%d 胜%.1f%% 均%.2f%% 封%.1f%%" % (v["n"], v["胜率"], v["均收"], v["封板率"])) if isinstance(v, dict) else v))
