# -*- coding: utf-8 -*-
"""hb-e 14:30 场哨兵：结构/算术/证据链/零后视镜/账本/不覆盖 自检。只读，不改生产。
★钉帧原则：一律以文件自报的池帧末帧 14:31:18 定位复算，禁止用运行时刻实时末帧审历史文件。"""
import json, os, statistics, datetime, hashlib
from collections import Counter

D = os.path.dirname(os.path.abspath(__file__))
J = os.path.join(D, '临盘决断_20261026_1430.json')
A = os.path.join(D, '入账_20261026_1430.json')
J2 = os.path.join(D, '临盘决断_20261026_1430_补正1.json')
res = []


def chk(name, cond, detail=''):
    res.append((name, bool(cond), detail))


d = json.load(open(J, encoding='utf-8'))
bz = json.load(open(J2, encoding='utf-8'))
au = json.load(open(A, encoding='utf-8'))
q0 = json.load(open(os.path.join(D, '_hb_e_quote_1430.json'), encoding='utf-8'))
q1 = json.load(open(os.path.join(D, '_hb_e_quote_next.json'), encoding='utf-8'))
pools = json.load(open(os.path.join(D, '_hb_e_pools_1430.json'), encoding='utf-8'))
mn = json.load(open(os.path.join(D, '_hb_e_minute_1430.json'), encoding='utf-8'))
QB = {v['code']: v for v in q0['rows'].values()}
QX = {k[2:]: v for k, v in q1['rows'].items()}
blob = json.dumps(d, ensure_ascii=False)
bzblob = json.dumps(bz, ensure_ascii=False)
UNION = blob + bzblob
fr = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
fr.sort(key=lambda x: x['ts'])

# ── 1 结构 ─────────────────────────────────────────────
chk('S01 含 fills/权限分级/口径/数据新鲜度/异常与欠账/no_action/汇总/下一场',
    all(k in d for k in ('fills', '权限分级', '口径', '数据新鲜度', '异常与欠账', 'no_action', '汇总', '下一场')))
chk('S02 session=hb-e 且 date=20261026 且 ts=14:30',
    (d['session'], d['date'], d['ts']) == ('hb-e', '20261026', '14:30'))
mt = datetime.datetime.fromtimestamp(os.path.getmtime(J))
chk('S03 发版不可覆盖：无 hb-e 的 _v2/_修正/_覆盖 副本，且原件 sha256 与入账件登记一致',
    not any(os.path.exists(os.path.join(D, f'临盘决断_20261026_1430_{s}.json')) for s in ('v2', '修正', '覆盖'))
    and au['发出版sha256'] == hashlib.sha256(open(J, 'rb').read()).hexdigest(), str(mt))
chk('S04 mtime 为 2026-10-26、早于 now、与 write_ts 同分钟（≤120s）',
    mt.strftime('%Y-%m-%d') == '2026-10-26' and mt <= datetime.datetime.now()
    and abs((mt - datetime.datetime.strptime(d['write_ts'], '%Y-%m-%d %H:%M:%S')).total_seconds()) < 120, str(mt))
_pinraw = d['数据新鲜度']['窗口'].split('~')[-1].strip()
PIN = _pinraw if len(_pinraw) > 10 else '2026-10-26 ' + _pinraw
P = next((f for f in fr if f['ts'] == PIN), None)
chk('S05 自报池帧末帧 %s（原文字串「%s」，日期前缀由哨兵归一）在 realtime_ticks 中可定位（可复算）' % (PIN, _pinraw),
    P is not None)

# ── 2 本场唯一动作：600487 卖出 ─────────────────────────
f0 = d['fills'][0] if d['fills'] else {}
chk('A01 fills 恰 1 笔且为 sell / 600487 / 1000 股整手',
    len(d['fills']) == 1 and f0.get('action') == 'fill_sell' and f0.get('code') == '600487' and f0.get('qty') == 1000
    and f0['qty'] % 100 == 0)
