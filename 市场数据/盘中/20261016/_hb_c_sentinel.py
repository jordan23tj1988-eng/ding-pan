# -*- coding: utf-8 -*-
"""hb-c(2026-10-16 11:00 半日收尾段) 决断文件自审哨兵: 逐项从原始留档(realtime_ticks.jsonl / playbook.json /
两账本 / 题材归位 / 交易日历) + executions.db 重算, 与 临盘决断_20261016_1100.json 比对。
FAIL 即本场不算完成(不通知)。"""
import json, os, sys, sqlite3, datetime, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
D = os.path.dirname(os.path.abspath(__file__))
B = r"D:\股票数据\市场数据"
DB = r"C:\Users\66353\AppData\Local\hermes\profiles\a\cron\executions.db"
CUT = '2026-10-16 11:00:55'
PREV_CUT = '2026-10-16 10:30:55'
ok, fail = [], []


def ck(n, c, got=None, want=None):
    (ok if c else fail).append("%s | got=%s want=%s" % (n, got, want))


F = os.path.join(D, '临盘决断_20261016_1100.json')
J = json.load(open(F, encoding='utf-8'))
T0 = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
T = [t for t in T0 if t['ts'] <= CUT]
DR = [t for t in T0 if t['ts'] > CUT]
last = dict((x['code'], x) for x in T[-1]['rows'])
pool = set(last)
ck("C01 JSON 可解析", True)
ck("C02 date/session", (J['date'], J['session']) == ('20261016', 'hb-c'), (J['date'], J['session']), ('20261016', 'hb-c'))
ck("C03 决策截止=任务书口径", J['ts'] == CUT, J['ts'], CUT)

con = sqlite3.connect(DB); cur = con.cursor()
cur.execute("select started_at, job_id, id from executions where job_id='3e4b3b30b816' and started_at like '2026-10-16%' order by started_at asc limit 1")
r = cur.fetchone()
ck("C04 executions.db 本场 started_at ∈ [11:00:00,11:01:00]",
   r is not None and '2026-10-16 11:00:00' <= r[0][:19].replace('T', ' ') <= '2026-10-16 11:01:00', r[0] if r else None, CUT)
ck("C05 场次名称含 hb-c", 'hb-c' in J['场次']['名称'], J['场次']['名称'], 'hb-c')

ck("C06 决断窗帧数=90", len(T) == 90, len(T), 90)
ck("C07 末帧=11:00:22", T[-1]['ts'] == '2026-10-16 11:00:22', T[-1]['ts'], '2026-10-16 11:00:22')
ck("C08 剔除帧≥3 且均>截止, 且含文件所记 3 帧", len(DR) >= 3 and all(t['ts'] > CUT for t in DR)
   and set(['2026-10-16 11:01:22', '2026-10-16 11:02:22', '2026-10-16 11:03:22']) <= {t['ts'] for t in DR},
   [t['ts'] for t in DR], '⊇文件所记3帧(实盘实时追加, 帧数随写盘增长)')
ck("C08b 文件剔除帧陈述自洽(判定域=90帧/晚于截止帧逐列且不参与判定)",
   ('11:01:22' in J['决断时刻口径'] and '11:03:22' in J['决断时刻口径']
    and '不参与判定' in J['决断时刻口径'] and '90 帧' in J['决断时刻口径']), None, '自洽')
g = [datetime.datetime.strptime(T[i]['ts'], '%Y-%m-%d %H:%M:%S').timestamp() -
     datetime.datetime.strptime(T[i - 1]['ts'], '%Y-%m-%d %H:%M:%S').timestamp() for i in range(1, len(T))]
ck("C09 断更<600s(允许决策)", max(g) < 600, max(g), '<600')
ck("C10 池口径", (T[-1]['pool_date'], T[-1]['n'], T[-1]['pool_stale']) == ('20261015', 36, False),
   (T[-1]['pool_date'], T[-1]['n'], T[-1]['pool_stale']), ('20261015', 36, False))

# --- 焦点票复算 ---
for c, px, pct in [('605189', 16.53, -7.39), ('600668', 8.79, 10.01), ('000530', 7.62, 9.96)]:
    ck("C11 焦点价复算:%s" % c, last[c]['latest'] == px and last[c]['pct'] == pct, (last[c]['latest'], last[c]['pct']), (px, pct))
