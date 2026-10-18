# -*- coding: utf-8 -*-
"""hb-a(20261016) 决断文件自审哨兵: 逐项从原始留档重算, 与 临盘决断_20261016_0940.json 比对。
FAIL 即本场不算完成。"""
import json, gzip, csv, io, os, sys, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
D = os.path.dirname(os.path.abspath(__file__))
B = r"D:\股票数据\市场数据"
CUT = '2026-10-16 09:40:55'
fails, oks = [], []

def ck(name, cond, got=None, want=None):
    (oks if cond else fails).append("%s | got=%s want=%s" % (name, got, want))

J = json.load(open(os.path.join(D, '临盘决断_20261016_0940.json'), encoding='utf-8'))
ck("JSON可解析", True)
ck("date/session/ts", (J['date'] == '20261016' and J['session'] == 'hb-a'), (J['date'], J['session']), ('20261016', 'hb-a'))
ck("no_action形状", J.get('no_action') is None, J.get('no_action'), None)

# --- fills 契约 ---
need = {'ts', 'code', 'name', 'action', 'px', 'px_exec', 'qty', 'rule', 'route', 'note'}
for f in J['fills']:
    ck("fill字段完整:%s%s" % (f['code'], f['action']), need <= set(f), sorted(need - set(f)), '—')
    ck("fill action合法:%s" % f['code'], f['action'] in ('fill_buy', 'fill_sell'), f['action'], 'fill_*')
    ck("fill px>0:%s" % f['code'], isinstance(f['px'], (int, float)) and f['px'] > 0, f['px'], '>0')
    ck("fill px_exec>0:%s" % f['code'], isinstance(f['px_exec'], (int, float)) and f['px_exec'] > 0, f['px_exec'], '>0')
    if f['action'] == 'fill_buy':
        ck("买入整手:%s" % f['code'], isinstance(f['qty'], int) and f['qty'] > 0 and f['qty'] % 100 == 0, f['qty'], '整百')
ck("fills条数=4", len(J['fills']) == 4, len(J['fills']), 4)
ck("买2卖2", (sum(1 for f in J['fills'] if f['action'] == 'fill_buy') == 2 and
              sum(1 for f in J['fills'] if f['action'] == 'fill_sell') == 2), None, '2/2')

# --- 原始留档重算 ---
ticks = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8')]
T = [t for t in ticks if t['ts'] <= CUT]
ck("决断窗帧数=10", len(T) == 10, len(T), 10)
ck("决断窗末帧=09:40:07", T[-1]['ts'] == '2026-10-16 09:40:07', T[-1]['ts'], '2026-10-16 09:40:07')
ck("剔除帧均晚于截止", all(t['ts'] > CUT for t in ticks if t not in T), None, True)

A = [json.loads(l) for l in open(os.path.join(D, 'auction_traj.jsonl'), encoding='utf-8')]
auc = {r['code']: r for r in A[-1]['rows']}
t0 = {r['code']: r for r in T[0]['rows']}
gap = {}
for c in ['600668', '605189', '000530']:
    gap[c] = round(t0[c]['open'] / t0[c]['preClose'] * 100 - 100, 2)
    ck("gap复算:%s" % c, abs(gap[c] - (auc[c]['pct'])) < 0.02, gap[c], auc[c]['pct'])
ck("600668 落带[-3,+3]→A", -3.0 <= gap['600668'] <= 3.0, gap['600668'], '[-3,3]')
ck("605189 落带[-3,+5]→A", -3.0 <= gap['605189'] <= 5.0, gap['605189'], '[-3,5]')
ck("000530 破位<-4→B", gap['000530'] < -4.0, gap['000530'], '<-4')
ck("000530 未写fill", not any(f['code'] == '000530' for f in J['fills']), None, True)

fx = {f['code']: f for f in J['fills']}
ck("600668 px=开盘8.15", fx['600668']['px'] == t0['600668']['open'] == 8.15, fx['600668']['px'], 8.15)
ck("605189 px=开盘17.97", fx['605189']['px'] == t0['605189']['open'] == 17.97, fx['605189']['px'], 17.97)
ck("600668 整手复算", fx['600668']['qty'] == int(1000000 * 0.05 / 8.15 / 100) * 100, fx['600668']['qty'], 6100)
ck("605189 整手复算", fx['605189']['qty'] == int(1000000 * 0.02 / 17.97 / 100) * 100, fx['605189']['qty'], 1100)
ck("金额/权重复算", (fx['600668']['qty'] * 8.15 == 49715.0 and fx['605189']['qty'] * 17.97 == 19767.0), None, True)
ck("新暴露≤8%", (49715.0 + 19767.0) / 1000000 * 100 <= 8.0, round((49715.0 + 19767.0) / 1000000 * 100, 2), '≤8')

