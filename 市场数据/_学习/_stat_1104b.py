# -*- coding: utf-8 -*-
"""零后视镜：20260615~20261104 本地 zt_pool 逐日，算连板晋级/收红率。"""
import os, csv, json, statistics as st
root = r"D:/股票数据/市场数据"
days = sorted([d for d in os.listdir(root) if d.isdigit() and len(d) == 8 and os.path.isdir(os.path.join(root, d)) and os.path.exists(os.path.join(root, d, "zt_pool.csv"))])
days = [d for d in days if d <= "20261104"]
print("池日", len(days), days[0], days[-1])

def load(d, fn):
    p = os.path.join(root, d, fn)
    if not os.path.exists(p): return []
    rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    return rows

def load_bars(code):
    p = os.path.join(root, "_学习/_bars_cache", code + ".csv")
    if not os.path.exists(p): return {}
    b = {}
    for r in csv.DictReader(open(p, encoding="utf-8")):
        try: b[r["date"]] = (float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]))
        except: pass
    return b

pools = {d: load(d, "zt_pool.csv") for d in days}
# 连板晋级率 by k
from collections import defaultdict
tot = defaultdict(int); seal = defaultdict(int); seal4 = defaultdict(int)
for i in range(len(days)-1):
    d, d2 = days[i], days[i+1]
    s2 = set(r["代码"] for r in pools[d2])
    for r in pools[d]:
        try: k = int(float(r["连板数"]))
        except: continue
        tot[k] += 1
        if r["代码"] in s2: seal[k] += 1
print("="*20, "连板数 -> 次日封板率")
for k in sorted(tot):
    if tot[k] >= 10:
        print("  %d板 n=%4d 封板 %3d = %.1f%%" % (k, tot[k], seal[k], seal[k]/tot[k]*100))

# 3板及以上的次日收红率（bars 开→收 / 收→收）
def nextbar(code, d):
    b = load_bars(code)
    if d not in b: return None, b
    ks = [x for x in sorted(b) if x > "%s-%s-%s" % (d[:4], d[4:6], d[6:])]
    return (b[ks[0]] if ks else None), b

print("="*20, "今日(20261104)各票 次日不可知，仅统计历史格")
# 历史格：2板 & 末封>=1400 & 换手3-10 → 次日封板/执1
def hm(t):
    t = (t or "").strip()
    if len(t) != 6 or not t.isdigit(): return None
    return int(t[:2])*60 + int(t[2:4])
stat = defaultdict(lambda: {"n":0,"seal":0,"red":0,"r1":[]})
for i in range(len(days)-1):
    d, d2 = days[i], days[i+1]
    s2 = set(r["代码"] for r in pools[d2])
    for r in pools[d]:
        try:
            k = int(float(r["连板数"])); to = float(r["换手率"]); zha = int(float(r["炸板次数"]))
        except: continue
        last = hm(r.get("最后封板时间"))
        if last is None: continue
        tags = []
        if k == 2 and last >= 840 and 3 <= to < 10: tags.append("2板&尾盘&换手3-10")
        if k == 1 and last >= 840 and 10 <= to < 20: tags.append("首板&尾盘&换手10-20")
        if k == 1 and last >= 840: tags.append("首板&尾盘")
        if k == 3: tags.append("3板")
        if k == 3 and r.get("所属行业","").startswith(("出版","影视","文媒","文化")): tags.append("3板&传媒")
        for t in tags:
            s = stat[t]; s["n"] += 1
            if r["代码"] in s2: s["seal"] += 1
            nb, b = nextbar(r["代码"], d)
            ds = "%s-%s-%s" % (d[:4], d[4:6], d[6:])
            if nb and ds in b:
                o, c = b[ds][0], b[ds][3]
                if c > o: s["red"] += 1
                s["r1"].append((c/o-1)*100)
for t, s in stat.items():
    if s["n"] >= 5:
        r1 = s["r1"]
        print("  %-22s n=%4d 次日封板 %3d=%.1f%% 收红(开→收) %3d/%d=%.1f%% 执1均 %+.3f%%" % (
            t, s["n"], s["seal"], s["seal"]/s["n"]*100, s["red"], len(r1), (s["red"]/len(r1)*100 if r1 else 0), (st.mean(r1) if r1 else 0)))
