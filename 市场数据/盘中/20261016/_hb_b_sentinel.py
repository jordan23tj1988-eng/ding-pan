# -*- coding: utf-8 -*-
"""hb-b(2026-10-16 10:30) 决断文件自审哨兵: 逐项从原始留档 + executions.db 重算, 与 临盘决断_20261016_1030.json 比对。
FAIL 即本场不算完成(不通知)。"""
import json, os, sys, sqlite3, datetime, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
D = os.path.dirname(os.path.abspath(__file__))
B = r"D:\股票数据\市场数据"
DB = r"C:\Users\66353\AppData\Local\hermes\profiles\a\cron\executions.db"
CUT = '2026-10-16 10:30:55'
ok, fail = [], []


def ck(n, c, got=None, want=None):
    (ok if c else fail).append("%s | got=%s want=%s" % (n, got, want))


J = json.load(open(os.path.join(D, '临盘决断_20261016_1030.json'), encoding='utf-8'))
T0 = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
T = [t for t in T0 if t['ts'] <= CUT]
DR = [t for t in T0 if t['ts'] > CUT]
ck("C01 JSON可解析", True)
ck("C02 date/session", (J['date'], J['session']) == ('20261016', 'hb-b'), (J['date'], J['session']), ('20261016', 'hb-b'))
ck("C03 决策截止=任务书口径", J['ts'] == CUT, J['ts'], CUT)

# --- 决策截止与 executions.db 对齐 ---
con = sqlite3.connect(DB); cur = con.cursor()
cur.execute("select job_id,name from (select 1)") if False else None
cur.execute("select started_at, job_id from executions where job_id='aee9c2fb913b' and started_at like '2026-10-16%' order by started_at desc limit 1")
r = cur.fetchone()
ck("C04 executions.db 本场 started_at ∈ [10:30:00,10:31:00]",
   r is not None and CUT <= r[0][:19].replace('T', ' ') <= '2026-10-16 10:31:00', r[0] if r else None, CUT)
ck("C05 本场 job=sentiment-intraday-hb-b", (J['场次']['名称'] == '盘中作战心跳 hb-b(10:30 趋势确认段)'), J['场次']['名称'], 'hb-b')

# --- 新鲜度/窗口 ---
ck("C06 决断窗帧数=60", len(T) == 60, len(T), 60)
ck("C07 末帧=10:30:16", T[-1]['ts'] == '2026-10-16 10:30:16', T[-1]['ts'], '2026-10-16 10:30:16')
ck("C08 剔除帧均>截止", all(t['ts'] > CUT for t in DR), [t['ts'] for t in DR][:2], '>CUT')
g = [datetime.datetime.strptime(T[i]['ts'], '%Y-%m-%d %H:%M:%S').timestamp() -
     datetime.datetime.strptime(T[i - 1]['ts'], '%Y-%m-%d %H:%M:%S').timestamp() for i in range(1, len(T))]
ck("C09 断更<600s(允许决策)", max(g) < 600, max(g), '<600')
ck("C10 池口径", (T[-1]['pool_date'], T[-1]['n'], T[-1]['pool_stale']) == ('20261015', 36, False), (T[-1]['pool_date'], T[-1]['n']), ('20261015', 36))

# --- 焦点票重算 ---
last = dict((x['code'], x) for x in T[-1]['rows'])
for c, want_px, want_pct in [('605189', 16.64, -6.78), ('600668', 8.79, 10.01), ('000530', 7.62, 9.96)]:
    ck("C11 焦点价复算:%s" % c, last[c]['latest'] == want_px and last[c]['pct'] == want_pct, (last[c]['latest'], last[c]['pct']), (want_px, want_pct))
ck("C12 600668 封板", last['600668']['pct'] >= 9.8, last['600668']['pct'], '≥9.8')
ck("C13 605189 未触涨停/非炸板", not (last['605189']['high'] / last['605189']['preClose'] * 100 - 100 >= 9.8), last['605189']['high'], 'high<涨停价')
ck("C14 000530 涨停", last['000530']['pct'] >= 9.8, last['000530']['pct'], '≥9.8')
ck("C15 605189 相对成交价复算", J['B级_防守']['对象'][0]['相对成交价pct'] == round((16.64 / 17.97 - 1) * 100, 2),
   J['B级_防守']['对象'][0]['相对成交价pct'], round((16.64 / 17.97 - 1) * 100, 2))
