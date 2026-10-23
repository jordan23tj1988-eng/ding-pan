# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
recs = json.load(open(os.path.join(L, "_tmp_cold_recs.json"), encoding="utf-8"))

def stats(xs, base=None):
    if not xs: return dict(n=0)
    m = sum(x["e1"] for x in xs)/len(xs)
    w = 100*sum(1 for x in xs if x["e1"] > 0)/len(xs)
    d = dict(n=len(xs), mean=round(m, 3), win=round(w, 1))
    if base is not None: d["ex"] = round(m-base, 3)
    return d

def run(tag, rs):
    allm = sum(r["e1"] for r in rs)/len(rs)
    tr = [r for r in rs if r["tradeable"]]
    trm = sum(r["e1"] for r in tr)/len(tr)
    print("\n### %s  天数=%d 全池n=%d 全池均%.3f%% | 可成交n=%d 均%.3f%%" % (tag, len(set(r['d'] for r in rs)), len(rs), allm, len(tr), trm))
    defs = [("①薄封<0.5%×换手3-10%", lambda r: r["seal"] < 0.5 and 3 <= r["to"] <= 10),
            ("②强封≥4%×炸0", lambda r: r["seal"] >= 4 and r["zb"] == 0),
            ("③首封>14:30×首板", lambda r: r["ft"] > "143000" and r["lb"] == 1)]
    for nm, fn in defs:
        a = [r for r in rs if fn(r)]
        b = [r for r in a if r["tradeable"]]
        sa, sb = stats(a, allm), stats(b, trm)
        print("%-24s 全池 n=%3d 均%+.3f%% 超额%+.3fpp 胜率%.1f%% | 剔%2d 可成交 n=%3d 均%+.3f%% 超额%+.3fpp 胜率%.1f%%" % (
            nm, sa["n"], sa["mean"], sa["ex"], sa["win"], sa["n"]-sb["n"], sb["n"], sb["mean"], sb["ex"], sb["win"]))

# 19日口径（信号日 <= 20261021）复核昨日数字
run("复核:窗口至20261021", [r for r in recs if r["d"] <= "20261021"])
run("主口径:窗口至20261022", recs)

# 逐日为正次数（复合桶① vs 当日可成交基准）
print("\n### ① 逐日超额为正的冰点日数")
days = sorted(set(r["d"] for r in recs))
pos = 0; tot = 0
for d in days:
    dd = [r for r in recs if r["d"] == d]
    tb = [r for r in dd if r["tradeable"]]
    if not tb: continue
    base = sum(r["e1"] for r in tb)/len(tb)
    a = [r for r in tb if r["seal"] < 0.5 and 3 <= r["to"] <= 10]
    if not a: continue
    m = sum(r["e1"] for r in a)/len(a)
    tot += 1
    if m > base: pos += 1
    print("  %s n=%2d 桶均%+.2f%% 基准%+.2f%% 超额%+.2fpp" % (d, len(a), m, base, m-base))
print("为正 %d/%d" % (pos, tot))

# 003021 口径：更窄的邻近格
print("\n### 003021 邻近格（可成交口径）")
allm = sum(r["e1"] for r in recs)/len(recs)
tr = [r for r in recs if r["tradeable"]]; trm = sum(r["e1"] for r in tr)/len(tr)
for nm, fn in [("封单<0.5%×换手3-5%", lambda r: r["seal"] < 0.5 and 3 <= r["to"] <= 5),
               ("封单0.2-0.5%×换手3-10%", lambda r: 0.2 <= r["seal"] < 0.5 and 3 <= r["to"] <= 10),
               ("封单<0.5%×换手3-10%×首板", lambda r: r["seal"] < 0.5 and 3 <= r["to"] <= 10 and r["lb"] == 1),
               ("封单<0.5%×换手3-10%×炸≥2", lambda r: r["seal"] < 0.5 and 3 <= r["to"] <= 10 and r["zb"] >= 2),
               ("封单<0.5%×换手3-10%×炸0", lambda r: r["seal"] < 0.5 and 3 <= r["to"] <= 10 and r["zb"] == 0),
               ("封单<0.5%×换手<3%", lambda r: r["seal"] < 0.5 and r["to"] < 3),
               ("封单<0.5%×换手10-20%", lambda r: r["seal"] < 0.5 and 10 <= r["to"] <= 20)]:
    a = [r for r in tr if fn(r)]
    s = stats(a, trm)
    if s["n"]:
        print("  %-26s n=%3d 均%+.3f%% 超额%+.3fpp 胜率%.1f%%" % (nm, s["n"], s["mean"], s["ex"], s["win"]))
    else:
        print("  %-26s n=0" % nm)
