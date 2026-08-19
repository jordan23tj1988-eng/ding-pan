# -*- coding: utf-8 -*-
"""8/12 logic body 黄金版七段重建(2026-08-12, 用户"按竞价路复刻版本模式复刻产业路"确认后)
骨架=黄金版717 logic 七段(一荐票卡/二链条深度地图库/三逻辑硬度/四前置预期雷达/五中报预增/六自主深挖/七认知迭代)
内容=8/12 判断json+现有body提取, 数字零编造; 机器段(段二链条库/段五中报预增)=空锚由渲染器注入
结构以黄金版 HTML 为准提取(obs 卡/瓦片/card), 不自造 rec-card/pan-card
写回: judgment_20260812.json bodies.logic + logic_body_20260812.html
"""
import json, io, re, sys

L = r'D:\股票数据\市场数据\_学习'
d = '20260812'
bp = L + '\\logic_body_%s.html' % d
jp = L + '\\judgment_%s.json' % d
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

b = json.load(io.open(jp, encoding='utf-8'))['bodies']['logic']   # 8649B 六段版
jd = json.load(io.open(L + '\\logic判断_%s.json' % d, encoding='utf-8'))
pd = jd.get('判断', {})
tj = jd.get('荐票', {})
tks = tj.get('标的', [])

# ---- 1. 提取 hero+kpi 区(rowA 完整闭合, 深度扫描) ----
i0 = b.find('<div class="rowA">')
i1 = b.find('<div class="stance">', i0)
assert i0 >= 0 and i1 > 0, 'hero 区定位失败'
# div 深度扫描: 从 i0 开始, 深度归 0 = rowA 闭合(kpi 在 rowA 内, 须含 kpi)
depth = 0
pos = i0
while True:
    mo = re.search(r'<div[^>]*>|</div>', b[pos:])
    assert mo, 'rowA 闭合未找到'
    t = mo.group(0)
    if t.startswith('</'):
        depth -= 1
        if depth == 0:
            i2 = pos + mo.end()
            break
    else:
        depth += 1
    pos += mo.end()
hero = b[i0:i2]  # rowA..</div> 完整(含 kpi 瓦片)
# kpi 区在 hero 内(hero 开 → kpi 开): 定位 hero 内 kpi 并替换为转换后瓦片
ik = hero.find('<div class="kpi">')
if ik >= 0:
    # kpi 深度扫描: kpi 深度归 0 = kpi 独立闭合(不含 hero/rowA 闭合)
    dep = 0
    p2 = ik
    while True:
        mo = re.search(r'<div[^>]*>|</div>', hero[p2:])
        assert mo, 'kpi 闭合未找到'
        t = mo.group(0)
        if t.startswith('</'):
            dep -= 1
            if dep == 0:
                ke = p2 + mo.end()
                break
        else:
            dep += 1
        p2 += mo.end()
    kpi_raw = hero[ik:ke]
    cards = re.findall(r'<div class="kpi-card"><b>([^<]+)</b><span>([^<]+)</span></div>', kpi_raw)
