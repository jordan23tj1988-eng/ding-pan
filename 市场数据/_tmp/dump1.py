# -*- coding: utf-8 -*-
import json, os, sys
B = r'D:\股票数据\市场数据'
L = os.path.join(B, '_学习')
def j(p):
    return json.load(open(p, encoding='utf-8'))

out = []
def pr(t):
    out.append(t)

# 总审
zs = j(os.path.join(L, '总审_20261026.json'))
pr('=== 总审 keys: %s' % list(zs.keys()))
pr(json.dumps(zs, ensure_ascii=False, indent=1)[:6000])

pr('\n=== summary 20261026')
s = j(os.path.join(B, '20261026', 'summary.json'))
pr(json.dumps(s, ensure_ascii=False, indent=1)[:3000])

pr('\n=== 温度表 (20261026/20261023)')
t = j(os.path.join(L, '_市场温度表.json'))
for k in ('20261026', '20261023'):
    pr(k + ': ' + json.dumps(t.get(k), ensure_ascii=False))

pr('\n=== 先行指标')
ld = j(os.path.join(L, '_情绪先行指标.json'))
pr('keys: %s' % list(ld.keys())[-8:])
for k in ('20261026', '20261023'):
    pr(k + ': ' + json.dumps(ld.get(k), ensure_ascii=False))

pr('\n=== master 状态')
st = j(os.path.join(L, '_模拟盘', 'master', '状态.json'))
pr(json.dumps(st, ensure_ascii=False, indent=1)[:4000])

pr('\n=== 战绩画像汇总')
try:
    pz = j(os.path.join(L, '子agent增强', '战绩画像汇总_20261026.json'))
    pr(json.dumps(pz, ensure_ascii=False, indent=1)[:3000])
except Exception as e:
    pr('缺: %s' % e)

for f in ('质量荐票结算_20261023', '题材荐票结算_20261023', '逻辑荐票结算_20261023', '席位荐票结算_20261023', '竞价池结算_20261023', '校准_20261023'):
    pr('\n=== ' + f)
    try:
        d = j(os.path.join(L, f + '.json'))
        pr(json.dumps(d, ensure_ascii=False, indent=1)[:2500])
    except Exception as e:
        pr('缺: %s' % e)

open(os.path.join(B, '_tmp', 'dump.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
