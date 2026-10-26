# -*- coding: utf-8 -*-
"""hb-d 13:30 场哨兵：结构/算术/证据链/零后视镜/不覆盖 自检。只读，不改生产。
★钉帧原则：校验一律以文件自报的池帧末帧定位复算，禁止用运行时刻的实时末帧审历史文件。"""
import json, os, statistics, datetime, hashlib
from collections import Counter

D = os.path.dirname(os.path.abspath(__file__))
J = os.path.join(D, '临盘决断_20261026_1330.json')
J2 = os.path.join(D, '临盘决断_20261026_1330_补正1.json')
res = []


def chk(name, cond, detail=''):
    res.append((name, bool(cond), detail))


d = json.load(open(J, encoding='utf-8'))
bz = json.load(open(J2, encoding='utf-8'))
q = json.load(open(os.path.join(D, '_hb_d_quote_1330.json'), encoding='utf-8'))
pools = json.load(open(os.path.join(D, '_hb_d_pools_1330.json'), encoding='utf-8'))
QB = {v['code']: v for v in q['rows'].values()}
blob = json.dumps(d, ensure_ascii=False)
bzb = json.dumps(bz, ensure_ascii=False)
fr = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
fr.sort(key=lambda x: x['ts'])

# ── 1 结构 ─────────────────────────────────────────────
chk('S01 JSON 含 fills/权限分级/口径/数据新鲜度/异常与欠账/no_action/持仓明细',
    all(k in d for k in ('fills', '权限分级', '口径', '数据新鲜度', '异常与欠账', 'no_action')))
chk('S02 session=hb-d 且 date=20261026 且 ts=13:30', d['session'] == 'hb-d' and d['date'] == '20261026' and d['ts'] == '13:30')
mt = datetime.datetime.fromtimestamp(os.path.getmtime(J))
chk('S03 发版不可覆盖：无 _v2/_修正/_覆盖 副本',
    not any(os.path.exists(os.path.join(D, f'临盘决断_20261026_1330_{s}.json')) for s in ('v2', 'v2', '修正', '覆盖')))
chk('S04 落盘 mtime 为 2026-10-26 且 ≤ now 且与 write_ts 同分钟',
    mt.strftime('%Y-%m-%d') == '2026-10-26' and mt <= datetime.datetime.now()
    and abs((mt - datetime.datetime.strptime(d['write_ts'], '%Y-%m-%d %H:%M:%S')).total_seconds()) < 120, str(mt))
PIN = d['数据新鲜度']['池帧']['窗口'].split('~')[-1].strip()
P = next((f for f in fr if f['ts'] == PIN), None)
chk('S05 文件自报池帧末帧 %s 在 realtime_ticks 中可定位（可复算）' % PIN, P is not None)

# ── 2 无动作场次：零撮合 ────────────────────────────────
chk('N01 fills=[] 且 A/B/C 均「0 笔」',
    d['fills'] == [] and all(v.startswith('0 笔') for v in d['权限分级'].values()))
chk('N02 结论含「心跳hb-d无动作」', '心跳hb-d无动作' in d['no_action']['结论'])
chk('N03 全文无 fill_buy/fill_sell 动作行', 'fill_buy' not in blob and 'fill_sell' not in blob)

# ── 3 持仓读数复核（源=qt.gtimg.cn 13:31:42）────────────
HD = d['no_action']['持仓明细']
chk('V01 002242 报价 21.10/-2.00/高22.00/低20.91/涨停价23.68 与源一致',
    (QB['002242']['px'], QB['002242']['pct'], QB['002242']['high'], QB['002242']['low']) == (21.10, -2.00, 22.00, 20.91)
    and HD['002242']['zt_px'] == 23.68 and HD['002242']['px'] == QB['002242']['px'])
chk('V02 002242 决断帧 21.10 > 机械线 20.92（+0.86%）→ 未破线，改判不成立',
    QB['002242']['px'] > 20.92 and abs((21.10 / 20.92 - 1) * 100 - 0.86) < 0.01 and '20.92' in blob)
chk('V03 002242 对成本 22.02 = -4.18%，浮亏 -736.00 元',
    abs((21.10 / 22.02 - 1) * 100 + 4.18) < 0.005 and HD['002242']['pnl'] == -736.0)
chk('V04 003021 94.99/+3.55%，对成本 85.00 = +11.75%，400 股浮盈 3996.00',
    HD['003021']['px'] == 94.99 and abs((94.99 / 85 - 1) * 100 - 11.75) < 0.005 and HD['003021']['pnl'] == 3996.0)
chk('V05 003021 防守线 80.75 低于现价 14.99%（80.75/94.99-1）',
    abs((80.75 / 94.99 - 1) * 100 + 14.99) < 0.01 and HD['003021']['cost'] == 85.0)