# --- 竞价快照 ---
rows = list(csv.DictReader(io.TextIOWrapper(gzip.open(os.path.join(B, '_学习/竞价快照存档/20261016.csv.gz'), 'rb'), encoding='utf-8')))
idx = {r['代码']: r for r in rows}
ck("快照条数=5576", len(rows) == 5576, len(rows), 5576)
ck("快照mtime<=09:40:55", os.path.getmtime(os.path.join(B, '_学习/竞价快照存档/20261016.csv.gz')) <=
   datetime.datetime(2026, 10, 16, 9, 40, 55).timestamp(), None, True)
for c, want in [('600693', 9.87), ('605577', 17.99), ('000011', 10.86), ('002860', 20.06), ('600668', 8.15), ('605189', 17.97), ('000530', 6.64)]:
    ck("快照今开:%s=%s" % (c, want), float(idx[c]['今开']) == want, idx[c]['今开'], want)
ck("600693 gap=-10.03", float(idx['600693']['高开幅度']) == -10.03, idx['600693']['高开幅度'], -10.03)
# 全市场跌停开盘唯一性
def lim(pre, name, code):
    p = 0.20 if code.startswith(('688', '689', '300', '301')) else (0.05 if 'ST' in name else 0.10)
    return round(pre * (1 + p), 2), round(pre - round(pre * p, 2), 2)
dtl = []
for r in rows:
    try:
        pre = float(r['昨收']); op = float(r['今开'])
    except Exception:
        continue
    if not pre or not op:
        continue
    L, Dn = lim(pre, r['名称'], r['代码'])
    if abs(op - Dn) < 0.005:
        dtl.append(r['代码'])
ck("全市场跌停开盘=1只且=600693", dtl == ['600693'], dtl, ['600693'])
# 002860 引擎价
ck("002860引擎价=开盘×1.001", round(20.06 * 1.001, 2) == 20.08, round(20.06 * 1.001, 2), 20.08)

# --- 在持票在池内 ---
pool = set(r['code'] for r in T[-1]['rows'])
hold = ['000011', '002860', '600693', '605577', '000601', '603968', '000823']
ck("7只持票全不在池", all(c not in pool for c in hold), [c for c in hold if c in pool], [])

# --- 仓位/账本事实 ---
st = json.load(open(os.path.join(B, '_学习/_模拟盘/master/状态.json'), encoding='utf-8'))
ck("master现金830301.19", abs(st['现金'] - 830301.19) < 0.01, st['现金'], 830301.19)
ck("master持仓5", len(st['持仓']) == 5, len(st['持仓']), 5)
ck("master卖票股数", (fx['600693']['qty'] == 4000 and fx['605577']['qty'] == 2200), None, '4000/2200')
led = [json.loads(l) for l in open(os.path.join(B, '_学习/_模拟盘/master/账本.jsonl'), encoding='utf-8') if l.strip()]
ck("master账本末条=20261015", max(x['ts'] for x in led).startswith('2026-10-15'), max(x['ts'] for x in led), '2026-10-15*')
pz = [json.loads(l) for l in open(os.path.join(B, '_学习/_模拟盘/盘中作战/账本.jsonl'), encoding='utf-8') if l.strip()]
ck("第七账末条=002860@20.08", (pz[-1]['code'] == '002860' and pz[-1]['px'] == 20.08), (pz[-1]['code'], pz[-1]['px']), ('002860', 20.08))
ck("warboard缺件(15/16)", (not os.path.exists(os.path.join(B, '盘中/20261015/warboard.json'))) and
   (not os.path.exists(os.path.join(B, '盘中/20261016/warboard.json'))), None, True)
ck("执行流水缺件", not os.path.exists(os.path.join(D, '执行流水.jsonl')), None, True)
ck("pulse缺件", not os.path.exists(os.path.join(D, 'pulse.json')), None, True)
ck("报警文件缺件", not os.path.exists(os.path.join(D, '报警_20261016.jsonl')), None, True)

# --- 覆盖性检查(发出版不可覆盖) ---
import glob
others = [p for p in glob.glob(os.path.join(B, '盘中/*/临盘决断_*_0940.json'))]
prev = [p for p in others if '20261016' not in p]
ck("本文件名正确", os.path.basename(__file__).endswith('.py'), None, True)
ck("未覆盖历史0940文件(仅新建本日)", len(others) == len(prev) + 1, others, '历史+1')

print("== hb-a 自审 ==")
for x in oks:
    print(" OK  " + x)
print("  合计 OK=%d FAIL=%d" % (len(oks), len(fails)))
if fails:
    print("FAIL 明细:")
    for x in fails:
        print(" FAIL " + x)
    sys.exit(3)
print("哨兵: PASS")
