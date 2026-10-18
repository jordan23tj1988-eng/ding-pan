# -*- coding: utf-8 -*-
"""hb-d(2026-10-16 13:30 午后延续段) 决断文件自审哨兵: 逐项从原始留档(realtime_ticks.jsonl /
playbook.json / 两账本 / 题材归位 / 交易日历) + executions.db 独立重算, 与
临盘决断_20261016_1330.json 比对。FAIL 即本场不算完成(不通知)。
"""
import json, os, sys, sqlite3, datetime, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
D = os.path.dirname(os.path.abspath(__file__))
B = r"D:\股票数据\市场数据"
DB = r"C:\Users\66353\AppData\Local\hermes\profiles\a\cron\executions.db"
CUT = '2026-10-16 13:30:55'
PREV_CUT = '2026-10-16 11:00:55'
ok, fail = [], []


def ck(n, c, got=None, want=None):
    (ok if c else fail).append("%s | got=%s want=%s" % (n, got, want))


F = os.path.join(D, '临盘决断_20261016_1330.json')
J = json.load(open(F, encoding='utf-8'))
Jblob = json.dumps(J, ensure_ascii=False)
T0 = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
T = [t for t in T0 if t['ts'] <= CUT]
DR = [t for t in T0 if t['ts'] > CUT]
last = dict((x['code'], x) for x in T[-1]['rows'])
pool = set(last)
ck("C01 JSON 可解析", True)
ck("C02 date/session", (J['date'], J['session']) == ('20261016', 'hb-d'), (J['date'], J['session']), ('20261016', 'hb-d'))
ck("C03 决策截止=任务书口径", J['ts'] == CUT, J['ts'], CUT)

con = sqlite3.connect(DB); cur = con.cursor()
cur.execute("select started_at, job_id, id from executions where job_id='c415a7792216' and started_at like '2026-10-16%' order by started_at asc limit 1")
r = cur.fetchone()
ck("C04 executions.db 本场 started_at ∈ [13:30:00,13:31:00]",
   r is not None and '2026-10-16 13:30:00' <= r[0][:19].replace('T', ' ') <= '2026-10-16 13:31:00',
   r[0] if r else None, CUT)
ck("C05 场次名称含 hb-d", 'hb-d' in J['场次']['名称'], J['场次']['名称'], 'hb-d')

ck("C06 决断窗帧数=240", len(T) == 240, len(T), 240)
ck("C07 末帧=13:30:49", T[-1]['ts'] == '2026-10-16 13:30:49', T[-1]['ts'], '2026-10-16 13:30:49')
ck("C08 剔除帧≥2 且均>截止, 且含文件所记帧", len(DR) >= 2 and all(t['ts'] > CUT for t in DR)
   and set(['2026-10-16 13:31:49', '2026-10-16 13:32:49']) <= {t['ts'] for t in DR},
   [t['ts'] for t in DR], '⊇文件所记帧(实盘实时追加, 帧数随写盘增长)')
g = [datetime.datetime.strptime(T[i]['ts'], '%Y-%m-%d %H:%M:%S').timestamp() -
     datetime.datetime.strptime(T[i - 1]['ts'], '%Y-%m-%d %H:%M:%S').timestamp() for i in range(1, len(T))]
ck("C09 断更<600s(允许决策)", max(g) < 600, max(g), '<600')
ck("C10 池口径", (T[-1]['pool_date'], T[-1]['n'], T[-1]['pool_stale']) == ('20261015', 36, False),
   (T[-1]['pool_date'], T[-1]['n'], T[-1]['pool_stale']), ('20261015', 36, False))

# --- 午休帧复算(本场新增口径) ---
lunch = [t for t in T if '11:30:00' < t['ts'][11:] < '13:00:00']
same = sum(1 for x, y in zip(lunch[0]['rows'], lunch[-1]['rows']) if x['latest'] == y['latest']) if lunch else 0
ck("C10b 午休帧=90 且逐票冻结", len(lunch) == 90 and same == 36, (len(lunch), same), (90, 36))
ck("C10c 午休陈述已写入文件", '11:30~13:00' in Jblob and '冻结' in Jblob, None, True)