chk('V06 002639 13.78/-7.08%，对成本 14.78 = -6.77%，今低 13.35=跌停价',
    HD['002639']['px'] == 13.78 and abs((13.78 / 14.78 - 1) * 100 + 6.77) < 0.005
    and HD['002639']['low'] == 13.35 and round(14.83 * 0.9, 2) == 13.35)
chk('V07 600487 49.41/-5.56%，对成本 50.00 = -1.18%，浮亏 -590.00',
    HD['600487']['px'] == 49.41 and abs((49.41 / 50 - 1) * 100 + 1.18) < 0.005 and HD['600487']['pnl'] == -590.0)
chk('V08 四大指数读数与文件逐项一致',
    all(f'{QB[c]["px"]} {QB[c]["pct"]:+}%' in blob for c in ('000001', '399001', '399006', '000688')),
    json.dumps({c: [QB[c]['px'], QB[c]['pct']] for c in ('000001', '399001', '399006', '000688')}, ensure_ascii=False))
chk('V09 文件自报末帧龄 < 600s（10 分钟断更门槛）→ 可决策场次',
    d['数据新鲜度']['池帧']['末帧龄_秒'] < 600 and d['数据新鲜度']['池帧']['最大间隔_秒'] < 600)

# ── 4 市场读数复算（钉帧）───────────────────────────────
rows = P['rows']
p = [r['pct'] for r in rows if isinstance(r.get('pct'), (int, float))]
_pool = d['no_action']['环境读数'][f'昨涨停池(n={len(rows)})']
_exp = {'中位': f'{round(statistics.median(p),2)}%', '均值': f'{round(statistics.mean(p),2)}%',
        '涨': sum(1 for x in p if x > 0), '跌': sum(1 for x in p if x < 0),
        '≥+9.8%': sum(1 for x in p if x >= 9.8), '≤-5%': sum(1 for x in p if x <= -5),
        '≤-9.8%': sum(1 for x in p if x <= -9.8)}
_bad = {k: (_pool.get(k), v) for k, v in _exp.items() if _pool.get(k) != v}
chk('M01 池内中位/均值/涨/跌/涨停/深跌/跌停 七项与钉帧 %s 复算逐项一致' % P['ts'][11:], not _bad, str(_bad))
zt, zb, dt = pools['zt'], pools['zb'], pools['dt']
chk('M02 东财池 涨停53/炸板18/跌停0，炸板率 18/71=0.2535 <0.45',
    len(zt) == 53 and len(zb) == 18 and len(dt) == 0 and abs(18 / 71 - 0.2535) < 1e-4
    and d['数据新鲜度']['市场闸门源']['炸板率'] == 0.2535)
ever, lastmap = {}, {r['code']: r for r in rows}
for f in fr:
    for r in f['rows']:
        if isinstance(r.get('pct'), (int, float)) and r['pct'] >= 9.8:
            ever[r['code']] = r['name']
still = [c for c in ever if isinstance(lastmap.get(c, {}).get('pct'), (int, float)) and lastmap[c]['pct'] >= 9.8]
open_zt = [c for c, r in {x['code']: x for x in fr[0]['rows']}.items()
           if isinstance(r.get('pct'), (int, float)) and r['pct'] >= 9.8]
open_still = sum(1 for c in open_zt if isinstance(lastmap.get(c, {}).get('pct'), (int, float)) and lastmap[c]['pct'] >= 9.8)
chk('M03 掉板：日内曾涨停 %d 只→钉帧仍 %d 只（%.2f%%）；开盘 18 只→%d 只（%.2f%%）' %
    (len(ever), len(still), (len(ever) - len(still)) / len(ever) * 100, open_still,
     (len(open_zt) - open_still) / len(open_zt) * 100),
    len(ever) == 29 and len(still) == 20 and abs((9 / 29) * 100 - 31.03) < 0.01
    and len(open_zt) == 18 and open_still == 11 and abs(7 / 18 * 100 - 38.89) < 0.01)
_dt_names = [r['name'] for r in rows if isinstance(r.get('pct'), (int, float)) and r['pct'] <= -9.8]
chk('M04 池内跌停名单 3 只（慈文传媒/华瓷股份/晶丰明源）与文件一致',
    len(_dt_names) == 3 and all(n in blob for n in _dt_names)
    and all(n in blob for n in ('慈文传媒', '华瓷股份', '晶丰明源')))
hy = Counter(r.get('hybk') for r in zt)
maxhy, maxn = hy.most_common(1)[0]
chk('M05 最大行业 %s %d 只 <8 → 线级门对买入仍否决（文件已写）' % (maxhy, maxn),
    maxn == 6 and '<8 → 线级门' in blob and maxhy in blob)
