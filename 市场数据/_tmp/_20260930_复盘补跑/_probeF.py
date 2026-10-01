import json, re
from pathlib import Path
src = Path('review_pages.py').read_text(encoding='utf-8').splitlines()
for i, l in enumerate(src):
    if re.match(r'\s*def ledger\(', l):
        for k in range(i, min(i + 22, len(src))):
            print(k + 1, ':', src[k])
        break
print('--- 席位分档快照 rows:')
p = Path('_学习/_席位分档快照.jsonl')
for line in p.read_text(encoding='utf-8-sig').splitlines():
    if line.strip():
        r = json.loads(line)
        if r.get('日') in ('20260928', '20260929'):
            print(r.get('日'), json.dumps(r, ensure_ascii=False)[:600])
lib = Path('_学习/_席位分档.json')
if lib.exists():
    d = json.load(open(lib, encoding='utf-8'))
    print('分档库 更新=', d.get('更新'), '窗口=', d.get('窗口'), '席位n=', len(d.get('席位', {})), '口径=', str(d.get('口径'))[:200])
