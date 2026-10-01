import glob, os, json, re, time
from pathlib import Path
for f in sorted(glob.glob('_学习/*body_2026092[89].html')):
    n = os.path.basename(f)
    if n.split('_')[0] not in ('auction', 'lhb', 'limitup', 'index', 'theme', 'logic', 'cycle'):
        continue
    s = Path(f).read_text(encoding='utf-8', errors='ignore')
    hs = [re.sub(r'<[^>]+>', '', h).strip()[:60] for h in re.findall(r'<h2[^>]*>(.*?)</h2>', s, re.S)]
    print(os.path.getsize(f), time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(f))), n, '| LEDGER', s.count('<!--LEDGER-->'), s.count('<!--/LEDGER-->'))
    print('     h2:', hs)
