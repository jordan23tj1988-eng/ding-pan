# -*- coding: utf-8 -*-
"""hermes-verify-ths-vledger — 2026-08-13 THS原因根治(#047)+版本台账重建(#048)专项验证(ad-hoc)。
四层: A.THS取数.py机制(直连+实测落盘)  B.回填结果(题材归位两日)  C.下游链传播(对链条/judgment/页面/哨兵)  D.分层模型.json重建+驾驶舱消费。
"""
import json, os, re, subprocess, sys

ROOT = r'D:\股票数据\市场数据'
L = os.path.join(ROOT, '_学习')
PAGE = os.path.join(ROOT, '复盘', '盯盘台', 'limitup.html')
ARC12 = os.path.join(ROOT, '复盘', '盯盘台', 'archive', '20260812.html')
CKP = r'C:\Users\66353\AppData\Local\hermes\profiles\a'
PY = sys.executable

fails, oks = [], []
def chk(name, ok, detail=''):
    (oks if ok else fails).append(name)
    print(f"  {'✓' if ok else '✗'} {name}" + (f'  [{detail}]' if detail else ''))

def sh(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120)

# ── A. THS取数.py 机制 ──
sp = os.path.join(ROOT, 'THS取数.py')
src = open(sp, encoding='utf-8').read()
chk('A1 THS取数.py存在', os.path.exists(sp))
chk('A2 内置直连ProxyHandler({})', 'ProxyHandler({})' in src and 'proxy' in src.lower())
chk('A3 凭据读取credentials.env', 'credentials.env' in src)
p = sh([PY, 'THS取数.py', '20260813'], cwd=ROOT)
chk('A4 实测重取8/13', p.returncode == 0 and '59只' in p.stdout and '59/59' in p.stdout, p.stdout.strip()[-60:])
pool13 = json.load(open(os.path.join(L, 'THS涨停池_20260813.json'), encoding='utf-8'))
pool12 = json.load(open(os.path.join(L, 'THS涨停池_20260812.json'), encoding='utf-8'))
chk('A5 8/13池59只原因全非空', len(pool13) == 59 and all(x.get('limit_up_reason') for x in pool13))
chk('A6 8/12池91只原因全非空', len(pool12) == 91 and all(x.get('limit_up_reason') for x in pool12))

# ── B. 回填结果 ──
g13 = json.load(open(os.path.join(L, '题材归位_20260813.json'), encoding='utf-8'))['映射']
g12 = json.load(open(os.path.join(L, '题材归位_20260812.json'), encoding='utf-8'))['映射']
s13 = json.dumps(g13, ensure_ascii=False); s12 = json.dumps(g12, ensure_ascii=False)
chk('B1 8/13归位无THS原因缺', 'THS原因缺' not in s13)
chk('B2 8/13归位真实原因≥50', s13.count('(THS)') >= 50, f"{s13.count('(THS)')}处")
chk('B3 8/12归位无THS原因缺', 'THS原因缺' not in s12)
chk('B4 8/12归位真实原因≥75', s12.count('(THS)') >= 75, f"{s12.count('(THS)')}处")
chk('B5 北交所浩淼改口径不编造', 'THS池不含北交所' in s12 and '920856' in g12)
chk('B6 来源档全部B档(未篡改档位)', all(v.get('来源档') == 'B' for v in g13.values()))
chk('B7 大方向判断保留(蓝盾光电8/13仍机器人)', '机器人' in (g13.get('300862', {}).get('大方向') or ''))

# ── C. 下游链传播 ──
c13 = open(os.path.join(L, '涨停对链条_20260813.json'), encoding='utf-8').read()
chk('C1 对链条8/13无旧文本', 'THS原因缺' not in c13)
j13 = json.load(open(os.path.join(L, 'judgment_20260813.json'), encoding='utf-8'))
j12 = json.load(open(os.path.join(L, 'judgment_20260812.json'), encoding='utf-8'))
l13 = j13['bodies']['limitup']; l12 = j12['bodies']['limitup']
chk('C2 judgment8/13 LEDGER段无旧文本', 'THS原因缺' not in l13[l13.find('<!--LEDGER-->'):l13.find('<!--/LEDGER-->')])
chk('C3 judgment8/12 LEDGER段无旧文本', 'THS原因缺' not in l12[l12.find('<!--LEDGER-->'):l12.find('<!--/LEDGER-->')])
h = open(PAGE, encoding='utf-8').read()
a = open(ARC12, encoding='utf-8').read()
chk('C4 主页面无THS原因缺+真实催化', 'THS原因缺' not in h and h.count('(THS)') >= 300, f"(THS){h.count('(THS)')}处")
chk('C5 archive8/12无THS原因缺', 'THS原因缺' not in a)
chk('C6 主页面含北交所口径标注', 'THS池不含北交所' in h)
p = sh([PY, 'limitup数据核对.py', '20260813'], cwd=ROOT)
chk('C7 哨兵8/13 PASS', p.returncode == 0 and 'PASS' in p.stdout)

# ── D. 分层模型.json 重建 ──
lm = json.load(open(os.path.join(ROOT, '_架构', '分层模型.json'), encoding='utf-8'))
ids = [x.get('id') for x in lm.get('层', [])]
chk('D1 schema+updated', lm.get('schema') == 'layer-model/v1' and lm.get('updated') == '2026-08-13')
chk('D2 调度层L0+六层在位', lm.get('调度', {}).get('id') == 'L0' and ids == ['L1', 'L2', 'L3', 'L4', 'L5'])
l3 = [x for x in lm['层'] if x['id'] == 'L3'][0]
l4 = [x for x in lm['层'] if x['id'] == 'L4'][0]
chk('D3 L3七子路', len(l3.get('子路版本', [])) == 7 and all(r.get('名') and r.get('版本') for r in l3['子路版本']))
chk('D4 L4四页面', len(l4.get('页面版本', [])) == 4 and all(pg.get('名') and pg.get('版本') for pg in l4['页面版本']))
chk('D5 重建诚实标注(不编造历史号)', 'v1.0·重建' in json.dumps(lm, ensure_ascii=False) and '8-12' in lm.get('note', ''))
p = sh([PY, 'hermes_cockpit.py'], cwd=os.path.join(CKP, 'scripts'))
chk('D6 驾驶舱消费无缺失告警', p.returncode == 0 and 'OK:' in p.stdout)
ck = open(os.path.join(CKP, 'hermes_cockpit.html'), encoding='utf-8').read()
seg = ck[ck.find('项目能力版本'):ck.find('项目能力版本') + 4000]
chk('D7 版本卡恢复(分层+子路+页面)', 'L0 调度层' in seg and '战绩结算' in seg and '页面体系' in seg and '缺失' not in seg)
cv = json.load(open(os.path.join(CKP, 'cockpit_versions.json'), encoding='utf-8'))
chk('D8 Hermes侧台账bump', cv['meta']['last_change'] == '48' and any(l['key'] == 'external' and l['version'] == 'v1.1' for l in cv['layers']))

print()
print(f"通过 {len(oks)}/{len(oks)+len(fails)}")
if fails:
    print('FAIL:', '; '.join(fails)); sys.exit(1)
print('FAIL: 无 — 全部通过 (ad-hoc 专项验证, 非 suite)')
