import json, re
from pathlib import Path
learn = Path('_学习')
bak = learn / 'judgment_20260929.json.bak_force_cycle_20260930'
print('backup exists', bak.exists())
b = json.load(open(bak, encoding='utf-8'))
cur = json.load(open(learn / 'judgment_20260929.json', encoding='utf-8'))
for r in ['auction', 'lhb', 'limitup', 'index', 'theme', 'logic', 'cycle']:
    for tag, j in (('BAK', b), ('CUR', cur)):
        body = j.get('bodies', {}).get(r) or ''
        hs = [re.sub(r'<[^>]+>', '', h).strip() for h in re.findall(r'<h2[^>]*>(.*?)</h2>', body, re.S)]
        print(tag, r, len(body), hs)
    print()
