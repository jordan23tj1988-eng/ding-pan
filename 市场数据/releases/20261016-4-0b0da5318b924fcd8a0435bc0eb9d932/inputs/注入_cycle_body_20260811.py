# -*- coding: utf-8 -*-
"""注入 8/11 cycle body v2(修正版) 到 judgment_20260811.json bodies.cycle (发出版不可覆盖 → 显式覆盖+备份)
用法: python 注入_cycle_body_20260811.py [--force]
"""
import io, json, os, shutil, sys

BASE = r'D:\股票数据\市场数据'
J = os.path.join(BASE, '_学习', 'judgment_20260811.json')
B = os.path.join(BASE, '_学习', '_cycle_body_20260811.html')

body = io.open(B, encoding='utf-8').read()
j = json.load(io.open(J, encoding='utf-8'))
bodies = j['bodies']
if 'cycle' in bodies and '--force' not in sys.argv:
    print('bodies.cycle 已存在, 拒绝覆盖(发出版不可覆盖)。用 --force 显式覆盖(自动备份)')
    sys.exit(1)
if '--force' in sys.argv:
    shutil.copy2(J, J + '.bak_force_v2')
bodies['cycle'] = body
io.open(J, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=1))
j2 = json.load(io.open(J, encoding='utf-8'))
print('注入成功: bodies =', list(j2['bodies'].keys()), '| cycle 字节:', len(j2['bodies']['cycle']))
