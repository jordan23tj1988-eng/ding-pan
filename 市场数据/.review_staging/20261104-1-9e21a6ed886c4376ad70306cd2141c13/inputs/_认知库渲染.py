# -*- coding: utf-8 -*-
"""_认知库渲染.py —— 六路渲染器读认知库注入「更早的认知迭代」折叠区(2026-08-16 方案A)
方案A: 渲染器兜底注入历史认知时间线, 数字/日期全来自认知库 json 原文(零编造)。
认知库=蒸馏器 _认知库蒸馏_五路.py 每晚产出(结构化历史认知迭代, 带日期)。
输出 HTML: <details class="chain tlfold"><summary>更早的认知迭代 ...</summary>...
对齐黄金版 tlfold 折叠结构 + 现有各路 r_cog 折叠格式。
"""
import re, os, json, glob


def _load_lib(route, L):
    """取最新认知库文件(子agent增强/带日期 优先, fallback 主库), 返回条目列表或 None"""
    cand = sorted(glob.glob(os.path.join(L, '子agent增强', '认知库_%s_*.json' % route)))
    if not cand:
        cand = [os.path.join(L, '_认知库_%s.json' % route)]
    for p in reversed(cand):
        try:
            lib = json.load(open(p, encoding='utf-8'))
            return lib.get('条目', [])
        except Exception:
            continue
    return None


def r_cog_lib(route, d, L=None):
    """读认知库历史条目(日期<复盘日d), 渲染「更早的认知迭代」折叠时间线。
    route: 路名; d: 复盘日 YYYYMMDD; L: _学习 目录(默认同脚本相对路径)。
    返回 '' 若无历史条目或无认知库文件。
    """
    if L is None:
        L = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_学习')
    entries = _load_lib(route, L)
    if not entries:
        return ''
    dstr = '%s-%s-%s' % (d[:4], d[4:6], d[6:8])
    entries = [e for e in entries if (e.get('日期') or '') and (e.get('日期') or '') < dstr]
    entries = [e for e in entries if (e.get('正文') or '').strip() or (e.get('标题') or '').strip()]
    if not entries:
        return ''
    tlis = []
    for e in entries:
        dd = (e.get('日期') or '')[5:]  # MM-DD
        title = (e.get('标题') or '').strip()
        body = (e.get('正文') or '').strip()
        h = '<div class="h">%s</div>' % title if title else ''
        tlis.append('<div class="tli"><div class="d"><b>%s</b></div>%s<div class="b">%s</div></div>' % (dd, h, body))
    newest = (entries[0].get('日期') or '')[5:]
    oldest = (entries[-1].get('日期') or '')[5:]
    return ('<details class="chain tlfold"><summary><b>更早的认知迭代</b> '
            '<span class="chip">%d条</span> <span class="mut">%s ~ %s</span></summary>'
            '<div class="inner"><div class="tl">%s</div></div></details>\n'
            % (len(entries), oldest, newest, ''.join(tlis)))


def inject_into_section(out, route, d, L=None):
    """把历史认知折叠区插入认知段 <h2>…认知…</h2> 之后最近 </section> 之前。
    用于认知段包裹在 <section> 内的渲染器(auction); 找不到 </section> 则尾部追加。
    """
    hist = r_cog_lib(route, d, L)
    if not hist:
        return out
    m = re.search(r'<h2[^>]*>(?:六\s*)?(?:我的)?认知(?:迭代)?', out)
    if not m:
        return out + hist
    i = out.find('</section>', m.start())
    if i < 0:
        return out + hist
    return out[:i] + hist + out[i:]
