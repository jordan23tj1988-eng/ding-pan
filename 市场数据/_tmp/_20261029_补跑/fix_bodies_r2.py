# -*- coding: utf-8 -*-
"""20261029 补跑 r2: B 类骨架归一（标题归位，不增段）。
契约: BUSINESS_SECTIONS = auction/lhb/limitup 各 4 业务段;
展示层 legacy 段(自主深挖/认知迭代)会被 _strip_legacy_modules 摘除。
故只在既有 6 个 h2 内改标题, 使 4 个业务段命中缺的 section, 并挂机器锚。
判断正文一字不动。
"""
import json, os, re, shutil

BASE = r'D:\股票数据\市场数据'
L = os.path.join(BASE, '_学习')
D = '20261029'
BAK = os.path.join(BASE, '_tmp', '_20261029_补跑')

# 1) 从注入前备份恢复正文（台账内容稍后由脚本重跑重填，幂等）
for name in ('judgment_20261029.json',):
    shutil.copy(os.path.join(BAK, name + '.bak'), os.path.join(L, name))
for r in ('auction', 'lhb', 'limitup'):
    shutil.copy(os.path.join(BAK, f'{r}_body_{D}.html.bak'), os.path.join(L, f'{r}_body_{D}.html'))

jp = os.path.join(L, f'judgment_{D}.json')
J = json.load(open(jp, encoding='utf-8'))
b = J['bodies']

# ---------- auction: 缺 temperature ----------
a = b['auction']
old = '<h2>二 当日证据与闸门对账</h2>'
assert old in a, 'auction 二 标题未找到'
a = a.replace(old, '<h2>二 竞价温度与闸门对账</h2>')
assert '<h2>五 深挖</h2>' in a
a = a.replace('<h2>五 深挖</h2>', '<h2>五 自主深挖</h2>')
b['auction'] = a

# ---------- limitup: 缺 ledger ----------
lu = b['limitup']
old = '<h2>二 连板梯队与温度断层</h2>'
assert old in lu, 'limitup 二 标题未找到'
lu = lu.replace(old, '<h2>二 连板梯队与归位台账</h2>')
lu = lu.replace('<h2>五 深挖</h2>', '<h2>五 自主深挖</h2>')
# LEDGER 锚挂在二段末尾(下一 h2 之前)
lu = lu.replace('<h2>三 炸板与虚胖检测 · 质量库</h2>',
                '<!--LEDGER--><!--/LEDGER-->\n<h2>三 炸板与虚胖检测 · 质量库</h2>', 1)
b['limitup'] = lu

# ---------- lhb: 缺 ledger + tiers ----------
lh = b['lhb']
old = '<h2>三 席位训练库 · 游资量化扫描</h2>\n<!--LHBLEDGER-->'
assert old in lh, 'lhb 三段结构未找到'
lh = lh.replace(old, '<h2>三 龙虎榜台账 · 席位训练库与量化扫描</h2>\n<!--LHBLEDGER-->')
old4 = '<h2>四 席位荐票与明日预案</h2>'
assert old4 in lh, 'lhb 四 标题未找到'
lh = lh.replace(old4, '<h2>四 全市场席位分档库与席位荐票</h2>')
lh = lh.replace('<h2>五 深挖</h2>', '<h2>五 自主深挖</h2>')
b['lhb'] = lh

json.dump(J, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in ('auction', 'lhb', 'limitup'):
    open(os.path.join(L, f'{r}_body_{D}.html'), 'w', encoding='utf-8').write(b[r])

CN = '一二三四五六七八九十'
LEGACY = re.compile(r'自主深挖|我的认知迭代|认知迭代')
EXPECT = {'auction': 4, 'lhb': 4, 'limitup': 4}
ok = True
for r in ('auction', 'lhb', 'limitup'):
    s = b[r]
    h2 = [re.sub(r'<[^>]+>', '', m).strip() for m in re.findall(r'<h2[^>]*>.*?</h2>', s, re.S)]
    keep = [x for x in h2 if not LEGACY.search(x)]
    nums = [CN.index(x.strip()[0]) + 1 for x in keep if x.strip() and x.strip()[0] in CN]
    good = bool(nums) and max(nums) == EXPECT[r]
    ok &= good
    print(f'{r}: h2={h2}')
    print(f'   保留业务段={keep} max={max(nums) if nums else None} 期望={EXPECT[r]} ->',
          'OK' if good else 'FAIL')
    print('   锚 LHBLEDGER', s.count('<!--LHBLEDGER-->'), 'LEDGER', s.count('<!--LEDGER-->'),
          'POOLLEDGER', s.count('<!--POOLLEDGER-->'))
print('段数契约', 'PASS' if ok else 'FAIL')
