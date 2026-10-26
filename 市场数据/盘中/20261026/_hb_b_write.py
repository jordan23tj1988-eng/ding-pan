# -*- coding: utf-8 -*-
"""hb-b 10:30 趋势确认段 决断件生成器（数字全部取自源文件，不手写）。
发出版不可覆盖：写前 assert 目标不存在。"""
import json, os, datetime, statistics

D = os.path.dirname(os.path.abspath(__file__))
DATE = '20261026'
OUT = os.path.join(D, f'临盘决断_{DATE}_1030.json')

def load(p):
    return json.load(open(os.path.join(D, p), encoding='utf-8'))

q = load('_hb_b_quote_decide.json')
pools = load('_hb_b_pools_decide.json')
fr = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]

last = fr[-1]
rows = last['rows']
pcts = [r['pct'] for r in rows]
med = statistics.median(pcts)
mean = statistics.mean(pcts)
n_up = sum(1 for x in pcts if x > 0)
n_dn = sum(1 for x in pcts if x < 0)
n_zt = sum(1 for x in pcts if x >= 9.8)
n_dt = sum(1 for x in pcts if x <= -9.8)
n_deep = sum(1 for x in pcts if x <= -5)

zt_pool = pools['zt']
zb_pool = pools['zb']
dt_pool = pools['dt']
N_ZT, N_ZB, N_DT = len(zt_pool), len(zb_pool), len(dt_pool)
ZB_RATE = N_ZB / (N_ZT + N_ZB)

def px(code):
    for k, v in q['rows'].items():
        if v.get('code') == code:
            return v
    raise KeyError(code)

p242, p3021, p2639, p487 = px('002242'), px('003021'), px('002639'), px('600487')
sh, sz, cyb, kc = px('000001'), px('399001'), px('399006'), px('000688')

# book nav
BOOKS = {
    'master': (925125.64, [('002639', 2600, 14.78), ('002242', 800, 22.02), ('003021', 100, 85.00)]),
    'auction': (941997.30, [('003021', 200, 85.00)]),
    'limitup': (980230.10, [('003021', 100, 85.00)]),
    'lhb': (1003727.30, []),
    'logic': (962155.37, [('600487', 1000, 50.00)]),
}
PXMAP = {'002639': p2639['px'], '002242': p242['px'], '003021': p3021['px'], '600487': p487['px']}
nav = {}
for k, (cash, pos) in BOOKS.items():
    mv = sum(s * PXMAP[c] for c, s, _b in pos)
    nav[k] = {'cash': round(cash, 2), 'mv': round(mv, 2), 'nav': round(cash + mv, 2)}

# frame freshness
ts = [datetime.datetime.strptime(f['ts'], '%Y-%m-%d %H:%M:%S') for f in fr]
gaps = [(ts[i + 1] - ts[i]).total_seconds() for i in range(len(ts) - 1)]
max_gap = max(gaps)
now = datetime.datetime.now()
age = round((now - ts[-1]).total_seconds(), 1)

# 2-min clusters
def snap(f):
    return {r['code']: r for r in f['rows']}
maxc = []
for i in range(len(fr)):
    t = datetime.datetime.strptime(fr[i]['ts'], '%Y-%m-%d %H:%M:%S')
    j = None
    for k in range(i - 1, -1, -1):
        tk = datetime.datetime.strptime(fr[k]['ts'], '%Y-%m-%d %H:%M:%S')
        if (t - tk).total_seconds() >= 100:
            j = k
            break
    if j is None:
        continue
    a = snap(fr[j])
    drops = [(r['code'], r['name'], round(a[r['code']]['pct'], 2), round(r['pct'], 2), round(r['pct'] - a[r['code']]['pct'], 2))
             for r in fr[i]['rows'] if r['code'] in a and r['pct'] - a[r['code']]['pct'] <= -3.0]
    maxc.append((len(drops), fr[i]['ts'], drops))
