# -*- coding: utf-8 -*-
"""hb-f 14:45 深场B 哨兵：独立复算 + 出页自审。只读，不改任何文件。"""
import json, os, io, statistics, datetime, re

D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(D, '..', '..'))
DATE = '20261027'
DECF = os.path.join(D, f'临盘决断_{DATE}_1445.json')
CORR = os.path.join(D, f'临盘决断_{DATE}_1445_补正1.json')
MD = os.path.join(ROOT, '_学习', f'盘中尾盘复盘_{DATE}.md')
res = []


def chk(cid, name, ok, detail=''):
    res.append((cid, name, bool(ok), detail))


dec = json.load(open(DECF, encoding='utf-8'))
corr = json.load(open(CORR, encoding='utf-8'))
md = open(MD, encoding='utf-8').read()

# C1 结构
need = ['date', 'session', '实际决断时间戳', 'write_ts', '数据新鲜度', '执行流水对账',
        '持仓逐票表态', '预案来源与执行', '权限分级', 'fills', 'no_action',
        '市场读数_收盘前定格', '预收盘复盘要点', '明日预案要点', '异常与欠账', '口径']
miss = [k for k in need if k not in dec]
chk('C1', '决断件结构完整', not miss, f'缺 {miss}' if miss else '16 字段齐')

# C2 零动作一致性
chk('C2', 'fills 为空且权限分级 A/B/C 全 0',
    dec['fills'] == [] and all(str(dec['权限分级'][k]).startswith('0') for k in dec['权限分级']),
    json.dumps({k: v[:10] for k, v in dec['权限分级'].items()}, ensure_ascii=False))

# C3 零后视镜：决断时间戳 <= 写件时间戳，且早于 15:00
dt_dec = datetime.datetime.strptime(dec['实际决断时间戳'], '%Y-%m-%d %H:%M:%S')
dt_w = datetime.datetime.strptime(dec['write_ts'][:19], '%Y-%m-%d %H:%M:%S')
chk('C3', '零后视镜：决断帧 ≤ 写件时点 < 15:00 收盘',
    dt_dec <= dt_w and dt_w.hour < 15, f'{dt_dec} ≤ {dt_w}')

# C4 新鲜度 < 600s，独立复算
fr = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
fr = [f for f in fr if f.get('rows')]
last = [f for f in fr if datetime.datetime.strptime(f['ts'], '%Y-%m-%d %H:%M:%S') <= dt_dec][-1]
age = (dt_dec - datetime.datetime.strptime(last['ts'], '%Y-%m-%d %H:%M:%S')).total_seconds()
chk('C4', '数据新鲜度复算（红线 600s）', age < 600 and abs(age - dec['数据新鲜度']['末帧龄_秒']) <= 60,
    f'独立复算末帧 {last["ts"]}、龄 {age:.0f}s；件内 {dec["数据新鲜度"]["末帧龄_秒"]}s')

# C5 池温中位独立复算
med = round(statistics.median([r['pct'] for r in last['rows'] if r.get('pct') is not None]), 2)
chk('C5', '昨涨停池中位复算一致', f'{med}%' == dec['市场读数_收盘前定格']['池温(昨涨停池55只)']['中位'],
    f'复算 {med}% / 件内 {dec["市场读数_收盘前定格"]["池温(昨涨停池55只)"]["中位"]}')

# C6 炸板率与连板分布自洽
pl = dec['市场读数_收盘前定格']['全市场']
calc = round(pl['炸板'] / (pl['涨停'] + pl['炸板']), 4)
dist_sum = sum(int(v) for v in pl['连板分布'].values())
chk('C6', '炸板率=炸板/(涨停+炸板) 自洽', abs(calc - pl['炸板率']) < 0.0005, f'复算 {calc} / 件内 {pl["炸板率"]}')
chk('C7', '连板分布合计=涨停数', dist_sum == pl['涨停'], f'分布合计 {dist_sum} / 涨停 {pl["涨停"]}')