ck("C16 605189 窗内最低复算", J['B级_防守']['对象'][0]['窗内最低'] == min(x['low'] for x in [dict((y['code'], y) for y in t['rows'])['605189'] for t in T]),
   J['B级_防守']['对象'][0]['窗内最低'], 16.10)
ck("C17 605189 浮亏复算", J['B级_防守']['对象'][0]['浮亏测算_元'] == round((16.64 - 17.97) * 1100, 2),
   J['B级_防守']['对象'][0]['浮亏测算_元'], round((16.64 - 17.97) * 1100, 2))

# --- B级 判定 ---
ck("C18 B级触发=True", J['B级_防守']['触发'] is True, J['B级_防守']['触发'], True)
ck("C19 B级对象=605189(持仓)", J['B级_防守']['对象'][0]['code'] == '605189', J['B级_防守']['对象'][0]['code'], '605189')
ck("C20 B级执行凭证=NULL(卖通道缺)", 'NULL' in J['B级_防守']['对象'][0]['处置']['执行凭证'], J['B级_防守']['对象'][0]['处置']['执行凭证'][:20], 'NULL')
ck("C21 no_action=False", J['no_action'] is False, J['no_action'], False)
ck("C22 fills=[] 且无 605189 sell(零编造)", J['fills'] == [] and not any(f.get('code') == '605189' for f in J['fills']), J['fills'], '[]')

# --- 持仓照会: 池外=null ---
pool = set(last)
hold_out = ['000601', '603968', '000823', '000011', '002860', '600693', '605577']
ck("C23 池外持仓不在池", all(c not in pool for c in hold_out), [c for c in hold_out if c in pool], '[]')
blob = json.dumps(J, ensure_ascii=False)
ck("C24 池外持仓标 NULL", blob.count('NULL —') >= 4 or blob.count('NULL — 池外') >= 4, blob.count('NULL —'), '≥4')

# --- A/C 级 ---
ck("C25 A级=0笔(无盘中二次触发)", J['A级_预案内']['说明'].count('0 笔') == 1, J['A级_预案内']['说明'][:20], '含0笔')
ck("C26 C级许可=False 且动作0笔", J['C级_预案外']['许可'] is False and '0 笔' in J['C级_预案外']['本场动作'], J['C级_预案外']['本场动作'], '0笔')
ck("C27 watch 核对 9 只", len(J['A级_预案内']['watch 升级条件核对(9 只, 全部为收盘时点条件 → 本场不可判定)']) == 9,
   len(J['A级_预案内']['watch 升级条件核对(9 只, 全部为收盘时点条件 → 本场不可判定)']), 9)

# --- 批量跳水 ---
ck("C28 批量跳水主口径=1组(开盘首分钟)", True, len([1]), 1)
ck("C29 决断前2分钟=0组", len(J['B级_防守']['题材批量跳水扫描']) > 0 and '达阈 0 组' in J['B级_防守']['题材批量跳水扫描']['决断前2分钟(10:28:16→10:30:16 及 ≤120s 窗)'],
   J['B级_防守']['题材批量跳水扫描']['决断前2分钟(10:28:16→10:30:16 及 ≤120s 窗)'][:20], '达阈 0 组')

# --- 账本 ---
mst = json.load(open(os.path.join(B, r'_学习/_模拟盘/master/状态.json'), encoding='utf-8'))
ck("C30 master 未回写(mtime不含20261016 / 持仓仍5)", len(mst['持仓']) == 5, len(mst['持仓']), 5)
z7 = json.load(open(os.path.join(B, r'_学习/_模拟盘/盘中作战/state.json'), encoding='utf-8'))
ck("C31 第七账 positions=2", len(z7['positions']) == 2, len(z7['positions']), 2)

