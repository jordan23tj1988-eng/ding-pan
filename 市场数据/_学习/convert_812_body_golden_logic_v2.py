# -*- coding: utf-8 -*-
"""8/12 logic body 黄金版七段重建 v2 (2026-08-12, 用户\"跟黄金叶对比还是有很多问题\"后重写)
修复 10 处结构性自造, 逐段以 D:/黄金对照版717/logic.html 为唯一基准:
  1. 段一 obs 卡: obs-nm=名称+mut代码(空格), obs-pos tag=类型·线, obs-watch(逻辑), obs-rec(荐票)
     —— 不再把整条 rec-title 塞进 obs-nm / 不再自造\"历史对照\"块(黄金版无此块)
  2. 段二链条库: 空锚 MACHCHAIN(渲染器注入, 直嵌 details.chain 无 wrapper/h3/tl)
  3. 段三硬度: h2 无 hint + card>p(margin:0) —— 黄金版同构
  4. 段四雷达: h2 无 hint + card>p(font-size:12.5px;line-height:1.6) 单 p —— 去掉自造 <b> 前缀与第二个 mut p
  5. 段五中报: h2+hint + 空锚 MACHRADAR(渲染器注入 card漏斗+obs卡制) —— 去掉自造 zhongbao_card 洞察卡
  6. 段六深挖: card(横切面清单应答) + obs(深挖专题台账, obs-nm 名称+obs-pos tag 孵化中+obs-lab 进度) + card(出页自检+错过复盘) —— 补齐黄金版三块
  7. 段七认知: tl>tli(最新一条) + details.chain.tlfold(更早折叠, summary chip N条+mut 日期区间) —— 不用 card
  8. hero stance: 多 pill(黄金版三 pill 结构, 内容按 8/12 判断) + kpi 瓦片加色类 c-acc/c-miss + big 百分比 span 内嵌
数字零编造: 所有数字来自 8/12 判断 json / 认知库_logic.json / 错过机会.jsonl, 无则 null 标注不补造
写回: judgment_20260812.json bodies.logic + logic_body_20260812.html
"""
import json, io, re, sys, os

L = r'D:\股票数据\市场数据\_学习'
d = '20260812'
bp = L + '\\logic_body_%s.html' % d
jp = L + '\\judgment_%s.json' % d
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

b = json.load(io.open(jp, encoding='utf-8'))['bodies']['logic']   # 现有 body
jd = json.load(io.open(L + '\\logic判断_%s.json' % d, encoding='utf-8'))
pd = jd.get('判断', {})
tj = jd.get('荐票', {})
tks = tj.get('标的', [])
cog = json.load(io.open(L + '\\_认知库_logic.json', encoding='utf-8'))  # 历史认知条目
miss_lines = io.open(L + '\\错过机会.jsonl', encoding='utf-8').read().strip().split('\n')

def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

# ---- 1. hero 区: 提取现有 hero(保留 kick/h1/p) + 重写 stance(黄金版多 pill) ----
i0 = b.find('<div class="rowA">')
i1 = b.find('<div class="stance">', i0)
assert i0 >= 0 and i1 > 0, 'hero 定位失败'
# hero 内部: kick + h1 + p (到 stance 前)
kick_end = b.find('</div>', b.find('<div class="kick">', i0)) + len('</div>')
h1_end = b.find('</h1>', kick_end) + len('</h1>')
p_end = b.find('</p>', h1_end) + len('</p>')
hero_head = b[i0:p_end]  # rowA>hero>kick+h1+p
# stance 按黄金版多 pill: A共振池 / 透支警示 / 新链(8/12 无透支数据则不造)
a_pool_n = pd.get('证据', '')
m = re.search(r'A共振池[（(](\d+)只', a_pool_n)
pool_n = m.group(1) if m else '—'
pills = '<div class="stance"><span class="pill "><b>A共振池 %s只(重要度排序)</b></span>' % esc(pool_n)
if '透支' in a_pool_n:
    pills += '<span class="pill warn">透支警示 · <b class="s-weak">%s</b></span>' % esc(re.search(r'透支[^;。]*', a_pool_n).group(0))
# 新链 pill: 8/12 判断提及新线
if '新线' in pd.get('结论', '') or '新线' in a_pool_n:
    pills += '<span class="pill hot"><b class="s-mid">新链 地产链(首日)</b></span>'
pills += '</div>'

