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
    x = D[mask]; e1 = x['E1'].dropna(); e2 = x['E2'].dropna()
    gaps = []
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
                     触发15=round(float(((s > -3) & (s <= 1.5)).mean() * 100), 1) if len(s) else None,
                     触发3=round(float(((s > -3) & (s <= 3)).mean() * 100), 1) if len(s) else None,
                     gapn=int(len(s)))

IC = (D['温度b'] < 25)
cell(IC & (D['连板'] >= 4) & (D['换手'] >= 20), "冰点×4板+×换手≥20")
cell(IC & (D['连板'] >= 4) & (D['开板'] >= 2), "冰点×4板+×开2+")
cell(IC & (D['连板'] >= 4) & (D['封单比'] >= 2), "冰点×4板+×封单≥2%")
cell(IC & (D['换手'] >= 20) & (D['开板'] >= 2), "冰点×换手≥20×开2+")
cell(IC & (D['连板'] == 2) & (D['封单比'] < 2) & (D['换手'] >= 20) & (D['开板'] >= 2), "冰点×2板×封单<2%×换手≥20×开2+(600715)")
cell(IC & (D['连板'] == 2) & (D['换手'] >= 20) & (D['开板'] >= 2), "冰点×2板×换手≥20×开2+")
cell(IC & (D['连板'] == 1) & (D['封单比'] >= 4), "冰点×首板×封单≥4%(301513)")
cell(IC & (D['连板'] == 1) & (D['换手'] >= 20), "冰点×首板×换手≥20")
cell(IC & (D['连板'] == 3), "冰点×3板")
cell(IC & (D['连板'] == 3) & (D['封单比'] >= 4), "冰点×3板×封单≥4%(000995)")
cell(IC & (D['首封'] >= '14:00'), "冰点×尾盘≥14:00")
cell(IC & (D['首封'] >= '14:00') & (D['连板'] == 1), "冰点×尾盘×首板")
print(json.dumps(out, ensure_ascii=False, indent=1))