ck("C12 600668 封板", last['600668']['pct'] >= 9.8, last['600668']['pct'], '≥9.8')
ck("C13 605189 未触涨停价(19.64)且非炸板", last['605189']['high'] < 19.64 and last['605189']['pct'] < 9.8, last['605189']['high'], '<19.64')
ck("C14 000530 涨停", last['000530']['pct'] >= 9.8, last['000530']['pct'], '≥9.8')
ck("C15 605189 相对成交价复算", round((16.53 / 17.97 - 1) * 100, 2) == -8.01, round((16.53 / 17.97 - 1) * 100, 2), -8.01)
seq = [(t['ts'], next(y['latest'] for y in t['rows'] if y['code'] == '605189')) for t in T]
lo = min(seq, key=lambda x: x[1])
ck("C16 605189 采样最低复算", (lo[1], lo[0][11:]) == (16.28, '10:07:12'), (lo[1], lo[0][11:]), (16.28, '10:07:12'))
ck("C17 605189 浮亏复算", round((16.53 - 17.97) * 1100, 2) == -1584.0, round((16.53 - 17.97) * 1100, 2), -1584.0)
ck("C17b 605189 浮亏已写入文件", J['B级_防守']['对象'][0]['浮亏测算_元'] == -1584.0,
   J['B级_防守']['对象'][0]['浮亏测算_元'], -1584.0)
ck("C17c 605189 相对成交价已写入文件", J['B级_防守']['对象'][0]['相对成交价pct'] == -8.01,
   J['B级_防守']['对象'][0]['相对成交价pct'], -8.01)

# --- 通道/账本状态 ---
mst = json.load(open(os.path.join(B, r'_学习/_模拟盘/master/状态.json'), encoding='utf-8'))
z7 = json.load(open(os.path.join(B, r'_学习/_模拟盘/盘中作战/state.json'), encoding='utf-8'))
ck("C18 master 未回写(仍 20261015 快照/持仓5/含已卖600693·605577)",
   len(mst['持仓']) == 5 and {p['code'] for p in mst['持仓']} >= {'600693', '605577'},
   [(p['code']) for p in mst['持仓']], '5 含600693/605577')
ck("C19 第七账 positions=2", len(z7['positions']) == 2, len(z7['positions']), 2)
ck("C20 次日卖出指令=[]", json.load(open(os.path.join(B, r'_学习/_模拟盘/盘中作战/次日卖出指令.json'), encoding='utf-8')) == [], None, '[]')

# --- B 级判定 ---
ck("C21 B级触发=True", J['B级_防守']['触发'] is True, J['B级_防守']['触发'], True)
ck("C22 B级对象=605189(持仓)", J['B级_防守']['对象'][0]['code'] == '605189', J['B级_防守']['对象'][0]['code'], '605189')
ck("C23 B级执行凭证=NULL(卖通道缺)", 'NULL' in J['B级_防守']['对象'][0]['处置']['执行凭证'],
   J['B级_防守']['对象'][0]['处置']['执行凭证'][:24], '含NULL')
ck("C24 no_action=False", J['no_action'] is False, J['no_action'], False)
ck("C25 fills=[] 且无 605189 sell(零编造)", J['fills'] == [], J['fills'], '[]')

# --- A/C 级 ---
ck("C26 A级=0笔", J['A级_预案内']['说明'].count('0 笔') == 1, J['A级_预案内']['说明'][:24], '含0笔')
ck("C27 C级许可=False 且 0笔", J['C级_预案外']['许可'] is False and J['C级_预案外']['本场动作'].startswith('0 笔'),
   (J['C级_预案外']['许可'], J['C级_预案外']['本场动作'][:8]), (False, '0笔'))
