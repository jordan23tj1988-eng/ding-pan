import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 周期页黄金视觉恢复(与 restore_lhb_page.py 同构)。
# 2026-09-12 起支持发布候选站点后处理：POST_BASE/POST_SITE_ROOT/CYCLE_PAGE_TARGET
# 指向 stage/site 时，同一套逻辑先在候选站点跑一遍，使被门禁检查的页面与被部署的页面同源；
# 不带环境变量时行为与旧版完全一致(仍是现站 复盘/盯盘台/cycle.html)。
BASE = Path(os.environ.get('POST_BASE', r'D:/股票数据/市场数据'))
SITE_ROOT = Path(os.environ.get('POST_SITE_ROOT', str(BASE / '复盘' / '盯盘台')))
G = Path(os.environ.get('CYCLE_GOLDEN', r'D:/黄金对照版717/cycle.html'))
SITE = Path(os.environ.get('CYCLE_PAGE_TARGET', str(SITE_ROOT / 'cycle.html')))
BAK = SITE.with_name(SITE.name + '.before_evolution_sync_20260912.bak')
OUT = SITE.with_suffix('.html.cycle_restore_tmp')


def sec(s, sid):
    m = re.search(r'<section id="' + re.escape(sid) + r'"[^>]*>.*?</section>', s, re.S)
    if not m:
        raise RuntimeError('missing ' + sid)
    return m.group(0)


def evo(s):
    return re.findall(r'<section class="evolution"[^>]*>.*?</section>', s, re.S)


if not SITE.is_file():
    raise RuntimeError('cycle 恢复目标页缺失: ' + str(SITE))
if not G.is_file():
    raise RuntimeError('黄金版周期页缺失: ' + str(G))

g = G.read_text(encoding='utf-8')
old = BAK.read_text(encoding='utf-8') if BAK.exists() else ''
cur = SITE.read_text(encoding='utf-8')
date = sys.argv[1] if len(sys.argv) > 1 else '20260910'
# 能力模块从现站/概览取；正文必须从目标日 judgment 取，黄金页只提供壳和样式
cur_evo = evo(cur)
if len(cur_evo) < 2:
    idx = SITE_ROOT / 'index.html'
    if idx.exists():
        cur_evo = evo(idx.read_text(encoding='utf-8'))
# 候选站点上概览页尚未重建时，能力模块回退源(默认现站 index.html)
_fb = os.environ.get('CYCLE_EVO_SOURCE')
if len(cur_evo) < 2 and _fb:
    _fbp = Path(_fb)
    if not _fbp.is_file():
        raise RuntimeError('能力模块回退源缺失: ' + str(_fbp))
    cur_evo = evo(_fbp.read_text(encoding='utf-8'))
if len(cur_evo) < 2:
    raise RuntimeError('current evolution count=' + str(len(cur_evo)))
cur_evo = cur_evo[:2]
# 生产动态 body 必须来自模块化渲染器（机器卡+目标日正文），不直接复制黄金历史正文
render_out = BASE / '_tmp' / ('cycle_dynamic_' + date + '.html')
render_out.parent.mkdir(parents=True, exist_ok=True)
cp = subprocess.run([sys.executable, str(BASE / 'module_render_cycle.py'), date, '--out', str(render_out)],
                    cwd=str(BASE), capture_output=True, text=True, encoding='utf-8')
if cp.returncode != 0 or not render_out.exists():
    raise RuntimeError('cycle dynamic renderer failed: ' + cp.stderr[-1000:])
dynamic = render_out.read_text(encoding='utf-8')
# 黄金页头部要求 rowA 容器；将动态 hero 保持原文包入 rowA，不改数据正文。
if dynamic.lstrip().startswith('<div class="hero">') and '<div class="cycle-machine-inline">' in dynamic:
    dynamic = dynamic.replace('<div class="hero">', '<div class="rowA"><div class="hero">', 1)
    dynamic = dynamic.replace('</div>\n<div class="cycle-machine-inline">', '</div></div>\n<div class="cycle-machine-inline">', 1)
if dynamic.count('<h2>') < 7:
    raise RuntimeError('target cycle body incomplete')
# 黄金版 head 到 wrap 内容起点；动态 body 自带 hero+七段；页脚沿用黄金版
body_start = g.find('<div class="wrap">')
if body_start < 0:
    raise RuntimeError('golden wrap missing')
body_start = g.find('>', body_start) + 1
foot = g.rfind('<div class="foot">')
if foot < 0:
    raise RuntimeError('golden foot missing')
head = g[:body_start]
tail = g[foot:]
g = head + dynamic + '\n' + '\n'.join(cur_evo) + '\n' + tail
# 结构断言: 黄金 CSS + 当日七段 + 两个能力模块
for token in ('class="steps"', 'class="cols"', 'class="stages"', 'class="posmeter"'):
    if token not in g:
        raise RuntimeError('golden visual token missing ' + token)
if len(re.findall(r'<h2>', g)) < 7:
    raise RuntimeError('output h2 incomplete')
if len(re.findall(r'<section class="evolution"[^>]*>', g)) != 2:
    raise RuntimeError('output evolution count')
shutil.copy2(SITE, SITE.with_name(SITE.name + '.before_cycle_restore_' + date + '.bak'))
OUT.write_text(g, encoding='utf-8', newline='\n')
shutil.move(str(OUT), SITE)
print('restored', SITE, 'bytes', SITE.stat().st_size)
print('golden first5 visual tokens:', all(x in g for x in ('class="steps"', 'class="cols"', 'class="stages"', 'class="posmeter"')))
print('sections', re.findall(r'<section id="([^"]+)"', g))
print('evolution', len(evo(g)))
