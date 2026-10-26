# -*- coding: utf-8 -*-
import json, os, glob, csv
B = r'D:\股票数据\市场数据'; L = os.path.join(B, '_学习')
def j(p): return json.load(open(p, encoding='utf-8'))
out=[]
st = j(os.path.join(L,'_模拟盘','master','状态.json'))
out.append('=== 状态 持仓 full')
out.append(json.dumps(st['持仓'], ensure_ascii=False, indent=1))
out.append('cash=%s nav=%s' % (st.get('现金'), st.get('nav')))

out.append('\n=== 推演_20261023 结构')
t23 = j(os.path.join(L,'推演_20261023.json'))
out.append('keys=%s' % list(t23.keys()))
for k in t23:
    if k=='次日可证伪预测':
        for i,p in enumerate(t23[k][:3]):
            out.append('P%d %s' % (i, json.dumps(p, ensure_ascii=False)))
    else:
        out.append('%s: %s' % (k, str(t23[k])[:700]))

out.append('\n=== 持仓与候选 20261026 收盘价(bars)')
codes = ['002242','003021','300296','002979','300561','688386','000700','002931','603901','301502','688836']
for c in codes:
    p = os.path.join(L,'_bars_cache', c+'.csv')
    if not os.path.exists(p):
        out.append('%s: 无bars' % c); continue
    with open(p, encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    last = rows[-1]
    out.append('%s rows=%d last=%s' % (c, len(rows), json.dumps(last, ensure_ascii=False)))

out.append('\n=== zt_pool 20261026 逐行(关键列)')
p = os.path.join(B,'20261026','zt_pool.csv')
with open(p, encoding='utf-8-sig') as f:
    rows=list(csv.DictReader(f))
out.append('cols=%s rows=%d' % (list(rows[0].keys()), len(rows)))
for r in rows:
    out.append(json.dumps(r, ensure_ascii=False))

open(os.path.join(B,'_tmp','dump3.txt'),'w',encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