# C8 lbt 补零口径（补正件核心技术项）
ld = json.load(open(os.path.join(D, '_hb_f_line_detail.json'), encoding='utf-8'))
cylb = ld['by_ind']['汽车零部']
late = sorted([(str(r['lbt']).zfill(6), r['n'], r['c']) for r in cylb if str(r['lbt']).zfill(6) >= '144500'])
want = [('144612', '申达股份', '600626'), ('144703', '沪光股份', '605333'), ('144900', '亚太股份', '002284')]
chk('C8', '尾盘回封 3 只复算（lbt 六位补零）', late == want, f'{late}')
chk('C9', '补正件已登记该项错误且原件未改',
    any('尾盘回封名单' in x['项'] for x in corr['更正项']) and os.path.getmtime(DECF) < os.path.getmtime(CORR),
    '补正件 mtime 晚于原件（增量更正，原件未覆盖）')

# C10 md 与决断件数字一致（抽样硬串）
pairs = [
    (dec['市场读数_收盘前定格']['全市场']['炸板率'].__str__(), '炸板率'),
    (str(dec['市场读数_收盘前定格']['全市场']['涨停']), '涨停'),
    (dec['市场读数_收盘前定格']['池温(昨涨停池55只)']['中位'], '池温中位'),
    (dec['预收盘复盘要点']['龙头'][:12], '龙头段'),
]
bad = []
for s, tag in pairs:
    if s not in md:
        bad.append(f'{tag}:{s}')
chk('C10', 'md 关键数字与决断件一致', not bad, str(bad))

# C11 账务：state.json 逐账现金出现在 md 且合计正确
BOOKS = ['master', 'auction', 'limitup', 'lhb', 'logic', 'theme', '盘中作战']
cash = {b: json.load(open(os.path.join(ROOT, '_学习', '_模拟盘', b, 'state.json'), encoding='utf-8'))['cash'] for b in BOOKS}
tot = round(sum(cash.values()), 2)
miss2 = [b for b in BOOKS if f'{cash[b]:.2f}' not in md]
chk('C11', '七账现金逐账与合计均出自 state.json', not miss2 and f'{tot:.2f}'.replace('.0', '.') in md.replace(',', ''),
    f'缺失 {miss2}；合计 {tot}')
nilpos = [b for b in BOOKS if json.load(open(os.path.join(ROOT, '_学习', '_模拟盘', b, 'state.json'), encoding='utf-8'))['positions']]
chk('C12', '七账持仓确为空（无账本外持仓）', not nilpos, f'非空 {nilpos}')

# C13 无编造哨：md 不含"当月/本月首次"等未核验断言；不含 {DATE} 占位符
body = md.split('数据缺件：今日', 1)[-1]   # 排除“更正记录”块（该块按需引用原错误措辞）
bad_tok = [t for t in ('本月首次', '{DATE}', '{max_cluster_30m}', '2 只尾盘偷袭回封') if t in body]
chk('C13', 'md 正文无未核验断言/占位符残留（更正记录块除外）', not bad_tok, str(bad_tok))

# C14 缺件如实登记
ex = dec['异常与欠账'][0]
chk('C14', '缺件如实登记（pulse/warboard/执行流水/报警/playbook）',
    all(k in ex for k in ['pulse.json', 'warboard.json', '执行流水.jsonl', 'playbook.json']), ex[:40])

print('=' * 74)
for cid, name, ok, detail in res:
    print(f'{"PASS" if ok else "FAIL"}  {cid}  {name}' + (f'  | {detail}' if detail else ''))
n_fail = sum(1 for r in res if not r[2])
print('=' * 74)
print(f'结果: {len(res)-n_fail}/{len(res)} PASS, {n_fail} FAIL')
json.dump([{'id': c, 'name': n, 'pass': o, 'detail': d} for c, n, o, d in res],
          open(os.path.join(D, '_hb_f_sentinel.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
raise SystemExit(1 if n_fail else 0)
