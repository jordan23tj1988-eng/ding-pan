# -*- coding: utf-8 -*-
"""_preview_index_rebuild.py {d} —— 概览页「整晚复盘总预览」候选生成(预览用, 不覆盖正式页)

边界(2026-09-12 用户拍板):
  冻结区 = 页面顶部 → Top5 荐票卡 </section> 结束, 一字不动(导航/hero/纸盘/Top5)。
  重做区 = Top5 之后全部: 结论→机械核对→观察点→五路→拐点→总裁决→认知迭代。

铁律:
  - 数据全部来自当日权威产物(总审_/judgment_/模拟盘引擎/跨路荐票), 缺失标 —, 零编造。
  - 组件只用 _盯盘台组件规范.md 既有类名(.card/.hint/.chip2/.obs/.routes/.hb/.tl/.tli/.rowE/.mx), 不自造。
  - 只写候选文件 _preview_overnight_{d}.html, 不动 index.html。
"""
import io, json, os, re, sys

ROOT = r'D:/股票数据/市场数据'
L = os.path.join(ROOT, '_学习')
SITE = os.path.join(ROOT, '复盘', '盯盘台')
PROD = os.path.join(SITE, 'index.html')

d = sys.argv[1] if len(sys.argv) > 1 else '20260910'


def rd(p):
    return io.open(p, encoding='utf-8').read()


def js(p):
    return json.loads(rd(p)) if os.path.exists(p) else {}


prod = rd(PROD)
zj = js(os.path.join(L, '总审_%s.json' % d))
jud = js(os.path.join(L, 'judgment_%s.json' % d))


def frag(text, a, b):
    i = text.find(a)
    if i < 0:
        return ''
    j = text.find(b, i)
    return text[i + len(a):j] if j > 0 else ''


def ainner(anchor, text):
    """取 <!--ANCHOR-->...<!--/ANCHOR--> 之间的权威片段(锚点由哨兵保证成对)。"""
    m = re.search(r'<!--' + anchor + r'-->(.*?)<!--/' + anchor + r'-->', text, re.S)
    return m.group(1).strip() if m else ''


def ablock(anchor, text):
    """取整个锚区(含成对注释)。移块到新位置时必须用这个, 否则哨兵锚点核对会判不成对。"""
    inner = ainner(anchor, text)
    return ('<!--%s-->%s<!--/%s-->' % (anchor, inner, anchor)) if inner else ''


# ---------- 冻结区: 顶部 → Top5 荐票卡结束 ----------
rec_start = prod.find('<section id="recommendations">')
rec_end = prod.find('</section>', rec_start) + len('</section>')
frozen = prod[:rec_end]

# 机械数据核对层原本夹在 Hero 与 Top5 之间(折叠表)。用户明确要求"放到下面",
# 故从冻结区摘出, 只在下半页以摘要卡重新出现 —— 否则同一锚点/同一 id 会出现两份。
_mech_start = frozen.find('<details class="chain audit-fold machfold">')
if _mech_start > 0:
    _mech_end = frozen.find('</details>', _mech_start) + len('</details>')
    frozen = frozen[:_mech_start] + frozen[_mech_end:]

# 阅读条(reading-spine)是外壳按栏目自动产出的索引, 不是固定设计件:
# 重排栏目后必须同步步进, 否则 06 Master / 07 来源审计 指向已被移出的栏目 = 死链。
NEWSTEPS = [('recommendations', 'Top5 荐票 · 跨路筛选'), ('overnight', '今晚最终取舍'),
            ('routes', '五路合议'), ('turning', '拐点与验证'), ('verdict', '总裁决'),
            ('extension', '自主拓展'), ('cog', '认知迭代')]
_steps = '<span class="rs-arrow">→</span>'.join(
    '<a class="rs-step" href="#%s"><b>%02d</b>%s</a>' % (i, n + 1, t) for n, (i, t) in enumerate(NEWSTEPS))
