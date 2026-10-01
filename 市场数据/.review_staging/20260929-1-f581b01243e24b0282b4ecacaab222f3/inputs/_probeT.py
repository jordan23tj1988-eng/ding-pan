import json, re, glob
from pathlib import Path
# 市场温度 20260929
for f in glob.glob('_学习/*温度*20260929*'):
    print('FILE', f, Path(f).stat().st_size)
for f in ['_学习/市场温度表_20260929.json', '_学习/竞价撤单差分_20260929.json', '_学习/市场温度_20260929.json']:
    p = Path(f)
    print(f, 'EXISTS' if p.exists() else 'MISSING')
# staging auction model kpis + 温度 claims
m = sorted(glob.glob('.review_staging/20260929-*/site/models/auction.json'))
print(m)
d = json.load(open(m[-1], encoding='utf-8'))
print('KEYS', list(d.keys()))
print('kpis', json.dumps(d.get('kpis'), ensure_ascii=False)[:600])
for s in d.get('sections', []):
    print(' sec', s.get('id'), s.get('label'), 'claims', len(s.get('claim_refs') or []))
for c in d.get('claims', []):
    t = c.get('text', '')
    if '温度' in t or '胜率' in t:
        print('  claim', c.get('id'), c.get('section'), c.get('role'), ':', t[:200])
