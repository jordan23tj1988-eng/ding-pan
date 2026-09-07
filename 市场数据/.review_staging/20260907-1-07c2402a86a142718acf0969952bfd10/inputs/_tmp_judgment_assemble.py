# -*- coding: utf-8 -*-
"""组装 judgment_20260907.json 的完整 bodies（index/cycle 生成 + 五路 body 读入）"""
import json, os

L = r"D:\股票数据\市场数据\_学习"
D = "20260907"

def rd(p):
    with open(p, encoding='utf-8') as f:
        return f.read()

def wj(p, o):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(o, f, ensure_ascii=False, indent=1)

zs = json.loads(rd(os.path.join(L, '总审_%s.json' % D)))
wl = zs['五路裁决']
zj = zs['总裁决']
jc = zs['检查四项']
sh = zs['综合深挖']
rz = zs['认知迭代']
xs = zs['线索跟踪']
zp = zs['指派清单']

ROUTE_META = {
    'auction': ('01 / 第1路', '竞价·时机'),
    'lhb': ('02 / 第2路', '龙虎榜·席位'),
    'theme': ('03 / 第3路', '主线·题材'),
    'logic': ('04 / 第4路', '产业·逻辑'),
    'limitup': ('05 / 第5路', '涨停·质量'),
}

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def grade_cls(g):
    return {'A': 's-hot', 'B': 's-mid', 'C': 's-weak'}.get(g, 's-weak')

# ---------------- ticker ----------------
tk_items = [
    '量能 <b class="a">1.95万亿</b>',
    '涨停 <b class="u">93</b> / 跌停 <b class="d">2</b>',
    '炸板 <b>19</b>·炸板率 <b>17%</b>',
    '最高板 <b class="u">6板</b>·龙版传媒',
    '梯队 6板1·3板3·2板9·1板80',
    '情绪温度 <b>59.6</b>(中性)',
    '一进二 <b>26.9%</b>·二进三 <b>33.3%</b>',
]
grp = ''.join('<span>%s</span>' % x for x in tk_items)
ticker = ('<div class="ticker"><div class="in">'
          '<div class="grp">%s</div>'
          '<div class="grp" aria-hidden="true">%s</div>'
          '</div></div>' % (grp, grp))

# ---------------- index body ----------------
def kpi_temp():
    return ('<div class="kpi"><div class="top"><span class="ico">🌡</span><span class="chip2 c-mid">温度</span></div>'
            '<span class="lab">情绪温度</span><span class="big">59.6</span>'
            '<span class="sub2">昨13.4 → <b>+46.2</b> · 中性</span>'
            '<div class="gauge"><div class="gv">59.6 <span class="mut">中性</span></div>'
            '<div class="gtrack"><i class="gmark" style="left:59.6%"></i></div>'
            '<div class="gl"><span>冰点</span><span>偏冷</span><span>中性</span><span>偏热</span><span>过热</span></div></div></div>')

def kpi_zt():
    return ('<div class="kpi"><div class="top"><span class="ico">🔥</span><span class="chip2 c-mid">涨停</span></div>'
            '<span class="lab">涨停/跌停</span><span class="big">93<small>/ 2</small></span>'
            '<span class="sub2">涨停93(昨39,+138%)·跌停2(昨9)·炸板19(17%)</span></div>')

def kpi_vol():
    return ('<div class="kpi"><div class="top"><span class="ico">💰</span><span class="chip2 c-mid">量能</span></div>'
            '<span class="lab">两市成交额</span><span class="big">1.95<small>T</small></span>'
            '<span class="sub2">19460亿(昨20307,-4.2%)·维持2万亿量级</span></div>')

def kpi_board():
    return ('<div class="kpi"><div class="top"><span class="ico">🏔</span><span class="chip2 c-mid">最高板</span></div>'
            '<span class="lab">连板高度</span><span class="big">6<small>板</small></span>'
            '<span class="sub2">龙版传媒6板·梯队6板1·3板3·2板9·1板80(4/5板断层)</span></div>')