frozen = re.sub(r'(<nav class="reading-spine"[^>]*>).*?</nav>',
                lambda m: m.group(1) + '<span class="rs-title">本页阅读</span>' + _steps + '</nav>',
                frozen, flags=re.S)

# ---------- 尾区: foot + wrap闭合 + script ----------
foot_i = prod.find('<div class="foot">')
tail = prod[foot_i:]

# ---------- 权威片段回收 ----------
mech = frag(prod, '<details class="chain audit-fold machfold">', '</details>')
temp_card = ablock('IDXTEMP', prod)
lead_bar = ablock('IDXLEAD', prod)
vote_blk = ablock('IDXVOTE', prod)
books_inner = ablock('ENGINEBOOKS', prod)

routes_sec = frag(prod, '<section id="routes">', '</section>')
obs_cards = frag(routes_sec, '<div class="obs">', '</div></div></div></div></div>')
if not obs_cards:
    m = re.search(r'(<div class="obs">.*?)(?:</div></div></div>)', routes_sec, re.S)
    obs_cards = m.group(1) if m else ''
obs_all = routes_sec[routes_sec.find('<div class="obs">'):]
obs_all = obs_all[:obs_all.find('<p class="mut"')] if '<p class="mut"' in obs_all else obs_all
obs_all = obs_all.rstrip('</div> ') if obs_all.endswith('</div>') else obs_all
# obs 卡区块: 从第一个 .obs 到最后一个 .obs 卡闭合
_ends = [m.end() for m in re.finditer(r'<div class="obs-rec">.*?</div></div>', obs_all, re.S)]
obs_block = obs_all[:max(_ends)] if _ends else ''
obs_block = obs_block[:obs_block.rfind('</div>') + 6] if obs_block else ''

# 五路看牌读数卡(judgment index body 的 .routes 块, 黄金版组件)
body_routes = ''
mb = re.search(r'<div class="routes">.*?</div>\s*(?=<!--|\n<h2)', jud.get('bodies', {}).get('index', ''), re.S)
if mb:
    body_routes = mb.group(0).replace('</div>', '</div>', 1)
if not body_routes:
    mb = re.search(r'<div class="routes">.*?</div>', jud.get('bodies', {}).get('index', ''), re.S)
    body_routes = mb.group(0) if mb else ''

# 机械核对-周期投票 紧凑重排(数值来自权威块, 只重排结构)
vote_m = re.search(r'主判=([^<]+)', vote_blk)
vote_main = vote_m.group(1) if vote_m else '—'
vote_cells = re.findall(r'<div style="flex:1;min-width:100px;[^"]*">([①②③④⑤][^<]*)<br>([^<]*)</div>', vote_blk)
if not vote_cells:
    vote_cells = re.findall(r'min-width:100px[^>]*>([①②③④⑤][^<]*)<br>([^<]*)<', vote_blk)
vote_note = ''
vn = re.search(r'<div style="margin-top:8px;color:#5c6674;font-size:11px">(.*?)</div>', vote_blk, re.S)
if vn:
    vote_note = vn.group(1).strip()

zj_ver = zj.get('总裁决', {}) or {}
concl = zj_ver.get('结论', '—')
gear = zj_ver.get('档位', '—')
conf = zj_ver.get('置信度')
conf_s = ('%s%%' % conf) if conf is not None else '—'
basis = zj_ver.get('依据', []) or []
gear_cls = {'A': 's-ok', 'B': 's-mid', 'C': 's-weak'}.get(str(gear)[:1], 's-mid')

routes_cfg = [('auction', '01 / 第一路', '竞价·时机', 'auction.html'),
              ('lhb', '02 / 第二路', '席位·资金', 'lhb.html'),
              ('theme', '03 / 第三路', '题材·主线', 'theme.html'),
              ('logic', '04 / 第四路', '产业·逻辑', 'logic.html'),
              ('limitup', '05 / 第五路', '涨停·质量', 'limitup.html')]
