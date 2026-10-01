import json, re
from pathlib import Path
# ---- lhb 分档快照 20260929
for line in Path('_学习/_席位分档快照.jsonl').read_text(encoding='utf-8-sig').splitlines():
    if not line.strip():
        continue
    r = json.loads(line)
    if r.get('日') == '20260929':
        print('LHB 快照键:', list(r.keys()))
        print(json.dumps(r, ensure_ascii=False)[:900])
lib = json.load(open('_学习/_席位分档.json', encoding='utf-8'))
print('LHB 分档库键:', list(lib.keys()), '更新', lib.get('更新'), '窗口', lib.get('窗口'), '席位数', len(lib.get('席位', {})))
print('LHB 口径:', str(lib.get('口径'))[:400])
# ---- auction 评分库卡
s = Path('_学习/竞价评分库卡_20260929.html').read_text(encoding='utf-8', errors='ignore')
t = re.sub(r'<[^>]+>', '|', s)
t = re.sub(r'\|+', '|', t)
t = re.sub(r'\s+', ' ', t)
print('AUCTION 卡文本:', t[:1800])
