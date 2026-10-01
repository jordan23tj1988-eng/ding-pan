import json
from pathlib import Path
c = json.load(open('_契约/页面契约.v1.json', encoding='utf-8'))
print('KEYS', list(c.keys()))
print('template_version', c.get('template_version'))
for r, spec in c['routes'].items():
    print('=====', r, spec.get('title'))
    for s in spec['sections']:
        print('    ', s)
print('--- other top keys:')
for k, v in c.items():
    if k not in ('routes',):
        print(k, str(v)[:2000])