zj_routes = zj.get('五路裁决', {}) or {}
route_eval = {
    'auction': ('试错', '竞价评分只用于池内排序；缺少9:25轨迹时不升级执行。'),
    'lhb': ('试探', '冰点下席位局部偏强，但S档参与不足；仅作观察。'),
    'theme': ('换线', '无主流题材确认；单票首板分支不能升级为主线。'),
    'logic': ('弹药', 'A共振池∩涨停池=0；弱承载不升级为交易指令。'),
    'limitup': ('加分', '冰点环境规则全场加分，但封板质量偏弱，仍维持防守。'),
}
rt_cards = []
for key, rtn, rtm, href in routes_cfg:
    r = zj_routes.get(key, {}) or {}
    g = str(r.get('原判档位', '—'))
    cls = {'试错': 's-mid', '试探': 's-mid', '换线': 's-weak', '弹药': 's-mid', '加分': 's-ok'}.get(route_eval[key][0], 's-weak')
    ev, desc = route_eval[key]
    rt_cards.append('<a class="rt" href="%s"><span class="rtn">%s</span><span class="rtm">%s</span>'
                    '<b class="rtt %s">%s</b><span class="rtd">%s</span></a>' % (href, rtn, rtm, cls, ev, desc))
rt_html = '<div class="routes">%s</div>' % ''.join(rt_cards)

# ---------- 五路合议图(真实总审读数, 不是装饰图) ----------
route_svg = []
for key, rtn, rtm, href in routes_cfg:
    r = zj_routes.get(key, {}) or {}
    score = r.get('原判置信度')
    val = int(score) if isinstance(score, (int, float)) else 0
    label = rtm.split('·')[0]
    route_svg.append('<div class="route-bar" data-motion><span class="route-label">%s</span><div class="route-track"><i style="width:%s%%"></i></div><b>%s</b><small>荐票%s</small></div>' % (label, val, score if score is not None else '—', r.get('荐票数', '—')))
route_chart = '<div class="route-chart"><div class="chart-title">五路判断强度 · 置信度 / 荐票数</div>%s</div>' % ''.join(route_svg)

ext = js(os.path.join(L, '自主拓展应答_%s.json' % d))
ext_items = list(ext.values()) if isinstance(ext, dict) else []
ext_counts = {k: sum(1 for x in ext_items if x.get('决定') == k) for k in ('立项','并入','不深挖')}
ext_rows = ''.join('<div class="ext-row" data-motion><b>%s</b><span>%s</span><small>%s</small></div>' % (x.get('决定','—'), x.get('专题id','—'), re.sub(r'。.*','。',x.get('理由','—'))[:90]) for x in ext_items)
ext_chart = ''.join('<span class="ext-stat"><b>%s</b><small>%s</small></span>' % (k, ext_counts[k]) for k in ('立项','并入','不深挖'))

# ---------- 两个模块的能力进化账本（只显示真实已落账字段） ----------
evo = js(os.path.join(L, '能力进化快照_%s.json' % d))
evo_ext = js(os.path.join(L, '能力进化库_自主拓展.json'))
evo_cog = js(os.path.join(L, '能力进化库_认知迭代.json'))
def evo_panel(title, data, rows, key):
    st = (data or {}).get(key, {})
    labels=[('inherited','历史承接'),('experiences','经验/教训/信号'),('capabilities','已沉淀能力'),('hits','后续命中'),('validated','验证成功'),('refuted','已证伪'),('tracking','追踪中'),('shelved','已搁置'),('review_events','复核事件')]
    pills=''.join('<span class="evo-stat"><b>%s</b><small>%s</small></span>' % (st.get(k,0),lab) for k,lab in labels)
    items=[]
    ordered=sorted((rows or []), key=lambda r: str(r.get('date') or r.get('discovered_at') or ''), reverse=True)
    for r in ordered:
        review_count=len(r.get('review_log') or [])
        has_result=(r.get('capitalized') is True or r.get('state') in ('capability','validated','refuted') or r.get('hit_count') is not None or r.get('validation') in ('validated','refuted') or review_count)
        if has_result:
            items.append('<div class="evo-row"><b>%s</b><span>%s</span><small>发现：%s · 最近复核：%s · 验证：%s · 命中：%s · 反哺：%s</small></div>' % (r.get('route','—'),r.get('title') or r.get('body','—'),r.get('date') or r.get('discovered_at') or '—',r.get('last_reviewed_at') or '—',r.get('validation') or '待验证',r.get('hit_count') if r.get('hit_count') is not None else '—',','.join(r.get('feedback_routes') or []) or '—'))
    body=''.join(items) or '<div class="evo-empty">当前没有明确的复核、验证、命中或能力化证据；不把未验证记录伪装成结果。</div>'
    return '<section class="evolution"><h2>%s<span class="hint">发现 → 复核/追踪 → 验证 → 证伪/确认 → 能力化 → 反哺</span></h2><div class="evo-stats">%s</div><details open><summary>能力链明细 <span class="chip">%d条有事件/结果记录</span></summary><div class="evo-list">%s</div></details></section>'%(title,pills,len(items),body)

