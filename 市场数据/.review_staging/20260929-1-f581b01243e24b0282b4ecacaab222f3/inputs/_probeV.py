import json, re
from pathlib import Path
c = json.load(open('_契约/页面契约.v1.json', encoding='utf-8'))
print('top keys', list(c.keys()))
for r in ['auction', 'lhb', 'limitup']:
    v = c.get(r) or (c.get('routes') or {}).get(r)
    print('==', r, json.dumps(v, ensure_ascii=False)[:1200])
print('--- review_contract.py 检查项:')
s = Path('review_contract.py').read_text(encoding='utf-8')
for i, l in enumerate(s.splitlines()):
    if re.search(r'h2|标题|label|section|title', l):
        print(i + 1, ':', l.strip()[:150])
