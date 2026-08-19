# -*- coding: utf-8 -*-
"""hermes-verify-limitup-h2-dup — 2026-08-13 涨停复盘重复文字修复的专项验证(ad-hoc)。
覆盖 4 个改动点:
  A. module_render_limitup._body_h2 坏h2(内嵌块级元素)→回退标准模板 (本次加固核心)
  B. _body_h2 正常h2(标题+span.hint)→原文保真; 标题语义族偏离→回退 (白名单原行为不回归)
  C. limitup数据核对._rate_variants 数值等价(16.0 应对 16%/16.0%)
  D. 端到端: 已发布页面 h2全<2KB无块级 / 板块一荐票表唯一 / 板块一关键数字=1 /
     div配平 / 哨兵35项PASS
"""
import os, sys, tempfile, subprocess

BASE = r'D:\股票数据\市场数据'
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, '复盘', '盯盘台'))

FAILS = []


def chk(label, ok, detail=''):
    print(('  ✓ ' if ok else '  ✗ ') + label + ((' — ' + detail) if detail else ''))
    if not ok:
        FAILS.append(label)


# ---------- A/B: 渲染器 _body_h2 ----------
import importlib.util as _iu


def _load(mod, path):
    spec = _iu.spec_from_file_location(mod, os.path.join(BASE, path))
    m = _iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


mrl = _load('_mrl', 'module_render_limitup.py')

# A1: h2一 内嵌 table → 回退标准模板(不得含 <table)
bad1 = ('<h2>一 涨停复盘 · Top5荐票<span class="hint">x</span>'
        '<table><tr><td>600683</td></tr></table></h2>')
r = mrl._body_h2(bad1, '一 ')
chk('A1 坏h2一(嵌table)回退标准模板', r == mrl._H2_STD['一 '] and '<table' not in r, r[:60])

# A2: h2二 内嵌 div.kv → 回退标准模板
bad2 = ('<h2>二 市场温度 · 涨停生态<span class="hint">x</span>'
        '<div class="kv"><div class="l">市场温度</div><div class="v">40.1</div></div></h2>')
r = mrl._body_h2(bad2, '二 ')
chk('A2 坏h2二(嵌div)回退标准模板', r == mrl._H2_STD['二 '] and '<div' not in r)

# A3: 8/13 原始坏 body(h2一 754B) → 现在也必须回退(修复脚本已改body, 此处测渲染器兜底)
import json
j = json.load(open(os.path.join(BASE, '_tmp', 'dupfix_20260813',
                                'judgment_20260813.bak.json'), encoding='utf-8'))
raw_body = j['bodies']['limitup']
r = mrl._body_h2(raw_body, '一 ')
chk('A3 8/13原始坏body的h2一也被拦截回退', r == mrl._H2_STD['一 '] and '<table' not in r)

# B1: 正常 h2(标题+span.hint) 保真
good = '<h2>三 归位台账<span class="hint">LEDGER=台账脚本注入;题材归位=全系统唯一真源</span></h2>'
chk('B1 正常h2原文保真', mrl._body_h2(good, '三 ') == good)

# B2: 语义族偏离(标题错)仍回退(原白名单行为)
bad_title = '<h2>四 连板结构<span class="hint">自造标题</span></h2>'
chk('B2 标题语义族偏离回退模板(不回归)', mrl._body_h2(bad_title, '四 ') == mrl._H2_STD['四 '])

# ---------- C: 哨兵 _rate_variants ----------
snt = _load('_snt', 'limitup数据核对.py')
v = snt._rate_variants('16.0')
chk('C1 16.0 变体含 16% 与 16.0%', '16%' in v and '16.0%' in v and '16' in v, str(sorted(v)))
v = snt._rate_variants('18.4')
chk('C2 18.4 变体含 18.4% 且不含 18%', '18.4%' in v and '18%' not in v, str(sorted(v)))
v = snt._rate_variants('—')
chk('C3 非数值兜底', v == {'—', '—%'}, str(v))

# ---------- D: 端到端页面 ----------
PAGE = os.path.join(BASE, '复盘', '盯盘台', 'limitup.html')
h = open(PAGE, encoding='utf-8').read()
import re
BAD_BLOCK = re.compile(r'<(table|div|ul|ol|p|details|svg|pre)\b')
bad_h2 = 0
for m in re.finditer(r'<h2[^>]*>', h):
    e = h.find('</h2>', m.start())
    seg = h[m.start():e + 5]
    if len(seg) >= 2048 or BAD_BLOCK.search(seg):
        bad_h2 += 1
chk('D1 页面6个h2全<2KB且无块级元素', bad_h2 == 0 and len(re.findall(r'<h2', h)) == 6,
    f'坏h2={bad_h2}')
b1 = h[h.find('<h2>一'):h.find('<h2>二')]
chk('D2 板块一荐票表唯一且无h2小表表头',
    b1.count('<table') == 1 and b1.count('执1胜率/均涨') == 0)
chk('D3 板块一关键数字均=1次(防双重渲染)',
    all(b1.count(k) == 1 for k in ('40.7%/-0.52', '42.9%/-0.30', '17.8%', '15.9%')))
chk('D4 div配平', h.count('<div') == h.count('</div>'),
    f"<div={h.count('<div')} </div>={h.count('</div>')}")

r = subprocess.run([sys.executable, os.path.join(BASE, 'limitup数据核对.py'), '20260813'],
                   capture_output=True, text=True)
ok = r.returncode == 0 and 'PASS 全部一致' in r.stdout and '✗' not in r.stdout
chk('D5 哨兵35项全PASS(含负面注入拦截)', ok,
    (r.stdout or r.stderr).strip().split('\n')[-1][:80] if (r.stdout or r.stderr).strip() else 'no out')

print()
if FAILS:
    print('=== VERIFY FAIL:', len(FAILS), '项 ===')
    sys.exit(1)
print('=== hermes-verify 全部通过 (ad-hoc 专项验证, 非 suite) ===')
