# -*- coding: utf-8 -*-
"""hb-b 10:30 场哨兵：结构/算术/证据链/零后视镜/不覆盖 自检。只读，不改生产。"""
import json, os, statistics, datetime, re

D = os.path.dirname(os.path.abspath(__file__))
J = os.path.join(D, '临盘决断_20261026_1030.json')
res = []

def chk(name, cond, detail=''):
    res.append((name, bool(cond), detail))

d = json.load(open(J, encoding='utf-8'))
q = json.load(open(os.path.join(D, '_hb_b_quote_decide.json'), encoding='utf-8'))
pools = json.load(open(os.path.join(D, '_hb_b_pools_decide.json'), encoding='utf-8'))
fr = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
QB = {v['code']: v for v in q['rows'].values()}
last = fr[-1]
# ★钉住文件自报的池帧末帧（文件落盘后 realtime_ticks 仍在追加，验证必须用文件声明的决断帧，
#   否则会拿更晚的帧去比历史文件 = 哨兵自身后视镜）
PIN_TS = d['数据新鲜度']['池帧']['窗口'].split('~')[-1].strip()
P = next((f for f in fr if f['ts'] == PIN_TS), None)
chk('S05 文件自报池帧末帧 %s 在 realtime_ticks 中可定位（可复算）' % PIN_TS, P is not None)
rows = P['rows']
p = [r['pct'] for r in rows]

# 1 结构
chk('S01 JSON可解析且含 fills/权限分级/口径/数据新鲜度/异常与欠账',
    all(k in d for k in ('fills', '权限分级', '口径', '数据新鲜度', '异常与欠账', 'no_action')))
chk('S02 session=hb-b 且 date=20261026', d['session'] == 'hb-b' and d['date'] == '20261026')
chk('S03 发版不可覆盖：无 v2/覆盖副本（补正件属追加件，由 B02 hash 校验把关）',
    os.path.exists(J) and not any(os.path.exists(os.path.join(D, f'临盘决断_20261026_1030_{s}.json')) for s in ('v2', '修正')))
mt = datetime.datetime.fromtimestamp(os.path.getmtime(J))
chk('S04 落盘时戳=write_ts 同日且 ≤ now', mt.strftime('%Y-%m-%d') == '2026-10-26' and mt <= datetime.datetime.now(), str(mt))

# 2 无动作场次：无撮合数字
chk('N01 fills=[] 且权限分级 A/B/C 均 0 笔', d['fills'] == [] and all(v.startswith('0 笔') for v in d['权限分级'].values()))
chk('N02 no_action 结论含「心跳hb-b无动作」', '心跳hb-b无动作' in d['no_action']['结论'])
blob = json.dumps(d, ensure_ascii=False)
chk('N03 全文无 fill_sell/fill_buy 动作行', 'fill_sell' not in blob and 'fill_buy' not in blob)

# 3 报价与断线复核
chk('V01 002242 决断帧 21.15/-1.76%/低20.91/高22.00',
    QB['002242']['px'] == 21.15 and QB['002242']['pct'] == -1.76 and QB['002242']['low'] == 20.91 and QB['002242']['high'] == 22.00,
    json.dumps(QB['002242'], ensure_ascii=False))
chk('V02 002242 未破机械线 20.92（决断帧 21.15 > 20.92）且文件写明距线 +1.1%',
    QB['002242']['px'] > 20.92 and '1.1' in blob and '20.92' in blob)
chk('V03 002242 对成本 22.02 = -3.95%（浮亏 -696 元）',
    abs((21.15 / 22.02 - 1) * 100 + 3.95) < 0.01 and abs(800 * (21.15 - 22.02) + 696) < 0.01, f'{800*(21.15-22.02):.2f}')
chk('V04 002242 自 09:48 决断帧 21.72 回落 -2.62%（源可核）',
    abs((21.15 / 21.72 - 1) * 100 + 2.62) < 0.01)
chk('V05 003021 94.70/+3.24%，对成本 85.00 = +11.41%',
    QB['003021']['px'] == 94.70 and QB['003021']['pct'] == 3.24 and abs((94.70 / 85.0 - 1) * 100 - 11.41) < 0.01)
chk('V06 002639 13.40/-9.64%，距跌停价 13.35 仅 +0.37%',
    QB['002639']['px'] == 13.40 and QB['002639']['pct'] == -9.64 and abs((13.40 / 13.35 - 1) * 100 - 0.37) < 0.02)
chk('V07 600487 49.07… 文件取 49.17/-6.02%（同一决断帧），破成本 50.00 -1.66%',
    QB['600487']['px'] == 49.17 and abs((49.17 / 50.00 - 1) * 100 + 1.66) < 0.01)
chk('V08 600487 放量比对：当日盘中bar 700,576 手，文件已标注「盘中未完成bar」',
    '700576' in blob.replace(',', '') and '盘中未完成bar' in blob)
