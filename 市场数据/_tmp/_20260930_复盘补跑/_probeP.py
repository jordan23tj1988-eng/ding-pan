import re
from pathlib import Path
for name in ['auction.html', 'lhb.html', 'limitup.html']:
    p = Path('releases/20260928-1-a0e55911d9b24ee3a823e4ca1da356b7/site') / name
    s = p.read_text(encoding='utf-8', errors='ignore')
    hs = [re.sub(r'<[^>]+>', '', h).strip()[:70] for h in re.findall(r'<h[12][^>]*>(.*?)</h[12]>', s, re.S)]
    print('==', name, len(s))
    for h in hs:
        print('   ', h)
