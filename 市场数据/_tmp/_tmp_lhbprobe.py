# -*- coding: utf-8 -*-
"""探针: 复用 review_publish 的隔离环境, 直接构建单路 model 并打印完整性缺口。
用法: python _tmp_lhbprobe.py <frozen_dir> <stage_dir> <route> <YYYYMMDD>
"""
import sys, os
from pathlib import Path

ROOT = r'D:\股票数据\市场数据'
FROZEN = Path(sys.argv[1]); STAGE = Path(sys.argv[2]); ROUTE = sys.argv[3]; D = sys.argv[4]
sys.path.insert(0, ROOT); os.chdir(ROOT)

import review_publish as rp  # noqa: E402

with rp.isolated_imports(FROZEN, Path(ROOT)):
    b = rp.load_module(FROZEN / 'review_pages.py')
    m = b.build_page_model(FROZEN, D, ROUTE)

print('route      =', m.get('route'))
print('complete   =', m.get('complete'))
print('status     =', m.get('status'))
print('errors     =', m.get('errors'))
print('judgment_complete =', m.get('judgment_complete'))
print('machine_complete  =', m.get('machine_complete'))
print('paper_complete    =', m.get('paper_complete'))
print('data_conflicts    =', m.get('data_conflicts'))
print('limitations=', m.get('limitations'))
comps = m.get('components', [])
print('components:')
for c in comps:
    flag = '' if (c.get('status') == 'ok' or c.get('allow_missing')) else '   <<< NOT OK'
    mv = c.get('missing_values')
    print('   %-12s section=%-16s status=%-8s allow_missing=%s missing_values=%s%s'
          % (c.get('id'), c.get('section'), c.get('status'), c.get('allow_missing'), mv, flag))
print('sections without claims:')
for s in m.get('sections', []):
    if not s.get('claim_refs'):
        print('   ', s.get('id'), '|', s.get('label') or s.get('title') or '')
print('claims role 统计:', {r: sum(1 for c in m.get('claims', []) if c.get('role') == r)
                          for r in {c.get('role') for c in m.get('claims', [])}})
