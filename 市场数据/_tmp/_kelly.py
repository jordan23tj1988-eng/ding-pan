# -*- coding: utf-8 -*-
import sys, io, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
df = pd.read_csv(B + '_tmp/_robot20.csv', dtype={'code': str, 'd': str})
r = df[df.lb == 1].dropna(subset=['ret'])
def layer(t):
    t = float(t)
    return '冰点<25' if t < 25 else ('冷25~40' if t < 40 else ('中40~65' if t < 65 else '热>=65'))
r = r.assign(ly=r.temp.map(layer))
ice = r[r.ly == '冰点<25']
w = ice[ice.ret > 0].ret; l = ice[ice.ret <= 0].ret
p = len(w)/len(ice); aw = w.mean(); al = abs(l.mean())
b = aw/al
kelly = p - (1-p)/b
print(f'冰点层 n={len(ice)} p={round(p,3)} 均盈={round(aw,2)}% 均亏={round(al,2)}% 盈亏比b={round(b,2)} 凯利f={round(kelly,3)}')
print(f'半凯利={round(kelly/2,3)} 四分之一凯利={round(kelly/4,3)}')
nav = 1010811.99
for frac in [0.5, 0.25]:
    wgt = max(0.0, kelly*frac)
    print(f'  {frac}凯利仓位={round(wgt*100,2)}% 金额={round(nav*wgt,0)}')
# 规则化: 桶期望定权 但卡位证据缺失 → 折半 → 封顶2%
wgt = min(0.02, max(0.0, kelly*0.25))
print('规则后单票权重', round(wgt*100,2), '% 金额', round(nav*wgt))
for px in [17.41, 10.86, 55.90]:
    amt = nav*wgt
    sh = int(amt/px/100)*100
    print(f'  价{px} → {sh}股 ≈ {round(sh*px)}元')
print('cashes', nav)
