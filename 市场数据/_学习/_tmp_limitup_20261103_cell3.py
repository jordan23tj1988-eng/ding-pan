# -*- coding: utf-8 -*-
import sys, os, json
sys.path.insert(0, r"D:/股票数据/市场数据")
import 涨停质量训练 as M
import pandas as pd
P = M._factor_table(); D = M._enrich(P).copy()
D['E1'] = D['E1'] * 100; D['E2'] = D['E2'] * 100
D['温度b'] = pd.to_numeric(D['温度'], errors='coerce')
out = {}
def cell(mask, name):
    x = D[mask]; e1 = x['E1'].dropna(); e2 = x['E2'].dropna(); gaps = []
    for _, r in x.iterrows():
        b = M._bars(r['代码'])
        if b is None: continue
        idx = b.index[b['date'] == r['日']]
        if not len(idx): continue
        i = idx[0]
        if i + 1 >= len(b): continue
        tc = float(b.loc[i, 'close']); o1 = float(b.loc[i + 1, 'open'])
        if tc > 0 and o1 > 0: gaps.append((o1 / tc - 1) * 100)
    s = pd.Series(gaps)
    out[name] = dict(n=int(len(x)),
        执1=("%.1f%%/%+.2f%%" % ((e1 > 0).mean() * 100, e1.mean())) if len(e1) else None,
        执2=("%.1f%%/%+.2f%%" % ((e2 > 0).mean() * 100, e2.mean())) if len(e2) else None,
        gap中位=round(float(s.median()), 2) if len(s) else None,
        gap_gt3=round(float((s > 3).mean() * 100), 1) if len(s) else None,
        触发15=round(float(((s > -3) & (s <= 1.5)).mean() * 100), 1) if len(s) else None)
IC = (D['温度b'] < 25)
cell(IC & (D['连板'] >= 4) & (D['换手'] >= 20) & (D['开板'] >= 2), "冰点×4板+×换手≥20×开2+(600261)")
cell(IC & (D['连板'] >= 4) & (D['换手'] >= 20) & (D['封单比'] >= 2), "冰点×4板+×换手≥20×封单≥2%")
cell(IC & (D['首封'] >= '14:00') & (D['连板'] == 1) & (D['换手'] >= 10), "冰点×尾盘×首板×换手≥10")
cell(IC & (D['首封'] >= '14:00') & (D['连板'] == 1) & (D['封单比'] < 2), "冰点×尾盘×首板×封单<2%")
cell(IC & (D['连板'] == 1) & (D['换手'] >= 15) & (D['换手'] < 20), "冰点×首板×换手15-20%")
cell(IC & (D['连板'] == 1) & (D['开板'] == 0), "冰点×首板×未开板")
cell(IC & (D['连板'] == 1) & (D['开板'] >= 2), "冰点×首板×开2+")
cell((D['温度b'] >= 25) & (D['温度b'] < 45) & (D['连板'] >= 4), "偏冷25-45×4板+(对照)")
cell(IC & (D['连板'] >= 2), "冰点×2板+(全体连板)")
print(json.dumps(out, ensure_ascii=False, indent=1))
# 今日尾盘首板清单
import csv, io
zt = list(csv.DictReader(io.open(r"D:/股票数据/市场数据/20261103/zt_pool.csv", encoding="utf-8-sig")))
late = [(r["代码"], r["名称"], r["首次封板时间"], r["连板数"], r["封板资金"], r["流通市值"]) for r in zt if r["首次封板时间"] >= "140000"]
print("尾盘首封名单", json.dumps(late, ensure_ascii=False))
