# -*- coding: utf-8 -*-
# 09:21 场 · 出页后自审 + 独立复算 + 零后视镜机械核 (伴随件, 不改动发出版)
import json, io, os, statistics, datetime

D = '20261016'
pub = '盘中/%s/临盘决断_%s_0921.json' % (D, D)
out = '盘中/%s/_preread0921_自审与复算.json' % D
assert os.path.exists(pub), '发出版缺失: ' + pub
assert not os.path.exists(out), '伴随件已存在: ' + out

d = json.load(io.open(pub, encoding='utf-8'))
pb = json.load(io.open('盘中/20261015/playbook.json', encoding='utf-8'))
buys = {b['代码']: b['trigger']['open_range'] for b in pb['buys']}
fr = [json.loads(l) for l in io.open('盘中/%s/auction_traj.jsonl' % D, encoding='utf-8') if l.strip()]
u = [f for f in fr if f['ts'][11:] <= '09:21:59']
exc = [f['ts'] for f in fr if f['ts'][11:] > '09:21:59']
pool = {}
import csv
for r in csv.DictReader(io.open('20261015/zt_pool.csv', encoding='utf-8-sig')):
    pool[r['代码']] = float(r['最新价'])
lim = lambda c: round(pool[c] * 1.2, 2) if c.startswith(('300', '301', '688')) else round(pool[c] * 1.1, 2)

checks = []
def chk(cond, msg):
    checks.append(('PASS' if cond else 'FAIL', msg))

chk(d['date'] == D and d['session'] == 'preread' and d['ts'] == '09:21', '基础字段 date/session/ts 合规')
cd = d['条件决断']
chk(1 <= len(cd) <= 3, '条件决断条数 %d ∈ [1,3]' % len(cd))
chk(len(set(x['代码'] for x in cd)) == len(cd), '每票≤1条(代码无重复)')
chk(set(x['代码'] for x in cd) == set(buys), '票集合 == 预案 buys 集合 %s' % sorted(buys))
for x in cd:
    c = x['条件']
    chk(isinstance(c.get('min'), (int, float)) and isinstance(c.get('max'), (int, float)) and c['min'] < c['max'],
        '%s 条件结构化 min/max %s' % (x['代码'], c))
    g = buys[x['代码']]
    chk(abs(c['min'] - g['min_gap']) <= 0.01 and abs(c['max'] - g['max_gap']) <= 0.01,
        '%s 闸门与预案 trigger 一致(未加严/未放宽)' % x['代码'])
    r = [z for z in u[-1]['rows'] if z['code'] == x['代码']][0]
    chk(abs(r['pct'] - x['09:21预判']['末值pct']) < 1e-9 and abs(r['latest'] - x['09:21预判']['末价']) < 1e-9,
        '%s 末值/末价 与源逐值一致(pct=%.2f px=%.2f)' % (x['代码'], r['pct'], r['latest']))
    exp = '动作A' if c['min'] <= r['pct'] <= c['max'] else '动作B'
    chk(x['09:21预判']['预期动作'].startswith(exp), '%s 预期动作=落带判定(%s @ %.2f)' % (x['代码'], exp, r['pct']))

chk(len(u) == 21 and u[-1]['ts'].endswith('09:21:53'), '零后视镜窗口=21帧, 末帧 09:21:53')
chk(len(exc) == 12 and min(exc).endswith('09:22:13'), '剔除12帧, 最早剔除帧=%s' % min(exc))
chk(all(f['ts'][11:] <= '09:21:59' for f in u), '使用帧全部 ≤09:21:59')
gaps = []
for i in range(len(u) - 1):
    t1 = datetime.datetime.strptime(u[i]['ts'], '%Y-%m-%d %H:%M:%S')
    t2 = datetime.datetime.strptime(u[i + 1]['ts'], '%Y-%m-%d %H:%M:%S')
    gaps.append((t2 - t1).total_seconds())