hero = ('<div class="rowA"><div class="hero">'
        '<div class="kick">Index · 总判断 · 截至 09-07 收盘</div>'
        '<h1>冰点强反弹修复日 · 温度59.6中性 · 四路C档防守+logic业绩腿轻仓</h1>'
        '<p>情绪温度<b>59.6中性</b>(昨13.4冰点,+46.2强力反弹)，涨停93(昨39,+138%)/跌停2(昨9)/炸板率17%(昨55.2%大幅收敛)/封板率83%/最高6板(龙版传媒605577)但3板后断层/量能19460亿(昨20307)。昨日「冰点C档防守」被今日强反弹部分打脸(涨停39→93)，但四路仍防守空仓=炸板率17%仍&gt;10%封板质量未修复+主线PCB/元件宽9&lt;13门槛+高度6板孤立，唯一反向变量=logic业绩腿第8次验证机械兑现(0904中报预增A池163∩今日涨停93=6只≥3且沪电002463∈模板153)，<b>总裁决C档(置信78)</b>，logic业绩腿降级为沪电股份15%轻仓观察位，总仓≤15%。</p>'
        '<div class="stance"><span class="pill cold">C档·防守为主</span><span class="pill warn">炸板率17%·封板质量未修复</span><span class="pill hot">业绩腿第8次兑现·沪电轻仓15%</span></div></div>'
        + kpi_temp() + kpi_zt() + kpi_vol() + kpi_board() + '</div>')

# 一 总判断
card1 = ('<div class="card"><b>总裁决 · C档防守(置信78)</b><p class="mut" style="margin:4px 0 0">'
         + esc(zj['依据']) + '</p></div>')
card2 = ('<div class="card"><b>昨日战绩验收</b><p class="mut" style="margin:4px 0 0">'
         + esc(zs['总裁决']['昨日战绩验收']) + '</p></div>')
sec1 = '<h2>一 总判断</h2><div class="rowC">' + card1 + card2 + '</div>'

# 二 五路裁决
routes_html = []
for r, (num, name) in ROUTE_META.items():
    g = wl[r]['档位']
    conf = wl[r]['置信度']
    verdict = wl[r]['裁决']
    routes_html.append(
        '<a class="rt" href="%s.html"><span class="rtn">%s</span><span class="rtm">%s</span>'
        '<b class="rtt %s">%s·置信%d</b><span class="rtd">%s</span></a>'
        % (r, num, name, grade_cls(g), g, conf, esc(verdict)))
sec2 = '<h2>二 五路裁决</h2><div class="routes">' + ''.join(routes_html) + '</div>'

# 三 检查四项
jc_labels = [('① 矛盾捕获', jc['矛盾捕获']), ('② 趋同盲区', jc['趋同盲区']),
             ('③ 编造后视镜', jc['编造后视镜']), ('④ 打脸结算', jc['打脸结算'])]
sec3 = '<h2>三 检查四项</h2>' + ''.join(
    '<div class="card"><b>%s</b>%s</div>' % (k, esc(v)) for k, v in jc_labels)

# 四 总裁决 · 自主进化
sec4 = ('<h2>四 总裁决 · 自主进化</h2><div class="rowE"><div class="card">'
        '<b>总裁决 · %s档(置信%s)</b>%s</div>'
        '<div class="card"><b>环境加权依据</b><p class="mut" style="margin:4px 0 0">%s</p></div>'
        '<div class="card"><b>次日验证点</b><p class="mut" style="margin:4px 0 0">%s</p></div>'
        '</div>'
        % (zj['档位'], zj['置信度'], esc(zj['依据']),
           esc(zj['环境加权依据']), esc(zj['次日验证点'])))

# 五 深挖与线索
deep = sh[0]
sec5 = ('<h2>五 深挖与线索</h2>'
        '<div class="card"><b>综合深挖 · %s</b><p class="mut" style="margin:4px 0 0">%s</p>'
        '<p class="mut" style="margin:4px 0 0">判定条件: %s</p></div>' % (
            esc(deep['主题']), esc(deep['深挖结论']), esc(deep['判定条件'])))
xs_cards = ''.join('<div class="card"><b>%s · %s</b>%s · 判定: %s · %s</div>' % (
    esc(c['线索ID']), esc(c['来源路']), esc(c['内容']), esc(c['判定条件']), esc(c['状态'])) for c in xs)
sec5 += xs_cards

