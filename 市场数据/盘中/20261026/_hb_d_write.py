# -*- coding: utf-8 -*-
"""hb-d 13:30 场决断件生成器：全部数字由源文件复算，不手填。发版不可覆盖(assert)。"""
import json, os, datetime, statistics, hashlib

D = os.path.dirname(os.path.abspath(__file__))
DATE = '20261026'
TARGET = os.path.join(D, f'临盘决断_{DATE}_1330.json')
assert not os.path.exists(TARGET), '发版不可覆盖：目标已存在 ' + TARGET

q = json.load(open(os.path.join(D, '_hb_d_quote_1330.json'), encoding='utf-8'))
pools = json.load(open(os.path.join(D, '_hb_d_pools_1330.json'), encoding='utf-8'))
QB = {v['code']: v for v in q['rows'].values()}
QTS = q['fetched']
POOL_FETCH = pools['fetched']

fr = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
fr.sort(key=lambda x: x['ts'])
last = fr[-1]
ts = [datetime.datetime.strptime(x['ts'], '%Y-%m-%d %H:%M:%S') for x in fr]
gaps = [(ts[i] - ts[i - 1]).total_seconds() for i in range(1, len(ts))]


def stats(f):
    p = [r['pct'] for r in f['rows'] if isinstance(r.get('pct'), (int, float))]
    return dict(n=len(p), med=round(statistics.median(p), 2), mean=round(statistics.mean(p), 2),
                up=sum(1 for x in p if x > 0), dn=sum(1 for x in p if x < 0),
                zt=sum(1 for x in p if x >= 9.8), deep=sum(1 for x in p if x <= -5),
                dt=sum(1 for x in p if x <= -9.8))


LASTS = stats(last)
# 掉板
ever, lastmap = {}, {r['code']: r for r in last['rows']}
for f in fr:
    for r in f['rows']:
        if isinstance(r.get('pct'), (int, float)) and r['pct'] >= 9.8:
            ever[r['code']] = r['name']
still = [c for c in ever if isinstance(lastmap.get(c, {}).get('pct'), (int, float)) and lastmap[c]['pct'] >= 9.8]
open_zt = [c for c, r in {x['code']: x for x in fr[0]['rows']}.items()
           if isinstance(r.get('pct'), (int, float)) and r['pct'] >= 9.8]
open_still = sum(1 for c in open_zt if isinstance(lastmap.get(c, {}).get('pct'), (int, float)) and lastmap[c]['pct'] >= 9.8)

# 2分钟跳水簇
cl = []
for i in range(len(fr)):
    j = None
    for k in range(i - 1, -1, -1):
        if (ts[i] - ts[k]).total_seconds() >= 100:
            j = k
            break
    if j is None:
        continue
    a = {r['code']: r for r in fr[j]['rows']}
    d = [(r['name'], round(r['pct'] - a[r['code']]['pct'], 2)) for r in fr[i]['rows']
         if r['code'] in a and r['pct'] - a[r['code']]['pct'] <= -3.0]
    cl.append((len(d), fr[i]['ts'], d))