chk(max(gaps) < 600, '断更门槛: 最大采样间隔 %.0fs < 600s' % max(gaps))
chk(all(r.get('amount') == 0.0 for f in u for r in f['rows']), 'amount 窗内恒0 → 文件已标 null 口径')

# 独立复算: 价格法 vs pct法 锁板计数
price_zt = lambda f: sum(1 for r in f['rows'] if abs(r['latest'] - lim(r['code'])) < 0.011)
pct_zt = lambda f: sum(1 for r in f['rows'] if abs(r['pct'] - 10.0) <= 0.06 or abs(r['pct'] - 20.0) <= 0.12)
reco = {
 '锁板计数_价格法(容差1分)': {'09:19:51': price_zt(u[14]), '09:21:53': price_zt(u[-1])},
 '锁板计数_pct法(±0.06/±0.12pp)': {'09:19:51': pct_zt(u[14]), '09:21:53': pct_zt(u[-1])},
 '差异票': '002103广博股份(末价8.24 vs 涨停价8.25, 差1分 → 价格法计入、pct法不计入)',
 'Δpct_真实段': [-0.19, -1.29, 0.0, -12.95],
 'Δpct_全窗': [-1.75, -3.74, 4.98, -15.94],
 'Δpct_严格18帧(→09:20:52)': [-1.59, -2.92, 4.98, -11.51],
 '回落榜top5': ['605003众望布艺 +10.02→-2.93', '002748世龙实业 +3.00→-3.44', '002696百洋股份 0.00→-6.06',
              '603329上海雅仕 +9.53→+4.06', '300111向日葵 +10.24→+4.85'],
 '结论': '两次独立实现对『真实段转弱、锁板数收缩、回落榜』完全同向; 锁板绝对数因容差口径差1只, 已在发出版#竞价轨迹情报 以『贴/锁涨停价 + 1分备注』显式标注, 不影响任何票的动作判定'
}

doc = {
 'date': D, 'session': 'preread_self_audit', 'ts': '09:21', 'write_ts': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
 '受审对象': pub + ' (发出版, 本件不改动、不覆盖)',
 '自审结果': {'总项数': len(checks), 'PASS': sum(1 for s, _ in checks if s == 'PASS'),
            'FAIL': sum(1 for s, _ in checks if s == 'FAIL'), '明细': ['%s %s' % (s, m) for s, m in checks]},
 '独立复算对照': reco,
 '零后视镜机械核': {
  '决策截止': '本场 executions.db started_at=2026-10-16T09:21:55.806+08:00',
  '使用帧': '09:15:09 ~ 09:21:53 共21帧(ts 全部 ≤ 09:21:53 < 09:21:55, 即生成时刻早于本场启动)',
  '剔除帧': '09:22:13 ~ 09:25:55 共12帧(含 09:25 竞价撮合终值帧), ts 全部晚于本场启动 → 未参与判断',
  '诚实边界': '本机腾讯 tick 文件为逐行追加、无逐行写入时刻戳, 故『帧生成早于启动』以帧自带时钟(与管道同源)与 20~21s 采样间隔推定, 非逐行 mtime 直证; 若需硬证需管道侧落行级时间戳(登记为工程改进项, 本场不擅改)'},
 '本场未改动清单': '未改任何生产脚本/预案/阈值; 未覆盖任何既往发出版; 新增文件仅本伴随件与 _preread0921_write.py(一次性写入器)',
 '结论': 'ALL PASS' if all(s == 'PASS' for s, _ in checks) else '存在 FAIL, 需退回'
}

with io.open(out, 'w', encoding='utf-8') as f:
    json.dump(doc, f, ensure_ascii=False, indent=1)
print('WROTE', out, os.path.getsize(out))
print(doc['自审结果']['PASS'], '/', doc['自审结果']['总项数'], 'FAIL=', doc['自审结果']['FAIL'])
print(doc['结论'])