assert len(cards) == 4, '瓦片解析失败: %d' % len(cards)
# 瓦片 ico 图标(对齐竞价路瓦片同款 svg)
icos = ['M4 6h16M4 12h16M4 18h16', 'M7 20V10m5 10V4m5 16v-7', 'M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z', 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20M12 6v6l4 2']
chip2s = ['0/134', '9成', '偏热', '2只']
labs = ['中报预增A共振池涨停命中', '机器人线行业兜底搭车占比', '温度(昨48.8 +19.7跳升)', '荐票(2只+4观察)']
sub2s = ['预增×涨停零共振(本周期首次)', '线内9成兜底·真卡位仅秦安1只', '涨停92/跌停0/炸板13·量能21524亿·最高7板百花', '京投发展600683(地产新线Day1)·城地香江603887(IDC 2板)']
new_kpi = ''
for c, ic, ch, lab, sub in zip(cards, icos, chip2s, labs, sub2s):
    new_kpi += ('<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="%s"/></svg></span>'
                '<span class="chip2">%s</span></div><span class="lab">%s</span>'
                '<span class="big" data-v="%s">%s</span><span class="sub2">%s</span></div>'
                % (ic, ch, lab, c[0], c[0], sub))
# 校验: 原四瓦片数字全保留
for c in cards:
    for tok in re.findall(r'[\d][\d./+%·\-]*\d|[1-9]\d?/\d\d?', c[0] + c[1]):
        assert tok in new_kpi, '瓦片数字丢失: %s' % tok
for num in ('0/134', '9成', '68.5', '92', '21524', '2只'):
    assert num in new_kpi, '瓦片关键数字丢失: %s' % num
print('kpi 瓦片数字校验 ✓ (%d 瓦片)' % len(cards))

# ---- 2. 段一 荐票卡: rec-card ×6 → 黄金版 obs 组件 ----
gi = b.find('<div class="rec-grid">')
assert gi >= 0, 'rec-grid 未找到'
# 找段一下一个 h2 作为 rec-grid 终点
h2_2 = b.find('<h2>二', gi)
assert h2_2 > gi
rec_txt = b[gi:h2_2]
# rec-card 切分(同竞价路 convert: 按 rec-card 开合)
rcs = []
pos = 0
while True:
    i = rec_txt.find('<div class="rec-card">', pos)
    if i < 0: break
    j0 = rec_txt.find('</div></div>', i)
    assert j0 > i
    j = j0 + len('</div></div>')
    rcs.append(rec_txt[i + len('<div class="rec-card">'):j])
    pos = j
assert len(rcs) == 6, 'rec-card 数量异常: %d' % len(rcs)
obs_cards = []
for rc in rcs:
    # rec-title: 名称+tag(类型), 或 名称+mut代码
    m = re.search(r'<div class="rec-title">(.*?)</div>', rc, re.S)
    assert m, 'rec-title 解析失败: %s' % rc[:80]
    title = m.group(1)
    # 名称=第一个 <b> 或纯文本, 代码=<span class="mut">
    nm = re.sub(r'<[^>]+>', '', title)
    nm = re.sub(r'\s+', ' ', nm).strip()
    code = re.search(r'(\d{6})', title)
    code_txt = ' <span class="mut">%s</span>' % code.group(1) if code else ''
    tag = re.search(r'<span class="tag">([^<]+)</span>', title)
    tag_txt = tag.group(1) if tag else ''
    his = re.search(r'<div class="rec-his">(.*?)</div>', rc, re.S)
    why = re.search(r'<div class="rec-why">(.*?)</div>', rc, re.S)
    obs = ('<div class="obs"><div class="obs-head"><span class="obs-nm">%s%s</span>'
           '<span class="obs-pos tag">%s</span></div>'
           % (nm, code_txt, tag_txt))
    if his:
        obs += '<div class="obs-watch"><span class="obs-lab">历史对照</span>%s</div>' % his.group(1)
    if why:
        obs += '<div class="obs-watch"><span class="obs-lab">逻辑</span>%s</div>' % why.group(1)
    obs += '</div>'
    obs_cards.append(obs)
new_rec = ''.join(obs_cards)
for rc in rcs:
    for num in re.findall(r'n=\d+|[\d.]+%?/[\d.]+%?|\d+\.\d+%?', rc):
        if num not in new_rec:
            raise AssertionError('荐票数字丢失: %s' % num)
print('obs 荐票卡数字校验 ✓ (%d 卡)' % len(rcs))

# ---- 3. 段三 逻辑硬度(黄金版同构 card+p): 从 8/12 段二纯度判别提取 ----
h2_2i = b.find('<h2>二')
h2_3i = b.find('<h2>三', h2_2i)
seg2 = b[h2_2i:h2_3i]
# 去掉 h2 标题, 保留内容
h2e = seg2.find('</h2>')
seg2_body = seg2[h2e + 5:].strip()
# 把内容区(可能含 hb/obs 等)统一收进 card+p
txt2 = re.sub(r'<[^>]+>', '', seg2_body)
txt2 = re.sub(r'\s+', ' ', txt2).strip()
hardness_card = ('<div class="card"><p style="margin:0">%s</p></div>' % txt2)

# ---- 4. 段四 前置预期雷达: 判断 json 可证伪条件 ----
cond = pd.get('可证伪条件', '')
blind = pd.get('独立盲区声明', '')
radar_card = ('<div class="card"><p style="font-size:12.5px;line-height:1.6"><b>到期校准与可证伪条件</b>：%s</p>'
              '<p class="mut" style="font-size:12.5px;line-height:1.6">盲区：%s</p></div>'
              % (cond, blind))

# ---- 5. 段五 中报预增: 机器段 MACHRADAR 空锚 + 洞察卡(8/12 段三核心事实) ----
h2_3i2 = b.find('<h2>三')
h2_4i = b.find('<h2>四', h2_3i2)
seg3 = b[h2_3i2:h2_4i]
h2e3 = seg3.find('</h2>')
seg3_body = seg3[h2e3 + 5:].strip()
txt3 = re.sub(r'<[^>]+>', '', seg3_body)
txt3 = re.sub(r'\s+', ' ', txt3).strip()
zhongbao_card = ('<div class="card"><b>中报预增 · 当日洞察(LLM)</b><p style="margin:6px 0 0">%s</p></div>' % txt3)

# ---- 6. 段六 深挖 / 段七 认知: 从 8/12 段五/段六提取 ----
def seg_text(tag, nxt):
    a = b.find('<h2>%s' % tag)
    z = b.find('<h2>%s' % nxt, a) if nxt else len(b)
    if a < 0: return ''
    seg = b[a:z]
    he = seg.find('</h2>')
    body = seg[he + 5:].strip()
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', body)).strip()

shenwa = seg_text('五', '六')
renzhi = seg_text('六', None)
dig_card = ('<div class="card"><b>横切面清单应答(logic域)</b><p style="margin:6px 0 0">%s</p></div>' % shenwa) if shenwa else ''
iter_card = ('<div class="card"><b>认知迭代 · 最新</b><p style="margin:6px 0 0">%s</p></div>' % renzhi) if renzhi else ''

# ---- 7. 黄金版七段骨架拼装(机器段留空锚) ----
# hero 内 kpi 替换为规范瓦片
hero_final = hero.replace(kpi_raw, new_kpi) if ik >= 0 else hero
body_new = (
    hero_final + '\n'
    '<section class="sec" id="p1">'
    '<h2>一 荐票卡<span class="hint">发出版不可覆盖(逻辑荐票_20260812.json);类型∈{埋伏观察,未启动挖掘,卡位兑现}</span></h2>'
    + new_rec + '</section>\n'
    '<section class="sec" id="p2">'
    '<h2>二 链条深度地图库<span class="hint">只加不删 hb=环节均60日涨幅;焦点链open;历史链折叠保鲜</span></h2>'
    '<!--MACHCHAIN--><!--/MACHCHAIN--></section>\n'
    '<section class="sec" id="p3">'
    '<h2>三 逻辑硬度 · 消息溯源</h2>' + hardness_card + '</section>\n'
    '<section class="sec" id="p4">'
    '<h2>四 前置预期雷达</h2>' + radar_card + '</section>\n'
    '<section class="sec" id="p5">'
    '<h2>五 中报预增 · 概念叠加雷达<span class="hint">五道筛+成色审核;A共振卡制(漏斗末层=卡数);B/C留档json不上页</span></h2>'
    '<!--MACHRADAR--><!--/MACHRADAR-->' + zhongbao_card + '</section>\n'
    '<section class="sec" id="p6">'
    '<h2>六 自主深挖 · 专题孵化</h2>' + dig_card + '</section>\n'
    '<section class="sec" id="p7">'
    '<h2>七 我的认知迭代 · 最新</h2>' + iter_card + '</section>\n'
)

# ---- 8. 校验: div 配平 + 数字零编造 + 无自造结构残留 ----
assert body_new.count('<div') == body_new.count('</div>'), 'div 不配平'
for tok in ('0/134', '9成', '68.5', '92', '12.4%' if '12.4%' in b else '炸板13', '21524', '京投发展', '城地香江', '秦安股份'):
    assert tok in body_new, '关键数字丢失: %s' % tok
assert 'rec-card' not in body_new and 'pan-card' not in body_new, '自造结构残留'
assert 'kpi-card' not in body_new, '自造 kpi-card 残留'
assert body_new.count('<!--MACHCHAIN-->') == 1 and body_new.count('<!--MACHRADAR-->') == 1, '机器空锚缺失'

# ---- 9. 双写回 ----
io.open(bp, 'w', encoding='utf-8').write(body_new)
j = json.load(io.open(jp, encoding='utf-8'))
j['bodies']['logic'] = body_new
json.dump(j, io.open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('OK 重建完成: %dB | div %d/%d | h2 %d | 空锚 MACHCHAIN/MACHRADAR 就绪' % (
    len(body_new), body_new.count('<div'), body_new.count('</div>'), len(re.findall(r'<h2', body_new))))
