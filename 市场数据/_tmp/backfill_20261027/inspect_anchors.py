# -*- coding: utf-8 -*-
import json, re

L = '_学习/'
j = json.load(open(L + 'judgment_20261027.json', encoding='utf-8'))
bak = json.load(open('_tmp/backfill_20261027/bak/judgment_20261027.json', encoding='utf-8'))

for r in ('auction', 'lhb', 'limitup', 'theme', 'logic'):
    for tag, src in (('现在', j['bodies'][r]), ('备份', bak['bodies'][r])):
        marks = re.findall(r'<!--(/?(?:LHB)?(?:POOL)?LEDGER)-->', src)
        dates = sorted(set(re.findall(r'2026\d{4}', src)))
        print('%-8s %-4s len=%6d anchors=%s 日期出现=%s' % (r, tag, len(src), marks, dates[-4:]))
    print()

# auction 备份里 POOLLEDGER 附近文字
a = bak['bodies']['auction']
i = a.find('POOLLEDGER')
print('备份 auction POOLLEDGER 段前 400 字：')
print(a[max(0, i - 300):i + 700])
