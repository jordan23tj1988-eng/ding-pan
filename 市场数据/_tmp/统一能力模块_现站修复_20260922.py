# -*- coding: utf-8 -*-
"""现站一次性修复: 五路+概览两块标准能力模块统一(2026-09-22 用户指令)

背景: 历史实现只把主题页统一替换成两块标准能力模块 → 概览/竞价/产业逻辑/涨停页缺块,
龙虎榜页与旧『自主深挖/我的认知迭代』并存(用户看到的"有的路有, 有的路还没改过来")。

两阶段执行(拒绝半途改现站):
  1) 在临时副本上跑生产注入链(生成盯盘台._sync_capability_blocks)并逐页自检(能力进化模块.verify_page);
  2) 全过才覆盖现站, 覆盖前逐页备份到 _tmp/能力模块修复备份_20260922/。

主题页字节变化 → 用生产写入器重锚 .theme_page_freeze.json(同日冻结哈希), 备案见 _变更总账.md。
"""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r'D:\股票数据\市场数据')
SITE = ROOT / '复盘' / '盯盘台'
DATE = sys.argv[1] if len(sys.argv) > 1 else '20260921'
BAK = ROOT / '_tmp' / '能力模块修复备份_20260922'
STAGE = ROOT / '_tmp' / 'capability_repair_stage'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load('gen_repair', ROOT / '生成盯盘台.py')
evo = load('evo_repair', ROOT / '能力进化模块.py')

if STAGE.exists():
    shutil.rmtree(STAGE)
STAGE.mkdir(parents=True)
for route in evo.ROUTES:
    src = SITE / (route + '.html')
    if not src.is_file():
        raise SystemExit('现站缺页: %s' % src)
    shutil.copy2(src, STAGE / src.name)

report = gen._sync_capability_blocks(STAGE, DATE)
problems = {}
for route in evo.ROUTES:
    html = (STAGE / (route + '.html')).read_text(encoding='utf-8')
    found = evo.verify_page(html, route, ROOT, DATE)
    if found:
        problems[route] = found
if problems:
    print('自检未过, 现站零改动:', json.dumps(problems, ensure_ascii=False, indent=1))
    raise SystemExit(2)
print('注入报告:', ' | '.join(report))

BAK.mkdir(parents=True, exist_ok=True)
changed = []
for route in evo.ROUTES:
    live = SITE / (route + '.html')
    cand = STAGE / live.name
    if live.read_bytes() == cand.read_bytes():
        continue
    shutil.copy2(live, BAK / live.name)
    shutil.copy2(cand, live)
    changed.append(live.name)
print('已覆盖:', changed)

if 'theme.html' in changed:
    rec = gen._read_theme_freeze()
    if not rec:
        raise SystemExit('主题页变了但冻结记录缺失, 需人工确认')
    shutil.copy2(SITE / '.theme_page_freeze.json', BAK / '.theme_page_freeze.json')
    new = gen._write_theme_freeze(rec['d'], rec['build_id'], SITE / 'theme.html')
    print('冻结重锚: %s -> %s (d=%s)' % (rec['theme_sha256'][:12], new['theme_sha256'][:12], rec['d']))
print('备份目录:', BAK)
