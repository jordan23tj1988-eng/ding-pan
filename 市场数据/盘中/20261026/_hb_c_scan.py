# -*- coding: utf-8 -*-
"""hb-c 11:00 场池帧扫描：新鲜度 + 昨涨停池读数 + 题材批量跳水簇扫描。只读。"""
import json, datetime, statistics, os

OUT = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(OUT, 'realtime_ticks.jsonl')

fr = []
with open(F, encoding='utf-8') as f:
    for l in f:
        l = l.strip()
        if l:
            try:
                fr.append(json.loads(l))
            except Exception:
                pass
fr = [x for x in fr if x.get('ts')]
fr.sort(key=lambda x: x['ts'])
ts = [datetime.datetime.strptime(x['ts'], '%Y-%m-%d %H:%M:%S') for x in fr]
gaps = [(ts[i] - ts[i-1]).total_seconds() for i in range(1, len(ts))]
now = datetime.datetime.now()
print('帧数', len(fr), '窗口', fr[0]['ts'], '~', fr[-1]['ts'])
print('末帧龄_秒', round((now - ts[-1]).total_seconds(), 1), '最大间隔_秒', max(gaps) if gaps else None)
print('pool_date', fr[-1].get('pool_date'), 'pool_stale', fr[-1].get('pool_stale'), 'n', fr[-1].get('n'))


def stats(frame):
    rows = frame.get('rows') or []
    p = [r.get('pct') for r in rows if isinstance(r.get('pct'), (int, float))]
    return {
        'n': len(rows),
        'median': round(statistics.median(p), 2) if p else None,
        'mean': round(sum(p)/len(p), 2) if p else None,
        'up': sum(1 for v in p if v > 0), 'down': sum(1 for v in p if v < 0),
        'ge98': sum(1 for v in p if v >= 9.8),
        'le_m5': sum(1 for v in p if v <= -5),
        'le_m98': sum(1 for v in p if v <= -9.8),
        'le_m98_names': [f"{r.get('name')} {r.get('pct')}%" for r in rows if isinstance(r.get('pct'), (int, float)) and r.get('pct') <= -9.8],
    }

last = stats(fr[-1])
print('末帧读数', json.dumps(last, ensure_ascii=False))

# 最近 30 分钟题材簇扫描：同一 2 分钟窗口内跌幅≥3pp 只数
tail = fr[-31:]
mx = (0, None, [])
for i in range(len(tail)):
    w = tail[i:i+3]  # 约 3 帧=3分钟
    if len(w) < 2:
        continue
    drop = []
    for r in (w[-1].get('rows') or []):
        p = r.get('pct')
        if isinstance(p, (int, float)) and p <= -3:
            drop.append(f"{r.get('name')} {p}%")
    if len(drop) > mx[0]:
        mx = (len(drop), w[-1]['ts'], drop)
print('最近30分钟 跌≥3% 最大同簇', mx[0], mx[1], mx[2][:20])

# 历史对比点
for t in ('2026-10-26 10:33:00', '2026-10-26 10:59:00', '2026-10-26 11:00:00', '2026-10-26 11:01:00'):
    cand = [x for x in fr if x['ts'] <= t]
    if cand:
        s = stats(cand[-1])
        print('对比', cand[-1]['ts'], {k: s[k] for k in ('median', 'mean', 'up', 'down', 'ge98', 'le_m98')})

# 掉板：日内曾 ≥9.8 的票，末帧是否仍 ≥9.8
ever = {}
for x in fr:
    for r in (x.get('rows') or []):
        p = r.get('pct')
        if isinstance(p, (int, float)) and p >= 9.8:
            ever[r.get('code')] = r.get('name')
now_up = {r.get('code') for r in (fr[-1].get('rows') or []) if isinstance(r.get('pct'), (int, float)) and r.get('pct') >= 9.8}
print('日内曾涨停只数', len(ever), '末帧仍涨停', len(now_up), '掉板率', round((len(ever)-len(now_up))/len(ever), 4) if ever else None)

# 持仓/关注票轨迹（最近 8 帧）
watch = {'002242': [], '003021': [], '002639': [], '600487': []}
for x in fr[-8:]:
    for r in (x.get('rows') or []):
        c = r.get('code')
        if c in watch:
            watch[c].append((x['ts'][11:], r.get('pct'), r.get('low'), r.get('high')))
for k, v in watch.items():
    print('轨迹', k, v)
