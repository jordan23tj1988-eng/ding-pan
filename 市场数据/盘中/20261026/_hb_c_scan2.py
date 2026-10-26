# -*- coding: utf-8 -*-
"""hb-c 修正扫描：按 pct 变化(pp) 而非绝对跌幅找题材批量跳水。只读。"""
import json, os, datetime

OUT = os.path.dirname(os.path.abspath(__file__))
fr = []
with open(os.path.join(OUT, 'realtime_ticks.jsonl'), encoding='utf-8') as f:
    for l in f:
        l = l.strip()
        if l:
            try:
                fr.append(json.loads(l))
            except Exception:
                pass
fr = [x for x in fr if x.get('ts')]
fr.sort(key=lambda x: x['ts'])

def m(frame):
    return {r['code']: (r.get('name'), r.get('pct')) for r in (frame.get('rows') or [])
            if isinstance(r.get('pct'), (int, float))}

# 最近 30 分钟(≈30帧) 逐 3 分钟窗，找 pct 跌幅 ≥3pp 的同簇
tail = fr[-32:]
best = []
for i in range(len(tail) - 3):
    a, b = m(tail[i]), m(tail[i+3])
    d = [(b[c][0], round(b[c][1] - a[c][1], 2)) for c in b if c in a and b[c][1] - a[c][1] <= -3]
    best.append((len(d), tail[i]['ts'], tail[i+3]['ts'], d))
best.sort(key=lambda x: -x[0])
for n, t0, t1, d in best[:5]:
    print('窗', t0[11:], '->', t1[11:], '跌≥3pp 只数', n, d[:15])

# 最近 10 分钟（末 10 帧）同簇 + 全池中位变化
a, b = m(fr[-10]), m(fr[-1])
d = [(b[c][0], round(b[c][1] - a[c][1], 2)) for c in b if c in a and b[c][1] - a[c][1] <= -3]
print('末10分钟 跌≥3pp', len(d), sorted(d, key=lambda x: x[1])[:15])

# 持仓票最近 30 分钟极值（腾讯报价另取，这里看池内是否有）
