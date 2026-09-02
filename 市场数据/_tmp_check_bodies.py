# -*- coding: utf-8 -*-
import io, re, os
L = r'D:\股票数据\市场数据\_学习'
for r in ['auction','lhb','theme','logic','limitup']:
    f = os.path.join(L, f'{r}_body_20260902.html')
    b = io.open(f, encoding='utf-8').read()
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', b)
    print(f'=== {r} body ({len(b)}字节) ===')
    print('  h2:', h2s)
    for a in ['<!--LEDGER-->','<!--/LEDGER-->','<!--LHBLEDGER-->','<!--/LHBLEDGER-->','<!--FUNDTEMP-->','<!--/FUNDTEMP-->','<!--POOLLEDGER-->','<!--/POOLLEDGER-->','<!--SEATCARD-->','<!--SCORECARD-->']:
        if a in b:
            print(f'  锚 {a}: 有')
    print()
