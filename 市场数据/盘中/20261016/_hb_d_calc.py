# -*- coding: utf-8 -*-
"""hb-d(2026-10-16 13:30 午后延续段) 取数: 全部只读既有留档(零后视镜)。
决策截止 CUT = 本场 started_at 2026-10-16 13:30:55(executions.db id=c4f43b5940ac41d98dd9ae10d5d9c95e,
job_id=c415a7792216=sentiment-intraday-hb-d, scheduled_instant 2026-10-16T05:30:00+00:00,
claimed_at 13:30:55.338)。凡 >CUT 落档的帧一律剔除、不参与判定, 另册登记。
本脚本不发起任何实时取数(与 20261016 hb-a/hb-b/hb-c 同口径): 池外持仓标 null, 不补数。
"""
import json, os, sys, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

D = os.path.dirname(os.path.abspath(__file__))
B = r"D:\股票数据\市场数据"
TICK = os.path.join(D, 'realtime_ticks.jsonl')
CUT = '2026-10-16 13:30:55'
PREV_CUT = '2026-10-16 11:00:55'   # hb-c 决策截止(本场增量窗起点)

MASTER = os.path.join(B, r'_学习/_模拟盘/master/状态.json')
MLED = os.path.join(B, r'_学习/_模拟盘/master/账本.jsonl')
Z7 = os.path.join(B, r'_学习/_模拟盘/盘中作战/state.json')
ZLED = os.path.join(B, r'_学习/_模拟盘/盘中作战/账本.jsonl')
ZSELL = os.path.join(B, r'_学习/_模拟盘/盘中作战/次日卖出指令.json')
THEME = os.path.join(B, r'_学习/题材归位_20261015.json')
PB = os.path.join(B, r'盘中/20261015/playbook.json')

ticks = [json.loads(l) for l in open(TICK, encoding='utf-8') if l.strip()]
T = [t for t in ticks if t['ts'] <= CUT]
DROP = [t['ts'] for t in ticks if t['ts'] > CUT]
print("① 新鲜度")
print("   ticks 全 %d 帧 (%s ~ %s); 决断窗内 %d 帧 (%s ~ %s); 剔除 %d 帧 %s"
      % (len(ticks), ticks[0]['ts'], ticks[-1]['ts'], len(T), T[0]['ts'], T[-1]['ts'], len(DROP), DROP))


def secs(ts):
    return datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').timestamp()


gaps = [round(secs(T[i]['ts']) - secs(T[i - 1]['ts'])) for i in range(1, len(T))]
last_lag = round(secs(CUT) - secs(T[-1]['ts']))
print("   帧距 min/max/mean = %d/%d/%.1fs; 末帧距CUT %ds; 断更判定=%s"
      % (min(gaps), max(gaps), sum(gaps) / len(gaps), last_lag,
         "无(<<600s) → 允许决策" if max(gaps) < 600 else "★断更>10分钟 → 只报警禁决策"))
# 午休窗帧(11:30~13:00)是否存在 + 价格是否冻结
lunch = [t for t in T if '11:30:00' < t['ts'][11:] < '13:00:00']
print("   午休窗(11:30~13:00)帧数 = %d %s" % (len(lunch), ("首/末 " + lunch[0]['ts'][11:] + "~" + lunch[-1]['ts'][11:]) if lunch else ""))
if lunch:
    a, b = lunch[0]['rows'], lunch[-1]['rows']
    same = sum(1 for x, y in zip(a, b) if x['latest'] == y['latest'])
    print("     午休窗首末帧逐票价相同数 = %d/%d (冻结=%s)" % (same, len(a), same == len(a)))
print("   池: pool_date=%s kind=%s stale=%s n=%d" % (T[-1]['pool_date'], T[-1]['pool_kind'],
                                                 T[-1]['pool_stale'], T[-1]['n']))
print("   mtime(ticks) = %s" % datetime.datetime.fromtimestamp(os.path.getmtime(TICK)).strftime('%Y-%m-%d %H:%M:%S'))


