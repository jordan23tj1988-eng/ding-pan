# -*- coding: utf-8 -*-
import sys, os, json, io
sys.path.insert(0, r"D:/股票数据/市场数据")
import 涨停质量训练 as M
import pandas as pd

P = M._factor_table()
D = M._enrich(P)
D = D.copy()
D['E1'] = D['E1'] * 100
D['E2'] = D['E2'] * 100
out = {}

def cell(mask, name, minn=25):
    x = D[mask]
    e1 = x['E1'].dropna(); e2 = x['E2'].dropna()
    out[name] = dict(n=int(len(x)),
                     执1胜率=round(float((e1 > 0).mean() * 100), 1) if len(e1) else None,
                     执1均收=round(float(e1.mean()), 3) if len(e1) else None,
                     执1n=int(len(e1)),
                     执2胜率=round(float((e2 > 0).mean() * 100), 1) if len(e2) else None,
                     执2均收=round(float(e2.mean()), 3) if len(e2) else None,
                     执2n=int(len(e2)))

def gapdist(mask, name):
    x = D[mask]
    g = D.loc[mask, ['日', '代码', 'E1', 'E2']]
    # 需要 gap: T+1 open / T close -1 -> 用 bars 重算
    rows = []
    for _, r in x.iterrows():
        b = M._bars(r['代码'])
        if b is None: continue
        idx = b.index[b['date'] == r['日']]
        if not len(idx): continue
        i = idx[0]
        if i + 1 >= len(b): continue
        tc = float(b.loc[i, 'close']); o1 = float(b.loc[i + 1, 'open'])
        if tc <= 0 or o1 <= 0: continue
        rows.append((o1 / tc - 1) * 100)
    s = pd.Series(rows)
    if not len(s):
        out[name] = "no gap"; return
    g1 = ((s > -3) & (s <= 1.5)).mean() * 100
    g3 = ((s > -3) & (s <= 3)).mean() * 100
    out[name] = dict(n=int(len(s)), gap中位=round(float(s.median()), 2),
                     gap均值=round(float(s.mean()), 2),
                     le_neg3=round(float((s <= -3).mean() * 100), 1),
                     m3_0=round(float(((s > -3) & (s <= 0)).mean() * 100), 1),
                     g0_15=round(float(((s > 0) & (s <= 1.5)).mean() * 100), 1),
                     g15_3=round(float(((s > 1.5) & (s <= 3)).mean() * 100), 1),
                     gt3=round(float((s > 3).mean() * 100), 1),
                     触发率_gate15=round(float(g1), 1),
                     触发率_gate3=round(float(g3), 1))

D['温度b'] = pd.to_numeric(D['温度'], errors='coerce')
m4 = (D['连板'] >= 4)
cell(m4 & (D['封单比'] < 2), "4板+×封单<2%")
cell(m4 & (D['封单比'] >= 2), "4板+×封单>=2%")
cell(m4 & (D['温度b'] < 40), "4板+×冷<40")
cell(m4 & (D['封单比'] >= 2) & (D['温度b'] < 40), "4板+×封单>=2%×冷<40")
cell(m4 & (D['封单比'] >= 2) & (D['温度b'] < 40) & (D['开板'] >= 2), "4板+×封单>=2%×冷<40×开2+")
cell(m4 & (D['封单比'] < 2) & (D['换手'] >= 20) & (D['开板'] >= 2), "002172三格交叠(4板+×封单<2%×换手>=20×开2+)")
cell(m4 & (D['封单比'] < 2) & (D['换手'] >= 20), "4板+×封单<2%×换手>=20")
cell(m4 & (D['换手'] >= 20) & (D['开板'] >= 2), "4板+×换手>=20×开2+")
cell((D['温度b'] < 25), "冰点<25")
cell((D['温度b'] < 25) & (D['连板'] >= 4), "冰点<25×4板+")
cell((D['温度b'] < 25) & (D['连板'] == 1), "冰点<25×首板")
cell((D['温度b'] < 25) & (D['换手'] >= 20), "冰点<25×换手>=20")
cell((D['温度b'] < 25) & (D['开板'] >= 2), "冰点<25×开2+")
cell((D['温度b'] < 25) & (D['首封'] >= '14:00'), "冰点<25×尾盘>=14:00")
cell((D['温度b'] < 25) & (D['换手'] >= 20) & (D['开板'] >= 2), "冰点<25×换手>=20×开2+")
gapdist(m4 & (D['封单比'] >= 2), "GAP_4板+×封单>=2%")
gapdist(m4 & (D['封单比'] < 2), "GAP_4板+×封单<2%")
gapdist(m4 & (D['封单比'] >= 2) & (D['温度b'] < 40), "GAP_4板+×封单>=2%×冷<40")
gapdist(m4 & (D['封单比'] < 2) & (D['换手'] >= 20) & (D['开板'] >= 2), "GAP_002172三格")
out['样本'] = int(len(D)); out['窗口'] = [str(D['日'].min()), str(D['日'].max())]
print(json.dumps(out, ensure_ascii=False, indent=1))