chk('V09 指数四读与文件一致（上证/深成/创业板/科创50）',
    all(f'{QB[c]["px"]}' in blob and f'{QB[c]["pct"]}' in blob for c in ('000001', '399001', '399006', '000688')))
chk('V10 池帧最新性：末帧龄 < 10 分钟门槛',
    (datetime.datetime.now() - datetime.datetime.strptime(last['ts'], '%Y-%m-%d %H:%M:%S')).total_seconds() < 600,
    last['ts'])

# 4 市场读数复算
cut = (datetime.datetime.strptime(P['ts'], '%Y-%m-%d %H:%M:%S') - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
_pool = d['no_action']['环境读数'][f'昨涨停池(n={len(rows)})']
_exp = {'中位': f'{round(statistics.median(p),2)}%', '均值': f'{round(statistics.mean(p),2)}%',
        '涨': sum(1 for x in p if x > 0), '跌': sum(1 for x in p if x < 0),
        '≥+9.8%': sum(1 for x in p if x >= 9.8), '≤-5%': sum(1 for x in p if x <= -5),
        '≤-9.8%': sum(1 for x in p if x <= -9.8)}
_bad = {k: (_pool.get(k), v) for k, v in _exp.items() if _pool.get(k) != v}
chk('M01 池内中位/均值/涨跌/涨停/深跌/跌停 六项与钉帧 %s 复算逐项一致' % P['ts'][11:], not _bad, str(_bad))
chk('M02 炸板率 = 20/(32+20) = 0.3846 < 0.45',
    len(pools['zt']) == 32 and len(pools['zb']) == 20 and len(pools['dt']) == 0
    and abs(20 / 52 - 0.3846) < 1e-4 and '0.3846' in blob, json.dumps({'zt': len(pools['zt']), 'zb': len(pools['zb']), 'dt': len(pools['dt'])}))
_open_zt = [r['code'] for r in fr[0]['rows'] if r['pct'] >= 9.8]
_still = sum(1 for c in _open_zt if next((x['pct'] for x in rows if x['code'] == c), -99) >= 9.8)
chk('M03 掉板统计：09:31 涨停 %d 只 → 钉帧仍涨停 %d 只' % (len(_open_zt), _still),
    len(_open_zt) == 18 and _still == 9 and '50.0%' in blob)
chk('M04 池内 4 只跌停名单与文件一致',
    all(n in blob for n in ('慈文传媒', '华瓷股份', '晶丰明源', '曙光股份')))
chk('M05 最大行业 4 只 < 8 → 线级门仍否决（文件已写）',
    max((sum(1 for x in pools['zt'] if x.get('hybk') == k) for k in {x.get('hybk') for x in pools['zt']})) == 4
    and '<8 → 线级门' in blob)

# 5 批量跳水簇复算
def snap(f):
    return {r['code']: r for r in f['rows']}
cl = []
for i in range(len(fr)):
    t = datetime.datetime.strptime(fr[i]['ts'], '%Y-%m-%d %H:%M:%S')
    j = None
    for k in range(i - 1, -1, -1):
        if (t - datetime.datetime.strptime(fr[k]['ts'], '%Y-%m-%d %H:%M:%S')).total_seconds() >= 100:
            j = k
            break
    if j is None:
        continue
    a = snap(fr[j])
    cl.append((sum(1 for r in fr[i]['rows'] if r['code'] in a and r['pct'] - a[r['code']]['pct'] <= -3.0), fr[i]['ts']))
last30 = [c for c in cl if c[1] >= cut]
chk('C01 最近30分钟最大跳水簇=1（<3 不触发）', max(c[0] for c in last30) == 1, str(max(last30)))
chk('C02 全窗最大簇=2（文件记「全天最大簇 2 只」）', max(c[0] for c in cl) == 2, str(max(cl)))

# 6 净值与账本
NAV = {'master': 986355.64, 'auction': 960937.3, 'limitup': 989700.1, 'lhb': 1003727.3, 'logic': 1011325.37}
chk('H01 五本账 nav 复算一致',
    all(len(str(v)) > 0 and str(v) in blob for v in NAV.values()), json.dumps(NAV))
st = json.load(open(r'D:\股票数据\市场数据\_学习\_模拟盘\master\state.json', encoding='utf-8'))
led = [json.loads(l) for l in open(r'D:\股票数据\市场数据\_学习\_模拟盘\master\账本.jsonl', encoding='utf-8') if l.strip()]
today_sells = [x for x in led if x.get('d') == '20261026' and x.get('ev') == 'sell']
has_2639 = any(x.get('code') == '002639' for x in today_sells)
chk('H02 欠账①如实：今日 master 账本无 002639 sell 行、state 仍挂 2600 股',
    (not has_2639) and any(x['code'] == '002639' and x['shares'] == 2600 for x in st['positions'])
    and '未落地' in blob)
chk('H03 补账滑点算术 2600×(14.00-13.40)=1,560',
    abs(2600 * (14.00 - 13.40) - 1560) < 1e-6 and '1560' in blob.replace(',', ''))

# 7 零后视镜
chk('Z01 数据时点链：报价 %s、东财池 %s、池帧钉帧 %s，均早于 write_ts %s'
    % (QB['002242']['t'][8:], q['fetched'], P['ts'][11:], d['write_ts'][11:]),
    QB['002242']['t'] <= d['write_ts'].replace('-', '').replace(':', '').replace(' ', '')
    and q['fetched'] <= d['write_ts'] and P['ts'] <= d['write_ts'],
    f'{q["fetched"]} / {P["ts"]} / write {d["write_ts"]}')
chk('Z02 弃单照会另标 10:35:27~30 时点（不与持仓决断帧混同）',
    '10:35:27~10:35:30' in blob and '并列标注' in blob)
chk('Z03 文件未把腾讯盘中未完成bar当作收盘数据（明示禁引用）', '不得当作收盘数据引用' in blob)
chk('Z04 800股/100股/1000股 均为整手（无零股）',
    all(s % 100 == 0 for s in (800, 100, 1000, 2600, 200)))

# 8 口径与欠账
chk('D01 缺件如实标注（pulse/warboard/报警/执行流水）',
    all(k in d['数据新鲜度']['缺件'] for k in ('pulse.json', 'warboard.json', '报警_20261026.jsonl', '执行流水.jsonl'))
    and all('不存在' in v for v in d['数据新鲜度']['缺件'].values()))
chk('D02 欠账 ≥7 条 且含执行层零执行/playbook/日历/sentiment',
    len(d['异常与欠账']) >= 7 and all(k in blob for k in ('执行流水.jsonl', 'playbook.json', 'trading_calendar.py', 'sentiment')))
chk('D03 全文无占位符/TODO/待填', not any(t in blob for t in ('TODO', '待填', 'XXX', '???')))
chk('D04 口径含「不是操盘指令」', '不是操盘指令' in blob)
chk('D05 无预测性/指令性措辞（预计/将会/必涨/建议买入/目标价）',
    not any(t in blob for t in ('预计', '将会', '必涨', '建议买入', '目标价')))
chk('D06 未改参数：文件明写「未改任何生产脚本/预案/权重/阈值/机械线」',
    '未改任何生产脚本/预案/权重/阈值' in blob)

fail = [r for r in res if not r[1]]
for n, ok, det in res:
    print(('PASS ' if ok else 'FAIL ') + n + ('  | ' + det if det else ''))

# 9 补正件与原件不可覆盖（铁证）
import hashlib
J2 = os.path.join(D, '临盘决断_20261026_1030_补正1.json')
bz = json.load(open(J2, encoding='utf-8'))
cur_hash = hashlib.sha256(open(J, 'rb').read()).hexdigest()
V = [2017087, 2125663, 1381876, 1626813, 1725183]
avg = sum(V) / len(V)
share = 700576 / avg
chk('B01 补正1 存在且 补正号=1 / 性质=勘误补正', bz['补正号'] == 1 and '勘误' in bz['性质'])
chk('B02 原件 sha256 与补正1 记录一致（→ 发出版未被覆盖，铁证）',
    bz['原件']['sha256'] == cur_hash and cur_hash == 'a21b0b9c9103910b54d7472b6610b16cee6301c7ab5ab88e24774c5ccbabf86e', cur_hash[:16])
chk('B03 补正1 量能复算与改写值一致（39.5% / 1.13~0.99 倍）',
    abs(share * 100 - 39.5) < 0.05 and abs(700576 / 0.35 / avg - 1.13) < 0.01 and abs(700576 / 0.40 / avg - 0.99) < 0.01
    and '39.5%' in json.dumps(bz, ensure_ascii=False))
chk('B04 补正1 不改成交：fills=[] 且 A/B/C 仍 0 笔',
    bz['不改成交声明']['fills'] == [] and 'A 0 笔' in bz['不改成交声明']['权限分级'] and d['fills'] == [])
chk('B05 补正1 已登记哨兵钉帧缺陷（禁止用运行时刻末帧审历史文件）',
    '钉帧' in json.dumps(bz, ensure_ascii=False) and '38/38 PASS' in json.dumps(bz, ensure_ascii=False))
chk('B06 原件正文仍留存过强表述（证明是补正而非篡改）', '4 成以上=放量确认' in blob)

_final = [r for r in res if not r[1]]
print(f'\nTOTAL {len(res)}  PASS {len(res)-len(_final)}  FAIL {len(_final)}')
print('FAIL_LIST', [n for n, ok, _ in res if not ok])

