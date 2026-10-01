import json, re
from pathlib import Path
j = json.load(open('_学习/judgment_20260929.json', encoding='utf-8'))
for r in ['limitup', 'lhb']:
    b = j['bodies'][r]
    print('=====', r)
    for m in re.finditer(r'<!--[^>]*LEDGER[^>]*-->', b):
        s = max(0, m.start() - 160)
        print('  ANCHOR@', m.start(), ':', re.sub(r'\s+', ' ', b[s:m.end()])[-260:])
        print('     AFTER:', re.sub(r'\s+', ' ', b[m.end():m.end() + 200]))
    print('  has open/close:', b.count('<!--LEDGER-->'), b.count('<!--/LEDGER-->'), b.count('<!--LHBLEDGER-->'), b.count('<!--/LHBLEDGER-->'))
print('--- scripts referencing LEDGER anchor:')
import subprocess
hits = subprocess.run(['grep', '-rln', '--include=*.py', '<!--LEDGER', '.'], capture_output=True, text=True).stdout
print(hits)
hits2 = subprocess.run(['grep', '-rln', '--include=*.py', 'LHBLEDGER', '.'], capture_output=True, text=True).stdout
print(hits2)