# 六 指派清单 · 认知迭代
zp_cards = ''.join('<div class="card"><b>%s · 指派给 %s</b>%s · 理由: %s · 截止%s(%s)</div>' % (
    esc(c['指派ID']), esc(c['指派给']), esc(c['深挖任务']), esc(c['理由']), esc(c['截止']), esc(c['状态'])) for c in zp)
tli = ''.join('<div class="tli"><div class="d">%s</div><div class="h">%s</div><div class="b">%s · 可证伪: %s</div></div>' % (
    D, esc(c['认知点']), esc(c['依据']), esc(c['可证伪条件'])) for c in rz)
sec6 = '<h2>六 指派清单 · 认知迭代</h2>' + zp_cards + tli

index_body = hero + sec1 + sec2 + sec3 + sec4 + sec5 + sec6

# ---------------- cycle body ----------------
cycle_hero = ('<div class="rowA"><div class="hero">'
              '<div class="kick">Cycle · 周期情绪 · 截至 09-07 收盘</div>'
              '<h1>冰点→启动 · 温度59.6中性 · 放量普涨修复</h1>'
              '<p>温度13.4(冰点)→59.6(中性)强力反弹(+46.2)，涨停39→93、炸板率55.2%→17%、跌停9→2、封板率44.8%→83%，冰点反弹第1日坐实。但修复质量未同步：炸板率17%仍&gt;10%中性阈值、一进二率26.9%中性、二进三率33.3%中等、主线PCB/元件宽9&lt;13门槛、最高6板龙版传媒(出版)高度孤立断层到3板。属「放量普涨修复、非结构性进攻」。</p>'
              '<div class="stance"><span class="pill mid">启动 · 冰点反弹第1日</span><span class="pill warn">炸板率17%·质量未同步修复</span><span class="pill">主线宽9&lt;13·未确立</span></div></div>'
              + kpi_temp() + kpi_zt() + kpi_vol() + kpi_board() + '</div>')

# 一 量能台阶
cy1 = ('<h2>一 量能台阶 · 我站在哪一阶</h2>'
       '<div class="card"><b>量能19460亿 · 2万亿量级站稳</b>'
       '<p class="mut" style="margin:4px 0 0">昨20307亿(-4.2%)，连续2日站稳2万亿；但今日涨停93(昨39)放量普涨，'
       '量价结构=放量反弹修复，非缩量退潮。封板总额85.1亿(昨26.69亿大幅回升)承接资金回流。'
       '米开量能台阶: 2万亿为中性量级，站稳2万亿+涨停放量=冰点反弹的流动性底确认。</p></div>')

# 二 先行指标
cy2 = ('<h2>二 先行指标 · 三窗触发器</h2>'
       '<div class="card"><b>晋级率 · 一进二26.9% · 二进三33.3% · 高度42.9%</b>'
       '<p class="mut" style="margin:4px 0 0">一进二26.9%(昨12.2%大幅回升但仍中性)、二进三33.3%(昨0%回升)、'
       '高度晋级率42.9%(6板1只封住)。晋级率较冰点大幅修复但未到进攻阈值(一进二≥40%才算强承接)。'
       '核按钮0%、溢价spot失败(数据缺口)。</p></div>')

# 三 情绪五阶段 · 五路周期投票
cy3 = ('<h2>三 情绪五阶段 · 五路周期投票</h2>'
       '<div class="stages"><div class="st"><b>冰点</b>13.4→</div><div class="st on"><b>启动</b>59.6中性</div>'
       '<div class="st"><b>发酵主升</b></div><div class="st"><b>高潮</b></div><div class="st"><b>退潮</b></div></div>'
       '<div class="card"><b>五路周期投票(20260907) · 主判「启动·平」</b>'
       '<p class="mut" style="margin:4px 0 0">主判: 启动·平(温度强反弹但封板质量未同步, 明日看炸板率&lt;15%+主线宽≥13)。'
       '五路: auction平(60)/lhb平(65)/theme平(70)/logic升(65,业绩腿信号)/limitup平(65)。'
       'tally: 当日无复议(反对路0, 加权反对份额0)。</p></div>')

