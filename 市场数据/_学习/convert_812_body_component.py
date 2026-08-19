# -*- coding: utf-8 -*-
"""8/12 auction body 组件化改造(2026-08-12, 用户"组件都哪去了"后)
rec-card → .obs 组件(黄金版同构: obs-head/obs-nm/obs-pos tag/obs-watch+obs-lab)
kpi-card → 规范#17 瓦片(黄金版同构: top/ico svg/chip2/lab/big data-v/sub2)
铁律: 只换结构, 数字/判断内容逐字保留(零编造); judgment bodies.auction 与 body 文件同步改
"""
import io, json, re, os

L = r'D:\股票数据\市场数据\_学习'
d = '20260812'
bp = os.path.join(L, 'auction_body_%s.html' % d)
jp = os.path.join(L, 'judgment_%s.json' % d)

b = json.load(io.open(jp, encoding='utf-8'))['bodies']['auction']  # ★judgment=管道注入truth(35.9KB), body文件只是子agent草稿

# ---- 1. kpi 区: kpi-card 四瓦片 → 规范瓦片(数字全保留) ----
old_kpi = re.search(r'<div class="kpi">.*?</div></div>\n?', b, re.S)
assert old_kpi, 'kpi 区未找到'
kpi_txt = old_kpi.group(0)
assert kpi_txt.count('kpi-card') == 4, 'kpi-card 数量异常: %d' % kpi_txt.count('kpi-card')
# 提取原四瓦片数字(防手滑改数: 全部从原文提取校验)
cards = re.findall(r'<div class="kpi-card"><b>([^<]+)</b><span>([^<]+)</span></div>', kpi_txt)
assert len(cards) == 4, '瓦片解析失败'
new_kpi = (
    '<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16"/></svg></span>'
    '<span class="chip2 c-hit">%s</span></div><span class="lab">昨池(%s)今日封板</span>'
    '<span class="big" data-v="%s">%s</span><span class="sub2">%s</span></div>'
    % ('6/10', '8/11', '7', cards[0][0], '胜率6/10 · 均收+3.28%'))
new_kpi += (
    '<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M7 20V10m5 10V4m5 16v-7"/></svg></span>'
    '<span class="chip2 c-acc">+2.49pp</span></div><span class="lab">昨池闸门内均收(高开&lt;5%%)</span>'
    '<span class="big" data-v="5.77" data-dec="2">+5.77%%</span><span class="sub2">vs 全池+3.28%% · 增益+2.49pp</span></div>')
new_kpi += (
    '<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z"/></svg></span>'
    '<span class="chip2 c-half">偏热</span></div><span class="lab">竞价温度(昨48.8 +19.7跳升)</span>'
    '<span class="big" data-v="68.5" data-dec="1">68.5</span><span class="sub2">未触85过热线 · 量能21524亿</span></div>')
new_kpi += (
    '<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20M12 6v6l4 2"/></svg></span>'
    '<span class="chip2 c-hit">69%%</span></div><span class="lab">今日早盘首封(≤09:31)</span>'
    '<span class="big" data-v="13">13只</span><span class="sub2">09:25首封9只占69%% · 炸板率12.4%%</span></div>')
# 校验: 新 kpi 必须含原全部数字 token(原句被拆 lab/sub2, 逐数字核对)
for src in cards:
    for tok in re.findall(r'[\d][\d./+%·\-]*\d|[1-9]\d?/\d\d?|\+?[\d.]+%?', src[0] + src[1]):
        tok2 = tok.replace('·', ' · ')
        assert tok in new_kpi or tok2 in new_kpi, '数字丢失: %s' % tok
for num in ('+5.77%', '+3.28%', '+2.49pp', '68.5', '48.8', '21524', '12.4%', '69%'):
    assert num in new_kpi, '数字丢失: %s' % num
print('kpi 瓦片数字校验 ✓')

# ---- 2. rec-grid 区: rec-card ×6 → obs 组件 ----
gi = b.find('<div class="rec-grid">')
assert gi >= 0, 'rec-grid 未找到'
gn_i = b.find('<div class="gate-note">', gi)
assert gn_i > gi
rec_txt = b[gi:gn_i]
rcs = re.findall(r'<div class="rec-card">(.*?)</div></div>', rec_txt, re.S)
# 用更稳的切分: 按 rec-card 开合
rcs = []
pos = 0
while True:
    i = rec_txt.find('<div class="rec-card">', pos)
    if i < 0: break
    j0 = rec_txt.find('</div></div>', i)
    assert j0 > i
    j = j0 + len('</div></div>')  # 闭合包含进 rc, 否则 rec-why 正文后无 </div> 可匹配
    rcs.append(rec_txt[i + len('<div class="rec-card">'):j])
    pos = j
assert len(rcs) == 6, 'rec-card 数量异常: %d' % len(rcs)
obs_cards = []
for rc in rcs:
    m = re.match(r'<div class="rec-title">([^<]+)<span class="tag">([^<]+)</span></div>(.*)', rc, re.S)
    assert m, 'rec-title 解析失败: %s' % rc[:80]
    nm, tag, rest = m.group(1), m.group(2), m.group(3)
    his = re.search(r'<div class="rec-his">(.*?)</div>', rest, re.S)
    why = re.search(r'<div class="rec-why">(.*?)</div>', rest, re.S)
    obs = ('<div class="obs"><div class="obs-head"><span class="obs-nm">%s</span>'
           '<span class="obs-pos tag">%s</span></div>'
           % (nm, tag))
    if his:
        obs += '<div class="obs-watch"><span class="obs-lab">历史对照</span>%s</div>' % his.group(1)
    if why:
        obs += '<div class="obs-watch"><span class="obs-lab">理由</span>%s</div>' % why.group(1)
    obs += '</div>'
    obs_cards.append(obs)
new_rec = ''.join(obs_cards)
print('DEBUG obs_cards[0]完整: %s' % obs_cards[0])
# 数字校验: 6 卡原数字全保留
for rc in rcs:
    for num in re.findall(r'[\d.]+%?/[\d.]+%?|\d+\.\d+%?|n=\d+', rc):
        if num not in new_rec:
            print('丢失数字 %r | 全new_rec含6/6: %s | 附近: %r' % (num, '6/6' in new_rec, new_rec[max(0,new_rec.find('6/6')-60):new_rec.find('6/6')+60] if '6/6' in new_rec else ''))
            raise AssertionError('荐票数字丢失: %s' % num)
print('obs 荐票卡数字校验 ✓ (6卡)')

# ---- 3. 写回 ----
new_body = b.replace(kpi_txt, new_kpi).replace(rec_txt, new_rec)
assert new_body != b
assert new_body.count('<div') == new_body.count('</div>'), 'div 配平破坏'
# div 配平细查
print('div 配平: %d/%d ✓' % (new_body.count('<div'), new_body.count('</div>')))
for f, content in ((bp, new_body), (jp, None)):
    if content is None:
        j = json.load(io.open(jp, encoding='utf-8'))
        j['bodies']['auction'] = new_body
        json.dump(j, io.open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('已写回 judgment:', jp)
    else:
        io.open(f, 'w', encoding='utf-8').write(content)
        print('已写回 body:', f)
print('完成: 8/12 body 组件化(kpi瓦片×4 + obs荐票卡×6)')