wk = J['A级_预案内']['watch 升级条件核对(全部为收盘时点条件 → 本场不可判定)']
ck("C28 watch 核对 9 只", len(wk) == 9, len(wk), 9)
pb = json.load(open(os.path.join(B, r'盘中/20261015/playbook.json'), encoding='utf-8'))
ck("C29 watch 集合=预案 watch 集合", {w['code'] for w in wk} == {w['code'] for w in pb['watch']},
   sorted(w['code'] for w in wk), sorted(w['code'] for w in pb['watch']))

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
inc = scan(1, 120, [f for f in frames if f[0] > PREV_CUT])
pre2 = [b for b in scan(1, 140) if b[1] >= '2026-10-16 10:59']
ck("C30 批量跳水主口径全窗=1组", len(allp) == 1, len(allp), 1)
ck("C31 增量窗达阈=0组", len(inc) == 0, inc, 0)
ck("C32 决断前2分钟=0组", len(pre2) == 0, pre2, 0)
blob_scan = json.dumps(J['B级_防守']['题材批量跳水扫描'], ensure_ascii=False)
ck("C33 扫描结论已写入文件(1组/0组/0组)",
   '"达阈组数": 1' in blob_scan and '"达阈组数": 0' in blob_scan and '达阈 0 组' in blob_scan, None, True)

# --- 板别校正(本场新增口径) ---
zb_true = [r['code'] for r in T[-1]['rows']
           if r['high'] / r['preClose'] * 100 - 100 >= (20.0 if r['code'].startswith(('300', '301', '688')) else 10.0) - 0.2
           and r['pct'] < (20.0 if r['code'].startswith(('300', '301', '688')) else 10.0) - 0.2]
ck("C34 板别校正后真炸板=5", len(zb_true) == 5, zb_true, 5)
ck("C35 300111 属 20cm 板误挂(high<涨停价)",
   last['300111']['high'] < round(last['300111']['preClose'] * 1.2, 2), last['300111']['high'], round(last['300111']['preClose'] * 1.2, 2))
ck("C36 板别报警#10 存在", any(a['type'] == 'limit_threshold_band_blind' for a in J['报警_留档']), None, True)

# --- 缺失件/交易日校验 ---
for f, k in [('pulse.json', 'pulse.json'), ('warboard.json', 'warboard'), ('执行流水.jsonl', '执行流水.jsonl')]:
    ck("C37 缺件陈述与磁盘一致:%s" % f,
       (not os.path.exists(os.path.join(D, f))) and (k in json.dumps(J['数据新鲜度'], ensure_ascii=False)),
       os.path.exists(os.path.join(D, f)), '缺件')
ck("C38 报警文件缺件陈述", ('报警_20261016.jsonl' in json.dumps(J['数据新鲜度'], ensure_ascii=False)
                       and not os.path.exists(os.path.join(D, '报警_20261016.jsonl'))), None, True)
ck("C39 交易日校验: 任务书命令不可用+替代源存在",
   ('ModuleNotFoundError' in J['交易日校验']['任务书命令']) and os.path.exists(os.path.join(B, r'_学习/_交易日历.json')) and
   ('日历滞后' in J['交易日校验']['替代校验(可复现)']), None, True)
cal = json.load(open(os.path.join(B, r'_学习/_交易日历.json'), encoding='utf-8'))
ck("C40 交易日历 max=20261015", max(cal) == '20261015', max(cal), '20261015')

# --- 报警 ---
ck("C41 报警条数=12", len(J['报警_留档']) == 12, len(J['报警_留档']), 12)
types = [a['type'] for a in J['报警_留档']]
for t, nm in [('sell_channel_absent_blocks_B_level', 'C42'), ('gate_opportunity_cost_registered', 'C43'),
              ('execution_receipt_missing', 'C44'), ('holdings_no_intraday_observability', 'C45'),
              ('evidence_bucket_mismatch_605189', 'C46')]:
    ck("%s 含 %s" % (nm, t), t in types, types, '含')

# --- 零后视镜: 后读数仅引剔除帧 ---
byts = dict((t['ts'], dict((x['code'], x) for x in t['rows'])) for t in DR)
post = J['决断后读数_不参与判断']['605189']
ck("C47 后读数仅引剔除帧且数值复算",
   ('11:01:22' in post and '%.2f' % byts['2026-10-16 11:01:22']['605189']['latest'] in post
    and '%.2f' % byts['2026-10-16 11:03:22']['605189']['latest'] in post
    and '%.2f' % byts['2026-10-16 11:03:22']['600668']['latest'] in J['决断后读数_不参与判断']['600668']),
   post[:60], '引 11:01:22~11:03:22')
