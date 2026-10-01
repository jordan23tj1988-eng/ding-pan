import json, re, glob
from pathlib import Path
# 1) 精确 dump 正文分段判定代码
src = Path('review_pages.py').read_text(encoding='utf-8').splitlines()
for i, l in enumerate(src):
    if re.search(r'HEADING_MAP\s*=|MACHINE_ONLY_SECTIONS\s*=', l):
        for k in range(i, min(i + 40, len(src))):
            print(k + 1, ':', src[k])
        print('....')
        break
print('=========== 分段判定 (含 竞价选股池 关键字的那段)')
for i, l in enumerate(src):
    if '竞价选股池' in l:
        lo = max(0, i - 30)
        for k in range(lo, min(i + 30, len(src))):
            print(k + 1, ':', src[k])
        break
print('=========== 市场温度表 20260929')
p = Path('_学习/_市场温度表.json')
d = json.load(open(p, encoding='utf-8'))
print('type', type(d).__name__, 'keys', list(d)[:6])
r = d.get('20260929') if isinstance(d, dict) else None
print(json.dumps(r, ensure_ascii=False)[:800])
