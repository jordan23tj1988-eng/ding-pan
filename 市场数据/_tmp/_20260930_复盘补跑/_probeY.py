import re
from pathlib import Path
s = Path('review_publish.py').read_text(encoding='utf-8').splitlines()
for i, l in enumerate(s):
    if re.search(r"check (lhb|theme|consistency)|'check |_route_sentinel|sentinel", l):
        print(i + 1, ':', l.strip()[:180])
