# -*- coding: utf-8 -*-
"""极寒<20 × 跌停≥30 二维交叉:今日两者同时成立,必须看交集而不是各自边际。"""
import os, sys, json, importlib.util
BASE = r"D:\股票数据\市场数据"; L = os.path.join(BASE, "_学习")
spec = importlib.util.spec_from_file_location("bf", os.path.join(BASE, "竞价池分桶回填.py"))
bf = importlib.util.module_from_spec(spec); spec.loader.exec_module(bf)
ths = json.load(open(os.path.join(L, "_ths_zt_pool.json"), encoding="utf-8"))
wdt = json.load(open(os.path.join(L, "_市场温度表.json"), encoding="utf-8"))
days = sorted(ths.keys()); S = []
for di, d in enumerate(days[:-1]):
    dn = days[di+1]; pool = bf.build_pool(ths[d]); w = wdt.get(d) or {}
    nx = {x["code"] for x in ths.get(dn, [])}
    for t in pool:
        r = bf.settle(t["代码"], d, dn)
        if r is None: continue
        gk, ex, sg, mv = r
        S.append(dict(d=d, lb=t["连板"], sig=t["信号"].split("·")[0], zha=t["炸板"],
                      fdb=(round(t["封单额亿"]/mv*100, 2) if (mv and mv > 0) else None),
                      wd=w.get("温度"), dt=w.get("跌停数"), gk=gk, ex=ex, seal=t["代码"] in nx))
def agg(rows):
    n = len(rows)
    if n == 0: return None
    ex = [r["ex"] for r in rows]
    return dict(n=n, 胜率=round(sum(1 for e in ex if e > 0)/n*100, 1), 均收=round(sum(ex)/n, 2),
                封板率=round(sum(1 for r in rows if r["seal"])/n*100, 1), 注=("小样本" if n < 25 else None))
def gk(r): return "低开≤0" if r["gk"] <= 0 else ("高开0~5" if r["gk"] < 5 else "高开≥5")
def cell(r):
    a = "极寒" if (r["wd"] is not None and r["wd"] < 20) else "非极寒"
    b = "跌停≥30" if (r["dt"] is not None and r["dt"] >= 30) else "跌停<30"
    return a+"|"+b
out = {}
for c in ("极寒|跌停≥30", "极寒|跌停<30", "非极寒|跌停≥30", "非极寒|跌停<30"):
    rows = [r for r in S if cell(r) == c]
    out[c] = dict(全桶=agg(rows), 天数=len({r["d"] for r in rows}),
                  **{g: agg([r for r in rows if gk(r) == g]) for g in ("低开≤0", "高开0~5", "高开≥5")},
                  **{"炸1+": agg([r for r in rows if r["zha"] >= 1]), "未炸": agg([r for r in rows if r["zha"] == 0])})
# 交集日的具体日期与逐日
rows = [r for r in S if cell(r) == "极寒|跌停≥30"]
byd = {}
for r in rows: byd.setdefault(r["d"], []).append(r["ex"])
out["交集_逐日"] = {d: dict(n=len(v), 均收=round(sum(v)/len(v), 2)) for d, v in sorted(byd.items())}
json.dump(out, open(os.path.join(L, "子agent增强", "auction_2x2_20261022.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in out.items():
    if "n" in v: print("##", k, v); continue
    if k == "交集_逐日": print("##", k, json.dumps(v, ensure_ascii=False)); continue
    print("##", k, "天数=", v["天数"])
    for kk, vv in v.items():
        if kk == "天数": continue
        print("   ", kk, "=", ("n=%d 胜%.1f%% 均%.2f%% 封%.1f%%" % (vv["n"], vv["胜率"], vv["均收"], vv["封板率"])) if isinstance(vv, dict) and "n" in vv else vv)
