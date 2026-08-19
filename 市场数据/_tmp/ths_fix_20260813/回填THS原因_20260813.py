# -*- coding: utf-8 -*-
"""回填8/13题材归位的THS涨停原因: 50只行业兜底票的催化字段
"XX行业(THS原因缺,行业兜底)" → "{THS limit_up_reason}(THS)"。
大方向/环节/来源档=agent判断保留不动; 9只agent手写催化的票不动。
用法: python 回填THS原因_20260813.py  (改前自动备份)
"""
import json, os, sys, shutil, datetime

BASE = r'D:\股票数据\市场数据'
L = os.path.join(BASE, '_学习')
D = '20260813'

sys.stdout.reconfigure(encoding='utf-8')

pool = json.load(open(os.path.join(L, f'THS涨停池_{D}.json'), encoding='utf-8'))
reason = {x['ticker']: (x.get('limit_up_reason') or '').strip() for x in pool}
print(f'THS涨停池: {len(pool)}只, 原因非空 {sum(1 for v in reason.values() if v)}')

rp = os.path.join(L, f'题材归位_{D}.json')
bak = rp + '.bak_th前'
shutil.copy(rp, bak)
j = json.load(open(rp, encoding='utf-8'))
m = j['映射']

done, skipped, no_match, unchanged = [], [], [], []
for code, v in m.items():
    cat = v.get('催化', '')
    if 'THS原因缺' not in cat:
        unchanged.append(code)
        continue
    r = reason.get(code)
    if not r:
        no_match.append((code, cat[:40]))
        continue
    # 保留原催化里的非兜底部分(若有), 兜底串替换为真实原因
    newcat = r + '(THS)'
    v['催化'] = newcat
    done.append((code, v.get('大方向', '?'), r))
    # 来源档保持 B (B=THS口径, 原本就是B)

json.dump(j, open(rp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print(f'\n回填 {len(done)} 只 | 无匹配 {len(no_match)} | 未含兜底串不动 {len(unchanged)}')
for code, d, r in done[:8]:
    print(f'  {code} [{d}] → {r}')
if len(done) > 8:
    print(f'  ... 共{len(done)}只')
for code, c in no_match:
    print(f'  [无匹配] {code}: {c}')
print(f'\n备份: {bak}')