def snap(t):
    R = t['rows']; P = [r['pct'] for r in R]
    zt = [r for r in R if r['pct'] >= 9.8]
    dt = [r for r in R if r['pct'] <= -9.8]
    zb = [r for r in R if (r.get('preClose') and r['high'] / r['preClose'] * 100 - 100 >= 9.8
                           and r['pct'] < 9.8)]
    sp = sorted(P)
    return {"ts": t['ts'], "n": len(R), "median": round(sp[len(sp) // 2], 2),
            "mean": round(sum(P) / len(P), 2), "min": round(min(P), 2), "max": round(max(P), 2),
            "red": sum(1 for x in P if x > 0), "green": sum(1 for x in P if x < 0),
            "flat": sum(1 for x in P if x == 0),
            "zt": len(zt), "dt": len(dt), "zb": len(zb),
            "zt_names": [a['code'] + a['name'] for a in zt],
            "dt_names": [a['code'] + a['name'] for a in dt],
            "zb_names": [a['code'] + a['name'] + "高%.1f→现%.1f" % (a['high'] / a['preClose'] * 100 - 100, a['pct']) for a in zb]}


traj = [snap(t) for t in T]
S = traj[-1]
print("\n② 决断时点(%s)池截面: n=%d 中位%+.2f 均值%+.2f 最低%+.2f 最高%+.2f 红%d绿%d平%d 封板%d 跌停%d 炸板%d"
      % (S['ts'], S['n'], S['median'], S['mean'], S['min'], S['max'], S['red'], S['green'],
         S['flat'], S['zt'], S['dt'], S['zb']))
print("   封板: %s" % S['zt_names'])
print("   炸板: %s" % S['zb_names'])
print("   跌停: %s" % S['dt_names'])
print("   全窗轨迹(每10帧):")
for i, s in enumerate(traj):
    if i % 10 == 0 or i == len(traj) - 1:
        print("     %s 中位%+.2f 均值%+.2f 红%d绿%d 封%d 炸%d 跌停%d"
              % (s['ts'][11:], s['median'], s['mean'], s['red'], s['green'], s['zt'], s['zb'], s['dt']))

INC = [t for t in T if t['ts'] > PREV_CUT]
inc_traj = [snap(t) for t in INC]
print("\n   增量窗 %s ~ %s (%d 帧) 首/末: 中位%+.2f→%+.2f 均值%+.2f→%+.2f 红%d→%d绿%d→%d 封%d→%d 炸%d→%d 跌停%d→%d"
      % (INC[0]['ts'][11:], INC[-1]['ts'][11:], len(INC), inc_traj[0]['median'], inc_traj[-1]['median'],
         inc_traj[0]['mean'], inc_traj[-1]['mean'], inc_traj[0]['red'], inc_traj[-1]['red'],
         inc_traj[0]['green'], inc_traj[-1]['green'], inc_traj[0]['zt'], inc_traj[-1]['zt'],
         inc_traj[0]['zb'], inc_traj[-1]['zb'], inc_traj[0]['dt'], inc_traj[-1]['dt']))

rows = T[-1]['rows']
B9 = [r['code'] for r in rows]
FOCUS = {'600668': '在持(master·09:40 A级成交 8.15×6100)', '605189': '在持(master·09:40 A级成交 17.97×1100)',
         '000530': '弃单(09:40 破位作废; 10:21 起封板=机会成本立案)',
         '300111': 'watch(lhb·席位命门)', '603230': 'watch(lhb·席位命门)', '002815': 'watch(logic+theme)',
         '001318': 'watch(theme)', '301282': 'watch(logic)', '002134': 'watch(logic)',
         '605058': 'watch(limitup)', '600812': 'watch(limitup)', '002945': 'watch(limitup)'}
print("\n③ 焦点票(持仓2 + 弃单1 + watch9) 决断时点读数")
foc = {}
for c, tag in FOCUS.items():
    r = next((x for x in rows if x['code'] == c), None)
    if not r:
        print("   %s <<不在池>>" % c); foc[c] = None; continue
    seq = [(t['ts'], next((y['latest'] for y in t['rows'] if y['code'] == c), None)) for t in T]
    vals = [(ts, v) for ts, v in seq if v]
    hi = max(vals, key=lambda x: x[1]); lo = min(vals, key=lambda x: x[1])
    inc = [(ts, v) for ts, v in vals if ts > PREV_CUT]
    ztp = round(r['preClose'] * (1.2 if c.startswith(('300', '301', '688')) else 1.1), 2)
    reach = r['high'] / r['preClose'] * 100 - 100 >= 9.8
    foc[c] = {"name": r['name'], "tag": tag, "open": r['open'], "preClose": r['preClose'],
              "gap_pct": round(r['open'] / r['preClose'] * 100 - 100, 2),
              "latest": r['latest'], "pct": r['pct'], "high": r['high'], "low": r['low'],
              "zt_px": ztp, "触涨停价": reach, "现是否封板": r['pct'] >= 9.8,
              "炸板": bool(reach and r['pct'] < 9.8),
              "窗内最高": [hi[1], hi[0][11:]], "窗内最低": [lo[1], lo[0][11:]],
              "窗内最高相对前收pct": round(hi[1] / r['preClose'] * 100 - 100, 2),
              "窗内最低相对前收pct": round(lo[1] / r['preClose'] * 100 - 100, 2),
              "窗内峰谷回撤pct": round((lo[1] - hi[1]) / hi[1] * 100, 2),
              "增量窗": {"起": [inc[0][1], inc[0][0][11:]], "末": [inc[-1][1], inc[-1][0][11:]],
                        "极差pct": round((max(v for _, v in inc) - min(v for _, v in inc)) / inc[0][1] * 100, 2),
                        "位移pct": round((inc[-1][1] / inc[0][1] - 1) * 100, 2),
                        "最高": [max(v for _, v in inc), max(inc, key=lambda x: x[1])[0][11:]],
                        "最低": [min(v for _, v in inc), min(inc, key=lambda x: x[1])[0][11:]]} if inc else None}
    print("   %s %s [%s] 开%s(gap%+.2f%%) 现%s(%+.2f%%) 高%.2f 低%.2f 涨停价%s 触板=%s 炸板=%s 增量窗 %s→%s(%+.2f%%)"
          % (c, r['name'], tag, r['open'], foc[c]['gap_pct'], r['latest'], r['pct'], r['high'],
             r['low'], ztp, reach, foc[c]['炸板'],
             foc[c]['增量窗']['起'][1] if foc[c]['增量窗'] else '-',
             foc[c]['增量窗']['末'][1] if foc[c]['增量窗'] else '-',
             foc[c]['增量窗']['位移pct'] if foc[c]['增量窗'] else 0.0))

frames = [(t['ts'], secs(t['ts']), dict((r['code'], r) for r in t['rows'])) for t in T]
IF = [f for f in frames if f[0] > PREV_CUT]


def scan(win_lo, win_hi, pool=None):
    src = pool if pool is not None else frames
    out = []
    for i in range(len(src)):
        for j in range(i + 1, len(src)):
            dt = src[j][1] - src[i][1]
            if dt < win_lo or dt > win_hi:
                continue
            a, b = src[i][2], src[j][2]
            hits = []
            for c in a:
                if c in b and a[c].get('latest') and b[c].get('latest'):
                    d = (b[c]['latest'] / a[c]['latest'] - 1) * 100
                    if d <= -3.0:
                        hits.append([c, b[c]['name'], round(d, 2)])
            if len(hits) >= 3:
                out.append({"from": src[i][0], "to": src[j][0], "dt_s": int(dt),
                            "n": len(hits), "hits": hits})
    return out


allp = scan(1, 120)
allp.sort(key=lambda x: (-x['n'], x['from']))
incp = scan(1, 120, IF)
incp.sort(key=lambda x: (-x['n'], x['from']))
print("\n④ 批量跳水扫描(门槛 ≥3只 / ≤120s / 每只价跌≥-3%)")
print("   主口径(全窗 全对 ≤120s): 达阈 %d 组" % len(allp))
for b in allp[:8]:
    print("     %s→%s(%ds) n=%d %s" % (b['from'][11:], b['to'][11:], b['dt_s'], b['n'], b['hits']))
print("   增量窗口径(仅 %s 后帧): 达阈 %d 组" % (PREV_CUT[11:], len(incp)))
for b in incp[:8]:
    print("     %s→%s(%ds) n=%d %s" % (b['from'][11:], b['to'][11:], b['dt_s'], b['n'], b['hits']))
pre2 = [b for b in scan(1, 140) if b['to'] >= '2026-10-16 13:29']
print("   决断前2分钟窗(≤140s, to≥13:29): 达阈 %d 组 %s" % (len(pre2), [(b['from'][11:], b['to'][11:], b['n']) for b in pre2]))
pp = []
for i in range(len(frames)):
    for j in range(i + 1, len(frames)):
        dt = frames[j][1] - frames[i][1]
        if dt > 120:
            continue
        a, b = frames[i][2], frames[j][2]
        hits = [[c, b[c]['name'], round(b[c]['pct'] - a[c]['pct'], 2)] for c in a
                if c in b and a[c].get('pct') is not None and b[c].get('pct') is not None
                and b[c]['pct'] - a[c]['pct'] <= -3.0]
        if len(hits) >= 3:
            pp.append({"from": frames[i][0], "to": frames[j][0], "n": len(hits), "hits": hits})
print("   对照口径(pct 位移≥3pp / ≤120s): 达阈 %d 组; 最大批 %s" % (len(pp), max((b['n'] for b in pp), default=0)))

# 午后开盘位移(13:00 帧 vs 11:30 末帧) —— 午休后的第一读数
noon_prev = [t for t in T if t['ts'][11:] <= '11:30:00']
noon_post = [t for t in T if t['ts'][11:] >= '13:00:00']
if noon_prev and noon_post:
    a = dict((r['code'], r['latest']) for r in noon_prev[-1]['rows'])
    b = dict((r['code'], r['latest']) for r in noon_post[0]['rows'])
    mv = [(round((b[c] / a[c] - 1) * 100, 2), c) for c in a if c in b and a[c]]
    mv.sort()
    print("\n④b 午后首帧(%s) vs 午前末帧(%s) 逐票位移: 最弱 %s 最强 %s"
          % (noon_post[0]['ts'][11:], noon_prev[-1]['ts'][11:], mv[:4], mv[-4:]))

try:
    th = json.load(open(THEME, encoding='utf-8'))['映射']
except Exception as e:
    th = {}
    print("   题材归位读取失败: %s" % e)
linemap = {}
for r in rows:
    l = th.get(r['code'], {}).get('大方向', '未映射')
    linemap.setdefault(l, []).append(r)
print("\n⑤ 池内线分布(>=2只) 决断时点读数")
for L, rs in sorted(linemap.items(), key=lambda x: -len(x[1])):
    if len(rs) >= 2:
        print("     %s(%d): %s" % (L, len(rs), ", ".join("%s%+.1f" % (r['name'], r['pct']) for r in rs)))

rr = []
for r in rows:
    seq = [(t['ts'], next((y['latest'] for y in t['rows'] if y['code'] == r['code']), None)) for t in T]
    vals = [(ts, v) for ts, v in seq if v]
    if len(vals) < 2:
        continue
    best = min((round((vals[j][1] / vals[i][1] - 1) * 100, 2), vals[i][0][11:], vals[j][0][11:])
               for i in range(len(vals)) for j in range(i + 1, len(vals)))
    rr.append((best[0], r['code'], r['name'], best[1], best[2]))
print("\n⑥ 池内单票窗内最大回撤 Top8")
for x in sorted(rr)[:8]:
    print("   %s %s %.2f%% (%s→%s)" % (x[1], x[2], x[0], x[3], x[4]))
disp = []
for r in rows:
    seq = [(t['ts'], next((y['latest'] for y in t['rows'] if y['code'] == r['code']), None)) for t in INC]
    vals = [(ts, v) for ts, v in seq if v]
    if len(vals) < 2:
        continue
    disp.append((round((vals[-1][1] / vals[0][1] - 1) * 100, 2), r['code'], r['name'], vals[0][0][11:], vals[-1][0][11:]))
print("   增量窗(11:00→13:30)位移最弱 Top6 / 最强 Top6:")
for x in sorted(disp)[:6]:
    print("     弱 %s %s %+.2f%% (%s→%s)" % (x[1], x[2], x[0], x[3], x[4]))
for x in sorted(disp, reverse=True)[:6]:
    print("     强 %s %s %+.2f%% (%s→%s)" % (x[1], x[2], x[0], x[3], x[4]))

print("\n⑦ 账本事实")


def mt(p):
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return None


mst = json.load(open(MASTER, encoding='utf-8'))
z7 = json.load(open(Z7, encoding='utf-8'))
mpos = mst.get('positions') or mst.get('持仓') or []
mcash = mst.get('cash', mst.get('现金'))
print("   master 状态.json mtime=%s 现金=%s 持仓=%d" % (mt(MASTER), mcash, len(mpos)))
for p in mpos:
    print("     %s" % json.dumps(p, ensure_ascii=False))
print("   第七账 state.json mtime=%s cash=%s positions=%s" % (mt(Z7), z7.get('cash'), json.dumps(z7.get('positions'), ensure_ascii=False)))
led = [json.loads(l) for l in open(MLED, encoding='utf-8') if l.strip()]
print("   master 账本末条(%d 条): %s" % (len(led), json.dumps(led[-1], ensure_ascii=False)[:300]))
print("   master 账本 20261016 记录数: %d" % sum(1 for x in led if x.get('d') == '20261016'))
zled = [json.loads(l) for l in open(ZLED, encoding='utf-8') if l.strip()]
print("   第七账 账本末条(%d 条): %s" % (len(zled), json.dumps(zled[-1], ensure_ascii=False)[:300]))
zsell = json.load(open(ZSELL, encoding='utf-8'))
print("   次日卖出指令.json = %s" % json.dumps(zsell, ensure_ascii=False)[:200])
missing = {}
for f in ['pulse.json', 'warboard.json', '执行流水.jsonl', '报警_20261016.jsonl', 'pipeline_alarm.jsonl']:
    missing[f] = os.path.exists(os.path.join(D, f))
    print("   缺件检查 %s → 存在=%s" % (f, missing[f]))

pb = json.load(open(PB, encoding='utf-8'))
print("\n⑧ 预案(真源 %s, date=%s route=%s version=%s)" % (PB, pb.get('date'), pb.get('route'), pb.get('version')))
print("   buys=%d sells=%d watch=%d cash_pct=%s" % (len(pb.get('buys', [])), len(pb.get('sells', [])),
                                                  len(pb.get('watch', [])), pb.get('cash_pct')))

json.dump({"cut": CUT, "prev_cut": PREV_CUT, "frames_all": len(ticks),
           "frames_in_cut": [t['ts'] for t in T], "dropped": DROP,
           "gap_sec": {"min": min(gaps), "max": max(gaps), "mean": round(sum(gaps) / len(gaps), 1)},
           "last_lag_s": last_lag, "ticks_mtime": mt(TICK),
           "lunch_frames": len(lunch),
           "pool": {"date": T[-1]['pool_date'], "n": T[-1]['n'], "stale": T[-1]['pool_stale']},
           "traj": traj, "snapshot": S, "inc_traj": inc_traj, "focus": foc,
           "batch120_all_pairs": allp, "batch120_inc": incp, "batch120_pre2": pre2, "batch_pct_pp": pp[:20],
           "lines_pool": {L: [(r['code'], r['name'], r['pct']) for r in rs] for L, rs in linemap.items()},
           "peak2trough_top": sorted(rr)[:8], "inc_disp": sorted(disp),
           "master": {"mtime": mt(MASTER), "cash": mcash, "positions": mpos},
           "z7": {"mtime": mt(Z7), "cash": z7.get('cash'), "positions": z7.get('positions')},
           "ledger_master_last": led[-1], "ledger_master_1016_n": sum(1 for x in led if x.get('d') == '20261016'),
           "ledger_z7_last": zled[-1], "z7_sell_orders": zsell, "missing_files": missing,
           "playbook": {"path": PB, "date": pb.get('date'), "buys": len(pb.get('buys', [])),
                        "sells": len(pb.get('sells', [])), "watch": len(pb.get('watch', [])), "cash_pct": pb.get('cash_pct')}},
          open(os.path.join(D, '_hb_d_calc.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("\n落档: _hb_d_calc.json")