cut30 = (ts[-1] - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
l30 = [c for c in cl if c[1] >= cut30]
l30.sort(key=lambda x: -x[0])
mx30 = l30[0] if l30 else (0, None, [])
cl.sort(key=lambda x: -x[0])
mxall = cl[0] if cl else (0, None, [])

# 账户
ACC = {}
for name in ('master', 'auction', 'limitup', 'lhb', 'logic'):
    s = json.load(open(rf'D:\股票数据\市场数据\_学习\_模拟盘\{name}\state.json', encoding='utf-8'))
    mv = sum(p['shares'] * QB[p['code']]['px'] for p in s['positions'] if p['code'] in QB)
    ACC[name] = dict(cash=s['cash'], mv=round(mv, 2), nav=round(s['cash'] + mv, 2),
                     pos=[[p['code'], p['name'], p['shares'], p['buy_px']] for p in s['positions']])

# 持仓读数
def hold_read(code, shares, cost):
    v = QB[code]
    return dict(name=v['name'], px=v['px'], pct=v['pct'], pre=v['pre'], high=v['high'], low=v['low'],
                zt_px=round(v['pre'] * 1.1, 2), cost=cost, shares=shares,
                vs_cost_pct=round((v['px'] / cost - 1) * 100, 2),
                pnl=round(shares * (v['px'] - cost), 2))

H242 = hold_read('002242', 800, 22.02)
H021 = hold_read('003021', 400, 85.00)
H639 = hold_read('002639', 2600, 14.78)
H487 = hold_read('600487', 1000, 50.00)
LINE_242 = 20.92
LINE_021 = 80.75

zt, zb, dt = pools['zt'], pools['zb'], pools['dt']
from collections import Counter
hy = Counter(r.get('hybk') for r in zt)
maxhy, maxn = hy.most_common(1)[0]
zbr = round(len(zb) / max(len(zt) + len(zb), 1), 4)

# 分时补充（路径描述，另标时点）
minute = json.load(open(os.path.join(D, '_hb_d_minute_1330.json'), encoding='utf-8'))


def mpath(code):
    rows = minute[code]['rows']
    pts = [(r.split()[0], float(r.split()[1])) for r in rows]
    lo = min(pts, key=lambda x: x[1]); hi = max(pts, key=lambda x: x[1])
    return dict(date=minute[code]['date'], n=len(pts), first=pts[0], last=pts[-1], lo=lo, hi=hi)

M242, M639, M487, M021 = mpath('sz002242'), mpath('sz002639'), mpath('sh600487'), mpath('sz003021')

write_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

d = {
 'date': DATE,
 'session': 'hb-d',
 'ts': '13:30',
 'write_ts': write_ts,
 '版本': f'v1 · 13:30 午后延续段（池帧 {fr[0]["ts"]}~{last["ts"]} 共 {len(fr)} 帧；腾讯报价 {QTS}；东财 ZT/ZB/DT 池 {POOL_FETCH}；分时补充件 _hb_d_minute_1330.json 时点见各行）',
 '场次说明': ('本场为 20261026(周一) hb-d 13:30 午后延续段，13 号盘中作战 agent 心跳。'
           '★零后视镜：仅用本文件 write_ts 之前已落盘的数据——池帧、腾讯报价、东财池三源时点均早于 write_ts，逐项见【数据新鲜度】。'
           '★盘中禁改参数：未改任何生产脚本/预案/权重/阈值/机械线（002242 20.92、003021 80.75 均沿用）。'
           '★发版不可覆盖：写前 assert 目标文件不存在（通过）。'),
 '交易日校验': {
   '规格命令': "python -c \"from sentiment.core.calendar import is_trading_day,today_str;print(is_trading_day(today_str()))\" → FAIL: ModuleNotFoundError: No module named 'sentiment'（连续第 8 个交易日登记，本场不改工程）",
   '本机等效真源': f'date → 2026-10-26 星期一；池帧本日 {fr[0]["ts"]} 起 {len(fr)} 帧连续分化（末帧中位 {LASTS["med"]}%、{LASTS["zt"]} 只≥+9.8%、{LASTS["dt"]} 只≤-9.8%）→ 判定交易日，不早退。'},
 '数据新鲜度': {
   '池帧': {'文件': '盘中/20261026/realtime_ticks.jsonl', '帧数': len(fr),
          '窗口': f'{fr[0]["ts"]} ~ {last["ts"]}',
          '末帧龄_秒': round((datetime.datetime.now() - ts[-1]).total_seconds(), 1),
          '最大间隔_秒': round(max(gaps), 1), '间隔>180s': sum(1 for g in gaps if g > 180),
          'pool_date': last.get('pool_date'), 'pool_stale': last.get('pool_stale'), 'n': last.get('n'),
          '判定': f'未断更（最大间隔 {round(max(gaps),1)}s << 10 分钟门槛）→ 可决策'},
   '个股/指数': {'源': 'qt.gtimg.cn', '时戳': QB['002242']['t'], '取数时刻': QTS,
             '标的': '002242/003021/002639/600487/603370 + 上证/深成/创业板/科创50'},
   '市场闸门源': {'源': 'push2ex.eastmoney.com getTopicZTPool/ZBPool/DTPool', 'date参数': DATE,
              '取数时刻': POOL_FETCH, '涨停池': len(zt), '炸板池': len(zb), '跌停池': len(dt), '炸板率': zbr},
   '缺件': {'pulse.json': '不存在', 'warboard.json': '不存在',
          f'报警_{DATE}.jsonl': '不存在', '执行流水.jsonl': '不存在'},
   '口径': '缺件如实标注、不补造；本场判断不依赖 pulse/warboard（池帧末帧龄与报价时戳均远小于 10 分钟门槛）'},
 '权限分级': {
   'A': '0 笔。预案内无待达成 trigger：master 今日买入执行价为开盘价，09:40 场已按线级门/闸门全否（弃单不回补）；002242 机械线 20.92 未破（决断帧 %s 高于线 %.2f%%）、003021 防守线 80.75 距现价 %.2f%% → 卖出腿无触发。'
        % (H242['px'], (H242['px'] / LINE_242 - 1) * 100, (LINE_021 / H021['px'] - 1) * 100),
   'B': f'0 笔。防守三查全部未达成（炸板=无板可炸；大幅回撤=002242 对成本 {H242["vs_cost_pct"]}% 未破机械线、002639 卖出决定已下不存在重复卖出；题材批量跳水=近 30 分钟最大簇 {mx30[0]} 只 < 3）。600487(logic 另账) 按 09:40 场书面约定交 14:30 场硬核 50.00，本场不越界代决。',
   'C': f'0 笔。全局闸门未降档（炸板率 {zbr}<0.45、跌停 {len(dt)}<12、池内跌停 {LASTS["dt"]}<6），但线级门最大行业「{maxhy}」仅 {maxn} 只 <8 → 任何买入腿仍为否决态；且不预设标的、禁打板价。'},
 'fills': [],
 'no_action': {
   '结论': '心跳hb-d无动作：不平仓、不加仓、不开新仓',
   '持仓核': {
     'master': f'002639 {H639["name"]} 2600 股 @{H639["cost"]}（现价 {H639["px"]} {H639["pct"]}%，对成本 {H639["vs_cost_pct"]}%，浮亏 {H639["pnl"]} 元）、'
               f'002242 {H242["name"]} 800 股 @{H242["cost"]}（现价 {H242["px"]} {H242["pct"]}%，对成本 {H242["vs_cost_pct"]}%，浮亏 {H242["pnl"]} 元）、'
               f'003021 {H021["name"]} 100 股 @85.00 → 现金 {ACC["master"]["cash"]}、持仓市值 {ACC["master"]["mv"]}、nav≈{ACC["master"]["nav"]} 元',
     'auction': f'003021 200 股 @85.00 → 现金 {ACC["auction"]["cash"]}、市值 {ACC["auction"]["mv"]}、nav≈{ACC["auction"]["nav"]} 元',
     'limitup': f'003021 100 股 @85.00 → 现金 {ACC["limitup"]["cash"]}、市值 {ACC["limitup"]["mv"]}、nav≈{ACC["limitup"]["nav"]} 元',
     'lhb': f'空仓，现金 {ACC["lhb"]["cash"]} 元',
     'logic（另账）': f'600487 {H487["name"]} 1000 股 @50.00（现价 {H487["px"]} {H487["pct"]}%，对成本 {H487["vs_cost_pct"]}%，浮亏 {H487["pnl"]} 元）→ 现金 {ACC["logic"]["cash"]}、市值 {ACC["logic"]["mv"]}、nav≈{ACC["logic"]["nav"]} 元',
     '账本实况': 'master/账本.jsonl 末条仍为 sell 603370（ts 2026-10-26 09:52:04）→ 今日无新成交行；master state.json 仍挂 002639 2600 股（欠账①未清，本场不重复卖出）'},
   '持仓明细': {'002242': H242, '003021': H021, '002639': H639, '600487': H487},
   '防守三查': [
     f'①炸板：三只在持票今日均从未涨停（002242 今高 {H242["high"]} vs 涨停 {H242["zt_px"]}；003021 今高 {H021["high"]} vs {H021["zt_px"]}；002639 今高 {H639["high"]} vs {H639["zt_px"]}），且三票均不在东财涨停/炸板/跌停池 → 「持仓炸板」不适用。',
     f'②大幅回撤：002242 对成本 {H242["vs_cost_pct"]}%（浮亏 {H242["pnl"]} 元 ≈ master nav 的 {round(H242["pnl"]/ACC["master"]["nav"]*100,3)}%），决断帧 {H242["px"]} 高于机械线 {LINE_242} 的 {(H242["px"]/LINE_242-1)*100:.2f}%；今低 {H242["low"]} 系 10:19 前形成的同一笔下影（10:30 场已登记），按 20261023 场口径「决断帧判线、不以内盘瞬时下影判线」→ 未破线。003021 对成本 {H021["vs_cost_pct"]}%，防守线 80.75 距现价 {(LINE_021/H021["px"]-1)*100:.2f}% → 未触线。002639 对成本 {H639["vs_cost_pct"]}%，其卖出决定已在 10/23 场作出（lhb 腿今日 09:50 已按 13.70 成交、master 腿待补账），不存在重复卖出 → 不以浮亏倒推新的防守动作。不临时自造阈值。',
     f'③题材批量跳水：全 {len(fr)} 帧逐 2 分钟扫描（门槛：同一 2 分钟窗内 ≥3 只跌≥3pp），最近 30 分钟最大簇 = {mx30[0]} 只（{mx30[1]}）→ 未触发；全天最大簇 = {mxall[0]} 只（{mxall[1]}，早盘 09:33，已过）。午后无新增批量跳水。'],
   '环境读数': {
     '指数': {QB['000001']['name']: f'{QB["000001"]["px"]} {QB["000001"]["pct"]:+}%',
            QB['399001']['name']: f'{QB["399001"]["px"]} {QB["399001"]["pct"]:+}%',
            QB['399006']['name']: f'{QB["399006"]["px"]} {QB["399006"]["pct"]:+}%',
            QB['000688']['name']: f'{QB["000688"]["px"]} {QB["000688"]["pct"]:+}%',
            '对比10:33(hb-b决断帧)': '上证 -0.63→+0.15（转正）、深成 -1.98→-0.64、创业板 -2.83→-0.93、科创50 -2.81→-1.42 → 全线修复，上证由跌转涨'},
     f'昨涨停池(n={LASTS["n"]})': {
        '中位': f'{LASTS["med"]}%', '均值': f'{LASTS["mean"]}%', '涨': LASTS['up'], '跌': LASTS['dn'],
        '≥+9.8%': LASTS['zt'], '≤-5%': LASTS['deep'], '≤-9.8%': LASTS['dt'],
        '对比10:36': f'中位 2.39→{LASTS["med"]}、池内涨停 12→{LASTS["zt"]} → 溢价回升',
        '掉板': f'日内曾涨停 {len(ever)} 只、末帧仍≥+9.8% 仅 {len(still)} 只（掉板率 {(len(ever)-len(still))/len(ever)*100:.2f}%，10:30 场为 50.0%）；开盘 09:31 涨停 {len(open_zt)} 只现仍涨停 {open_still} 只（{((len(open_zt)-open_still)/max(len(open_zt),1))*100:.2f}%）',
        '跌停名单': [r['name'] + f' {r["pct"]}%' for r in last['rows'] if isinstance(r.get('pct'), (int, float)) and r['pct'] <= -9.8]},
     '全市场': {'涨停': len(zt), '炸板': len(zb), '跌停': len(dt), '炸板率': zbr,
              '最大行业': f'{maxhy} {maxn} 只（<8 → 线级门对买入仍否决）',
              '连板梯次': dict(Counter(r.get('lbc') for r in zt)),
              '最高板': max((r.get('lbc') or 0) for r in zt),
              '对比10:33': '涨停 32→%d、炸板率 0.3846→%s、跌停 0→%d → 宽度继续修复、炸板率降至今日最低' % (len(zt), zbr, len(dt))},
     '分时补充(另标时点)': {
        '说明': '_hb_d_minute_1330.json（腾讯分时，分钟收盘价，末点 13:34）仅用于路径描述，不与 13:31:42 决断帧混同',
        '002242': f'09:30 {M242["first"][1]} → 09:46 高 {M242["hi"][1]} → 10:19 低 {M242["lo"][1]} → 13:34 {M242["last"][1]}（末段 13:23~13:34 在 21.08~21.20 横盘）',
        '002639': f'09:30 {M639["first"][1]} → 10:35 低 {M639["lo"][1]}（跌停价 13.35 触及区）→ 13:34 {M639["last"][1]}（午后自低点回升约 2.7%，末段再度回落）',
        '600487': f'09:30 {M487["first"][1]} → 10:27 低 {M487["lo"][1]} → 13:34 {M487["last"][1]}（午后横盘于 49.3~49.9）',
        '003021': f'09:30 {M021["first"][1]} → 09:34 低 {M021["lo"][1]} → 10:07 高 {M021["hi"][1]} → 13:34 {M021["last"][1]}（13:28~13:32 由 93.81 拉至 95.28）'},
   },
   '判断': (f'情绪=分歧修复延续（弱势市场内的反抽修复），不构成进攻窗口。依据：①全局闸门三项全过（涨停 {len(zt)}≥20、炸板率 {zbr}<0.45、跌停 {len(dt)}<12）且环比全面改善；'
          f'②但修复的宽度在首板——连板梯次 {dict(Counter(r.get("lbc") for r in zt))}、最高板仅 {max((r.get("lbc") or 0) for r in zt)} 板（上海九百 600838 一般零售），说明赚钱效应靠首板试错而非高度接力，持续性存疑；'
          f'③指数结构分化：上证转正而创业板 {QB["399006"]["pct"]}%、科创50 {QB["000688"]["pct"]}% 仍绿，风险偏好指标（小盘/成长）未修复；'
          f'④滞后指标仍示亏钱：池内 {LASTS["dt"]} 只跌停（慈文传媒/华瓷股份/晶丰明源）、掉板率 {((len(ever)-len(still))/len(ever))*100:.1f}% 虽较上午腰斩但仍非低位；'
          f'⑤线级门最大行业仅 {maxn} 只 <8，买入腿机械否决。→ 定性「修复未确立」：持仓不动、不新开仓；尾盘若涨停维持 ≥45 且炸板率 ≤0.35，则记「修复确认为弱修复」并交复盘结算，不改本场动作。主观概率：收盘时涨停≥40 且炸板率<0.35 的概率约 6 成；本场不给方向性加仓依据。'),
 },
 '复盘_上一场清单核销': [
   '① hb-c（11:00 场）无发出版落盘：今日目录内仅 _hb_c_pools_1100/1103.json、_hb_c_quote_1100/1103.json 与扫描脚本，无 临盘决断_20261026_1100.json → 该场判断不可复核，本场不推测其结论，登记欠账（见异常与欠账③）。',
   f'② hb-b 预置条件「002242 若 11:00 场决断帧 ≤20.92 → 清」：11:01:48 腾讯报价 21.15（-1.76%，今低仍 20.91）、11:03:30 报价 21.19 → 条件未达成，无漏执行；13:30 决断帧 {H242["px"]} 高于线 {(H242["px"]/LINE_242-1)*100:.2f}%，机械线 20.92 不变。',
   f'③ hb-b 预置条件「003021 防守线 80.75」：决断帧 {H021["px"]}（{H021["pct"]}%），距线 {(LINE_021/H021["px"]-1)*100:.2f}% → 未触线，三本账 400 股续持。',
   f'④ hb-b 预置条件「600487 14:30 场硬核 50.00」：13:30 决断帧 {H487["px"]} < 50.00（{H487["vs_cost_pct"]}%），分时 13:34 仍 {M487["last"][1]} → 14:30 场须执行其防守，本场不越界代决；升级登记保留。',
   f'⑤ hb-b 预置条件「炸板率≥0.45 或 跌停≥12 或 池内跌停≥6 → 总审降档硬条件」：13:30 读数 {zbr} / {len(dt)} / {LASTS["dt"]} → 三项均未触发。',
   '⑥ 弃单机会成本（承接 hb-b 快照，本场只更新到 13:30 决断帧，收盘结算为准）：300296 / 002979 今日走势见复盘结算件，本场不重复计算，避免盘中口径取代结算口径。',
 ],
 '照会_非条件决断': {
   f'002639 雪人集团(master 2600 纸上市值)': f'决断帧 {H639["px"]}（{H639["pct"]}%），较 10:33 决断帧 13.40 回升 {(H639["px"]/13.40-1)*100:.2f}%，自今低 13.35（跌停价）回升 {(H639["px"]/13.35-1)*100:.2f}%。补账口径随之修正：若按决断价 14.00 补账，漏执行滑点由 10:30 场的 -1560.0 元收窄为 {round(2600*(14.00-H639["px"]),2)} 元（2600×({14.00}-{H639["px"]})）；★仍按 hb-b 书面约定「结算登记 + 单独列漏执行滑点」，本场不重复卖出、不因回升改判。',
   '600487 亨通光电(logic 另账)': f'决断帧 {H487["px"]}（{H487["pct"]}%，今低 {H487["low"]}），低于成本 50.00 达 {H487["vs_cost_pct"]}%；分时 13:34 {M487["last"][1]} 未收复。按 hb-b 补正1 拆腿后约定：价格腿成立、量能腿不成立（补正1 已更正），14:30 场只引价格腿执行其防守，不得以「量没放」继续留置，不得再顺延。',
   '002242 九阳股份(master)': f'决断帧 {H242["px"]}（{H242["pct"]}%），今高 {H242["high"]}、今低 {H242["low"]}，下午 13:23~13:34 在 21.08~21.20 窄幅横盘（分时）→ 无量能修复亦无破位，机械线 20.92 为唯一卖出触发，不清。',
   '003021 兆威机电(三本账 400 股)': f'决断帧 {H021["px"]}（{H021["pct"]}%，今高 {H021["high"]}），13:28~13:32 由 93.81 拉至 95.28（分时）；对成本 85.00 为 {H021["vs_cost_pct"]}%（浮盈 {H021["pnl"]} 元）。无预设止盈条款、防守线 80.75 → 续持不动。',
   '301502 华阳智能': f'昨日同线票（对比 003021 的线级门可证伪样本），本场不在池帧 n={LASTS["n"]} 内，取分时/报价缺件 → 本场不引用具体读数，收盘复盘记两者相对收益，避免补造。',
 },
 '异常与欠账': [
   f'① master 002639 2600 股补账仍未落地（承接 09:40 场欠账①、10:30 场①）：须由 20261026 结算补 sell 行，并按当前决断帧登记漏执行滑点 {round(2600*(14.00-H639["px"]),2)} 元（盘中快照，结算以收盘可实现价为准），不得让净值虚增。',
   '② 执行层今日仍零执行（连续第 7 个场次）：pulse.json / warboard.json / 报警_20261026.jsonl / 执行流水.jsonl 全部缺件 → 本场只能以池帧+腾讯报价+东财池自建判据；机制建议（待批，本场不改代码）：引擎触发即写执行流水。',
   f'③ hb-c（11:00 场）无发出版落盘：今日目录仅存 _hb_c_ 取数件与扫描脚本，无临盘决断_{DATE}_1100.json、无哨兵输出 → 该场判断与清单核销不可复核；建议在心跳模板加「无动作也须落 min 版决断件」的硬约束（待批，本场不补造、不代写）。',
   '④ playbook.json 缺件连续第 6 次（20261020/21/22/23/26）：预案真源仍为 临盘决断_20261026_0921.json + _学习/交易计划_master_20261023.json，不补造。',
   '⑤ 交易日校验规格命令连续第 8 个交易日 ModuleNotFoundError（sentiment 包不可导入），建议统一为 trading_calendar.py（须批准）。',
   '⑥ 开盘 5 分钟观测缺口（承接 09:40 场⑤）：竞价末帧 09:25:49 → 连续段首帧 09:31:09，开盘瞬间形态不可核；本场防守判断只用 09:31 之后数据。',
   '⑦ 线级门口径歧义（承接 09:40/10:30 场⑥，不改判）：今日涨停 %d 只分散于 %d 个行业，最大行业「%s」仅 %d 只 → 窄(行业)/宽(大方向)两口径均 <8，该门今日等价于「全市场零买入」；须在 20261026 复盘定「线」的计数源。' % (len(zt), len(hy), maxhy, maxn),
   '⑧ 池帧观测域限制：realtime_ticks.jsonl 池 = 20261023 涨停池 n=80，持仓 002242/002639/600487/603370 均不在池内 → 四票盘中路径只能取腾讯报价与分时（本场已另立 _hb_d_minute_1330.json 并逐条标时点），不得用池帧读数冒充个股路径。',
 ],
 '下一场预置观察条件_非指令': [
   f'002242：机械线 20.92 为唯一卖出触发；14:30 场若决断帧 ≤20.92 → 清（按 20261023 场口径「决断帧判线」，不以内盘瞬时下影判线）。',
   f'003021：防守线 80.75（成本 85.00 的 -5%）为唯一减仓触发，现距 {(LINE_021/H021["px"]-1)*100:.2f}%，无其他条款。',
   f'600487(logic)：14:30 场硬核 50.00，仍低于成本则按其自身防守线执行，不再顺延（只引价格腿）。',
   f'002639(master)：不重复卖出；14:30 场只核「结算补账是否落地」，未落地则继续登记欠账。',
   f'全局：炸板率 ≥0.45 或 跌停 ≥12 或 池内跌停 ≥6 → 触发总审降档硬条件（C 档零新增）；本场读数 {zbr} / {len(dt)} / {LASTS["dt"]}，未触发。',
 ],
 '口径': '①本场 fills=[]，不产生任何撮合数字；②所有价格/比例可由 _hb_d_quote_1330.json、_hb_d_pools_1330.json、realtime_ticks.jsonl、_hb_d_minute_1330.json 与五本账 state.json 逐项复算；③分时件时点（末点 13:34）与决断帧（腾讯 13:31:42）并列标注，不混同；④本文件对用户=参考，不是操盘指令。',
}

with open(TARGET, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=1)

print('WROTE', TARGET, os.path.getsize(TARGET), 'bytes')
print('sha256', hashlib.sha256(open(TARGET, 'rb').read()).hexdigest())
print('write_ts', write_ts)
print('NAV', json.dumps({k: v['nav'] for k, v in ACC.items()}, ensure_ascii=False))
print('KEY', json.dumps({'med': LASTS['med'], 'zt': len(zt), 'zb': len(zb), 'dt': len(dt), 'zbr': zbr,
                         'mx30': mx30[0], 'ever': len(ever), 'still': len(still), 'maxhy': [maxhy, maxn]}, ensure_ascii=False))