# --- 焦点票复算 ---
for c, px, pct in [('605189', 16.76, -6.11), ('600668', 8.79, 10.01), ('000530', 7.62, 9.96)]:
    ck("C11 焦点价复算:%s" % c, last[c]['latest'] == px and last[c]['pct'] == pct, (last[c]['latest'], last[c]['pct']), (px, pct))
ck("C12 600668 封板", last['600668']['pct'] >= 9.8, last['600668']['pct'], '≥9.8')
ck("C13 605189 未触涨停价(19.64)且非炸板", last['605189']['high'] < 19.64 and last['605189']['pct'] < 9.8, last['605189']['high'], '<19.64')
ck("C14 000530 涨停", last['000530']['pct'] >= 9.8, last['000530']['pct'], '≥9.8')

rel = round((16.76 / 17.97 - 1) * 100, 2)
ck("C15 605189 相对成交价复算", rel == -6.73, rel, -6.73)
ck("C15b 相对成交价已写入文件", J['B级_防守']['对象'][0]['相对成交价pct'] == -6.73,
   J['B级_防守']['对象'][0]['相对成交价pct'], -6.73)
seq = [(t['ts'], next(y['latest'] for y in t['rows'] if y['code'] == '605189')) for t in T]
lo = min(seq, key=lambda x: x[1])
ck("C16 605189 采样最低复算", (lo[1], lo[0][11:]) == (16.28, '10:07:12'), (lo[1], lo[0][11:]), (16.28, '10:07:12'))
pnl = round((16.76 - 17.97) * 1100, 2)
ck("C17 605189 浮亏复算", pnl == -1331.0, pnl, -1331.0)
ck("C17b 浮亏已写入文件", J['B级_防守']['对象'][0]['浮亏测算_元'] == -1331.0,
   J['B级_防守']['对象'][0]['浮亏测算_元'], -1331.0)
inc = [(t['ts'], next(y['latest'] for y in t['rows'] if y['code'] == '605189')) for t in T if t['ts'] > PREV_CUT]
disp = round((inc[-1][1] / inc[0][1] - 1) * 100, 2)
hi = max(inc, key=lambda x: x[1]); lo2 = min(inc, key=lambda x: x[1])
ck("C18 605189 增量窗位移复算", disp == 1.33, disp, 1.33)
ck("C18b 增量窗位移已写入文件", '16.54→16.76(+1.33%)' in Jblob, None, True)
ck("C19 605189 增量窗最高=17.01@13:02:44", (hi[1], hi[0][11:]) == (17.01, '13:02:44'), (hi[1], hi[0][11:]), (17.01, '13:02:44'))
ck("C19b 增量窗最高已写入文件", '17.01@13:02:44' in Jblob, None, True)
ck("C19c 午后未创新低(增量窗最低=起点 16.54)", lo2[1] == inc[0][1] == 16.54 and lo2[0] == inc[0][0], (lo2[1], lo2[0][11:]), (16.54, '11:01:22'))
p668 = round((8.79 / 8.15 - 1) * 100, 2)
ck("C19d 600668 相对成交价/浮盈复算", p668 == 7.85 and round((8.79 - 8.15) * 6100, 2) == 3904.0,
   (p668, round((8.79 - 8.15) * 6100, 2)), (7.85, 3904.0))
lim = [t['ts'] for t in T if next((y['latest'] for y in t['rows'] if y['code'] == '600668'), None) == 8.79]
ck("C19e 600668 恒封帧复算=239 且写入文件", len(lim) == 239 and '239 帧恒封' in Jblob, len(lim), 239)

# --- 通道/账本状态 ---
mst = json.load(open(os.path.join(B, r'_学习/_模拟盘/master/状态.json'), encoding='utf-8'))
z7 = json.load(open(os.path.join(B, r'_学习/_模拟盘/盘中作战/state.json'), encoding='utf-8'))
mpos = mst.get('positions') or mst.get('持仓')
ck("C20 master 未回写(仍 20261015 快照/持仓5/含已卖600693·605577)",
   len(mpos) == 5 and {p['code'] for p in mpos} >= {'600693', '605577'},
   [p['code'] for p in mpos], '5 含600693/605577')
led = [json.loads(l) for l in open(os.path.join(B, r'_学习/_模拟盘/master/账本.jsonl'), encoding='utf-8') if l.strip()]
ck("C20b master 账本 20261016 记录数=0", sum(1 for x in led if x.get('d') == '20261016') == 0,
   sum(1 for x in led if x.get('d') == '20261016'), 0)
