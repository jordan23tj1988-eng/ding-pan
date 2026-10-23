# -*- coding: utf-8 -*-
import os, csv, json
B = r"D:/股票数据/市场数据"
L = os.path.join(B, "_学习")
BC = os.path.join(L, "_bars_cache")

temp = json.load(open(os.path.join(L, "_市场温度表.json"), encoding="utf-8"))
dirs = sorted([d for d in os.listdir(B) if d.isdigit() and len(d) == 8 and "20260615" <= d <= "20261022"])

bars_cache = {}
def bars(code):
    if code in bars_cache:
        return bars_cache[code]
    p = os.path.join(BC, code + ".csv")
    rows = []
    if os.path.exists(p):
        rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    bars_cache[code] = rows
    return rows

recs = []
missing_bar = 0
for d in dirs:
    t = temp.get(d, {}).get("温度")
    if t is None or t >= 25:
        continue
    p = os.path.join(B, d, "zt_pool.csv")
    rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    for r in rows:
        code = r["代码"]
        try:
            amt = float(r["封板资金"]); cmv = float(r["流通市值"]); to = float(r["换手率"])
            ft = str(r["首次封板时间"]).zfill(6)
            zb = int(float(r["炸板次数"])); lb = int(float(r["连板数"]))
        except Exception:
            continue
        if cmv <= 0:
            continue
        bs = bars(code)
        idx = {b["date"].replace("-", ""): b for b in bs}
        if d not in idx:
            missing_bar += 1
            continue
        ds = sorted(idx.keys())
        i = ds.index(d)
        if i + 1 >= len(ds):
            continue  # no T+1
        b0, b1 = idx[ds[i]], idx[ds[i+1]]
        b2 = idx[ds[i+2]] if i + 2 < len(ds) else None
        c0 = float(b0["close"]); o1 = float(b1["open"]); h1 = float(b1["high"]); l1 = float(b1["low"]); c1 = float(b1["close"])
        if o1 <= 0 or c0 <= 0:
            continue
        gap = (o1 / c0 - 1) * 100
        e1 = (c1 / o1 - 1) * 100
        e2 = (float(b2["close"]) / o1 - 1) * 100 if b2 else None
        yizi = (abs(h1 - l1) < 1e-9 and abs(o1 - h1) < 1e-9)
        open_seal = (gap >= 9.5 and abs(o1 - h1) < 1e-9)
        tradeable = not (yizi or open_seal)
        recs.append(dict(d=d, code=code, name=r["名称"], seal=amt / cmv * 100, to=to,
                         ft=ft, zb=zb, lb=lb, gap=gap, e1=e1, e2=e2,
                         yizi=yizi, open_seal=open_seal, tradeable=tradeable,
                         ind=r.get("所属行业", "")))

print("冰点样本(信号日<=20261022):", len(recs), "缺bar:", missing_bar)
days = sorted(set(r["d"] for r in recs))
print("冰点日数:", len(days))
print("不可成交:", sum(1 for r in recs if not r["tradeable"]), "=%.1f%%" % (100*sum(1 for r in recs if not r['tradeable'])/len(recs)))
allm = sum(r["e1"] for r in recs)/len(recs)
tr = [r for r in recs if r["tradeable"]]
trm = sum(r["e1"] for r in tr)/len(tr)
print("全池执1均 %.3f%% 胜率 %.1f%%" % (allm, 100*sum(1 for r in recs if r['e1']>0)/len(recs)))
print("可成交执1均 %.3f%% 胜率 %.1f%% n=%d" % (trm, 100*sum(1 for r in tr if r['e1']>0)/len(tr), len(tr)))

def cell(name, fn, base_all, base_tr):
    a = [r for r in recs if fn(r)]
    b = [r for r in a if r["tradeable"]]
    if not a:
        print(name, "EMPTY"); return
    def st(xs, base):
        if not xs: return (0, None, None)
        m = sum(x["e1"] for x in xs)/len(xs)
        w = 100*sum(1 for x in xs if x["e1"] > 0)/len(xs)
        return (len(xs), m, m-base, w)
    n1, m1, x1, w1 = st(a, base_all)
    n2, m2, x2, w2 = st(b, base_tr)
    print("%-34s 全池 n=%4d 均%+.3f%% 超额%+.3fpp 胜率%.1f%% | 剔除%3d 可成交 n=%4d 均%+.3f%% 超额%+.3fpp 胜率%.1f%%" %
          (name, n1, m1, x1, w1, n1-n2, n2, (m2 if m2 is not None else 0), (x2 if x2 is not None else 0), (w2 or 0)))

print("\n--- MA-20261022-01 三格 ---")
cell("①封单<0.5%×换手3-10%", lambda r: r["seal"] < 0.5 and 3 <= r["to"] <= 10, allm, trm)
cell("②封单≥4%×炸0", lambda r: r["seal"] >= 4 and r["zb"] == 0, allm, trm)
cell("③首封>14:30×首板", lambda r: r["ft"] > "143000" and r["lb"] == 1, allm, trm)

print("\n--- 单维复核（对齐昨日 19日口径需另算）---")
for nm, fn in [("封单<0.5%", lambda r: r["seal"] < 0.5),
               ("封单≥4%", lambda r: r["seal"] >= 4),
               ("换手3-10%", lambda r: 3 <= r["to"] <= 10),
               ("换手<3%", lambda r: r["to"] < 3),
               ("首封>14:30", lambda r: r["ft"] > "143000"),
               ("炸0", lambda r: r["zb"] == 0),
               ("首板", lambda r: r["lb"] == 1)]:
    cell("  " + nm, fn, allm, trm)

json.dump(recs, open(os.path.join(L, "_tmp_cold_recs.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("\nsaved recs")