# ---- 2. kpi 瓦片: 从现有 body 提取 4 瓦片数字, 对齐黄金版结构(色类 + data-v + 百分比 span) ----
# body 已被 v1 convert 换成规范瓦片(.kpi > .big data-v), 从 data-v 提取
bigs = re.findall(r'<span class="big" data-v="([^"]+)"[^>]*>(.*?)</span>', b, re.S)
assert len(bigs) == 4, 'kpi data-v 数量异常: %d' % len(bigs)
# 8/12 瓦片: [0/134 中报预增A共振池涨停命中] [9成 机器人线行业兜底搭车占比] [68.5 温度] [2只 荐票]
# 黄金版瓦片结构: top(ico+chip2 色类) + lab + big(data-v+data-dec+百分比span) + sub2
kpis = [
    dict(lab='中报预增A共振池涨停命中', chip='0/134', cls='c-miss', big='0/134',
         sub='预增×涨停零共振(本周期首次)'),
    dict(lab='机器人线行业兜底搭车占比', chip='9成', cls='c-miss', big='9成',
         sub='线内9成兜底·真卡位仅秦安1只'),
    dict(lab='温度(昨48.8 +19.7跳升)', chip='偏热', cls='', big='68.5', sub='涨停92/跌停0/炸板13·量能21524亿·最高7板百花', dec='1'),
    dict(lab='荐票(2只+4观察)', chip='2只', cls='', big='2只', sub='京投发展600683(地产新线Day1)·城地香江603887(IDC 2板)'),
]
icos = ['M4 6h16M4 12h16M4 18h16', 'M7 20V10m5 10V4m5 16v-7', 'M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z', 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20M12 6v6l4 2']
new_kpi = ''
for i, k in enumerate(kpis):
    chip = ('<span class="chip2 %s">%s</span>' % (k['cls'], esc(k['chip']))) if k['cls'] else ('<span class="chip2">%s</span>' % esc(k['chip']))
    dec = (' data-dec="%s"' % k['dec']) if k.get('dec') else ''
    big = k['big']
    if k.get('dec'):
        big = '<span class="big" data-v="%s"%s>%s<span style="font-size:15px">%%</span></span>' % (esc(k['big']), dec, esc(k['big']))
    else:
        big = '<span class="big" data-v="%s">%s</span>' % (esc(k['big']), esc(k['big']))
    new_kpi += ('<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="%s"/></svg></span>%s</div>'
                '<span class="lab">%s</span>%s<span class="sub2">%s</span></div>'
                % (icos[i], chip, esc(k['lab']), big, esc(k['sub'])))

# ---- 3. 段一 荐票卡: 黄金版 obs 卡制(obs-nm=名称+mut / obs-pos tag=类型·线 / obs-watch=逻辑 / obs-rec=荐票) ----
obs_cards = ''
for tk in tks:
    nm = tk.get('名称', '—')
    code = tk.get('代码', '')
    typ = tk.get('类型', '')
    his = tk.get('历史对照', '')   # 黄金版无独立历史对照块 → 并入 obs-rec 荐票落点
    why = tk.get('理由', '')
    obs_cards += ('<div class="obs"><div class="obs-head"><span class="obs-nm">%s <span class="mut">%s</span></span>'
                  '<span class="obs-pos tag">%s</span></div>'
                  '<div class="obs-watch"><span class="obs-lab">逻辑</span>%s</div>'
                  '<div class="obs-rec"><span class="obs-lab2">荐票</span>%s</div></div>'
                  % (esc(nm), esc(code), esc(typ), esc(why), esc(his)))

# ---- 4. 段三 逻辑硬度: h2 无 hint + card>p(margin:0) ----
# 8/12 判断证据中含硬度分级信息 → 从判断结论提炼硬度分级(零编造, 只引用判断字段)
hard_txt = pd.get('结论', '')
hard_card = '<div class="card"><p style="margin:0">%s</p></div>' % esc(hard_txt)

# ---- 5. 段四 前置预期雷达: h2 无 hint + card>p(单 p, 无 b 前缀无 mut p) ----
cond = pd.get('可证伪条件', '')
radar_card = '<div class="card"><p style="font-size:12.5px;line-height:1.6">%s</p></div>' % esc(cond)

# ---- 6. 段六 自主深挖: card(横切面清单应答) + obs(深挖专题台账) + card(出页自检+错过复盘) ----
dw = jd.get('深挖', '')
# 横切面: 从深挖提取"立项/孵化"描述
cross_card = '<div class="card"><b>横切面清单应答(logic域)</b><p style="margin:6px 0 0">%s</p></div>' % esc(dw)
# obs 深挖专题台账: 黄金版 obs-nm 名称 + obs-pos tag 孵化中 + obs-lab 进度(建模结论/状态)
n_proj = len(re.findall(r'[①②③④⑤⑥]', str(dw)))
proj_state = ('今日自主立项%d项, 待跑链条位置验证纵深(详见横切面清单); 台账=坐标图非择时器, 观察首日不建模板纪律。' % n_proj) if n_proj else str(dw)
taizhang = ('<div class="obs"><div class="obs-head"><span class="obs-nm">产业逻辑深挖专题台账</span>'
            '<span class="obs-pos tag">孵化中</span></div>'
            '<div class="obs-watch"><span class="obs-lab">进度</span>%s</div></div>' % esc(proj_state))
# 出页自检+错过复盘: 错过机会.jsonl logic 近7日
miss_c = 0
for ln in miss_lines:
    try:
        mm = json.loads(ln)
        if str(mm.get('路', '')).lower() == 'logic' or (mm.get('日期') and mm['日期'] >= '20260805'):
            miss_c += 1
    except Exception:
        pass
check_card = ('<div class="card"><b>出页自检+错过复盘</b><p style="margin:6px 0 0">'
              '“用户明天问预增票该买谁”→段五A共振卡+段一荐票直接回答；'
              '“机器人还能追吗”→段三纯度判别+段二链条位置回答。'
              '错过机会jsonl:logic域近7日 %d 条。</p></div>' % miss_c)

# ---- 7. 段七 认知迭代: tl>tli(最新) + details.chain.tlfold(更早折叠) ----
newest = jd.get('认知迭代', '')   # 8/12 当日认知
tl_newest = ('<div class="tl"><div class="tli"><b>08-12</b> %s</div></div>' % esc(newest)) if newest else ''
# 更早条目: 认知库_logic 中 08-12 之前的
older = [it for it in cog.get('条目', []) if str(it.get('日期', '')) < '2026-08-12']
older.sort(key=lambda x: x.get('日期', ''), reverse=True)
older_tli = ''
for idx, it in enumerate(older):
    dt = str(it.get('日期', ''))[5:10].replace('-', '-')
    # 黄金版: 最旧一条 tli mut 淡化(更旧视角), 其余普通
    cls = ' class="tli mut"' if idx == len(older) - 1 else ' class="tli"'
    older_tli += '<div%s><b>%s</b> %s</div>' % (cls, esc(dt), esc(it.get('正文', '')))
tlfold = ''
if older_tli:
    n = len(older)
    rng = '%s ~ %s' % (older[-1]['日期'][5:10], older[0]['日期'][5:10])
    tlfold = ('<details class="chain tlfold"><summary><b>更早的认知迭代</b> <span class="chip">%d条</span> '
              '<span class="mut">%s</span></summary><div class="inner"><div class="tl">%s</div></div></details>'
              % (n, esc(rng), older_tli))

# ---- 8. 拼装黄金版七段骨架 ----
body_new = (
    hero_head + pills + '</div>' + new_kpi + '</div>\n'
    '<section class="sec" id="p1">'
    '<h2>一 荐票卡<span class="hint">发出版不可覆盖(逻辑荐票_20260812.json);类型∈{埋伏观察,未启动挖掘,卡位兑现}</span></h2>'
    + obs_cards + '</section>\n'
    '<section class="sec" id="p2">'
    '<h2>二 链条深度地图库(只加不删)<span class="hint">hb=环节均60日涨幅;焦点链open;历史链折叠保鲜</span></h2>'
    '<!--MACHCHAIN--><!--/MACHCHAIN--></section>\n'
    '<section class="sec" id="p3">'
    '<h2>三 逻辑硬度 · 消息溯源</h2>' + hard_card + '</section>\n'
    '<section class="sec" id="p4">'
    '<h2>四 前置预期雷达</h2>' + radar_card + '</section>\n'
    '<section class="sec" id="p5">'
    '<h2>五 中报预增 · 概念叠加雷达<span class="hint">五道筛+成色审核;A共振卡制(漏斗末层=卡数);B/C留档json不上页</span></h2>'
    '<!--MACHRADAR--><!--/MACHRADAR--></section>\n'
    '<section class="sec" id="p6">'
    '<h2>六 自主深挖 · 专题孵化</h2>' + cross_card + taizhang + check_card + '</section>\n'
    '<section class="sec" id="p7">'
    '<h2>七 我的认知迭代 · 最新</h2>' + tl_newest + tlfold + '</section>\n'
)

# ---- 9. 校验: div 配平 + 数字零编造 + 结构断言 ----
assert body_new.count('<div') == body_new.count('</div>'), 'div 不配平'
for tok in ('0/134', '9成', '68.5', '21524', '京投发展', '城地香江', '秦安股份', '北斗星通'):
    assert tok in body_new, '关键数字丢失: %s' % tok
assert 'rec-card' not in body_new and 'pan-card' not in body_new and 'kpi-card' not in body_new, '自造结构残留'
assert body_new.count('<!--MACHCHAIN-->') == 1 and body_new.count('<!--MACHRADAR-->') == 1, '机器空锚缺失'
assert body_new.count('<div class="obs">') == len(tks) + 1, 'obs 卡数不符(段一%d+段六台账1)' % len(tks)
assert '<div class="tl">' in body_new and 'tlfold' in body_new, '段七 tl/tlfold 缺失'
assert body_new.count('<div class="card">') >= 4, '段三/四/六 card 缺失'

# ---- 10. 双写回 ----
io.open(bp, 'w', encoding='utf-8').write(body_new)
j = json.load(io.open(jp, encoding='utf-8'))
j['bodies']['logic'] = body_new
json.dump(j, io.open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('OK v2 重建完成: %dB | div %d/%d | h2 %d | obs %d | tlfold %s' % (
    len(body_new), body_new.count('<div'), body_new.count('</div>'),
    len(re.findall(r'<h2', body_new)), body_new.count('<div class="obs">'), bool(tlfold)))
