import json, glob, os, time
from pathlib import Path
sts = sorted(glob.glob('.review_staging/20260929-*'), key=os.path.getmtime)
print('staging dirs:')
for s in sts:
    print('  ', s, time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(s))))
tgt = Path(sts[-1])
mf = tgt / 'manifest.json'
d = json.load(open(mf, encoding='utf-8'))
print('status:', d.get('status'), 'published:', d.get('published'))
print('errors:', json.dumps(d.get('errors'), ensure_ascii=False)[:1500])
for c in d.get('checks', []):
    st = c.get('status')
    if st != 'pass':
        print('  CHECK', st, c.get('name'), str(c.get('detail'))[:200])
print('stage_postprocess:', json.dumps(d.get('stage_postprocess'), ensure_ascii=False)[:300])
p1 = tgt / 'p1_report.json'
if p1.exists():
    r = json.load(open(p1, encoding='utf-8'))
    print('p1 keys', list(r.keys()))
    print(json.dumps({k: v for k, v in r.items() if k != 'checks'}, ensure_ascii=False)[:1200])
    for c in r.get('checks', []):
        if c.get('status') not in (None, 'pass'):
            print('  P1', c.get('status'), c.get('check') or c.get('name'), str(c.get('detail') or c.get('message'))[:200])
