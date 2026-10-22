import json
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


def fix_nav_update_date(html, root, d):
    """导航“更新 …”行改写为当日 更新label。

    根因: 黄金壳(D:/黄金对照版717/*.html)头部自带
    “更新 2026-07-16 18:00 傍晚复盘(冰点·多agent)”, 恢复器整段搬壳时把黄金版日期带到当日页面。
    零编造: label 只取当日 judgment 的 更新label, 缺省 f"{d} 复盘"; 读不到文件不报错。
    改写后必须断言黄金版日期已消失, 否则 raise(宁可不发, 不发错日期页)。
    同源复制: 与 restore_cycle_page.py 同名函数保持一致。
    """
    label = None
    jf = Path(root) / '_学习' / ('judgment_' + str(d) + '.json')
    if jf.is_file():
        try:
            label = (json.loads(jf.read_text(encoding='utf-8')) or {}).get('更新label') or None
        except Exception:
            label = None
    label = label or (str(d) + ' 复盘')
    out, n = re.subn(r'(<span class="upd">.*?<span class="txt">)更新[^<]*',
                     lambda m: m.group(1) + '更新 ' + label, html, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError('导航更新时间行未命中: ' + str(d))
    if '2026-07-16' in out:
        raise RuntimeError('导航日期改写失败(仍含黄金版日期): ' + str(d))
    if ('更新 ' + label) not in out:
        raise RuntimeError('导航日期改写失败(未写入 label): ' + str(d))
    return out


def build_cycle_kpis(root, d):
    """当日真值 KPI 四卡(黄金卡骨架: ico+chip2 在 top / lab / big / sub2)。

    槽位: 两市量能 / 情绪阶段(主判) / 市场温度 · 250日分位 / 执行状态。
    任一槽位数据缺失 → 该卡 big/sub2 填 —, 不填假值、不省略卡。
    仅用于“正文只给了 hero、没有 KPI 卡”的当日; 正文自带 4 卡时不注入。
    """
    L = Path(root) / '_学习'

    def _j(fn):
        p = L / fn
        if not p.is_file():
            return {}
        try:
            return json.loads(p.read_text(encoding='utf-8')) or {}
        except Exception:
            return {}

    # ico 内层与黄金版同款(黄金卡骨架: ico+chip2 在同一行 top)
    ICO_VOL = '<path d="M3 17l5-6 4 4 6-8 3 4"/>'
    ICO_STAGE = '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>'
    ICO_TEMP = '<path d="M12 3v10.3a4 4 0 1 0 2 0V3z"/><circle cx="13" cy="17" r="1.6"/>'
    ICO_POS = '<path d="M4 20h16M6 16l4-8 4 5 4-9"/>'

    def _ico(inner):
        return '<span class="ico"><svg viewBox="0 0 24 24">%s</svg></span>' % inner

    def _card(ico, chip, chip_cls, lab, big, big_style, gauge, sub2):
        g = ('<div class="gauge"><div class="gtrack"><i class="gmark" style="left:%s%%"></i></div>'
             '<div class="gl"><span>冰点</span><span>偏冷</span><span>中性</span><span>偏热</span><span>过热</span></div></div>'
             % gauge) if gauge is not None else ''
        return ('<div class="kpi"><div class="top">%s<span class="chip2 %s">%s</span></div>'
                '<span class="lab">%s</span><span class="big"%s>%s</span>%s<span class="sub2">%s</span></div>'
                % (ico, chip_cls, chip, lab, (' style="font-size:20px"' if big_style else ''), big, g, sub2))

    tt = _j('_市场温度表.json')
    trow = tt.get(str(d)) or {}
    ks = sorted(k for k in tt if re.fullmatch(r'\d{8}', str(k)) and str(k) <= str(d))
    prev = tt.get(ks[-2]) if len(ks) >= 2 else None
    tj = _j('周期主判_%s.json' % d)
    zs = _j('总审_%s.json' % d).get('总裁决') or {}

    # --- 1 两市量能 ---
    w = trow.get('成交额亿')
    if w is None:
        c1 = _card(_ico(ICO_VOL), '量能 —', 'c-miss', '两市量能', '—', False, None, '当日温度表无成交额字段')
    else:
        seq = [tt[k].get('成交额亿') for k in ks[-3:] if (tt.get(k) or {}).get('成交额亿') is not None]
        trend = ''
        if len(seq) >= 2:
            d1, d2 = seq[-1], seq[-2]
            same = '落' if d2 is not None and d1 < d2 else ('升' if d2 is not None and d1 > d2 else '平')
            trend = ('·连%d%s' % (len(seq), same)) if len(seq) == 3 else ('·%s' % same)
        try:
            import module_render_cycle as _mc
            tier = _mc.vol_tier(w / 10000.0)
            tier_name = tier[1] if tier else '—'
        except Exception:
            tier_name = '—'
        c1 = _card(_ico(ICO_VOL), '%s台阶%s' % (tier_name, trend), 'c-half', '两市量能',
                   '%.1f<span style="font-size:15px">亿</span>' % w, False, None,
                   '成交额 %s(温度表当日); 档位按米开量能台阶换算' % ('→'.join('%.0f' % x for x in seq) if seq else '—'))

    # --- 2 情绪阶段(主判) ---
    stage, direction = tj.get('stage'), tj.get('direction')
    if not stage:
        c2 = _card(_ico(ICO_STAGE), '主判 —', 'c-miss',
                   '情绪阶段(主判)', '—', True, None, '当日无 周期主判_%s.json' % d)
    else:
        big2 = '%s%s' % (stage, ('·' + str(direction)) if direction else '')
        sub2 = '总审%s档·置信度%s/100; 主判来源: %s' % (zs.get('档位', '—'), zs.get('置信度', '—'), tj.get('source', '—'))
        c2 = _card(_ico(ICO_STAGE), '%s档' % (zs.get('档位') or '—'),
                   'c-half', '情绪阶段(主判)', big2, True, None, sub2)

    # --- 3 市场温度 · 250日分位 ---
    temp, tband = trow.get('温度'), trow.get('温度档')
    if temp is None:
        c3 = _card(_ico(ICO_TEMP), '温度 —', 'c-miss', '市场温度 · 250日分位', '—', False, None,
                   '当日温度表无温度字段')
    else:
        pv = (prev or {}).get('温度')
        c3 = _card(_ico(ICO_TEMP), (tband or '—'), 'c-cool', '市场温度 · 250日分位',
                   '%.1f' % temp, False, max(0.0, min(100.0, float(temp))),
                   '前一日 %s; 三窗: 冰点<25 / 过热≥85 / 溢价连负3日' % ('%.1f' % pv if pv is not None else '—'))

    # --- 4 执行状态 ---
    band = zs.get('档位')
    concl = str(zs.get('结论') or '')
    if not band:
        c4 = _card(_ico(ICO_POS), '执行 —', 'c-miss', '执行状态', '—', True, None, '当日无总审总裁决')
    else:
        big4 = '空仓' if '空仓' in concl else '%s档' % band
        c4 = _card(_ico(ICO_POS), '%s档防守' % band, 'c-cool', '执行状态', big4, True, None,
                   '总审总裁决(%s档 · 置信度%s/100, 未校准评分); %s' % (band, zs.get('置信度', '—'), concl or '结论见总审'))

    return c1 + c2 + c3 + c4


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
# 能力模块 = 本路唯一真源直出(能力进化模块.py, route=cycle);
# 不再从现站/概览搬运同一份字节 —— 2026-09-28 用户口径: 所有路都是各自的能力板块。
# 与发布门禁/哨兵 canonical_sections(root, d, 'cycle') 同源, 字节必然一致。
def _capability_module():
    import importlib.util
    p = BASE / '能力进化模块.py'
    if not p.is_file():
        raise RuntimeError('能力进化模块.py 缺失: ' + str(p))
    spec = importlib.util.spec_from_file_location('capability_module_source', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cur_evo = _capability_module().canonical_sections(BASE, date, 'cycle')
if len(cur_evo) != 2:
    raise RuntimeError('能力模块产出异常: %d' % len(cur_evo))
# 生产动态 body 必须来自模块化渲染器（机器卡+目标日正文），不直接复制黄金历史正文
render_out = BASE / '_tmp' / ('cycle_dynamic_' + date + '.html')
render_out.parent.mkdir(parents=True, exist_ok=True)
cp = subprocess.run([sys.executable, str(BASE / 'module_render_cycle.py'), date, '--out', str(render_out)],
                    cwd=str(BASE), capture_output=True, text=True, encoding='utf-8')
if cp.returncode != 0 or not render_out.exists():
    raise RuntimeError('cycle dynamic renderer failed: ' + cp.stderr[-1000:])
dynamic = render_out.read_text(encoding='utf-8')
# 第六、七项由标准能力模块承载。生成器旧 body 里的 research/cognition
# 只保留在数据审计中，不再混入展示页，避免同一能力出现两套卡片。
_old_ability = dynamic.find('<h2>六')
if _old_ability >= 0:
    dynamic = dynamic[:_old_ability].rstrip()
# 黄金页头部要求 rowA 容器；将动态 hero 保持原文包入 rowA，不改数据正文。
# 仅当正文只给 hero、且没有自带 KPI 卡时注入当日真值四卡;
# 若正文已自带 rowA+4卡(如 9/24 重写版)则跳过, 避免 8 张卡与 rowA 契约破坏。
if (dynamic.lstrip().startswith('<div class="hero">')
        and '<div class="cycle-machine-inline">' in dynamic
        and 'class="kpi"' not in dynamic):
    dynamic = dynamic.replace('<div class="hero">', '<div class="rowA"><div class="hero">', 1)
    kpis = build_cycle_kpis(BASE, date)
    # 关闭紧凑 KPI 容器、hero 与 rowA 三层；此前少关一层导致 C6 div 差1。
    dynamic = dynamic.replace('</div>\n<div class="cycle-machine-inline">', '</div><div class="kpis">'+kpis+'</div></div>\n<div class="cycle-machine-inline">', 1)
if dynamic.count('<h2>') < 5:
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
g = fix_nav_update_date(g, BASE, date)
shutil.copy2(SITE, SITE.with_name(SITE.name + '.before_cycle_restore_' + date + '.bak'))
OUT.write_text(g, encoding='utf-8', newline='\n')
shutil.move(str(OUT), SITE)
print('restored', SITE, 'bytes', SITE.stat().st_size)
print('golden first5 visual tokens:', all(x in g for x in ('class="steps"', 'class="cols"', 'class="stages"', 'class="posmeter"')))
print('sections', re.findall(r'<section id="([^"]+)"', g))
print('evolution', len(evo(g)))