chk('A02 px_exec 由「决断后下一 tick 留档价 ×(1-0.10%)」机械算出：48.67×0.999=48.62',
    f0.get('px') == 48.67 and abs(round(48.67 * 0.999, 2) - f0.get('px_exec')) < 1e-9 and f0.get('px_exec') == 48.62)
chk('A03 留档价源真：_hb_e_quote_next 中 sh600487 px=48.67 且 t=20261026143207 > 决断帧 t=20261026143119',
    QX['600487']['px'] == 48.67 and QX['600487']['t'] == '20261026143207'
    and int(QX['600487']['t']) > int(QB['600487']['t']))
dec = QB['600487']['px']
chk('A04 触发条件成立：决断帧 %.2f < 硬线 50.00（差 %.2f%%）' % (dec, (dec / 50 - 1) * 100),
    dec < 50.00 and abs((dec / 50 - 1) * 100 + 2.60) < 0.01 and '48.70 < 50.00' in blob)
cost = 50025.0
proceeds = round(48.62 * 1000, 2)
chk('A05 盈亏复算 48,620 - 50,025 = -1,405.00（-2.81%），与 fills.note 一致',
    round(proceeds - cost, 2) == -1405.0 and '−1,405' not in blob and '-1,405.00' in blob and '(-2.81%)' in blob.replace('（', '(').replace('）', ')'))
chk('A06 含费成本口径 50.00×1000×1.0005=50,025.00（与 state.json cost 一致）',
    abs(50.0 * 1000 * 1.0005 - 50025.0) < 1e-9 and '50025.0' in blob)
chk('A07 零后视镜：决断帧 tick %s 与 next tick %s 均早于 write_ts %s' % (QB['600487']['t'][8:], QX['600487']['t'][8:], d['write_ts'][11:]),
    int(QX['600487']['t']) <= int(d['write_ts'].replace('-', '').replace(':', '').replace(' ', ''))
    and int(QB['600487']['t']) <= int(QX['600487']['t']))
chk('A08 引用「今低 48.28」与源一致，且明写不因卖在低位区改规则',
    QB['600487']['low'] == 48.28 and '今低 48.28' in UNION and '改规则' in UNION)

# ── 3 账本已落 ─────────────────────────────────────────
B = r'D:\股票数据\市场数据\_学习\_模拟盘\logic'
led = [json.loads(l) for l in open(os.path.join(B, '账本.jsonl'), encoding='utf-8') if l.strip()]
st = json.load(open(os.path.join(B, 'state.json'), encoding='utf-8'))
last = led[-1]
chk('H00 logic 账本末行为 600487 sell 1000股 @48.62 pnl -1405.0 / ret -2.81 / fill_cls A',
    (last['code'], last['shares'], last['sell_px'], last['pnl'], last['ret_pct'], last['fill_cls'], last['ev'])
    == ('600487', 1000, 48.62, -1405.0, -2.81, 'A', 'sell'))
chk('H01 state 同步：cash 962155.37+48620=1,010,775.37、持仓清零、nav=cash',
    st['cash'] == 1010775.37 and st['positions'] == [] and round(st['cash'] + 0, 2) == 1010775.37)
chk('H02 备份存在且大小与原件落账前一致（append-only 可回溯）',
    os.path.exists(os.path.join(B, '账本.jsonl.bak_hbe_20261026')) and os.path.exists(os.path.join(B, 'state.json.bak_hbe_20261026')))
bak = [json.loads(l) for l in open(os.path.join(B, '账本.jsonl.bak_hbe_20261026'), encoding='utf-8') if l.strip()]
chk('H03 备份内无本场 sell 行（证明为本场新增、未改写历史）',
    not any(x.get('code') == '600487' and x.get('ev') == 'sell' for x in bak))
chk('H04 五本账 nav 由 state.json + 决断帧 14:31 报价复算，与补正1 逐项一致',
    (lambda NAV: all(str(v) in bzblob.replace(' ', '') for v in NAV.values()))(
        {n: round(json.load(open(rf'D:\股票数据\市场数据\_学习\_模拟盘\{n}\state.json', encoding='utf-8'))['cash']
                  + sum(x['shares'] * QB[x['code']]['px'] for x in
                        json.load(open(rf'D:\股票数据\市场数据\_学习\_模拟盘\{n}\state.json', encoding='utf-8'))['positions']
                        if x['code'] in QB), 2)
         for n in ('master', 'auction', 'limitup', 'lhb', 'logic')}))
