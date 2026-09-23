import os
import re
from pathlib import Path

# 能力模块 CSS 注入(cycle)。2026-09-12 起支持发布候选站点后处理：
# POST_BASE/POST_SITE_ROOT/CYCLE_PAGE_TARGET 指向 stage/site 时作用于候选页；
# 不带环境变量时行为与旧版一致(现站 复盘/盯盘台/cycle.html)。
BASE = Path(os.environ.get('POST_BASE', r'D:/股票数据/市场数据'))
SITE_ROOT = Path(os.environ.get('POST_SITE_ROOT', str(BASE / '复盘' / '盯盘台')))
site = Path(os.environ.get('CYCLE_PAGE_TARGET', str(SITE_ROOT / 'cycle.html')))
idx = SITE_ROOT / 'index.html'
if not site.is_file():
    raise RuntimeError('cycle 页缺失: ' + str(site))
if not idx.is_file():
    raise RuntimeError('index 页缺失: ' + str(idx))
s = site.read_text(encoding='utf-8')
i = idx.read_text(encoding='utf-8')


def _evolution_css(text):
    m = re.search(r'(\.evolution\{.*?)(?=\.chart-title\{)', text, re.S)
    return m.group(1) if m else None


# 候选站点上概览页尚未重建时，CSS 源回退到现站(CYCLE_EVO_SOURCE)
block = _evolution_css(i)
if block is None:
    _fb = os.environ.get('CYCLE_CSS_SOURCE') or os.environ.get('CYCLE_EVO_SOURCE')
    if not _fb:
        raise RuntimeError('evolution css not found in index')
    _fbp = Path(_fb)
    if not _fbp.is_file():
        raise RuntimeError('能力模块 CSS 回退源缺失: ' + str(_fbp))
    block = _evolution_css(_fbp.read_text(encoding='utf-8'))
    if block is None:
        raise RuntimeError('evolution css not found in fallback source: ' + _fb)
# 概览页模块使用 --mut，黄金周期页使用 --sub；补同义变量但不改变模块样式
if '--mut' not in s:
    block = ':root{--mut:var(--sub)}' + block
s = re.sub(r'\n?<!--EVOLUTION_STYLE_SYNC_START-->.*?<!--EVOLUTION_STYLE_SYNC_END-->\n?', '\n', s, flags=re.S)
style = '\n<!--EVOLUTION_STYLE_SYNC_START-->\n<style id="evolution-style-sync">' + block + '</style>\n<!--EVOLUTION_STYLE_SYNC_END-->\n'
pos = s.find('</head>')
if pos < 0:
    raise RuntimeError('head missing')
s = s[:pos] + style + s[pos:]
site.write_text(s, encoding='utf-8', newline='\n')
print('injected evolution css chars', len(block), 'page bytes', site.stat().st_size)
