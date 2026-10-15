# -*- coding: utf-8 -*-
"""hb-d(2026-10-15 13:30) 取数: ①决断时点实价(腾讯同源) ②09:25竞价gap ③池内2分钟跳水/炸板
零编造: 一切数字均来自本脚本落档的原始响应/留档文件, 落盘供审计。
"""
import json, os, subprocess, sys, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

D = os.path.dirname(os.path.abspath(__file__))
TICK = os.path.join(D, 'realtime_ticks.jsonl')
AUC = os.path.join(D, 'auction_traj.jsonl')

def ths_code(c):
    c = str(c).split('.')[0]
    return ('sh' if c[0] in '569' else 'sz') + c

def fetch_tencent(codes):
    q = ",".join(ths_code(c) for c in codes)
    url = "http://qt.gtimg.cn/q=" + q
    r = subprocess.run(["curl", "--noproxy", "*", "-s", "-m", "15", url],
                       capture_output=True, timeout=40)
    raw = r.stdout or b''
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
    return url, out

# ---------- ① 决断时点实价 ----------
targets = ["000011", "600693", "605577",            # 在持(账本 + 10/14决断记录)
           "000601", "002343", "000823", "603968"]  # 本日条件单标的
url, quotes = fetch_tencent(targets)
fetch_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
json.dump({"url": url, "fetch_ts": fetch_ts, "src": "腾讯 qt.gtimg.cn",
           "quotes": quotes}, open(os.path.join(D, '_hb_d_quote.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print("① 决断时点实价 fetch_ts=%s" % fetch_ts)
for c in targets:
    v = quotes.get(c)
    if v:
        print("  %s %s latest=%s pct=%s%% open=%s pre=%s high=%s low=%s quote_ts=%s zt=%s dt=%s"
              % (c, v['name'], v['latest'], v['pct'], v['open'], v['preClose'], v['high'],
                 v['low'], v['ts_quote'], v['zt_px'], v['dt_px']))
    else:
        print("  %s <<无数据>>" % c)

# ---------- ② 09:25 竞价 gap(留档复算) ----------
ticks = [json.loads(l) for l in open(TICK, encoding='utf-8')]
auction = [json.loads(l) for l in open(AUC, encoding='utf-8')]
last_auc = auction[-1]
auc_map = {r['code']: r for r in last_auc['rows']}
# 开盘价 = 连续段首帧的 open 字段(交易所开盘价, 非推断)
first_tick = ticks[0]
open_map = {r['code']: r for r in first_tick['rows']}
print("\n② 竞价gap (竞价末帧 %s, 开盘=首帧 open)" % last_auc['ts'])
gaps = {}
for c in ["000601", "002343", "000823", "603968"]:
    o = open_map.get(c)
    a = auc_map.get(c)
    if o:
        gap = round(o['open'] / o['preClose'] * 100 - 100, 2)
        gaps[c] = {"name": o['name'], "open": o['open'], "preClose": o['preClose'], "gap_pct": gap,
                   "auc_last_pct": (a or {}).get('pct')}
        print("  %s %s open=%s pre=%s gap=%+.2f%% 竞价末帧pct=%s"
              % (c, o['name'], o['open'], o['preClose'], gap, (a or {}).get('pct')))
    else:
        print("  %s <<首帧无此票>>" % c)

# ---------- ③ 池内: 炸板 / 2分钟批量跳水 / 尾段分布 ----------
rows_last = ticks[-1]['rows']
lb = {r['code']: r for r in rows_last}
print("\n③ 末帧 %s 池内 n=%d" % (ticks[-1]['ts'], len(rows_last)))
pool_up = [r for r in rows_last if r['pct'] >= 9.8]
pool_dn = [r for r in rows_last if r['pct'] <= -9.8]
# 炸板: 触及涨停价(用pct近似: high/preClose>=9.8%) 但现价未封
zb = []
for r in rows_last:
    hi_pct = r['high'] / r['preClose'] * 100 - 100 if r.get('preClose') else None
    if hi_pct is not None and hi_pct >= 9.8 and r['pct'] < 9.8:
        zb.append((r['code'], r['name'], round(hi_pct, 2), round(r['pct'], 2)))
print("  封板(>=9.8%%)=%d 跌停(<=-9.8%%)=%d 炸板(曾触涨停未封)=%d"
      % (len(pool_up), len(pool_dn), len(zb)))
print("  炸板明细:", "; ".join("%s %s 高%+.1f→现%+.1f" % x for x in zb))

# 2分钟批量跳水: 对每个一分钟相邻帧对, 统计跌幅<=-1.5pp 的票数(池内)
win = [t for t in ticks if t['ts'][11:16] >= '13:00']
frames = [dict((r['code'], r) for r in t['rows']) for t in win]
batch = []
for i in range(1, len(frames)):
    a, b = frames[i - 1], frames[i]
    hits = []
    for c in a:
        if c in b and a[c]['latest'] and b[c]['latest']:
            d = (b[c]['latest'] / a[c]['latest'] - 1) * 100
            if d <= -1.5:
                hits.append((c, b[c]['name'], round(d, 2)))
    if len(hits) >= 3:
        batch.append({"ts": win[i]['ts'], "n": len(hits), "hits": hits})
print("\n  13:00后『≥3只单帧跌≥1.5%%』帧数=%d" % len(batch))
for b in batch[-6:]:
    print("   ", b['ts'], b['n'], b['hits'])

# 池内均值轨迹(午后)
print("\n  午后池均pct: ", "; ".join("%s %+.2f%%" % (t['ts'][11:16], sum(r['pct'] for r in t['rows']) / len(t['rows']))
                                 for t in win[::10]))
json.dump({"open_ticks_ts": first_tick['ts'], "last_ticks_ts": ticks[-1]['ts'],
           "auction_last_ts": last_auc['ts'], "gaps": gaps,
           "pool_last": {"zt": len(pool_up), "dt": len(pool_dn), "zb": len(zb),
                         "zb_detail": [list(x) for x in zb]},
           "batch_dump": batch},
          open(os.path.join(D, '_hb_d_calc.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("\n落档: _hb_d_quote.json / _hb_d_calc.json")
