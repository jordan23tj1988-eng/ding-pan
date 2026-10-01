import json, re
from pathlib import Path
j = json.loads(Path('_学习/judgment_20260929.json').read_text(encoding='utf-8'))
pats = [r'不可达', r'网络未刷新', r'未刷新沿', r'沿用20260928',
        r'溢价\s*null', r'null\s*[\(（]源', r'结算\s*(全)?None', r'价源\s*null', r'数据缺口待补', r'挂起未重训']
for route in list(j['bodies'].keys()):
    body = j['bodies'][route]
    text = re.sub(r'<[^>]+>', ' ', body)
    hits = []
    for pat in pats:
        for m in re.finditer(pat, text):
            hits.append((pat, ' '.join(text[max(0, m.start() - 40):m.end() + 40].split())))
    if hits:
        print('==', route, len(hits))
        for pat, ctx in hits:
            print('   ', pat, '->', ctx[:150])
# 其他顶层字段
for k, v in j.items():
    if isinstance(v, str) and '沿用20260928' in v:
        print('== 顶层字段', k, '含 沿用20260928')
