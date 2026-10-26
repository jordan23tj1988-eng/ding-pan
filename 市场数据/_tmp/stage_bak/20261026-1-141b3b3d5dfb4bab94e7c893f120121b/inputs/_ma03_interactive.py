# -*- coding: utf-8 -*-
"""MA-20261023-03 交互表：炸板次数×执1（全样本 + 可成交子集）。
数据源：_学习/_ths_zt_pool.json（303日，open_num=炸板次数）；_学习/_bars_cache/<code>.csv（T+1开/T+1收/T+2收）。
口径：执1= T+1开盘买入→T+1收盘（A股T+1当日不可卖，逐日盯市）；
      可成交子集 = T+1开盘涨幅 < 涨停幅度-0.1pp（开盘未一字封死，可在集合竞价成交）。
"""
import json, os, csv, sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")
BC = os.path.join(L, "_bars_cache")

pool = json.load(open(os.path.join(L, "_ths_zt_pool.json"), encoding="utf-8"))
days = sorted(pool.keys())

def limit_pct(code):
    if code[:3] in ("300", "301", "688", "689"): return 20.0
    if code[0] in ("4", "8") or code.startswith("92"): return 30.0
    return 10.0

bars_cache = {}
def bars(code):
    if code in bars_cache: return bars_cache[code]
    p = os.path.join(BC, code + ".csv")
    out = []
    if os.path.isfile(p):
        with open(p, encoding="utf-8-sig") as f:
            r = csv.DictReader(f)
            for x in r:
                try:
                    out.append((x["date"], float(x["open"]), float(x["close"])))
                except Exception:
                    pass
    bars_cache[code] = out
    return out

buckets = [0,1,2,3,4,5,6]
stat = {b: {"n":0,"win":0,"sum":0.0,"kn":0,"kwin":0,"ksum":0.0,"kmiss":0} for b in buckets}
tot = {"n":0,"win":0,"sum":0.0,"kn":0,"kwin":0,"ksum":0.0}
cover = {"zt":0,"bar_ok":0,"fwd_ok":0}

for d in days:
    rows = pool[d]
    for r in rows:
        cover["zt"] += 1
        code = str(r["code"]).zfill(6)
        op = r.get("open_num")
        # 同花顺口径：未开板时 open_num 缺省(None)，出现次数=炸板次数
        b = 0 if op is None else (6 if int(op) >= 6 else int(op))
        bb = bars(code)
        if not bb: continue
        cover["bar_ok"] += 1
        idx = None
        for i, (dt, o, c) in enumerate(bb):
            if dt.replace("-", "") == d:
                idx = i; break
        if idx is None or idx + 1 >= len(bb): continue
        d1, o1, c1 = bb[idx+1]
        if idx + 2 < len(bb):
            d2, o2, c2 = bb[idx+2]
        else:
            d2 = None
        if o1 <= 0 or c1 <= 0: continue
        cover["fwd_ok"] += 1
        ret = (c1 / o1 - 1) * 100.0
        lp = limit_pct(code)
        open_pct = (o1 / bb[idx][2] - 1) * 100.0  # 相对T日收盘
        tradeable = open_pct < lp - 0.1
        s = stat[b]
        s["n"] += 1; s["sum"] += ret
        if ret > 0: s["win"] += 1
        tot["n"] += 1; tot["sum"] += ret
        if ret > 0: tot["win"] += 1
        if tradeable:
            s["kn"] += 1; s["ksum"] += ret
            if ret > 0: s["kwin"] += 1
            tot["kn"] += 1; tot["ksum"] += ret
            if ret > 0: tot["kwin"] += 1
        else:
            s["kmiss"] += 1

def pct(a, b): return round(100.0 * a / b, 1) if b else None
def avg(s, n): return round(s / n, 2) if n else None

print("覆盖:", cover, " 窗口:", days[0], "~", days[-1])
print("基准(全样本) n=%d 执1胜率=%s 均收=%s | 可成交 n=%d 胜率=%s 均收=%s" % (
    tot["n"], pct(tot["win"], tot["n"]), avg(tot["sum"], tot["n"]),
    tot["kn"], pct(tot["kwin"], tot["kn"]), avg(tot["ksum"], tot["kn"])))
table = []
for b in buckets:
    s = stat[b]
    row = {"炸板次数": b, "n": s["n"], "执1胜率": pct(s["win"], s["n"]), "执1均收": avg(s["sum"], s["n"]),
           "可成交子集n": s["kn"], "可成交胜率": pct(s["kwin"], s["kn"]), "可成交均收": avg(s["ksum"], s["kn"]),
           "不可成交(一字)_n": s["kmiss"]}
    table.append(row)
    print(row)

# 合并 炸<=3 (封板质量门) vs 炸>=5 (可成交正桶)
def merge(bs):
    n = sum(stat[b]["n"] for b in bs); w = sum(stat[b]["win"] for b in bs); sm = sum(stat[b]["sum"] for b in bs)
    kn = sum(stat[b]["kn"] for b in bs); kw = sum(stat[b]["kwin"] for b in bs); ks = sum(stat[b]["ksum"] for b in bs)
    return {"n": n, "胜率": pct(w, n), "均收": avg(sm, n), "可成交n": kn, "可成交胜率": pct(kw, kn), "可成交均收": avg(ks, kn)}
g1 = merge([0,1,2,3]); g2 = merge([4,5,6])
print("炸<=3(封板质量门):", g1)
print("炸>=4:", g2)
print("炸>=5:", merge([5,6]))

json.dump({"窗口": [days[0], days[-1]], "覆盖": cover, "基准": {
    "n": tot["n"], "执1胜率": pct(tot["win"], tot["n"]), "执1均收": avg(tot["sum"], tot["n"]),
    "可成交n": tot["kn"], "可成交胜率": pct(tot["kwin"], tot["kn"]), "可成交均收": avg(tot["ksum"], tot["kn"])},
    "table": table, "合并_炸LE3": g1, "合并_炸GE4": g2, "合并_炸GE5": merge([5,6])},
    open(os.path.join(L, "_ma03_table.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE _ma03_table.json")