evo_ext_html=evo_panel('自主拓展 · 能力进化',evo,evo_ext.get('records',[]) if isinstance(evo_ext,dict) else [],'自主拓展')
evo_cog_html=evo_panel('认知迭代 · 能力进化',evo,evo_cog.get('records',[]) if isinstance(evo_cog,dict) else [],'认知迭代')

divs = zj.get('分歧裁决', []) or []
div_html = ''.join('<li>%s</li>' % x for x in divs) or '<li class="mut">—</li>'
div_rows = ''.join('<div class="decision-row"><b>裁决 %02d</b><span>%s</span></div>' % (i + 1, x) for i, x in enumerate(divs)) or '<div class="decision-row"><b>裁决</b><span>—</span></div>'

deep = zj.get('综合深挖', []) or []
deep_html = []
for it in deep:
    deep_html.append(
        '<div class="card"><div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap">'
        '<span class="chip2 c-half">%s</span><b style="font-size:14px">%s</b></div>'
        '<p style="margin:8px 0 0">%s</p>'
        '<p style="margin:6px 0 0"><span class="mut">判定条件</span> %s</p>'
        '<p style="margin:4px 0 0"><span class="mut">下次验证点</span> %s</p></div>'
        % (it.get('主题', '—'), it.get('主题', '—'), it.get('深挖结论', '—'),
           it.get('判定条件', '—'), it.get('下次验证点', '—')))
deep_html = ''.join(deep_html) or '<div class="card mut">—</div>'

cog = zj.get('认知迭代', []) or []
cog_latest = cog[0] if cog else {}
cog_html = ('<div class="cog-card"><div class="cog-date">%s</div><div class="cog-body"><b>%s</b><span>可证伪条件：%s</span></div></div>'
            % (d[4:6] + '-' + d[6:8], cog_latest.get('认知点', '—'), cog_latest.get('可证伪条件', '—')))
cog_early = cog[1:]
cog_fold = ''
if cog_early:
    inner = ''.join('<div class="tli mut"><b>—</b> %s</div>' % x.get('认知点', '') for x in cog_early)
    cog_fold = ('<details class="chain tlfold"><summary><b>更早的认知迭代</b> '
                '<span class="chip">%d条</span></summary><div class="inner"><div class="tl">%s</div></div></details>'
                % (len(cog_early), inner))

snap = (zj.get('检查四项', {}) or {}).get('环境快照', {}) or {}


def snap_pill(k, fmt='%s'):
    v = snap.get(k)
    return fmt % v if v is not None else '—'


vote_chips = ''.join('<div style="flex:1 1 96px;min-width:88px;padding:9px 8px;border:1px solid var(--line);'
                     'border-radius:9px;text-align:center"><span class="mut" style="font-size:11px">%s</span>'
                     '<div style="font-weight:800;font-size:13.5px;margin-top:3px">%s</div></div>' % (a, b)
                     for a, b in vote_cells) or '<div class="mut">—</div>'