# 四 连板梯队
cy4 = ('<h2>四 连板梯队</h2>'
       '<div class="ladbar">'
       '<div class="r"><span>6板</span><b>龙版传媒605577</b><i class="w" style="width:12%"></i>1只</div>'
       '<div class="r"><span>3板</span><b>百大集团等</b><i class="w" style="width:30%"></i>3只</div>'
       '<div class="r"><span>2板</span><b>二板加13</b><i class="w" style="width:55%"></i>9只</div>'
       '<div class="r"><span>1板</span><b>首板扩散</b><i class="w" style="width:100%"></i>80只</div>'
       '</div>'
       '<p class="mut" style="margin:4px 0 0">梯队6板1·3板3·2板9·1板80：6板高度孤立(出版宽3)，4/5板断层，'
       '连板梯队头重脚轻=高度龙与梯队脱节，接力资金集中在首板扩散。</p>')

# 五 攻防 · 仓位总开关
cy5 = ('<h2>五 攻防 · 仓位总开关</h2>'
       '<div class="posmeter"><div class="bar"><i class="p" style="width:15%"></i></div>'
       '<div class="pos-l"><span>防守</span><b>≤15%</b><span>进攻</span></div></div>'
       '<div class="card"><b>总仓≤15% · C档防守为主</b>'
       '<p class="mut" style="margin:4px 0 0">温度59.6中性但炸板率17%&gt;10%+主线未确立(PCB宽9&lt;13)，'
       '攻防档=防守为主；唯一进攻信号=logic业绩腿(沪电股份15%轻仓观察位)，由logic路交易计划承载。'
       '总仓上限15%，非全面进攻。</p></div>')

# 六 自主深挖
cy6 = ('<h2>六 自主深挖 · 指标与阈值孵化</h2>'
       '<div class="card"><b>封板率83% vs 炸板率17% 分化阈值</b>'
       '<p class="mut" style="margin:4px 0 0">今日封板率83.04%(昨44.8%大幅修复)但炸板率17%仍&gt;10%中性阈值，'
       '呈现「封得住但炸得多」的分化——首板扩散质量参差。孵化假设: 炸板率&lt;15%且封板率&gt;80%=质量修复确认阈值，'
       '待累计样本验证。</p></div>')

# 七 认知迭代
cy7 = ('<h2>七 我的认知迭代 · 最新</h2>'
       '<div class="tli"><div class="d">%s</div><div class="h">冰点强反弹≠进攻信号</div>'
       '<div class="b">温度13.4→59.6+46.2、涨停39→93放量普涨，但炸板率17%%&gt;10%%+主线宽9&lt;13+高度6板孤立，'
       '反弹修复的是流动性底而非封板质量与主线结构——「放量普涨修复」与「结构性进攻」是两回事，'
       '防守共识正确(四路C档)，仅logic业绩腿机械信号降级为轻仓。</div></div>'
       '<div class="tli"><div class="d">%s</div><div class="h">量能2万亿≠进攻，封板质量是先行</div>'
       '<div class="b">连续2日站稳2万亿但0904涨停缩量(44→39)是放量分歧，今日涨停放量(93)才是真修复；'
       '量能台阶判断须结合涨停方向与封板率，单看量能会误读。</div></div>' % (D, D))

cycle_body = cycle_hero + cy1 + cy2 + cy3 + cy4 + cy5 + cy6 + cy7

# ---------------- 组装 judgment ----------------
bodies = {'index': index_body, 'cycle': cycle_body}
for r in ROUTE_META:
    p = os.path.join(L, '%s_body_%s.html' % (r, D))
    bodies[r] = rd(p)

judgment = {
    'date': D,
    '更新label': '%s 复盘' % D,
    '一句话': '冰点强反弹修复日·温度59.6中性(昨13.4+46.2)·涨停39→93·炸板率55.2%→17%·封板率83%·最高6板龙版传媒(高度孤立断层到3板)·量能19460亿·四路C档防守+logic业绩腿第8次兑现(沪电002463∈模板153)·总裁决C档置信78·总仓≤15%',
    'ticker': ticker,
    'bodies': bodies,
    'archive_body': '',
}

wj(os.path.join(L, 'judgment_%s.json' % D), judgment)
print('judgment_%s.json 已组装: 7 bodies (index/cycle/auction/lhb/theme/logic/limitup)' % D)
for r in bodies:
    print('  %s: %d chars' % (r, len(bodies[r])))
print('一句话:', judgment['一句话'][:50], '...')
