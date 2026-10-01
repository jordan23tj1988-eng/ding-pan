import json, re
from pathlib import Path
src = Path('review_pages.py').read_text(encoding='utf-8')
m = re.search(r'MACHINE_ONLY_SECTIONS\s*=\s*\{[^}]*\}', src, re.S)
print('MACHINE_ONLY_SECTIONS =', m.group(0) if m else None)
m2 = re.search(r'HEADING_MAP\s*=\s*\{.*?\n\}\n', src, re.S)
print('HEADING_MAP =', (m2.group(0)[:3000] if m2 else None))
st = Path(r'.review_staging/20260929-1-a54d0b1cf47f449d8eec05dc30fc48b4/site/models')
for r in ['auction', 'lhb', 'limitup']:
    mm = json.load(open(st / (r + '.json'), encoding='utf-8'))
    print('==', r, [(c['id'], c['section'], c['status'], c.get('anchors')) for c in mm['components']])
