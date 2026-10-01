import json, re
from pathlib import Path
b = json.load(open('_学习/judgment_20260929.json', encoding='utf-8'))['bodies']['limitup']
print('len', len(b), 'anchors', b.count('<!--LEDGER-->'), b.count('<!--/LEDGER-->'), 'tail', repr(b[-20:]))
print('h2:', [re.sub(r'<[^>]+>', '', h)[:26] for h in re.findall(r'<h2[^>]*>(.*?)</h2>', b, re.S)])
a = b.find('<!--LEDGER-->')
print('锚后200:', re.sub(r'\s+', ' ', b[a:a + 200]))
c = b.find('<!--/LEDGER-->')
print('闭合前160:', re.sub(r'\s+', ' ', b[c - 160:c + 40]))
print('闭合后200:', re.sub(r'\s+', ' ', b[c:c + 200]))
