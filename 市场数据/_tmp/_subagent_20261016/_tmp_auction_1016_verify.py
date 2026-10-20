# -*- coding: utf-8 -*-
"""验收：4个产物的 schema/编码/代码可溯/%%残留/HTML标题与配平。"""
import json, sys, os, csv, io
sys.stdout.reconfigure(encoding='utf-8')
D = '20261016'; OUT = '_学习'
def raw(p):
    b = open(p, 'rb').read()
    return b, (b'\xef\xbb\xbf' not in b), b.decode('utf-8')
files = ['auction判断_%s.json' % D, 'auction_body_%s.html' % D, '交易计划_auction_%s.json' % D, '能力回执_auction_%s.json' % D]
ok = True
for f in files:
    p = os.path.join(OUT, f)
    b, nobom, txt = raw(p)
    print('[%s] bytes=%d noBOM=%s' % (f, len(b), nobom))
    if not nobom: ok = False
    if f.endswith('.json'):
        o = json.load(io.StringIO(txt))
        print('   top keys:', list(o.keys()))
    if '%%' in txt:
        print('   !! 残留 %%', txt.count('%%')); ok = False

du = json.load(open(os.path.join(OUT, files[0]), encoding='utf-8'))
print('判断.判断 keys:', list(du['判断'].keys()))
print('档位=%s 置信度=%s 证据%d条 认知%d条 深挖%d段' % (du['判断']['档位'], du['判断']['置信度'], len(du['判断']['证据']), len(du['认知迭代']), len(du['深挖'])))
print('荐票结论前缀:', du['荐票']['结论'][:40])
print('标的:', [(x['代码'], x['名称'], x['类型']) for x in du['荐票']['标的']])
print('深挖是否含Master指派:', any('MA-20261015-05' in s for s in du['深挖']))
print('盲区条数(①..⑩):', du['判断']['独立盲区声明'].count('①') + sum(du['判断']['独立盲区声明'].count(c) for c in '②③④⑤⑥⑦⑧⑨⑩'))

# 代码可溯：zt_pool ∪ 今日竞价留档(评分/池/快照/traj)
zt = {str(r['代码']) for r in csv.DictReader(open(os.path.join(D, 'zt_pool.csv'), encoding='utf-8-sig'))}
pool = {p['代码'] for p in json.load(open(os.path.join(OUT, '竞价池发出_%s.json' % D), encoding='utf-8'))['池']}
import gzip
snap = {r['代码'] for r in csv.DictReader(gzip.open(os.path.join(OUT, '竞价快照存档', '%s.csv.gz' % D), 'rt', encoding='utf-8-sig'))}
traj = set()
for l in open(os.path.join('盘中', D, 'auction_traj.jsonl'), encoding='utf-8'):
    for r in json.loads(l)['rows']: traj.add(r['code'])
allowed = zt | pool | snap | traj
print('允许集合大小 zt=%d pool=%d snap=%d traj=%d' % (len(zt), len(pool), len(snap), len(traj)))
for x in du['荐票']['标的']:
    print('  %s %s in allowed=%s (zt=%s pool=%s)' % (x['代码'], x['名称'], x['代码'] in allowed, x['代码'] in zt, x['代码'] in pool))
    if x['代码'] not in allowed: ok = False

plan = json.load(open(os.path.join(OUT, files[2]), encoding='utf-8'))
print('计划 buys=%d sells=%d' % (len(plan['buys']), len(plan['sells'])))
st = json.load(open(os.path.join(OUT, '_模拟盘', 'auction', '状态.json'), encoding='utf-8'))
held = [p['code'] for p in st['持仓']]
sold = [s['代码'] for s in plan['sells']]
print('在持%s 卖出表态%s 漏票=%s' % (held, sold, sorted(set(held) - set(sold))))
txtnotes = plan['notes']
for c in held:
    print('  notes提及%s=%s' % (c, c in txtnotes))
if set(held) - set(sold): ok = False
print('计划目标日=%s 路=%s' % (plan['日期'], plan['路']))

html = raw(os.path.join(OUT, files[1]))[2]
import re
print('h2标题:', re.findall(r'<h2>([^<]{2,10})', html))
print('div %d/%d  spancount=%d' % (html.count('<div'), html.count('</div>'), html.count('<span')))
print('组件类:', sorted({c for c in re.findall(r'class="([a-z\- ]+)"', html)}))
print('残留 %%:', html.count('%%'))
print('OK' if ok else 'FAIL')
