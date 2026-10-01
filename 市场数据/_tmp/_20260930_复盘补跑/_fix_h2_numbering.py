import json
from pathlib import Path
jp = Path('_学习/judgment_20260929.json')
J = json.load(open(jp, encoding='utf-8'))
fix = [('>八 今日竞价温度', '>八、今日竞价温度'), ('>九 竞价信号胜率追踪', '>九、竞价信号胜率追踪'), ('>八 席位分档库', '>八、席位分档库')]
for route in ('auction', 'lhb'):
    b = J['bodies'][route]
    for a, c in fix:
        if a in b:
            b = b.replace(a, c)
            print('renamed', route, a)
    J['bodies'][route] = b
json.dump(J, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
J2 = json.load(open(jp, encoding='utf-8'))
print('ok', {k: len(v) for k, v in J2['bodies'].items()})
