# -*- coding: utf-8 -*-
"""hb-a(2026-10-16 09:40 开盘博弈段) 取数: ①决断时点实价(腾讯同源) ②池内截面/炸板/批量跳水
③预案3买单 gap ④在持票/观察池照会。零编造: 一切数字来自本脚本落档的原始响应/留档文件。
决策截止 = 2026-10-16 09:40:00; ticks 仅用 <=09:40:00 的帧做判断, 09:40:07/09:41:08/09:42:08 剔除。
"""
import json, os, subprocess, sys, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

D = os.path.dirname(os.path.abspath(__file__))
TICK = os.path.join(D, 'realtime_ticks.jsonl')
AUC = os.path.join(D, 'auction_traj.jsonl')
CUT = '2026-10-16 09:40:55'  # 本场 started_at(executions.db id=a8ff5e4aa8854b57adb6e8fd663208a6) → 决策截止

def ths_code(c):
    c = str(c).split('.')[0]
    return ('sh' if c[0] in '569' else 'sz') + c

def parse_tencent(raw):
    out = {}
    for line in raw.decode('gbk', errors='replace').strip().split(';'):
        if '=' not in line:
            continue
        head, body = line.split('=', 1)
        code = head.split('_')[-1][2:]
        f = body.strip('"\n').split('~')
        if len(f) < 45:
            continue
        def g(i):
            try:
                return float(f[i])
            except Exception:
                return None
        out[code] = {"name": f[1], "latest": g(3), "preClose": g(4), "open": g(5),
                     "ts_quote": f[30], "chg": g(31), "pct": g(32), "high": g(33),
                     "low": g(34), "amount_wan": g(37), "turnover_pct": g(38),
                     "zt_px": g(47), "dt_px": g(48), "bid1": g(9), "ask1": g(19)}
    return out

def fetch_tencent(codes):
    q = ",".join(ths_code(c) for c in codes)
    url = "http://qt.gtimg.cn/q=" + q
    r = subprocess.run(["curl", "--noproxy", "*", "-s", "-m", "15", url],
                       capture_output=True, timeout=40)
    return url, parse_tencent(r.stdout or b'')

HOLD = ["000011", "002860",                        # 第七账·盘中作战独立账
        "600693", "605577", "000601", "603968", "000823"]  # master账
BUYS = ["600668", "605189", "000530"]              # 盘中/20261015/playbook.json buys
WATCH = ["300111", "603230", "002815", "301318", "301282", "002134", "605058", "600812", "002945"]
WATCH = ["300111", "603230", "002815", "001318", "301282", "002134", "605058", "600812", "002945"]