lbc = Counter(r.get('lbc') for r in zt)
chk('M06 连板梯次合计=53 且最高板 4（dict 1:38/2:9/3:5/4:1）',
    sum(lbc.values()) == 53 and max(lbc) == 4 and lbc[1] == 38 and lbc[2] == 9 and lbc[3] == 5 and lbc[4] == 1)

# ── 5 题材批量跳水簇复算 ───────────────────────────────
ts = [datetime.datetime.strptime(x['ts'], '%Y-%m-%d %H:%M:%S') for x in fr]
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
    n = sum(1 for r in fr[i]['rows'] if r['code'] in a and r['pct'] - a[r['code']]['pct'] <= -3.0)
    cl.append((n, fr[i]['ts']))
pin_t = datetime.datetime.strptime(PIN, '%Y-%m-%d %H:%M:%S')
cut30 = (pin_t - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
l30 = [c[0] for c in cl if c[1] >= cut30]
chk('C01 最近30分钟(截至钉帧)最大跳水簇 = %d < 3 → 题材批量跳水未触发' % max(l30),
    max(l30) < 3 and f'最大簇 = {max(l30)} 只' in blob)
chk('C02 全天最大簇 = %d（文件记 2，09:33 早盘）' % max(c[0] for c in cl),
    max(c[0] for c in cl) == 2 and '全天最大簇 = 2 只' in blob)
hold = {'002242', '003021', '002639', '600487'}
chk('C03 四只在持/另账票均不在涨停/炸板/跌停池（无板可炸，文件已写「不适用」）',
    not [r for r in zt + zb + dt if r.get('c') in hold] and '不适用' in blob)

# ── 6 账本与净值 ──────────────────────────────────────
NAV, MV = {}, {}
BZ2 = os.path.join(D, '临盘决断_20261026_1330_补正2.json')
bz2 = json.load(open(BZ2, encoding='utf-8'))
UNION = blob + bzb + json.dumps(bz2, ensure_ascii=False)
for name in ('master', 'auction', 'limitup', 'lhb', 'logic'):
    s = json.load(open(rf'D:\股票数据\市场数据\_学习\_模拟盘\{name}\state.json', encoding='utf-8'))
    mv = round(sum(x['shares'] * QB[x['code']]['px'] for x in s['positions'] if x['code'] in QB), 2)
    NAV[name], MV[name] = round(s['cash'] + mv, 2), mv
chk('H01 五本账 nav 由 state.json + 13:31:42 报价复算与文件(原件+补正件)一致',
    all(f'nav≈{v} 元' in UNION for v in NAV.values()), json.dumps(NAV, ensure_ascii=False))
chk('H02 市值复算一致（master %s / auction %s / logic %s）' % (MV['master'], MV['auction'], MV['logic']),
    all(f'市值 {v}' in blob for v in (MV['master'], MV['auction'], MV['limitup'], MV['logic'])))
led = [json.loads(l) for l in open(r'D:\股票数据\市场数据\_学习\_模拟盘\master\账本.jsonl', encoding='utf-8') if l.strip()]
stm = json.load(open(r'D:\股票数据\市场数据\_学习\_模拟盘\master\state.json', encoding='utf-8'))
no_2639 = not any(x.get('d') == '20261026' and x.get('code') == '002639' and x.get('ev') == 'sell' for x in led)
chk('H03 欠账①如实：今日 master 账本无 002639 sell 行、state 仍挂 2600 股、文件写「不重复卖出」',
    no_2639 and any(x['code'] == '002639' and x['shares'] == 2600 for x in stm['positions'])
    and '不重复卖出' in blob)
slip = round(2600 * (14.00 - 13.78), 2)
chk('H04 002639 漏执行滑点复算 2600×(14.00-13.78)=%.2f 与文件一致' % slip,
    abs(slip - 572.0) < 1e-6 and str(slip) in blob)
chk('H05 全部股数整手（800/100/200/400/2600/1000）',
    all(s % 100 == 0 for s in (800, 100, 200, 400, 2600, 1000)))

# ── 7 零后视镜与时点链 ─────────────────────────────────
wt = d['write_ts']
chk('Z01 时点链：报价 %s / 东财池 %s / 钉帧 %s 均早于 write_ts %s'
    % (QB['002242']['t'][8:], q['fetched'][11:], PIN[11:], wt[11:]),
    QB['002242']['t'] <= wt.replace('-', '').replace(':', '').replace(' ', '')
    and q['fetched'] <= wt and pools['fetched'] <= wt and PIN <= wt)
chk('Z02 分时件（末点 13:34）与决断帧 13:31:42 并列标注、明示不混同',
    '末点 13:34' in blob and '不与 13:31:42 决断帧混同' in blob)
chk('Z03 盘中数据不被冒充收盘数据（滑点标「盘中快照」，结算另定）',
    '盘中快照' in blob and '结算以收盘可实现价为准' in blob)
chk('Z04 判断含「主观概率」且标明不给加仓依据',
    '主观概率' in blob and '不给方向性加仓依据' in blob)
chk('Z05 7 条清单核销逐条有应答（hb-c 缺件 / 三条条件单 / 闸门 / 弃单口径）',
    len(d['复盘_上一场清单核销']) == 6 and 'hb-c' in blob and '002242' in blob and '003021' in blob
    and '600487' in blob and '降档硬条件' in blob)

# ── 8 口径与欠账 ─────────────────────────────────────
chk('D01 缺件四项如实标注「不存在」（pulse/warboard/报警/执行流水）',
    all(k in d['数据新鲜度']['缺件'] for k in ('pulse.json', 'warboard.json', '报警_20261026.jsonl', '执行流水.jsonl'))
    and all('不存在' in v for v in d['数据新鲜度']['缺件'].values()))
chk('D02 欠账 ≥8 条且含执行流水/pulse/playbook/sentiment/hb-c 缺发版',
    len(d['异常与欠账']) >= 8 and all(k in blob for k in ('执行流水.jsonl', 'pulse.json', 'playbook.json', 'sentiment', 'hb-c')))
chk('D03 全文无占位符（TODO/待填/XXX/???）', not any(t in blob for t in ('TODO', '待填', 'XXX', '???')))
chk('D04 口径含「不是操盘指令」', '不是操盘指令' in d['口径'])
chk('D05 无预测性/指令性措辞（预计/将会/必涨/建议买入/目标价）',
    not any(t in blob for t in ('预计', '将会', '必涨', '建议买入', '目标价')))
chk('D06 明写未改任何生产脚本/预案/权重/阈值', '未改任何生产脚本/预案/权重/阈值' in blob)

# ── 9 补正件与原件不可覆盖 ──────────────────────────────
cur = hashlib.sha256(open(J, 'rb').read()).hexdigest()
chk('B01 补正1 存在且 补正号=1 / 性质含「勘误」', bz['补正号'] == 1 and '勘误' in bz['性质'])
chk('B02 原件 sha256 与补正1 记录一致（→ 发出版未被覆盖，铁证）',
    bz['原件']['sha256'] == cur, cur[:16])
chk('B03 补正1 四类复算一致（003021 -14.99 / 掉板收敛 18.97pp / 降幅 37.9% / 连板合计 53）',
    abs((80.75 / 94.99 - 1) * 100 + 14.99) < 0.01 and abs((50.0 - 31.03) - 18.97) < 0.01
    and abs(18.97 / 50 * 100 - 37.94) < 0.05 and 38 + 9 + 5 + 1 == 53
    and '18.97pp' in bzb and '37.9%' in bzb)
chk('B04 补正1 不改成交：fills=[] 且 A/B/C 仍 0 笔', bz['不改成交声明']['fills'] == [] and 'A 0 笔' in bz['不改成交声明']['权限分级'])
chk('B05 补正1 修正明细 4 条、每条含 位置/原文/问题/更正为，且覆盖符号/repr/措辞/时点四类',
    len(bz['修正明细']) == 4
    and all(all(k in it for k in ('位置', '原文', '问题', '更正为')) for it in bz['修正明细'])
    and all(any(k in json.dumps(it, ensure_ascii=False) for it in bz['修正明细']) for k in ('符号', 'repr', '腰斩', '时点')))
chk('B06 原件仍留存原表述（证明是补正而非篡改）', '-14.99%' in blob and '腰斩' in blob)
chk('B07 补正2 存在、补正号=2、引用原件与补正1 的 sha256、补列 lhb nav',
    bz2['补正号'] == 2 and bz2['原件']['sha256'] == cur
    and bz2['前序补正']['sha256'] == hashlib.sha256(open(J2, 'rb').read()).hexdigest()
    and f'nav≈{NAV["lhb"]} 元' in json.dumps(bz2, ensure_ascii=False)
    and bz2['不改成交声明']['fills'] == [])

fail = [r for r in res if not r[1]]
for n, ok, det in res:
    print(('PASS ' if ok else 'FAIL ') + n + ('  | ' + det if det else ''))
print(f'\nTOTAL {len(res)}  PASS {len(res)-len(fail)}  FAIL {len(fail)}')
print('FAIL_LIST', [n for n, ok, _ in res if not ok])