ck("C21 第七账 positions=2", len(z7['positions']) == 2, len(z7['positions']), 2)
ck("C22 次日卖出指令=[]", json.load(open(os.path.join(B, r'_学习/_模拟盘/盘中作战/次日卖出指令.json'), encoding='utf-8')) == [], None, '[]')

# --- B 级判定 ---
ck("C23 B级触发=True", J['B级_防守']['触发'] is True, J['B级_防守']['触发'], True)
ck("C24 B级对象=605189(持仓)", J['B级_防守']['对象'][0]['code'] == '605189', J['B级_防守']['对象'][0]['code'], '605189')
ck("C25 B级=维持(非新增, 承 hb-b/hb-c)", '维持' in J['B级_防守']['触发类型'] and '非新增事件' in J['B级_防守']['触发类型'],
   J['B级_防守']['触发类型'][:40], '维持/非新增')
ck("C26 B级执行凭证=NULL(卖通道缺)", 'NULL' in J['B级_防守']['对象'][0]['处置']['执行凭证'],
   J['B级_防守']['对象'][0]['处置']['执行凭证'][:24], '含NULL')
ck("C27 no_action=False", J['no_action'] is False, J['no_action'], False)
ck("C28 fills=[] 且无 sell/buy 记录(零编造)", J['fills'] == [], J['fills'], '[]')

# --- A/C 级 ---
ck("C29 A级=0笔", 'A级 0 笔' in J['A级_预案内']['说明'], J['A级_预案内']['说明'][:24], '含A级 0 笔')
ck("C30 C级许可=False 且 0笔", J['C级_预案外']['许可'] is False and J['C级_预案外']['本场动作'].startswith('0 笔'),
   (J['C级_预案外']['许可'], J['C级_预案外']['本场动作'][:8]), (False, '0笔'))
wk = J['A级_预案内']['watch 9 只(本场核对)']
ck("C31 watch 核对 9 只", len(wk) == 9, len(wk), 9)
pb = json.load(open(os.path.join(B, r'盘中/20261015/playbook.json'), encoding='utf-8'))
ck("C32 watch 集合=预案 watch 集合", {w['code'] for w in wk} == {w['code'] for w in pb['watch']},
   sorted(w['code'] for w in wk), sorted(w['code'] for w in pb['watch']))
ck("C33 预案未改(playbook mtime=2026-10-15 19:59 且 date=20261015)",
   datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(B, r'盘中/20261015/playbook.json'))).strftime('%Y-%m-%d %H:%M') == '2026-10-15 19:59'
   and pb.get('date') == '20261015', pb.get('date'), '20261015')

# --- 批量跳水 ---
frames = [(t['ts'], datetime.datetime.strptime(t['ts'], '%Y-%m-%d %H:%M:%S').timestamp(),
           dict((r['code'], r) for r in t['rows'])) for t in T]


def scan(lo_s, hi_s, src=None):
    src = src or frames
    out = []
    for i in range(len(src)):
        for j in range(i + 1, len(src)):
            dt = src[j][1] - src[i][1]
            if dt < lo_s or dt > hi_s:
                continue
            a, b = src[i][2], src[j][2]
            hits = [c for c in a if c in b and a[c]['latest'] and b[c]['latest']
                    and (b[c]['latest'] / a[c]['latest'] - 1) * 100 <= -3.0]
            if len(hits) >= 3:
                out.append((src[i][0], src[j][0], int(dt), len(hits)))
    return out


allp = scan(1, 120)
incp = scan(1, 120, [f for f in frames if f[0] > PREV_CUT])
pre2 = [b for b in scan(1, 140) if b[1] >= '2026-10-16 13:29']
ck("C34 批量跳水主口径全窗=1组", len(allp) == 1, len(allp), 1)
ck("C34b 唯一达阈组=09:31:06→09:32:06", allp[0][0][11:] == '09:31:06' and allp[0][1][11:] == '09:32:06', allp[:1], '09:31→09:32')
ck("C35 增量窗达阈=0组", len(incp) == 0, incp, 0)
ck("C36 决断前2分钟=0组", len(pre2) == 0, pre2, 0)
ck("C37 扫描结论已写入文件(1组/0组/0组)",
   '"达阈组数": 1' in Jblob and '"达阈组数": 0' in Jblob and '达阈 0 组' in Jblob, None, True)

