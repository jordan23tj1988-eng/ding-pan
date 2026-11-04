# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = '_学习/交易计划_logic_20261104.json'
raw = open(p, encoding='utf-8').read()
pat = chr(92) * 2 + 'n'
print('pattern count', raw.count(pat))
raw2 = raw.replace(pat, '◆')
d = json.loads(raw2)
assert d['buys'] == [] and len(d['sells']) == 1
open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1))
print('OK bytes', len(json.dumps(d, ensure_ascii=False, indent=1).encode('utf-8')))
print(d['notes'][:120])
print('---')
print(d['notes'][-160:])