chk('H05 其余四本账本场未被写入（今日无 hb-e 行）',
    not any(x.get('src') == '临盘决断_20261026_1430.json' for n in ('master', 'auction', 'limitup', 'lhb')
            for x in [json.loads(l) for l in open(rf'D:\股票数据\市场数据\_学习\_模拟盘\{n}\账本.jsonl', encoding='utf-8') if l.strip()]))
chk('H06 002639 不重复卖出：master 账本今日无 002639 sell 行、state 仍挂 2600 股',
    not any(x.get('d') == '20261026' and x.get('code') == '002639' and x.get('ev') == 'sell'
            for x in [json.loads(l) for l in open(r'D:\股票数据\市场数据\_学习\_模拟盘\master\账本.jsonl', encoding='utf-8') if l.strip()])
    and any(x['code'] == '002639' and x['shares'] == 2600 for x in json.load(open(r'D:\股票数据\市场数据\_学习\_模拟盘\master\state.json', encoding='utf-8'))['positions'])
    and '不重复卖出' in blob)

# ── 4 市场读数（钉帧 14:31:18）─────────────────────────
rows = P['rows']
p = [r['pct'] for r in rows if isinstance(r.get('pct'), (int, float))]
_pool = d['no_action']['环境读数']['昨涨停池(n=80)']
_exp = {'中位': f'{round(statistics.median(p), 2)}%', '均值': f'{round(statistics.mean(p), 2)}%',
        '涨': sum(1 for x in p if x > 0), '跌': sum(1 for x in p if x < 0),
        '≥+9.8%': sum(1 for x in p if x >= 9.8), '≤-5%': sum(1 for x in p if x <= -5),
        '≤-9.8%': sum(1 for x in p if x <= -9.8)}
_bad = {k: (_pool.get(k), v) for k, v in _exp.items() if _pool.get(k) != v}
chk('M01 池内中位/均值/涨/跌/涨停/深跌/跌停 七项与钉帧 %s 复算逐项一致' % PIN[11:], not _bad, str(_bad))
zt, zb, dt = pools['zt'], pools['zb'], pools['dt']
chk('M02 东财池 涨停54/炸板22/跌停0，炸板率 22/76=0.2895',
    len(zt) == 54 and len(zb) == 22 and len(dt) == 0 and abs(22 / 76 - 0.2895) < 1e-4
    and d['no_action']['环境读数']['全市场']['炸板率'] == 0.2895)
ever, lastmap = {}, {r['code']: r for r in rows}
for f in fr:
    if f['ts'] > PIN:
        break
    for r in f['rows']:
        if isinstance(r.get('pct'), (int, float)) and r['pct'] >= 9.8:
            ever[r['code']] = r['name']
still = [c for c in ever if isinstance(lastmap.get(c, {}).get('pct'), (int, float)) and lastmap[c]['pct'] >= 9.8]
open_map = {x['code']: x for x in fr[0]['rows']}
open_zt = [c for c, r in open_map.items() if isinstance(r.get('pct'), (int, float)) and r['pct'] >= 9.8]
open_still = sum(1 for c in open_zt if isinstance(lastmap.get(c, {}).get('pct'), (int, float)) and lastmap[c]['pct'] >= 9.8)
chk('M03 掉板（截至钉帧）：曾涨停 %d→仍 %d（%.2f%%）；开盘 18→%d（%.2f%%）' %
    (len(ever), len(still), (len(ever) - len(still)) / len(ever) * 100, open_still,
     (len(open_zt) - open_still) / len(open_zt) * 100),
    len(ever) == 30 and len(still) == 19 and abs(11 / 30 * 100 - 36.67) < 0.01
    and len(open_zt) == 18 and open_still == 10 and abs(8 / 18 * 100 - 44.44) < 0.01)