# --- 池截面复算 ---
sk = sorted(last[c]['pct'] for c in pool)
med = round(sk[len(sk) // 2], 2); mean = round(sum(sk) / len(sk), 2)
zt = sum(1 for c in pool if last[c]['pct'] >= 9.8)
dt_ = sum(1 for c in pool if last[c]['pct'] <= -9.8)
zb = sum(1 for c in pool if last[c]['preClose'] and last[c]['high'] / last[c]['preClose'] * 100 - 100 >= 9.8 and last[c]['pct'] < 9.8)
ck("C38 池截面复算(中位/均值/封板5/跌停3/炸板5)",
   (med, mean, zt, dt_, zb) == (-2.87, -1.32, 5, 3, 5), (med, mean, zt, dt_, zb), (-2.87, -1.32, 5, 3, 5))
ck("C39 文件内池截面陈述一致", '-2.87' in Jblob and '-1.32' in Jblob and '封板 5 只' in Jblob, None, True)
# 跌停逐帧首现复算
dt_first = {}
prev = None
for t in [x for x in T if x['ts'] > PREV_CUT]:
    codes = sorted(r['code'] for r in t['rows'] if r['pct'] <= -9.8)
    for c0 in codes:
        dt_first.setdefault(c0, t['ts'])
ck("C40 跌停首现复算", dt_first == {'001225': '2026-10-16 13:20:47', '002696': '2026-10-16 13:24:48', '002134': '2026-10-16 13:26:48'},
   dt_first, '001225 13:20:47 / 002696 13:24:48 / 002134 13:26:48')
ck("C40b 跌停首现已写入文件", '13:20:47' in Jblob and '13:24:48' in Jblob and '13:26:48' in Jblob, None, True)

# --- 缺失件/交易日校验 ---
for f, k in [('pulse.json', 'pulse.json'), ('warboard.json', 'warboard'), ('执行流水.jsonl', '执行流水.jsonl')]:
    ck("C41 缺件陈述与磁盘一致:%s" % f,
       (not os.path.exists(os.path.join(D, f))) and (k in json.dumps(J['数据新鲜度'], ensure_ascii=False)),
       os.path.exists(os.path.join(D, f)), '缺件')
ck("C42 报警文件缺件陈述", ('报警_20261016.jsonl' in json.dumps(J['数据新鲜度'], ensure_ascii=False)
                       and not os.path.exists(os.path.join(D, '报警_20261016.jsonl'))), None, True)
ck("C43 交易日校验: 任务书命令不可用+替代源存在",
   ('ModuleNotFoundError' in J['交易日校验']['任务书指定命令']) and
   os.path.exists(os.path.join(B, r'_学习/竞价快照存档/20261016.csv.gz')) and
   os.path.exists(os.path.join(B, r'_学习/_交易日历.json')), None, True)
cal = json.load(open(os.path.join(B, r'_学习/_交易日历.json'), encoding='utf-8'))
ck("C44 交易日历 max=20261015(滞后, 已在文件注明)", max(cal) == '20261015', max(cal), '20261015')

# --- 报警 ---
ck("C45 报警条数=11", len(J['报警_留档']) == 11, len(J['报警_留档']), 11)
types = [a['type'] for a in J['报警_留档']]
for t, nm in [('sell_channel_absent_blocks_B_level', 'C46'), ('gate_opportunity_cost_registered', 'C47'),
              ('execution_receipt_missing', 'C48'), ('holdings_no_intraday_observability', 'C49'),
              ('afternoon_pool_decay_and_limitdown_cluster', 'C50'), ('lunch_session_frames_frozen', 'C51'),
              ('limit_threshold_band_blind', 'C52'), ('warboard_pulse_alarm_missing', 'C53')]:
    ck("%s 含 %s" % (nm, t), t in types, types, '含')

# --- 零后视镜: 后读数仅引剔除帧 ---
byts = dict((t['ts'], dict((x['code'], x) for x in t['rows'])) for t in DR)
src_txt = J['决断后读数_不参与判断']['源']
import re as _re
src_list = _re.findall(r"'(2026-10-16 \d\d:\d\d:\d\d)'", src_txt)
post = J['决断后读数_不参与判断']['剔除帧逐票读数']
ck("C54 后读数仅引剔除帧且数值复算",
   len(post) >= 1 and len(src_list) >= len(post)
   and all(t_ in src_list and t_ > CUT for t_ in src_list)
   and all(e['ts'] in byts and all(
       abs(e[c]['latest'] - byts[e['ts']][c]['latest']) < 1e-9 and abs(e[c]['pct'] - byts[e['ts']][c]['pct']) < 1e-9
       for c in ('600668', '605189', '000530')) for e in post),
   [(e['ts'], e['605189']) for e in post], '剔除帧读数(ts 逐条对上原始帧)')
ck("C55 无网络取数(无 _hb_d_quote 文件)", not glob.glob(os.path.join(D, '_hb_d_quote*')), glob.glob(os.path.join(D, '_hb_d_quote*')), '[]')
ck("C56 判定区不含晚于截止的读数(零后视镜)",
   all(k not in json.dumps(J['B级_防守'], ensure_ascii=False) for k in ('13:31:49', '13:32:49', '13:33')), None, True)

# --- 发出版不可覆盖 ---
others = sorted(glob.glob(os.path.join(B, '盘中/*/临盘决断_*_1330.json')))
today = [p for p in others if '20261016' in p]
ck("C57 本日1330仅1个(新建)", len(today) == 1, today, 1)
ck("C58 历史1330未被改(mtime<今日)", all(datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y%m%d') < '20261016'
                                     for p in others if '20261016' not in p),
   [(os.path.basename(p), datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%m-%d')) for p in others], '<20261016')
mt = dict((os.path.basename(p), datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M:%S'))
          for p in glob.glob(os.path.join(D, '临盘决断_20261016_*.json')))
ck("C59 本场文件 mtime=今日", mt.get('临盘决断_20261016_1330.json', '').startswith('2026-10-16'), mt, '2026-10-16')
ck("C60 早前场次文件未被覆盖(mtime=原值)",
   mt.get('临盘决断_20261016_0921.json') == '2026-10-16 09:32:44' and
   mt.get('临盘决断_20261016_0940.json') == '2026-10-16 09:50:55' and
   mt.get('临盘决断_20261016_1030.json') == '2026-10-16 10:40:55' and
   mt.get('临盘决断_20261016_1100.json') == '2026-10-16 11:09:27', mt, '原值')
ck("C61 v1/v2 草稿已归档(可追溯)",
   os.path.exists(os.path.join(D, '_hb_d_1330_v1_superseded.json')) and
   os.path.exists(os.path.join(D, '_hb_d_1330_v2_superseded.json')) and
   'v3' in J['版本']['本版'] and len(J['版本']['前版']) == 2, None, True)

# --- 题材线 ---
th = json.load(open(os.path.join(B, r'_学习/题材归位_20261015.json'), encoding='utf-8'))['映射']
line = [c for c in pool if th.get(c, {}).get('大方向') == th['605189']['大方向']]
ck("C62 染料印染线含605189", set(line) >= {'605189'}, line, '含605189')
ck("C63 同线全绿", all(last[c]['pct'] < 0 for c in line), [(c, last[c]['pct']) for c in line], '全负')

# --- 零编造: 池外持仓必须标 NULL ---
hold_out = ['000601', '603968', '000823', '000011', '002860', '600693', '605577']
ck("C64 池外持仓不在池", all(c not in pool for c in hold_out), [c for c in hold_out if c in pool], '[]')
ck("C65 池外持仓标 NULL ≥6 处", Jblob.count('NULL —') >= 6, Jblob.count('NULL —'), '≥6')

ck("C66 终稿无 %% 残留", '%%' not in Jblob, Jblob.count('%%'), 0)
ck("C67 权限分级未越权(0笔A/C, 无 weight 记录)", ('weight≤10%' in J['场次']['权限'] and J['fills'] == [] and J['C级_预案外']['许可'] is False), None, True)

print("== hb-d 自审 ==")
for x in ok:
    print(" OK  " + x)
print("  合计 OK=%d FAIL=%d" % (len(ok), len(fail)))
if fail:
    print("FAIL 明细:")
    for x in fail:
        print(" FAIL " + x)
    sys.exit(3)
print("哨兵: PASS")
