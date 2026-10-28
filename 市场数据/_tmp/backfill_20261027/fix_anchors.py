# -*- coding: utf-8 -*-
"""修 1027 三件事：①auction POOLLEDGER 回退（去后视镜块）②lhb/limitup 补闭合锚 ③题材生命周期判断 归位"""
import json, re, shutil

L = '_学习/'
jp = L + 'judgment_20261027.json'
j = json.load(open(jp, encoding='utf-8'))

# —— 0 先看 1026 的锚点约定 ——
j26 = json.load(open(L + 'judgment_20261026.json', encoding='utf-8'))
for r, mk in (('lhb', 'LHB'), ('limitup', '')):
    b = j26['bodies'][r]
    o, c = b.count('<!--%sLEDGER-->' % mk), b.count('<!--/%sLEDGER-->' % mk)
    print('1026 %-8s open=%d close=%d  末尾120字=%r' % (r, o, c, b[-120:]))

# —— ① auction 回退 ——
bak = json.load(open('_tmp/backfill_20261027/bak/judgment_20261027.json', encoding='utf-8'))
old = j['bodies']['auction']
if old != bak['bodies']['auction']:
    j['bodies']['auction'] = bak['bodies']['auction']
    print('\nauction 已回退到备份（去掉 %d 字的后视镜结算块）' % (len(old) - len(bak['bodies']['auction'])))
    m = re.findall(r'<b>(10-\d\d)池终结算</b>', j['bodies']['auction'])
    print('auction 现有结算块日期：', m)

# —— ② lhb / limitup 补闭合锚 ——
for r, mk in (('lhb', 'LHB'), ('limitup', '')):
    b = j['bodies'][r]
    o, c = b.count('<!--%sLEDGER-->' % mk), b.count('<!--/%sLEDGER-->' % mk)
    if o == 1 and c == 0:
        b = b.rstrip() + '\n<!--/%sLEDGER-->' % mk
        j['bodies'][r] = b
        print('%-8s 补闭合锚，新 open=%d close=%d' % (r, b.count('<!--%sLEDGER-->' % mk), b.count('<!--/%sLEDGER-->' % mk)))
    else:
        print('%-8s 跳过 open=%d close=%d' % (r, o, c))

json.dump(j, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# —— ③ 题材生命周期判断 归位 ——
p = L + '题材生命周期判断_20261027.json'
t = json.load(open(p, encoding='utf-8'))
print('\n题材生命周期判断 KEYS:', list(t.keys()))
bad = t.pop('阶段矩阵', None)
if bad is not None:
    note = (t.get('说明') or '').strip()
    txt = json.dumps(bad, ensure_ascii=False) if not isinstance(bad, str) else bad
    t['说明'] = (note + '｜' if note else '') + '阶段矩阵：' + txt
    json.dump(t, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已把「阶段矩阵」并入说明，说明长度', len(t['说明']))
print('剩余 KEYS:', list(t.keys()))
