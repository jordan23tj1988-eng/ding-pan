# -*- coding: utf-8 -*-
"""hermes-verify-redeploy-cycle-20260912.py — 定向重发周期情绪页(只到站 cycle.html)

用途: 展示完整性契约修好后, 用真链路重建 20260910 发出版并把 cycle 页到站;
     其他五路页面不动(用户 2026-09-12 定向: 其他路的先不要动)。
纪律: 走 review_publish.build_release 门禁(fail-closed), 不手改产物; 只额外复制+同步 cycle 单页。
"""
import importlib, os, shutil, sys
from pathlib import Path

BASE = Path(r"D:/股票数据/市场数据")
os.chdir(BASE)
sys.path[:] = [p for p in sys.path if 'PYTHONPATH' not in p]
sys.path.insert(0, str(BASE))

mod = importlib.import_module('生成盯盘台')
date = sys.argv[1] if len(sys.argv) > 1 else '20260910'

print('[1/5] P2 production audit ...')
ok2 = mod._run_p2_production_audit(date)
print('      P2 =', ok2)
if not ok2:
    raise SystemExit('P2 audit blocked -> 不发布')

print('[2/5] P3 production bridge ...')
ok3 = mod._run_p3_production_bridge(date)
print('      P3 =', ok3, '(仅约束生产登记, 页面可继续)')

print('[3/5] build_release ...')
from review_publish import build_release
res = build_release(BASE, date, publish=True)
print('      status =', res.get('status'), '| release =', res.get('release_dir'))
if res.get('status') != 'pass':
    raise SystemExit('release blocked: %s' % res.get('errors'))

rel = Path(res['release_dir'])
src = rel / 'site'
site = BASE / '复盘' / '盯盘台'
for k in ['cycle']:                      # ← 只到站周期情绪页
    shutil.copy2(src / (k + '.html'), site / (k + '.html'))
print('[4/5] 到站 cycle.html 完成; 其他五路未动')

print('[5/5] 能力进化模块由 release builder 统一生成，跳过追加同步 ...')
print('      no append; prevents duplicate sections')
print('DONE')