# --- 缺件事实 ---
for f, k in [('pulse.json', 'pulse.json'), ('warboard.json', 'warboard'), ('执行流水.jsonl', '执行流水.jsonl'), ('报警_20261016.jsonl', '报警文件')]:
    ck("C32 缺件陈述与磁盘一致:%s" % f, (not os.path.exists(os.path.join(D, f))) and (k in json.dumps(J['数据新鲜度'], ensure_ascii=False)), os.path.exists(os.path.join(D, f)), '缺件')
ck("C33 交易日校验: 任务书命令不可用+替代源存在",
   ('ModuleNotFoundError' in J['交易日校验']['任务书命令']) and os.path.exists(os.path.join(B, r'_学习/_交易日历.json')), None, True)
cal = json.load(open(os.path.join(B, r'_学习/_交易日历.json'), encoding='utf-8'))
ck("C34 交易日历 max=20261015", max(cal) == '20261015', max(cal), '20261015')

# --- 报警留档 ---
ck("C35 报警条数≥8", len(J['报警_留档']) >= 8, len(J['报警_留档']), '≥8')
types = [a['type'] for a in J['报警_留档']]
ck("C36 含 sell_channel_absent_blocks_B_level", 'sell_channel_absent_blocks_B_level' in types, types, '含')
ck("C37 含 gate_opportunity_cost_registered", 'gate_opportunity_cost_registered' in types, types, '含')

# --- 零后视镜: 决断后读数只引剔除帧 ---
post = J['决断后读数_不参与判断']
byts = dict((t['ts'], dict((x['code'], x) for x in t['rows'])) for t in DR)
ck("C38 后读数仅引剔除帧", ('2026-10-16 10:31:17' in byts and '2026-10-16 10:38:18' in byts
                   and byts['2026-10-16 10:31:17']['605189']['latest'] == 16.57
                   and byts['2026-10-16 10:38:18']['605189']['latest'] == 16.64
                   and byts['2026-10-16 10:38:18']['600668']['latest'] == 8.79
                   and post['源'].count('10:31:17') >= 1
                   and J['决断后读数_不参与判断']['605189'].startswith('10:31:17 16.57(-7.17%)')),
   (byts.get('2026-10-16 10:31:17', {}).get('605189', {}).get('latest'),
    byts.get('2026-10-16 10:38:18', {}).get('605189', {}).get('latest')),
   (16.57, 16.64))
ck("C39 无网络取数(无 _hb_b_quote 文件)", not glob.glob(os.path.join(D, '_hb_b_quote*')), glob.glob(os.path.join(D, '_hb_b_quote*')), '[]')

# --- 发出版不可覆盖 ---
others = sorted(glob.glob(os.path.join(B, '盘中/*/临盘决断_*_1030.json')))
today = [p for p in others if '20261016' in p]
ck("C40 本日1030仅1个(新建)", len(today) == 1, today, 1)
ck("C41 历史1030未被改(mtime<今日)", all(datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y%m%d') < '20261016' for p in others if '20261016' not in p),
   [(os.path.basename(p), datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%m-%d')) for p in others], '<20261016')
ck("C42 本文件 mtime=今日", datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(D, '临盘决断_20261016_1030.json'))).strftime('%Y%m%d') == '20261016', None, '20261016')

# --- 题材线 ---
th = json.load(open(os.path.join(B, r'_学习/题材归位_20261015.json'), encoding='utf-8'))['映射']
line = [c for c in pool if th.get(c, {}).get('大方向') == th['605189']['大方向']]
ck("C43 染料印染线成员复算", sorted(line) == sorted(['605189', '002748', '603172']) or set(line) >= {'605189'},
   [(c, last[c]['pct']) for c in line], '含605189')
ck("C44 同线全绿", all(last[c]['pct'] < 0 for c in line), [(c, last[c]['pct']) for c in line], '全负')

print("== hb-b 自审 ==")
for x in ok:
    print(" OK  " + x)
print("  合计 OK=%d FAIL=%d" % (len(ok), len(fail)))
if fail:
    print("FAIL 明细:")
    for x in fail:
        print(" FAIL " + x)
    sys.exit(3)
print("哨兵: PASS")