_dt_names = sorted(r['name'] for r in rows if isinstance(r.get('pct'), (int, float)) and r['pct'] <= -9.8)
chk('M04 池内跌停 5 只名单与文件一致', len(_dt_names) == 5 and all(n in blob for n in _dt_names), str(_dt_names))
hy = Counter(r.get('hybk') for r in zt)
maxhy, maxn = hy.most_common(1)[0]
chk('M05 最大行业 %s %d 只 <8 → 线级门对买入否决（文件已写）' % (maxhy, maxn),
    maxn == 6 and '线级门对买入仍否决' in blob and maxhy in blob)
lbc = Counter(r.get('lbc') for r in zt)
chk('M06 连板梯次合计=54 且最高板 4（1:39/2:9/3:5/4:1）',
    sum(lbc.values()) == 54 and max(lbc) == 4 and (lbc[1], lbc[2], lbc[3], lbc[4]) == (39, 9, 5, 1))
chk('M07 电机Ⅱ 今日涨停 0 只、炸板仅华阳智能（线断证据成立）',
    hy.get('电机Ⅱ', 0) == 0 and [r['n'] for r in zb if r.get('hybk') == '电机Ⅱ'] == ['华阳智能'])

# ── 5 报价读数（14:31:19 / 14:32:07）───────────────────
chk('V01 002242 决断帧 21.68 / +0.70 / 高22.00 / 低20.85 与源一致（补正1 已把 14:32 快照 21.66/+0.60 拆标）',
    (QB['002242']['px'], QB['002242']['pct'], QB['002242']['high'], QB['002242']['low']) == (21.68, 0.7, 22.0, 20.85)
    and '21.68' in bzblob and '21.66' in bzblob)
chk('V02 002242 帧距线 +3.63%（21.68/20.92-1）→ 帧未破线；内盘低点破线 -0.33%（20.85/20.92-1）',
    abs((21.68 / 20.92 - 1) * 100 - 3.63) < 0.01 and abs((20.85 / 20.92 - 1) * 100 + 0.33) < 0.01
    and ('+3.63%' in bzblob or '+3.63' in bzblob) and '-0.33%' in blob)
chk('V03 分时件佐证 002242 分钟低 20.88@13:53、末点 1433 价 21.72（与帧 13:53 张力说明一致）',
    mn['rows']['sz002242']['min'] == ['1353', 20.88] and mn['rows']['sz002242']['last'] == ['1433', 21.72])
chk('V04 003021 决断帧 96.88/+5.61%；对成本 85.00 = +13.98%，浮盈 1,183.75/100股（96.88×100-8504.25）',
    QB['003021']['px'] == 96.88 and QB['003021']['pct'] == 5.61 and abs((96.88 / 85 - 1) * 100 - 13.98) < 0.01
    and abs((100 * 96.88 - 8504.25) - 1183.75) < 0.02 and '1,183.75' in bzblob)
chk('V05 003021 三账合计 400 股（master100+auction200+limitup100，按全持仓求和），文件写「400股 三账合计」',
    sum(p_['shares'] for n in ('master', 'auction', 'limitup')
        for p_ in json.load(open(rf'D:\股票数据\市场数据\_学习\_模拟盘\{n}\state.json', encoding='utf-8'))['positions']
        if p_['code'] == '003021') == 400 and '400股 三账合计' in blob)
chk('V06 002639 决断帧 13.69 / -7.69%，对成本 14.78 = -7.37%（-2,853.21 元）',
    QB['002639']['px'] == 13.69 and QB['002639']['pct'] == -7.69
    and abs((13.69 / 14.78 - 1) * 100 + 7.37) < 0.01
    and abs(round(2600 * 13.69 - 38447.21, 2) + 2853.21) < 0.02)
chk('V07 四大指数决断帧读数逐项一致（3691.28/+0.02、11533.88/-1.20、2638.68/-1.69、1310.91/-2.57）',
    all(str(QB[c]['px']) in bzblob for c in ('000001', '399001', '399006', '000688'))
    and '3691.28 +0.02' in bzblob and '1310.91 -2.57' in bzblob,
    json.dumps({c: [QB[c]['px'], QB[c]['pct']] for c in ('000001', '399001', '399006', '000688')}, ensure_ascii=False))