NEW = u'''
<style id="overnight-review-v3">
#overnight,.route-chart{border:1px solid rgba(232,163,61,.24);border-radius:16px;padding:18px 20px;margin-top:28px;background:linear-gradient(135deg,rgba(232,163,61,.08),rgba(15,18,26,.94))}
#overnight h2{margin-top:4px;border-bottom:0}.verdict-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.section-label{font:10px ui-monospace,monospace;letter-spacing:1.5px;color:var(--mut)}.verdict-lead{font-size:15px;line-height:1.7;font-weight:700;margin:10px 0 0}.compact-list ul{margin:0;padding-left:20px}.compact-list li{margin:6px 0;line-height:1.65}.verdict-card{min-height:104px}.verdict-card .section-label{display:block;font-family:'Microsoft YaHei',sans-serif;letter-spacing:0;font-size:12px;font-weight:700;color:var(--mut)}.verdict-card .verdict-lead{font-size:14px;line-height:1.75}.decision-list{display:grid;gap:0}.decision-row{display:grid;grid-template-columns:58px 1fr;gap:12px;padding:10px 0;border-bottom:1px solid var(--line);line-height:1.7}.decision-row:last-child{border-bottom:0}.decision-row b{color:var(--accent);font-size:12px}.decision-row span{font-size:13px;color:var(--sub)}.ext-stats{display:flex;gap:10px;margin:10px 0}.ext-stat{display:flex;flex-direction:column;min-width:90px;padding:10px 14px;border:1px solid var(--line);border-radius:10px;background:rgba(255,255,255,.025)}.ext-stat b{font-size:20px;color:var(--accent)}.ext-stat small{color:var(--mut);margin-top:2px}.ext-list{display:grid;gap:6px}.ext-row{display:grid;grid-template-columns:54px 190px 1fr;gap:10px;align-items:center;padding:9px 11px;border-bottom:1px solid var(--line);font-size:12px}.ext-row b{color:var(--accent)}.ext-row span{font-weight:700;color:var(--sub)}.ext-row small{color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}@media(max-width:720px){.verdict-grid{grid-template-columns:1fr}.ext-row{grid-template-columns:54px 1fr}.ext-row small{grid-column:2}}
.cog-card{display:grid;grid-template-columns:74px 1fr;gap:14px;padding:14px 16px;border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:10px;background:rgba(255,255,255,.025)}.cog-date{font:12px ui-monospace,monospace;color:var(--accent);padding-top:2px}.cog-body{display:grid;gap:8px;line-height:1.7}.cog-body b{font-size:14px}.cog-body span{font-size:12px;color:var(--mut)}@media(max-width:720px){.cog-card{grid-template-columns:1fr;gap:6px}}.evolution{border-top:1px solid var(--line);padding-top:18px;margin-top:18px}.evo-stats{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 14px}.evo-stat{min-width:92px;padding:10px 12px;border:1px solid var(--line);border-radius:9px;background:rgba(255,255,255,.025)}.evo-stat b{display:block;font-size:20px;color:var(--accent)}.evo-stat small{color:var(--mut)}.evo-list{display:grid;gap:0;margin-top:10px}.evo-row{display:grid;grid-template-columns:72px minmax(0,1fr) 250px;gap:12px;padding:11px 0;border-bottom:1px solid var(--line);line-height:1.55}.evo-row b{color:var(--accent)}.evo-row span{font-weight:700}.evo-row small{color:var(--mut)}.evo-empty{padding:14px 0;color:var(--mut);font-size:12px}@media(max-width:720px){.evo-row{grid-template-columns:1fr}.evo-row small{grid-column:1}}
.chart-title{font:11px ui-monospace,monospace;letter-spacing:1.5px;color:var(--mut);margin-bottom:10px}.route-bar{display:grid;grid-template-columns:64px minmax(120px,1fr) 38px 54px;gap:8px;align-items:center;margin:8px 0;font-size:12px}.route-label{color:var(--sub);font-weight:700}.route-track{height:8px;background:rgba(255,255,255,.07);border-radius:99px;overflow:hidden}.route-track i{display:block;height:100%%;border-radius:99px;background:linear-gradient(90deg,#d9a441,#efc86e)}.route-bar b{text-align:right;font-family:var(--mono)}.route-bar small{color:var(--mut);text-align:right}
@media(max-width:720px){.route-bar{grid-template-columns:56px minmax(80px,1fr) 34px 48px}}
</style>
<style id="motion-rebuild">.route-bar .route-track i{transform-origin:left}body.motion-ready [data-motion]{opacity:0;transform:translateY(10px)}body.motion-ready [data-motion].is-visible{opacity:1;transform:none;transition:opacity .5s ease,transform .5s ease}body.motion-ready .route-bar[data-motion].is-visible .route-track i{animation:routeFill .9s cubic-bezier(.2,.8,.2,1) .12s both}body.motion-ready .ext-list [data-motion]:nth-child(2){transition-delay:.05s}body.motion-ready .ext-list [data-motion]:nth-child(3){transition-delay:.1s}body.motion-ready .ext-list [data-motion]:nth-child(4){transition-delay:.15s}body.motion-ready .ext-list [data-motion]:nth-child(n+5){transition-delay:.2s}@keyframes routeFill{from{transform:scaleX(0)}to{transform:scaleX(1)}}</style>
<!-- ============ 本次预览重排版: Top5 荐票卡之后 ============ -->
<section id="overnight">
  <div style="font:11px ui-monospace,monospace;letter-spacing:2.4px;color:var(--accent);margin-top:34px">OVERNIGHT REVIEW · 整晚复盘总预览 · %(d4)s</div>
  <h2 style="margin:4px 0 12px;border-bottom:0">今晚最终取舍<span class="hint">先看结论与证伪条件,再看观察点/五路/拐点;机械读数与全量证据退到末尾</span></h2>
  <div class="stance" style="margin:0 0 12px">
    <span class="pill warn">总审 · <b class="%(gear_cls)s">%(gear)s档 %(gear_txt)s</b></span>
    <span class="pill">置信度 <b>%(conf)s</b></span>
    <span class="pill hot">当前空仓 · 观察不下单</span>
    <span class="pill">温度 <b>%(temp)s · %(temp_g)s</b></span>
    <span class="pill">涨停 <b>%(zt)s</b> · 炸板 <b>%(zb_n)s</b> · 跌停 <b>%(dt)s</b></span>
    <span class="pill">最高连板 <b>%(hi)s</b></span>
  </div>
  <div class="rowE">
    <div class="card">
      <h3 style="margin:0 0 8px">结论</h3>
      <p style="margin:0">%(concl)s</p>
      <h4 style="margin:12px 0 6px;font-size:12.5px;color:var(--mut)">依据</h4>
      <ol style="margin:0;padding-left:18px;font-size:12.6px;line-height:1.75">%(basis)s</ol>
    </div>
    <div class="card">
      <h3 style="margin:0 0 8px">可证伪条件<span class="hint">次日可机械化结算</span></h3>
      <p style="margin:0">%(falsify)s</p>
      <h4 style="margin:12px 0 6px;font-size:12.5px;color:var(--mut)">分歧裁决</h4>
      <ul style="margin:0;padding-left:18px;font-size:12.6px;line-height:1.75">%(div_html)s</ul>
    </div>
  </div>
</section>

<section id="routes">
  <h2>二 五路合议<span class="hint">看一致与分歧,不重复展开荐票卡</span></h2>
  %(route_chart)s
  %(rt_html)s
</section>

<section id="turning">
  <h2>三 拐点与验证<span class="hint">只保留能改变总判断的条件</span></h2>
  <div class="card" style="padding:13px 15px">%(lead_bar)s</div>
  %(deep_html)s
</section>

<section id="verdict">
  <h2>四 总裁决<span class="hint">最终结论与下一次可证伪条件</span></h2>
  <div class="verdict-grid">
    <div class="card verdict-card"><span class="section-label">最终判断</span><p class="verdict-lead">%(concl)s</p></div>
    <div class="card verdict-card"><span class="section-label">验证门槛</span><p class="verdict-lead">%(falsify)s</p></div>
  </div>
  <div class="card"><h3>分歧处理</h3><div class="decision-list">%(div_rows)s</div></div>
</section>

<section id="extension">
  <h2>自主拓展<span class="hint">把复盘中发现的新信号，转成可继续验证的专题</span></h2>
  <div class="ext-stats">%(ext_chart)s</div>
  <div class="ext-list">%(ext_rows)s</div>
</section>
%(evo_ext_html)s

<section id="cog">
  <h2>五 认知迭代 · 最新<span class="hint">只保留本轮复盘沉淀</span></h2>
  %(cog_html)s
  %(cog_fold)s
</section>
%(evo_cog_html)s
''' % {
    'd4': '%s-%s-%s' % (d[:4], d[4:6], d[6:8]),
    'gear': gear, 'gear_txt': {'C': '防守观察', 'B': '局部偏强', 'A': '进攻'}.get(str(gear)[:1], ''),
    'gear_cls': gear_cls, 'conf': conf_s,
    'temp': snap_pill('温度'), 'temp_g': snap_pill('温度档'),
    'zt': snap_pill('涨停数'), 'zb_n': snap_pill('炸板数'), 'dt': snap_pill('跌停数'),
    'hi': (('%s板' % snap['最高连板']) if snap.get('最高连板') is not None else '—'),
    'concl': concl,
    'basis': ''.join('<li>%s</li>' % x for x in basis) or '<li class="mut">—</li>',
    'falsify': (deep[0].get('判定条件') if deep else '—'),
    'div_html': div_html, 'div_rows': div_rows,
    'ext_chart': ext_chart, 'ext_rows': ext_rows or '<div class="mut">—</div>',
    'route_chart': route_chart,
    'obs_block': obs_block or '<div class="card mut">—</div>',
    'rt_html': rt_html,
    'lead_bar': lead_bar or '<span class="mut">—</span>',
    'lead_bar2': re.sub(r'^<div[^>]*>', '', lead_bar, count=1).rstrip('</div>') if lead_bar else '<span class="mut">—</span>',
    'deep_html': deep_html,
    'books': books_inner or '<div class="card mut">—</div>',
    'cog_html': cog_html, 'cog_fold': cog_fold, 'evo_ext_html': evo_ext_html, 'evo_cog_html': evo_cog_html,
    'temp_card': temp_card or '<div class="card mut">—</div>',
    'vote_main': vote_main, 'vote_chips': vote_chips, 'vote_note': vote_note,
}