# ---------- ① 决断时点实价(腾讯同源, 落档) ----------
url, quotes = fetch_tencent(HOLD + BUYS + WATCH)
fetch_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
json.dump({"url": url, "fetch_ts": fetch_ts, "src": "腾讯 qt.gtimg.cn", "cut": CUT,
           "quotes": quotes}, open(os.path.join(D, '_hb_a_quote.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print("① 决断时点实价 fetch_ts=%s (决策截止 %s)" % (fetch_ts, CUT))
for grp, lst in [("在持票", HOLD), ("预案买单", BUYS), ("观察池", WATCH)]:
    print(" [" + grp + "]")
    for c in lst:
        v = quotes.get(c)
        if v:
            print("  %s %s latest=%s pct=%s%% open=%s pre=%s high=%s low=%s quote_ts=%s zt=%s dt=%s"
                  % (c, v['name'], v['latest'], v['pct'], v['open'], v['preClose'], v['high'],
                     v['low'], v['ts_quote'], v['zt_px'], v['dt_px']))
        else:
            print("  %s <<无数据>>" % c)

# ---------- ② ticks 池内(仅 <=09:40:00) ----------
ticks = [json.loads(l) for l in open(TICK, encoding='utf-8')]
T = [t for t in ticks if t['ts'] <= CUT]
print("\n② ticks 全%d帧 -> 决断窗内 %d 帧 (%s ~ %s)"
      % (len(ticks), len(T), T[0]['ts'], T[-1]['ts']))
print("   池: pool_date=%s kind=%s stale=%s n=%d" % (T[-1]['pool_date'], T[-1]['pool_kind'],
                                                     T[-1]['pool_stale'], T[-1]['n']))
print("   剔除帧(决断后落档): %s" % [t['ts'] for t in ticks if t['ts'] > CUT])

last = T[-1]
rows = last['rows']
pcts = [r['pct'] for r in rows]
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
            "flat": sum(1 for x in P if x == 0), "zt": len(zt), "dt": len(dt), "zb": len(zb),
            "zt_names": [a['code'] + a['name'] for a in zt], "dt_names": [a['code'] + a['name'] for a in dt],
            "zb_names": [a['code'] + a['name'] + "高%.1f→现%.1f" % (a['high'] / a['preClose'] * 100 - 100, a['pct']) for a in zb]}
print("\n   决断时点(%s)截面: n=%d 中位%+.2f 均值%+.2f 最低%+.2f 最高%+.2f 红%d绿%d平%d 封板%d 跌停%d 炸板%d"
      % (snap(last)['ts'], snap(last)['n'], snap(last)['median'], snap(last)['mean'],
         snap(last)['min'], snap(last)['max'], snap(last)['red'], snap(last)['green'],
         snap(last)['flat'], snap(last)['zt'], snap(last)['dt'], snap(last)['zb']))
traj = [snap(t) for t in T]
for s in traj:
    print("    %s n=%d 中位%+.2f 均值%+.2f 封%d 跌停%d 炸%d" % (s['ts'][11:], s['n'], s['median'], s['mean'], s['zt'], s['dt'], s['zb']))

# 批量跳水: 相邻帧对(≈60s) 与 跨2帧(≈120s)
frames = [(t['ts'], dict((r['code'], r) for r in t['rows'])) for t in T]
batch1, batch2 = [], []
for i in range(1, len(frames)):
    a, b = frames[i - 1][1], frames[i][1]
    hits = []
    for c in a:
        if c in b and a[c].get('latest') and b[c].get('latest'):
            d = (b[c]['latest'] / a[c]['latest'] - 1) * 100
            if d <= -3.0:
                hits.append([c, b[c]['name'], round(d, 2)])
    if len(hits) >= 3:
        batch1.append({"ts": frames[i][0], "n": len(hits), "hits": hits})
for i in range(2, len(frames)):
    a, b = frames[i - 2][1], frames[i][1]
    hits = []
    for c in a:
        if c in b and a[c].get('latest') and b[c].get('latest'):
            d = (b[c]['latest'] / a[c]['latest'] - 1) * 100
            if d <= -3.0:
                hits.append([c, b[c]['name'], round(d, 2)])
    if len(hits) >= 3:
        batch2.append({"ts": frames[i][0], "n": len(hits), "hits": hits})
print("\n   批量跳水(>=3只/帧, 单帧≈60s): %d 组" % len(batch1))
for b in batch1:
    print("    ", b['ts'], b['n'], b['hits'])
print("   批量跳水(>=3只/跨2帧≈120s): %d 组" % len(batch2))
for b in batch2:
    print("    ", b['ts'], b['n'], b['hits'])
# 决断前2分钟
for i in range(1, len(frames)):
    if frames[i][0] > '2026-10-16 09:38:00':
        a, b = frames[i - 1][1], frames[i][1]
        hits = [[c, b[c]['name'], round((b[c]['latest'] / a[c]['latest'] - 1) * 100, 2)]
                for c in a if c in b and a[c].get('latest') and b[c].get('latest')
                and (b[c]['latest'] / a[c]['latest'] - 1) * 100 <= -3.0]
        print("    决断前窗 %s->%s: <=-3.0%% 只数=%d %s" % (frames[i - 1][0][11:], b and frames[i][0][11:], len(hits), hits))

# 单票最大回撤(窗内 latest 峰谷)
def peak2trough(code_rows):
    seq = [(t['ts'], next((r['latest'] for r in t['rows'] if r['code'] == code_rows), None)) for t in T]
    vals = [(ts, v) for ts, v in seq if v]
    if not vals:
        return None
    mx = max(vals, key=lambda x: x[1]); mn = min(vals, key=lambda x: x[1])
    # 峰在谷前
    draw = None
    best = None
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            d = (vals[j][1] / vals[i][1] - 1) * 100
            if best is None or d < best[0]:
                best = (round(d, 2), vals[i][0][11:], vals[j][0][11:])
    return best
print("\n   池内单票窗内最大回撤 Top5:")
rr = []
for r in rows:
    b = peak2trough(r['code'])
    if b:
        rr.append((b[0], r['code'], r['name'], b[1], b[2]))
for x in sorted(rr)[:5]:
    print("    %s %s 回撤%.2f%% (%s->%s)" % (x[1], x[2], x[0], x[3], x[4]))

# ---------- ③ 预案3买单 gap ----------
auction = [json.loads(l) for l in open(AUC, encoding='utf-8')]
auc_last = auction[-1]
A = dict((r['code'], r) for r in auc_last['rows'])
t0 = T[0]
O0 = dict((r['code'], r) for r in t0['rows'])
print("\n③ 预案3买单 gap (竞价末帧 %s / 开盘首帧 %s)" % (auc_last['ts'], t0['ts']))
gaps = {}
for c in BUYS:
    o = O0.get(c); a = A.get(c)
    if o and o.get('preClose'):
        gap = round(o['open'] / o['preClose'] * 100 - 100, 2)
        gaps[c] = {"name": o['name'], "preClose": o['preClose'], "open": o['open'], "gap_pct": gap,
                   "auc_last_pct": (a or {}).get('pct'), "auc_last": (a or {}).get('latest'),
                   "auc_bid1": (a or {}).get('bid1'), "auc_ask1": (a or {}).get('ask1'),
                   "now_pct": o.get('pct'), "zt_px": round(o['preClose'] * 1.1, 2)}
        print("  %s %s pre=%s open=%s gap=%+.2f%% | 竞价末 %s(%s) bid1=%s ask1=%s | 首帧now=%s%%"
              % (c, o['name'], o['preClose'], o['open'], gap, (a or {}).get('latest'),
                 (a or {}).get('pct'), (a or {}).get('bid1'), (a or {}).get('ask1'), o.get('pct')))
    else:
        print("  %s <<首帧/竞价无此票>>" % c)
        gaps[c] = None

# ---------- ④ 持有/观察照会 ----------
print("\n④ 在持票/观察池 是否在实时观测池(36码)")
pool_codes = set(r['code'] for r in rows)
for c in HOLD:
    print("  持仓 %s in_pool=%s" % (c, c in pool_codes))
for c in WATCH:
    r = next((x for x in rows if x['code'] == c), None)
    print("  观察 %s in_pool=%s pct=%s" % (c, c in pool_codes, r['pct'] if r else None))

json.dump({"cut": CUT, "fetch_ts": fetch_ts, "frames_all": [t['ts'] for t in ticks],
           "frames_in_cut": [t['ts'] for t in T], "dropped": [t['ts'] for t in ticks if t['ts'] > CUT],
           "pool": {"date": last['pool_date'], "n": last['n'], "stale": last['pool_stale']},
           "traj": traj, "snapshot_decision": snap(last), "batch60s": batch1, "batch120s": batch2,
           "gaps": gaps, "hold_in_pool": {c: (c in pool_codes) for c in HOLD},
           "watch": {c: next((r['pct'] for r in rows if r['code'] == c), None) for c in WATCH},
           "peak2trough_top": sorted(rr)[:8]},
          open(os.path.join(D, '_hb_a_calc.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("\n落档: _hb_a_quote.json / _hb_a_calc.json")
