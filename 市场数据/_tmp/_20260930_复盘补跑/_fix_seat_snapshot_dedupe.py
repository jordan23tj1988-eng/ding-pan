import json
from pathlib import Path
p = Path('_学习/_席位分档快照.jsonl')
lines = [l for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
rows = [json.loads(l) for l in lines]
print('原始行数', len(rows))
seen = {}
order = []
for r in rows:
    k = r.get('日')
    if k not in seen:
        order.append(k)
    seen[k] = r          # 后写覆盖=保留最后一条
print('去重后日数', len(order), '被合并的重复日:', [k for k in order if sum(1 for r in rows if r.get('日') == k) > 1])
out = ''.join(json.dumps(seen[k], ensure_ascii=False, sort_keys=True) + '\n' for k in order)
p.write_text(out, encoding='utf-8')
rows2 = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
print('写入后行数', len(rows2), '末行日', rows2[-1].get('日'), '笔数', rows2[-1].get('笔数'))
print('同时段重复检查:', len(rows2) - len({r['日'] for r in rows2}))
