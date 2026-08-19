# -*- coding: utf-8 -*-
"""hermes-verify-reco-v51 — 2026-08-13 荐票机制v5.1修复(负筛只作用于0命中票)的专项验证(ad-hoc)。
三层: A.数据源产物断言  B.负筛行为重放(源码算法照抄,验证产物=算法输出非手工改)  C.页面一致性。
用法: <python> hermes-verify-reco-v51.py   (工作目录=D:/股票数据/市场数据)
"""
import json, os, sys, subprocess

L = r'D:\股票数据\市场数据\_学习'
PAGE = r'D:\股票数据\市场数据\复盘\盯盘台\limitup.html'
ROOT = r'D:\股票数据\市场数据'
EXPECT = [  # (名称, 代码, 命中数, 抓龙率, 质量分)
    ('蓝盾光电', '300862', 6, 20.8, 3),
    ('金 螳 螂', '002081', 2, 19.1, 3),
    ('坤泰股份', '001260', 1, 22.1, 3),
    ('兆日科技', '300333', 1, 22.1, 3),
    ('秦安股份', '603758', 1, 18.0, 2),
]
fails = []
def chk(ok, label):
    print(('  ✓ ' if ok else '  ✗ ') + label)
    if not ok: fails.append(label)

# ---------- A. 产物断言 ----------
r = json.load(open(os.path.join(L, '涨停质量荐票_20260813.json'), encoding='utf-8'))
top5 = r['top5']
chk(len(top5) == 5, f'A1 top5=5只(实际{len(top5)})')
for i, (nm, code, hit, rate, score) in enumerate(EXPECT):
    t = top5[i]
    chk((t['名称'] == nm and t['代码'] == code and t['命中数'] == hit
         and abs(float(t['抓龙率']) - rate) < 0.01 and t['质量分'] == score),
        f'A2 top5[{i+1}]={nm}/{code} 命中{hit} 抓龙{rate}% 分{score}')
chk(r.get('荐票源', '').startswith('12_涨停复盘(v5.1'), f"A3 荐票源=v5.1({r.get('荐票源')})")

# ---------- B. 负筛行为重放(算法照抄 涨停质量荐票.py main 62-74行, v5.1) ----------
rows = r['明细']
rows.sort(key=lambda x: (-x['命中数'], -(x['抓龙率'] or 0), -x['质量分']))
if len(rows) >= 8:
    z0 = [x for x in rows if x['命中数'] <= 0]
    if z0 and len(z0) >= 4:
        q25 = sorted(x['质量分'] for x in z0)[len(z0) // 4]
        pool = [x for x in rows if x['命中数'] > 0 or x['质量分'] > q25] or rows
    else:
        pool = rows
else:
    pool = rows
replay = pool[:5]
chk([(x['名称'], x['代码']) for x in replay] == [(n, c) for n, c, *_ in EXPECT],
    'B1 重放Top5=产物Top5(产物=算法输出)')
z0_hit = [x for x in rows if x['命中数'] > 0]
chk(all(x in pool for x in z0_hit), f'B2 规则命中票({len(z0_hit)}只)全部保留(负筛不作用)')
z0_kept = [x for x in pool if x['命中数'] == 0]
chk(all(x['质量分'] > q25 for x in z0_kept), 'B3 0命中票仍受负筛(质量分>q25才留)')
print(f'  (重放: 打标{len(rows)} q25={q25} 池{len(pool)}只)')

# ---------- C. 页面一致性 ----------
h = open(PAGE, encoding='utf-8').read()
b1 = h[h.find('<h2>一'):h.find('<h2>二')]
chk(all(nm in b1 for nm, *_ in EXPECT), 'C1 板块一荐票卡=新Top5全在')
chk('京投发展' not in b1, 'C2 板块一无旧Top5')
chk(h.count('<div') == h.count('</div>'), 'C3 div配平')
chk('负筛只作用于0命中票' in h, 'C4 页面hint已v5.1口径')
chk('全0规则命中' not in h and '矮子里拔将军' not in h, 'C5 无过时描述')
i3 = h.find('当日涨停质量Top5荐票'); e3 = h.find('</table>', i3)
chk('蓝盾光电' in h[i3:e3+8] and '京投发展' not in h[i3:e3+8], 'C6 台账荐票卡同步新Top5')

# ---------- D. 哨兵 ----------
p = subprocess.run([sys.executable, os.path.join(ROOT, 'limitup数据核对.py'), '20260813'], capture_output=True, text=True)
chk(p.returncode == 0 and 'PASS 全部一致' in p.stdout, 'D1 哨兵35项PASS')

print()
print('FAIL:', fails if fails else '无 — 全部通过 (ad-hoc 专项验证, 非 suite)')
sys.exit(1 if fails else 0)
