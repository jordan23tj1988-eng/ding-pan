import json, re
from pathlib import Path
for d in ['20260928', '20260929']:
    j = json.load(open('_学习/judgment_%s.json' % d, encoding='utf-8'))
    b = j['bodies'].get('limitup', '')
    print(d, 'LEDGER open/close:', b.count('<!--LEDGER-->'), b.count('<!--/LEDGER-->'), 'len', len(b))
    if d == '20260928':
        i = b.find('<!--LEDGER-->')
        print('   28 region head:', re.sub(r'\s+', ' ', b[i:i + 300]))
        k = b.find('<!--/LEDGER-->')
        print('   28 region tail:', re.sub(r'\s+', ' ', b[max(0, k - 200):k + 40]))
print('--- 涨停复盘台账.py CLI:')
s = Path('涨停复盘台账.py').read_text(encoding='utf-8', errors='ignore').splitlines()
for i, l in enumerate(s):
    if re.search(r'LEDGER|argparse|add_argument|def main|__main__|bodies', l):
        print(i + 1, ':', l.strip()[:170])
