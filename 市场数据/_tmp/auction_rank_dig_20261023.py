# -*- coding: utf-8 -*-
"""MA/孵化:925竞价额排名 从C档转A档首读 —— 42个存档日(20260713~20261023),
执行日=T+1;排名/分位取 T+1 09:26 快照(≤09:30红线内=A档),收益=T+1开→T+1收。
全部输入在09:25可知 ⇒ 因果合法,非后视镜。"""
import os, json, gzip, csv, glob
import importlib.util
B = r"D:/股票数据/市场数据"; L = B + "/_学习"; SD = L + "/竞价快照存档"
spec = importlib.util.spec_from_file_location("bf", B + "/竞价池分桶回填.py")
bf = importlib.util.module_from_spec(spec); spec.loader.exec_module(bf)

ths = json.load(open(L + "/_ths_zt_pool.json", encoding="utf-8"))
wdt = json.load(open(L + "/_市场温度表.json", encoding="utf-8"))
days = sorted(ths.keys())
snapdays = sorted(os.path.basename(p)[:8] for p in glob.glob(SD + "/*.csv.gz"))
metas = {}
for d in snapdays:
    try:
        m = json.load(open(f"{SD}/{d}_meta.json", encoding="utf-8"))
        metas[d] = m
    except Exception:
        metas[d] = None
bad = [d for d in snapdays if not metas.get(d) or metas[d].get("状态") != "成功" or (metas[d].get("采集时间") or "99:99") > "09:30"]
print("快照日", len(snapdays), "污染/失败", bad)
good = [d for d in snapdays if d not in bad]

CACHE = {}
def load_snap(d):
    if d in CACHE: return CACHE[d]
    o = {}
    with gzip.open(f"{SD}/{d}.csv.gz", "rt", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try: o[r["代码"]] = (int(r["竞价额排名"] or 0), float(r["成交额"] or 0))
            except Exception: pass
    CACHE[d] = o
    return o

S = []
for di, d in enumerate(days[:-1]):
    dn = days[di + 1]
    if dn not in good:   # 执行日必须有快照
        continue
    sn = load_snap(dn)
    tot = len(sn)
    pool = bf.build_pool(ths[d])
    for t in pool:
        b = bf.bars(t["代码"])
        if b is None: continue
        idx = b.index[b['date'] == d]
        if not len(idx): continue
        i = idx[0]
        if i + 1 >= len(b) or str(b.loc[i + 1, 'date']) != dn: continue
        o1, c1 = float(b.loc[i + 1, 'open']), float(b.loc[i + 1, 'close'])
        Tc = float(b.loc[i, 'close'])
        gap = round((o1 / Tc - 1) * 100, 2); ex = round((c1 / o1 - 1) * 100, 2)
        rk, amt = sn.get(t["代码"], (None, None))
        pct = round(rk / tot * 100, 2) if rk else None
        S.append(dict(日=d, 执行日=dn, 代码=t["代码"], 排名=rk, 分位=pct, 竞价额亿=round((amt or 0) / 1e8, 3),
                      高开=gap, 执行=ex, 温度=(wdt.get(d) or {}).get("温度")))
print("可用样本", len(S), "执行日数", len({x["执行日"] for x in S}))


def agg(s):
    if not s: return "n=0"
    ex = [x["执行"] for x in s]
    return f"n={len(s):4d} 胜率{sum(1 for e in ex if e>0)/len(ex)*100:5.1f}% 均收{sum(ex)/len(ex):+6.2f}% 中位{sorted(ex)[len(ex)//2]:+6.2f}%"


print("\n== 按 925竞价额排名分位 (全样本) ==")
for lo, hi, nm in [(0, 1, "前1%"), (1, 5, "1~5%"), (5, 10, "5~10%"), (10, 20, "10~20%"), (20, 50, "20~50%"), (50, 101, "后50%")]:
    print(f"{nm:8s}", agg([x for x in S if x["分位"] is not None and lo <= x["分位"] < hi]))

print("\n== 控制高开档后(闸门内 gap<5) ==")
G = [x for x in S if x["高开"] < 5]
for lo, hi, nm in [(0, 1, "前1%"), (1, 5, "1~5%"), (5, 10, "5~10%"), (10, 20, "10~20%"), (20, 50, "20~50%"), (50, 101, "后50%")]:
    print(f"gap<5 {nm:8s}", agg([x for x in G if x["分位"] is not None and lo <= x["分位"] < hi]))

print("\n== 二分位 前20% vs 后80%, 分高开档 ==")
for g0, g1, nm in [(-99, 0, "低开≤0"), (0, 5, "0~5"), (5, 999, "≥5")]:
    sub = [x for x in S if x["分位"] is not None and g0 <= x["高开"] < g1]
    print(f"{nm:8s} 前20%", agg([x for x in sub if x["分位"] < 20]), " | 后80%", agg([x for x in sub if x["分位"] >= 20]))

print("\n== 竞价额绝对额档(池票) ==")
for lo, hi, nm in [(0, 0.05, "<500万"), (0.05, 0.2, "500万~2千万"), (0.2, 0.5, "2千万~5千万"), (0.5, 1, "5千万~1亿"), (1, 999, "≥1亿")]:
    print(f"{nm:12s}", agg([x for x in S if x["竞价额亿"] is not None and lo <= x["竞价额亿"] < hi]))

print("\n== 本池今日(20261023)7只的925读数(执行日=20261024) ==")
sn = load_snap("20261023"); tot = len(sn)
for c in ["002474", "002535", "603280", "600838", "603933", "603028", "002982"]:
    rk, amt = sn.get(c, (None, None))
    print(c, "排名", rk, f"分位{round(rk/tot*100,2) if rk else None}%", "竞价额亿", round((amt or 0) / 1e8, 3))
json.dump(S, open(B + "/_tmp/auction_rank_samples.json", "w", encoding="utf-8"), ensure_ascii=False)