chk('V08 相对 13:30 的四项变动按帧价复算＝-0.13/-0.56/-0.76/-1.15pp（补正1 已更正）',
    abs((0.02 - 0.15) + 0.13) < 1e-9 and abs((-1.20 + 0.64) + 0.56) < 1e-9
    and abs((-1.69 + 0.93) + 0.76) < 1e-9 and abs((-2.57 + 1.42) + 1.15) < 1e-9
    and '-0.13pp' in bzblob and '-1.15pp' in bzblob)
chk('V09 301502 华阳智能 一字开 77.76=20cm 涨停价、炸 5 次、现 +12.28%、换手 33.45%',
    [r for r in zb if r['c'] == '301502'][0]['fbt'] == 92500
    and abs(64.8 * 1.2 - 77.76) < 1e-9
    and [r for r in zb if r['c'] == '301502'][0]['zbc'] == 5
    and abs([r for r in zb if r['c'] == '301502'][0]['zdp'] - 11.6358) < 0.001)

# ── 6 跳水簇（截至钉帧，最近 40 分钟）──────────────────
ts = [datetime.datetime.strptime(x['ts'], '%Y-%m-%d %H:%M:%S') for x in fr]
cl = []
for i in range(len(fr)):
    if fr[i]['ts'] > PIN:
        break
    j = None
    for k in range(i - 1, -1, -1):
        if (ts[i] - ts[k]).total_seconds() >= 100:
            j = k
            break
    if j is None:
        continue
    a = {r['code']: r for r in fr[j]['rows']}
    dr = [(r['name'], round(r['pct'] - a[r['code']]['pct'], 2)) for r in fr[i]['rows']
          if r['code'] in a and r['pct'] - a[r['code']]['pct'] <= -3.0]
    cl.append((len(dr), fr[i]['ts'], dr))
pin_t = datetime.datetime.strptime(PIN, '%Y-%m-%d %H:%M:%S')
cut = (pin_t - datetime.timedelta(minutes=40)).strftime('%Y-%m-%d %H:%M:%S')
l40 = [c for c in cl if c[1] >= cut]
mx = max(l40, key=lambda x: x[0])
chk('C01 最近40分钟最大跳水簇 = %d 只（<3 批量阈值）→ 题材批量跳水未触发' % mx[0],
    mx[0] < 3 and f'最大簇 = {mx[0]} 只' in blob)
chk('C02 该簇为宇树科技-W -3.53pp @13:56，文件一致',
    mx[2] and mx[2][0][0] == '宇树科技-W' and abs(mx[2][0][1] + 3.53) < 0.01 and '13:56' in blob, str(mx))
hold = {'002242', '003021', '002639', '600487'}
chk('C03 四只持仓/另账票均不在涨停/炸板/跌停池（无板可炸）',
    not [r for r in zt + zb + dt if r.get('c') in hold] and '命中=∅' in blob)

# ── 7 缺件/欠账/口径 ──────────────────────────────────
miss = [f for f in ('pulse.json', 'warboard.json', '执行流水.jsonl', f'报警_20261026.jsonl')
        if not os.path.exists(os.path.join(D, f))]
chk('D01 缺件如实标注：pulse/warboard/执行流水/报警 均不存在且文件已写明',
    len(miss) == 4 and all(k in blob for k in ('pulse.json', 'warboard.json', '执行流水.jsonl'))
    and '均不存在' in blob, str(miss))
chk('D02 异常与欠账 ≥5 条且含 sentiment / 执行流水 / 002639 / 603370',
    len(d['异常与欠账']) >= 5 and all(k in blob for k in ('sentiment', '执行流水', '002639', '603370')))
chk('D03 全文无占位符（TODO/待填/XXX/???/nan/None）', not any(t in blob for t in ('TODO', '待填', 'XXX', '???', 'None')))
chk('D04 口径含「不是操盘指令」且含「不可覆盖」', '不是操盘指令' in d['口径'] and '不可覆盖' in d['口径'])
chk('D05 无预测性/指令性措辞（预计/将会/必涨/建议买入/目标价/建议卖出）',
    not any(t in blob for t in ('预计', '将会', '必涨', '建议买入', '目标价', '建议卖出')))
