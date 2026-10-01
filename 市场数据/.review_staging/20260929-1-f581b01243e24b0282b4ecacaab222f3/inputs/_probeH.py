import subprocess, re
from pathlib import Path
files = [p.name for p in Path('.').glob('*.py')]
hits = []
for f in files:
    try:
        s = Path(f).read_text(encoding='utf-8', errors='ignore')
    except OSError:
        continue
    if 'LEDGER' in s or '节台账' in s or 'anchor' in s.lower():
        ls = [l.strip() for l in s.splitlines() if 'LEDGER' in l or 'anchor' in l.lower()]
        hits.append((f, ls[:6]))
for f, ls in hits:
    print('==', f)
    for l in ls:
        print('   ', l[:170])