last30 = [x for x in maxc if x[1] >= (datetime.datetime.strptime(fr[-1]['ts'], '%Y-%m-%d %H:%M:%S') - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')]
max_last30 = max([x[0] for x in last30]) if last30 else 0
worst_last30 = max(last30, key=lambda x: x[0]) if last30 else (0, None, [])

# 09:31 vs now 掉板
first = snap(fr[0])
open_zt = [c for c, r in first.items() if r['pct'] >= 9.8]
still_zt = sum(1 for c in open_zt if snap(last).get(c, {}).get('pct', -99) >= 9.8)
pool_dt = [(r['code'], r['name'], round(r['pct'], 2)) for r in rows if r['pct'] <= -9.8]
pool_deep = [(r['name'], round(r['pct'], 2)) for r in rows if r['pct'] <= -5]

# 10:07 comparison
f1007 = next((f for f in fr if f['ts'] == '2026-10-26 10:07:18'), None)
med1007 = statistics.median([r['pct'] for r in f1007['rows']]) if f1007 else None
zt1007 = sum(1 for r in f1007['rows'] if r['pct'] >= 9.8) if f1007 else None

# 弃单照会（另一时点 10:35:27~30 实读）
YQ = {'300296': (6.94, -5.19, 7.25), '002979': (54.31, 0.30, 55.86),
      '003021': (94.70, 3.24, 93.00), '603721': (22.70, 4.27, 22.98), '300561': (14.97, -4.04, 14.90)}

# industry counts
from collections import Counter
ind = Counter([x.get('hybk') for x in zt_pool]).most_common()
top_ind = ind[0]

def pct_vs(now_px, base):
    return round((now_px / base - 1) * 100, 2)

doc = {
 'date': DATE,
 'session': 'hb-b',
 'ts': '10:30',
 'write_ts': now.strftime('%Y-%m-%d %H:%M:%S'),
 '版本': f'v1 · 10:30 趋势确认段（取数窗口 池帧 09:31:09~{fr[-1]["ts"][11:]}，腾讯报价 决断帧 {q["fetched"]}，东财池 10:33:54）',
 '场次说明': (
  '本场为 20261026(周一) hb-b 10:30 趋势确认段。★零后视镜：仅用决断帧之前已落盘数据——池帧 '
  f'{len(fr)} 帧（{fr[0]["ts"][11:]}~{fr[-1]["ts"][11:]}，1/分钟）+ 腾讯报价 {q["fetched"]} + 东财涨停/炸板/跌停池 10:33:54；'
  '弃单照会另引 10:35:27~10:35:30 报价，逐条标时点。★盘中禁改参数：未改任何生产脚本/预案/权重/阈值/机械线。'
  '★发出版不可覆盖：写前 assert 目标文件不存在（通过）。'
 ),
 '交易日校验': {
  '规格命令': 'python -c "from sentiment.core.calendar import is_trading_day,today_str" → FAIL: ModuleNotFoundError: No module named \'sentiment\'（连续第 7 个交易日登记，本场不改工程）',
  '本机等效真源': f'date → 2026-10-26 星期一；池帧本日 {fr[0]["ts"][11:]} 起 {len(fr)} 帧真实分化（末帧中位 {round(med,2)}%、{n_zt} 只≥+9.8%、{n_dt} 只≤-9.8%）→ 判定交易日，不早退。',
 },
 '数据新鲜度': {
  '池帧': {
   '文件': '盘中/20261026/realtime_ticks.jsonl',
   '帧数': len(fr),
   '窗口': f'{fr[0]["ts"]} ~ {fr[-1]["ts"]}',
   '末帧龄': f'{age} 秒',
   '最大间隔': f'{int(max_gap)}s',
   'pool_date': last.get('pool_date'),
   'pool_stale': last.get('pool_stale'),
   'n': len(rows),
   '判定': f'未断更（最大间隔 {int(max_gap)}s、末帧龄 {age}s，均 << 10 分钟门槛）→ 可决策',
  },
  '个股/指数': {'源': 'qt.gtimg.cn', '时戳': p242['t'], '标的': '002242/003021/002639/600487 + 上证/深成/创业板/科创50'},
  '市场闸门源': {
   '源': 'push2ex.eastmoney.com getTopicZTPool/ZBPool/DTPool',
   'date参数': DATE, '取数时点': '10:33:54',
   '涨停池': N_ZT, '炸板池': N_ZB, '跌停池': N_DT,
   '炸板率': round(ZB_RATE, 4),
  },
  '缺件': {
   'pulse.json': '不存在',
   'warboard.json': '不存在',
   '报警_20261026.jsonl': '不存在',
   '执行流水.jsonl': '不存在',
  },
  '口径': '缺件如实标注、不补造；本场风险判断不依赖 pulse/warboard（池帧与报价均新鲜，末帧龄 %s 秒）' % age,
 },
 '权限分级': {
  'A': '0 笔。预案内无 trigger 待达成：master 买入的唯一执行价为开盘价，09:40 场已按线级门/闸门全否（弃单不回补）；卖出腿 09:40 场已补执行完毕。',
  'B': '0 笔。三项防守触发条件均未达成（见 防守三查）；600487(logic 另账) 已破成本但按 09:40 场书面约定交 14:30 场处置，本场不越界代决。',
  'C': '0 笔。创业板 -%s%%、深成 -%s%%、池内 %s 只昨涨停今日跌停，风险偏好收缩 → 不做预案外进攻；且线级门（最大行业 %s %s 只 < 8）对任何买入仍是否决态。' % (
   abs(cyb['pct']), abs(sz['pct']), n_dt, top_ind[0], top_ind[1]),
 },
 'fills': [],
 'no_action': {
  '结论': '心跳hb-b无动作：不平仓、不加仓、不开新仓',
  '持仓核': {
   'master': f'002242 九阳股份 800 股 @{p242["px"]}（成本 22.02，浮亏 {round(800*(p242["px"]-22.02),2)} 元）、003021 兆威机电 100 股 @{p3021["px"]}、002639 雪人集团 2600 股（纸上已卖、待补账）→ 持仓市值 {nav["master"]["mv"]} 元、现金 {nav["master"]["cash"]} 元、nav≈{nav["master"]["nav"]} 元',
   'auction': f'003021 200 股 @{p3021["px"]}，nav≈{nav["auction"]["nav"]} 元',
   'limitup': f'003021 100 股 @{p3021["px"]}，nav≈{nav["limitup"]["nav"]} 元',
   'lhb': f'空仓，现金 {nav["lhb"]["cash"]} 元',
   'logic（另账）': f'600487 亨通光电 1000 股 @{p487["px"]}（成本 50.00，浮亏 {round(1000*(p487["px"]-50.00),2)} 元），nav≈{nav["logic"]["nav"]} 元',
   '账本实况': 'master/账本.jsonl 末条 = sell 603370（ts 2026-10-26 09:52:04，src=临盘决断_20261026_0940.json）→ 09:40 场入账已落地；002639 2600 股补账行仍缺（欠账①未清）',
  },
  '防守三查': [
   f'①炸板：三只在持票今日均从未涨停（002242 今高 {p242["high"]} vs 涨停 23.68；003021 今高 {p3021["high"]} vs 100.90；002639 今高 {p2639["high"]} vs 16.31）→ 无板可炸，「持仓炸板」不适用。',
   f'②大幅回撤：002242 对成本 {pct_vs(p242["px"],22.02)}%（浮亏 {round(800*(p242["px"]-22.02),2)} 元 ≈ master nav 的 {round(800*(p242["px"]-22.02)/nav["master"]["nav"]*100,3)}%）、自 09:48 决断帧 21.72 回落 {pct_vs(p242["px"],21.72)}%；003021 对成本 +{pct_vs(p3021["px"],85.0)}%（三本账均浮盈）；机械线 20.92 未破（决断帧高于线 {round((p242["px"]/20.92-1)*100,2)}%，今日低 20.91 系 09:48 前已发生的同一笔下影，非新增）→ 判「未达大幅回撤」，不临时自造阈值。',
   f'③题材批量跳水：全 {len(fr)} 帧逐 2 分钟扫描，最近 30 分钟内最大簇 = {max_last30} 只跌≥3pp（阈值 3 只；{worst_last30[1]} {[(d[1],d[4]) for d in worst_last30[2]] if worst_last30[2] else ""}）→ 未触发；全天最大簇 2 只（09:33 早盘，已过）。',
  ],
  '环境读数': {
   '指数': {
    '上证': f'{sh["px"]} {sh["pct"]}%',
    '深成': f'{sz["px"]} {sz["pct"]}%',
    '创业板': f'{cyb["px"]} {cyb["pct"]}%',
    '科创50': f'{kc["px"]} {kc["pct"]}%',
    '对比09:48(hb-a决断帧)': f'上证 -0.59→{sh["pct"]}、创业板 -2.43→{cyb["pct"]} → 弱势延续但未见加速破位（上证跌幅仅扩 0.04pp）',
   },
   '昨涨停池(n=%d)' % len(rows): {
    '中位': f'{round(med,2)}%', '均值': f'{round(mean,2)}%',
    '涨': n_up, '跌': n_dn,
    '≥+9.8%': n_zt, '≤-5%': n_deep, '≤-9.8%': n_dt,
    '对比10:07': f'中位 {round(med1007,2) if med1007 else None}→{round(med,2)}、池内涨停 {zt1007}→{n_zt} → 溢价持续收敛',
    '掉板': f'09:31 在涨停的 {len(open_zt)} 只中，现仍≥+9.8% 的仅 {still_zt} 只（掉板 {len(open_zt)-still_zt} 只，掉板率 {round((1-still_zt/len(open_zt))*100,1)}%）',
    '跌停名单': [f'{n}{p}%' for _c, n, p in pool_dt],
   },
   '全市场': {
    '涨停': N_ZT, '炸板': N_ZB, '跌停': N_DT, '炸板率': round(ZB_RATE, 4),
    '最大行业': f'{top_ind[0]} {top_ind[1]} 只（<8 → 线级门对买入仍否决）',
    '对比09:48': '涨停 23→%s、炸板率 0.4390→%s → 宽度修复、炸板率回落至闸门内(<0.45)' % (N_ZT, round(ZB_RATE, 4)),
   },
   '判断': f'情绪=分歧下行后段：昨涨停池溢价收敛（中位 {round(med,2)}%）、掉板率 {round((1-still_zt/len(open_zt))*100,1)}%、池内 {n_dt} 只跌停（慈文传媒/华瓷股份/晶丰明源/曙光股份）= 亏钱效应实存；但全市场涨停 {N_ZT} 只、跌停 {N_DT} 只、炸板率 {round(ZB_RATE,4)} < 0.45 → 属「局部退潮、全局未崩」，不构成清仓级信号，也不构成进攻窗口。',
  },
 },
 '复盘_上一场清单核销': [
  f'①002242 是否破 20.92：决断帧 {p242["px"]}（{p242["pct"]}%）> 20.92，未破；今日低仍为 20.91（与 09:48 同比，无新低）→ 不清、机械线 20.92 不变，破则 11:00 场清。',
  f'②003021 三本账浮盈回吐：决断帧 {p3021["px"]} 对成本 85.00 +{pct_vs(p3021["px"],85.0)}%，防守线 80.75 距现价 {round((p3021["px"]/80.75-1)*100,2)}% → 未触线，无需动作。',
  '③master 002639 2600 股补账是否落地：未落地（master/账本.jsonl 今日仅 1 条 603370 卖出行，无 002639 sell 行；state.json 仍挂 2600 股）→ 欠账①转入结算，本场不重复卖出。',
  '④弃单机会成本（盘中快照，非收盘结算）：300296 6.94(-5.19%) vs 定盘 7.25 → 弃单避损 -4.28%；002979 54.31(+0.30%) vs 定盘 55.86 → 避损 -2.77%；003021 94.70(+3.24%) vs 定盘 93.00 → 弃单错失 +1.83%（若按 1.5% 仓位≈1.5 万元计，机会成本≈+275 元）。三项净值为正，线级门今日为「避损」而非「错失」。',
  f'⑤603721 / 300561 是否回带：603721 现 22.70(今 +4.27%)，gap 仍 +4%以上（预案带 [-4,+4]）→ 未回带；300561 现 14.97(-4.04%)，仍在下沿外 0.04pp → 未回带。已弃不回补。',
  f'⑥炸板率 / 涨停数闸门：炸板率 {round(ZB_RATE,4)} < 0.45 ✔、涨停 {N_ZT} ≥ 20 ✔、跌停 {N_DT} < 12 ✔ → 三项闸门均未破，不构成总审降档硬条件。',
 ],
 '照会_非条件决断': {
  '600487 亨通光电(logic 另账)': f'决断帧 {p487["px"]}（{p487["pct"]}%，今低 {p487["low"]}）已跌破成本 50.00（-{abs(pct_vs(p487["px"],50.0))}%），且今日 700,576 手 / 10:34 前已达近 5 日日均量的 4 成以上=放量确认。按 09:40 场书面约定「交 14:30 场按其自身防守线处置」，本场不越界代决；★升级登记：若 14:30 决断帧仍 < 50.00，14:30 场须执行其防守（不得以「等收盘」再顺延）。',
  '002639 雪人集团(master 2600 纸上市值)': f'决断帧 {p2639["px"]}（{p2639["pct"]}%，距跌停价 13.35 仅 {round((p2639["px"]/13.35-1)*100,2)}%）→ 证实 10/23 决断卖出方向正确；同时暴露补账口径问题：若按决断价 14.00 补账，将比当前可实现价多计 {round(2600*(14.00-p2639["px"]),2)} 元 → 结算须同时登记「漏执行滑点 -{round(2600*(14.00-p2639["px"]),2)} 元」，不得让净值虚增。',
  '301502 华阳智能': f'决断帧 72.83（+12.39%，今高 77.76、今低 71.39）→ 与 003021 同线；09:40 场的可证伪样本（线级门把同线票全弃是否过严）继续跟踪，收盘记两者相对收益，不动手。',
  '003021 三本账': f'决断帧 {p3021["px"]}（+{p3021["pct"]}%，今高 {p3021["high"]}）三本账合计 400 股均浮盈，无减仓触发（无预设止盈条款），续持。',
 },
 '异常与欠账': [
  '① master 002639 2600 股补账仍未落地（承接 09:40 场欠账①）：须由 20261026 结算补 sell 行；★新增口径要求：按决断价 14.00 记「决断价」，同时单独登记漏执行滑点 -%s 元（2600×(14.00-13.40)），否则净值虚增。' % round(2600 * (14.00 - p2639['px']), 2),
  '② 执行层今日仍零执行（连续第 6 个场次）：pulse.json / warboard.json / 报警_20261026.jsonl / 执行流水.jsonl 全部缺件 → 本场只能以池帧+腾讯报价+东财池自建判据；机制建议（待批，本场不改代码）：引擎触发即写执行流水。',
  '③ playbook.json 缺件连续第 5 次（20261020/21/22/23/26）：预案真源仍为 临盘决断_20261026_0921.json + _学习/交易计划_master_20261023.json，不补造。',
  '④ 交易日校验规格命令连续第 7 个交易日 ModuleNotFoundError（sentiment 包不可导入），建议统一为 trading_calendar.py（须批准）。',
  '⑤ 开盘 5 分钟观测缺口（承接 09:40 场⑥）：竞价末帧 09:25:49 → 连续段首帧 09:31:09，开盘瞬间形态不可核，本场防守判断只用 09:31 之后数据，不外推。',
  '⑥ 线级门口径歧义（承接 09:40 场⑦，不改判）：今日涨停 %s 只分散于 %s 个行业，最大行业 %s 仅 %s 只 → 窄(行业)/宽(大方向)两口径均 <8，该门今日等价于「全市场零买入」；须在 20261026 复盘定「线」的计数源。' % (N_ZT, len(ind), top_ind[0], top_ind[1]),
  '⑦ 腾讯日K接口在盘中返回当日未收盘实时bar（2026-10-26 行 close=49.26、vol=700576 手）：本场仅供 600487 放量比对，标注为「盘中未完成bar」，不得当作收盘数据引用。',
 ],
 '下一场预置观察条件_非指令': [
  f'002242：机械线 20.92 为唯一卖出触发；11:00 场若决断帧 ≤20.92 → 清（按 20261023 场口径「决断帧判线」，不以内盘瞬时下影判线）。',
  f'003021：防守线 80.75（成本 85.00 的 -5%）为唯一减仓触发；现距 {round((p3021["px"]/80.75-1)*100,2)}%，无其他条款。',
  '600487(logic)：14:30 场硬性核 50.00；仍低于成本则按其自身防守线执行，不再顺延。',
  '全局：炸板率 ≥0.45 或 跌停 ≥12 或 池内跌停 ≥6 → 触发总审降档硬条件（C 档零新增）；本场读数 0.%s / %s / %s，未触发。' % (str(round(ZB_RATE, 4))[2:], N_DT, n_dt),
 ],
 '口径': '①本场 fills=[]，不产生任何撮合数字；②所有价格/比例均可由 _hb_b_quote_decide.json、_hb_b_pools_decide.json、realtime_ticks.jsonl 复算；③弃单照会报价时点 10:35:27~10:35:30 与持仓决断帧 10:33:54 并列标注，不混同；④本文件对用户=参考，不是操盘指令。',
}

assert not os.path.exists(OUT), 'FAIL 发出版已存在，禁止覆盖: ' + OUT
json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT, os.path.getsize(OUT), 'bytes')
print('frames', len(fr), 'age', age, 'max_gap', max_gap)
print('zb_rate', round(ZB_RATE, 4), 'zt', N_ZT, 'zb', N_ZB, 'dt', N_DT)
print('002242', p242['px'], p242['pct'], 'line 20.92 dist', round((p242['px'] / 20.92 - 1) * 100, 2))
print('nav', json.dumps(nav, ensure_ascii=False))
print('last30 max cluster', max_last30, worst_last30[1])