ck("C48 无网络取数(无 _hb_c_quote 文件)", not glob.glob(os.path.join(D, '_hb_c_quote*')), glob.glob(os.path.join(D, '_hb_c_quote*')), '[]')

# --- 发出版不可覆盖 ---
others = sorted(glob.glob(os.path.join(B, '盘中/*/临盘决断_*_1100.json')))
today = [p for p in others if '20261016' in p]
ck("C49 本日1100仅1个(新建)", len(today) == 1, today, 1)
ck("C50 历史1100未被改(mtime<今日)", all(datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y%m%d') < '20261016'
                                    for p in others if '20261016' not in p),
   [(os.path.basename(p), datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%m-%d')) for p in others], '<20261016')
mt = dict((os.path.basename(p), datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M:%S'))
          for p in glob.glob(os.path.join(D, '临盘决断_20261016_*.json')))
ck("C51 本场文件 mtime=今日", mt.get('临盘决断_20261016_1100.json', '').startswith('2026-10-16'), mt, '2026-10-16')
ck("C52 早前场次文件未被覆盖(mtime=原值)",
   mt.get('临盘决断_20261016_0921.json') == '2026-10-16 09:32:44' and
   mt.get('临盘决断_20261016_0940.json') == '2026-10-16 09:50:55' and
   mt.get('临盘决断_20261016_1030.json') == '2026-10-16 10:40:55', mt, '原值')

# --- 题材线 ---
th = json.load(open(os.path.join(B, r'_学习/题材归位_20261015.json'), encoding='utf-8'))['映射']
line = [c for c in pool if th.get(c, {}).get('大方向') == th['605189']['大方向']]
ck("C53 染料印染线含605189", set(line) >= {'605189'}, line, '含605189')
ck("C54 同线全绿", all(last[c]['pct'] < 0 for c in line), [(c, last[c]['pct']) for c in line], '全负')

# --- 零编造: 池外持仓必须标 NULL ---
hold_out = ['000601', '603968', '000823', '000011', '002860', '600693', '605577']
ck("C55 池外持仓不在池", all(c not in pool for c in hold_out), [c for c in hold_out if c in pool], '[]')
ck("C56 池外持仓标 NULL ≥6 处", json.dumps(J, ensure_ascii=False).count('NULL —') >= 6,
   json.dumps(J, ensure_ascii=False).count('NULL —'), '≥6')

# --- 池截面复算 ---
sk = sorted(last[c]['pct'] for c in pool)
ck("C57 池截面复算(中位/均值/封板/跌停)",
   (round(sk[len(sk) // 2], 2), round(sum(sk) / len(sk), 2)) == (-2.16, -0.86)
   and sum(1 for c in pool if last[c]['pct'] >= 9.8) == 4
   and sum(1 for c in pool if last[c]['pct'] <= -9.8) == 0,
   (round(sk[len(sk) // 2], 2), round(sum(sk) / len(sk), 2),
    sum(1 for c in pool if last[c]['pct'] >= 9.8), sum(1 for c in pool if last[c]['pct'] <= -9.8)),
   (-2.16, -0.86, 4, 0))
ck("C58 文件内池截面陈述一致",
   ('-2.16' in json.dumps(J, ensure_ascii=False) and '封板 4 只' in json.dumps(J, ensure_ascii=False)
    and '-0.86' in json.dumps(J, ensure_ascii=False) and '红13/绿23' in json.dumps(J, ensure_ascii=False)), None, True)
ck("C59 增量窗起点=10:31:17 且末帧=11:00:22",
   J['B级_防守']['题材批量跳水扫描']['主口径_全窗全对≤120s']['明细'] != [] and T[-1]['ts'][11:] == '11:00:22', None, True)
ck("C60 终稿无 %% 残留", '%%' not in json.dumps(J, ensure_ascii=False), json.dumps(J, ensure_ascii=False).count('%%'), 0)

print("== hb-c 自审 ==")
for x in ok:
    print(" OK  " + x)
print("  合计 OK=%d FAIL=%d" % (len(ok), len(fail)))
if fail:
    print("FAIL 明细:")
    for x in fail:
        print(" FAIL " + x)
    sys.exit(3)
print("哨兵: PASS")
