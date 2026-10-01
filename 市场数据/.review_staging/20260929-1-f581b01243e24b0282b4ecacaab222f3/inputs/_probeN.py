import re
from pathlib import Path
def sect(path, kw, n=700):
    s = Path(path).read_text(encoding='utf-8', errors='ignore')
    i = s.find('<h2')
    # find the h2 whose text contains kw
    for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', s, re.S):
        head = re.sub(r'<[^>]+>', '', m.group(1))
        if kw in head:
            end = s.find('<h2', m.end())
            seg = s[m.start(): end if end > 0 else len(s)]
            return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', seg)).strip()[:n]
    return 'NOT FOUND ' + kw
print('== 20260928 auction 温度段:', sect('_学习/auction_body_20260928.html', '温度'))
print()
print('== 20260928 auction 胜率段:', sect('_学习/auction_body_20260928.html', '胜率'))
print()
print('== 20260928 lhb 分档段:', sect('_学习/lhb_body_20260928.html', '分档'))
print()
b = Path('_学习/limitup_body_20260929.html').read_text(encoding='utf-8', errors='ignore')
a = b.find('<!--LEDGER-->')
print('limitup_body 29: anchor@', a, 'len', len(b))
print('  between anchor and next h2:', re.sub(r'\s+', ' ', b[a:a + 400]))
print('  h2四 start:', b.find('<h2', a), re.sub(r'\s+', ' ', b[b.find('<h2', a):b.find('<h2', a) + 200]))