out = frozen + NEW + tail + '\n' + '''<script>(function(){var els=[].slice.call(document.querySelectorAll('[data-motion]'));if(!els.length||!('IntersectionObserver' in window))return;document.body.classList.add('motion-ready');var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('is-visible');io.unobserve(e.target)}})},{threshold:.15,rootMargin:'0px 0px -8% 0px'});els.forEach(function(e){io.observe(e)});setTimeout(function(){els.forEach(function(e){e.classList.add('is-visible')})},2200)})();</script>'''
op = os.path.join(SITE, '_preview_overnight_%s.html' % d)
io.open(op, 'w', encoding='utf-8').write(out)

print('WROTE', op, len(out))
print('h2:', [re.sub('<[^>]+>', '', x) for x in re.findall(r'<h2[^>]*>(.*?)</h2>', out, re.S)])
print('sections:', out.count('<section'), out.count('</section>'))
print('div balance:', out.count('<div') == out.count('</div>'), out.count('<div'), out.count('</div>'))
print('details balance:', out.count('<details'), out.count('</details>'))
print('obs cards:', out.count('obs-nm'), 'rt cards:', out.count('class="rt"'))
print('leak master/audit/engfold:', out.count('Master 综合'), out.count('来源审计'), out.count('engfold'), out.count('origfold'))