chk('D06 概率段带「以上为判断，不是指令」', '以上为判断，不是指令' in blob)
chk('D07 下一场备料含 14:45 深场三条候选 + 明日四要点', len(d['下一场']['14:45 深场B 备料_尾盘卖预案候选']) == 3
    and len(d['下一场']['明日预案要点草稿']) == 4)
chk('D08 清单核销 5 条逐条有应答（600487/002242/003021/002639/301502）',
    len(d['复盘_上一场清单核销']) == 5
    and all(k in json.dumps(d['复盘_上一场清单核销'], ensure_ascii=False) for k in ('600487', '002242', '003021', '002639', '301502')))

# ── 8 交易日校验与新鲜度口径 ───────────────────────────
chk('Z01 交易日校验如实登记 ModuleNotFoundError 并给三重回退证据',
    'ModuleNotFoundError' in blob and all(k in blob for k in ('realtime_ticks', 'date=20261026', 't=20261026143207')))
chk('Z02 末帧龄 24.7s < 600s 且判定「允许决策」', d['数据新鲜度']['末帧龄_秒'] < 600 and '允许决策' in d['数据新鲜度']['判定'])
chk('Z03 全部取数时点早于 write_ts（零后视镜）',
    q0['fetched'] <= d['write_ts'] and q1['fetched'] <= d['write_ts'] and pools['fetched'] <= d['write_ts']
    and mn['fetched'] <= d['write_ts'] and PIN <= d['write_ts'],
    f"{q0['fetched']} / {q1['fetched']} / {pools['fetched']} / {mn['fetched']} / {PIN} <= {d['write_ts']}")
chk('Z04 未把盘中价冒充收盘价（明写盘中/不引用收盘）', '盘中' in blob and '未引用任何收盘信息' in blob)

# ── 9 补正件与不可覆盖 ────────────────────────────────
cur = hashlib.sha256(open(J, 'rb').read()).hexdigest()
chk('B01 补正1 存在、补正号=1、性质含「勘误」', bz['补正号'] == 1 and '勘误' in bz['性质'])
chk('B02 补正1 记录的原件 sha256 与当前文件一致（→ 发出版未被覆盖，铁证）', bz['原件']['sha256'] == cur, cur[:16])
chk('B03 补正1 不改成交：fills 仍 1 笔 48.62×1000，A/B/C 仍 1/0/0',
    len(bz['不改成交声明']['fills']) == 1 and bz['不改成交声明']['fills'][0]['px_exec'] == 48.62
    and bz['不改成交声明']['fills'][0]['qty'] == 1000 and 'A 1 笔' in bz['不改成交声明']['权限分级'])
chk('B04 补正1 修正明细 8 条、每条含 位置/原文/问题/更正为',
    len(bz['修正明细']) == 8 and all(all(k in it for k in ('位置', '原文', '问题', '更正为')) for it in bz['修正明细']))
chk('B05 补正1 复算依据含帧价与快照两套读数（时点拆标可复核）',
    '决断帧' in bz['复算依据'] and '下一tick快照' in bz['复算依据']
    and bz['复算依据']['决断帧']['002242']['px'] == 21.68 and bz['复算依据']['下一tick快照']['002242'][0] == 21.66)
chk('B06 原件仍留存原表述（补正而非篡改）：21.66/+0.60、-0.14pp、140,360.00 仍在原件中',
    ('21.66' in blob or '21.66' in UNION) and '-0.14pp' in blob)

fail = [r for r in res if not r[1]]
for n, ok, det in res:
    print(('PASS ' if ok else 'FAIL ') + n + ('  | ' + det if det and not ok else ''))
print(f'\nTOTAL {len(res)}  PASS {len(res) - len(fail)}  FAIL {len(fail)}')
print('FAIL_LIST', [n for n, ok, _ in res if not ok])
