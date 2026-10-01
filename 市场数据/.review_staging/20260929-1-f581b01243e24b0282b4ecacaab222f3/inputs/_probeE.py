import re, json
from pathlib import Path
learn = Path('_学习')
def txt(p, n=900):
    s = Path(p).read_text(encoding='utf-8-sig', errors='ignore')
    s2 = re.sub(r'\s+', ' ', re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S))
    s2 = re.sub(r'<[^>]+>', ' ', s2)
    return Path(p).name, len(s), re.sub(r'\s+', ' ', s2).strip()[:n]

for name in ['竞价评分库卡_20260929.html', '质量库折叠_20260929.html', '席位荐票卡_20260929.html']:
    p = learn / name
    if p.exists():
        print(txt(p, 700))
    else:
        print(name, 'MISSING')
    print()
# seat library function source
src = Path('review_pages.py').read_text(encoding='utf-8').splitlines()
for i, l in enumerate(src):
    if 'def _seat_library' in l:
        for k in range(i, min(i + 40, len(src))):
            print(k + 1, ':', src[k])
        break
