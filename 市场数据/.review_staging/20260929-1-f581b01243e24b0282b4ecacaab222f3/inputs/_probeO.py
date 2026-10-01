import re
from pathlib import Path
b28 = Path('_学习/limitup_body_20260928.html').read_text(encoding='utf-8', errors='ignore')
a = b28.find('<!--LEDGER-->'); c = b28.find('<!--/LEDGER-->')
print('28: anchor@', a, 'close@', c, 'between len', c - a)
print('28 between:', re.sub(r'\s+', ' ', b28[a:a + 300]))
print('28 after close 200:', re.sub(r'\s+', ' ', b28[c:c + 200]))
b29 = Path('_学习/limitup_body_20260929.html').read_text(encoding='utf-8', errors='ignore')
a29 = b29.find('<!--LEDGER-->'); h4 = b29.find('<h2', a29)
print('29: anchor@', a29, 'h2四@', h4)
print('29 before h2四 (300):', re.sub(r'\s+', ' ', b29[h4 - 300:h4]))
print('29 after h2一 head:', re.sub(r'\s+', ' ', b29[:200]))
j = __import__('json').load(open('_学习/judgment_20260929.json', encoding='utf-8'))
jb = j['bodies']['limitup']
ja = jb.find('<!--LEDGER-->')
print('judgment chain tail char:', repr(jb[-30:]))
print('judgment: len', len(jb), 'anchor', ja)
