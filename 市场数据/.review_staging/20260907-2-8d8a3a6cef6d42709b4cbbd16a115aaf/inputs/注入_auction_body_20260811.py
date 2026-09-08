# -*- coding: utf-8 -*-
"""注入 8/11 auction body(补跑) 到 judgment_20260811.json bodies.auction
发出版不可覆盖 → 显式 --force 覆盖+备份
用法: python 注入_auction_body_20260811.py [--force]
"""
import io, json, os, shutil, sys

BASE = r'D:\股票数据\市场数据'
J = os.path.join(BASE, '_学习', 'judgment_20260811.json')
B = os.path.join(BASE, '_学习', 'auction_body_20260811.html')

if not os.path.isfile(B):
    print('【缺】%s 不存在, 先让子agent产出 body' % B)
    sys.exit(1)

body = io.open(B, encoding='utf-8').read()
j = json.load(io.open(J, encoding='utf-8'))
bodies = j['bodies']
if 'auction' in bodies and '--force' not in sys.argv:
    print('bodies.auction 已存在, 拒绝覆盖(发出版不可覆盖)。用 --force 显式覆盖(自动备份)')
    sys.exit(1)
if '--force' in sys.argv:
    shutil.copy2(J, J + '.bak_force_auction')
bodies['auction'] = body
io.open(J, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=1))
j2 = json.load(io.open(J, encoding='utf-8'))
print('注入成功: bodies =', list(j2['bodies'].keys()), '| auction 字节:', len(j2['bodies']['auction']))
