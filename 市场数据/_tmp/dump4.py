# -*- coding: utf-8 -*-
import json, os, csv
B = r'D:\股票数据\市场数据'; L = os.path.join(B, '_学习')
def j(p): return json.load(open(p, encoding='utf-8'))
out=[]
for pool in ('zt_pool.csv','zb_pool.csv','dt_pool.csv'):
    p=os.path.join(B,'20261026',pool)
    with open(p, encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    hit=[r for r in rows if str(r.get('代码','')).zfill(6) in ('002242','003021','300296','002979','300561','688386','000700')]
    out.append('%s rows=%d hits=%s' % (pool, len(rows), json.dumps(hit, ensure_ascii=False)))

zs = j(os.path.join(L,'总审_20261026.json'))
out.append('\n=== 总裁决 full\n'+json.dumps(zs['总裁决'], ensure_ascii=False, indent=1))
out.append('\n=== 指派清单\n'+json.dumps(zs['指派清单'], ensure_ascii=False, indent=1)[:6000])
out.append('\n=== 检查四项/矛盾捕获\n'+json.dumps(zs.get('检查四项'), ensure_ascii=False)[:1500])
out.append('\n=== 昨日战绩验收\n'+json.dumps(zs.get('昨日战绩验收'), ensure_ascii=False)[:2500])

mp = j(os.path.join(L,'交易计划_master_20261023.json'))
out.append('\n=== master_20261023 结构 keys=%s\n'%list(mp.keys())+json.dumps(mp, ensure_ascii=False, indent=1)[:3000])
open(os.path.join(B,'_tmp','dump4.txt'),'w',encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
