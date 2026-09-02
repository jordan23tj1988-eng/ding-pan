# -*- coding: utf-8 -*-
import json, os

L = '_学习'
d = '20260901'
BASE = os.path.dirname(os.path.abspath(__file__))

def jload(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None

# ============ 数据 ============
TEMP = '63.1'        # 情绪温度
TEMP_PREV = '52.6'   # 昨温度
ZT = '83'            # 涨停
DT = '0'             # 跌停
ZB = '6'             # 炸板
ZB_RATE = '6.7%'     # 炸板率
FB_RATE = '93.3%'    # 封板率
MAXB = '7'           # 最高板
MAXB_NAME = '海鸥住工'
MAXB_CODE = '002084'
VOL = '2.03万亿'     # 量能
VOL_YI = '20334'     # 量能亿
VOL_PREV = '21310'   # 昨量能亿
LADDER = '7板1·6板2·4板1·3板5·2板9·1板65'
J12 = '18.4%'        # 一进二
J23 = '80.0%'        # 二进三
GJ = '63.6%'         # 高度晋级
J12_PREV = '12.5%'
J23_PREV = '25.0%'

# ============ 一句话 ============
one_sentence = ('回暖第1日：温度52.6→63.1(+10.5),炸板率25.4%→6.7%封板率93.3%重回80+,'
                '最高板6→7(海鸥住工)跌停11→0清零,但质量停滞第12日(执1max45.9%)+资金冷27分位+无主线第6日,'
                '总裁决C档防守+保留auction轻仓窄窗')

# ============ ticker ============
def grp():
    return ('<div class="grp">'
            '<span>量能 <b class="a">%s</b></span>'
            '<span>涨停 <b class="u">%s</b> / 跌停 <b class="d">%s</b></span>'
            '<span>炸板 <b>%s</b>·炸板率 <b>%s</b></span>'
            '<span>最高 <b class="u">%s板</b>·%s</span>'
            '<span>梯队 %s</span>'
            '<span>情绪温度 <b>%s</b>(中性)</span>'
            '<span>一进二 <b>%s</b>·二进三 <b>%s</b></span>'
            '</div>') % (VOL, ZT, DT, ZB, ZB_RATE, MAXB, MAXB_NAME, LADDER, TEMP, J12, J23)

ticker = ('<div class="ticker"><div class="in">' + grp()
          + '<div class="grp" aria-hidden="true">'
          + grp().replace('<div class="grp">', '', 1).replace('</div>', '', 1)
          + '</div></div></div>')

# ============ index body ============
# hero
index_hero = (
'<div class="rowA">\n'
'<div class="hero"><div class="kick">Index · 总判断 · 截至 2026-09-01 收盘</div>\n'
'<h1>回暖第1日：温度52.6→63.1升温+10.5、炸板率25.4%→6.7%大降、跌停11→0清零、最高板6→7海鸥住工、晋级率全面修复，但三维冷(质量停滞第12日+资金冷27分位+无主线第6日)，总裁决C档防守+保留auction轻仓窄窗</h1>\n'
'<p>温度52.6→63.1(+10.5，回暖第1日)；涨停88→83(-5)；跌停11→0(清零)；炸板率25.4%→6.7%(-18.7pp，封板率93.3%重回80%+)；最高板6→7(海鸥住工002084)；量能21310→20334亿(-4.6%缩量)。晋级率全面修复：一进二12.5%→18.4%、二进三25%→80%、高度晋级35.7%→63.6%。但资金面冷(资金温度42→27分位回落，封板总额91.4→78.2亿-14.4%、单票封单max4.59→3.53亿连续第3日下移)与质量面停滞(全池执1max45.9%<50%负期望第12日)均未跟进，无主线第6日。情绪暖×资金冷×质量停三维分裂=回暖第1日·中继分歧，非进攻启动。总裁决C档防守。</p>\n'
'<div class="stance"><span class="s-weak">总裁决 C档·防守</span><span class="s-mid">温度63.1中性·回暖第1日</span><span class="s-weak">⚠防守不加仓·不追高</span></div>\n'
'</div>\n')

# kpi
def kpi_ico(svg):
    return '<span class="ico"><svg width="18" height="18" viewBox="0 0 18 18">' + svg + '</svg></span>'

kpi_temp = ('<div class="kpi"><div class="top">'
    + kpi_ico('<circle cx="9" cy="9" r="7" fill="none" stroke="#5f6577" stroke-width="1.4"/><path d="M9 9L13.2 4.8" stroke="#e8a33d" stroke-width="1.4"/>')
    + '<span class="chip2 c-acc">升温</span></div>'
    + '<span class="lab">情绪温度</span><span class="big" data-v="63.1" data-dec="1">63.1</span>'
    + '<span class="sub2">昨52.6 → +10.5 升温</span>'
    + '<div class="gauge"><div class="gv">63.1 <span class="mut">中性</span></div>'
    + '<div class="gtrack"><i class="gmark" style="left:63.1%"></i></div>'
    + '<div class="gl"><span>冰点</span><span>偏冷</span><span>中性</span><span>偏热</span><span>过热</span></div></div></div>')

kpi_zt = ('<div class="kpi"><div class="top">'
    + kpi_ico('<path d="M4 14V9M9 14V5M14 14v-3" stroke="#5f6577" stroke-width="1.6" fill="none"/>')
    + '<span class="chip2 c-acc">跌停清零</span></div>'
    + '<span class="lab">涨停 / 跌停</span><span class="big" data-v="83">83</span>'
    + '<span class="sub2">跌停0 · 昨88/11</span></div>')

kpi_vol = ('<div class="kpi"><div class="top">'
    + kpi_ico('<path d="M3 12l4-4 3 2 5-6" stroke="#5f6577" stroke-width="1.6" fill="none"/>')
    + '<span class="chip2 c-half">缩量</span></div>'
    + '<span class="lab">两市量能</span><span class="big" data-v="2.03">2.03万亿</span>'
    + '<span class="sub2">昨21310亿 · -4.6%</span></div>')

kpi_max = ('<div class="kpi"><div class="top">'
    + kpi_ico('<rect x="3" y="7" width="3" height="7" rx="1" fill="#5f6577"/><rect x="7.5" y="3" width="3" height="11" rx="1" fill="#e8a33d"/><rect x="12" y="9" width="3" height="5" rx="1" fill="#5f6577"/>')
    + '<span class="chip2 c-acc">7板</span></div>'
    + '<span class="lab">最高板</span><span class="big" data-v="7">7板</span>'
    + '<span class="sub2">海鸥住工 · 6→7</span></div>')

index_rowA = index_hero + kpi_temp + '\n' + kpi_zt + '\n' + kpi_vol + '\n' + kpi_max + '\n</div>\n'

# 一 总判断
index_s1 = (
'<h2>一 总判断</h2>\n'
'<div class="rowC">\n'
'<div class="card"><b>总裁决 C档·防守 置信72</b><p class="mut" style="margin:4px 0 0">auction B62 / lhb C68 / theme B62 / logic C78 / limitup C74，3C+2B防守为主，真实无条件进攻=0。核心共识=温度63.1中性回暖第1日(+10.5)+炸板率6.7%极低(抛压枯竭)+跌停0清零+晋级率全面修复(一进二18.4%·二进三80%)，但三维冷(质量停滞第12日执1max45.9%+资金冷27分位+无主线第6日)未跟进=情绪暖×三维冷分裂市。仅auction保留轻仓窄窗(掌阅科技603533带闸门≤2成)，其余四路空仓。</p></div>\n'
'<div class="card"><b>五路裁决 3C+2B</b><p class="mut" style="margin:4px 0 0">竞价B62(回暖第1日轻仓进攻) · 席位C68(资金冷空仓) · 题材B62(低切观察不铺开) · 产逻C78(业绩静默空仓) · 质量C74(负期望第12日防守)。2B均为"观察/轻仓"级非进攻级，总审采信防守侧。</p></div>\n'
'<div class="card"><b>次日验证点(可证伪)</b><p class="mut" style="margin:4px 0 0">①若明日(20260902)一进二率回落跌破10%且涨停家数<75→回暖第1日=反抽一日游证伪；②若海鸥住工002084断板且无新7板接力→高标断层坐实；③若lhb资金温度仍<34分位且S档独立席位<3→资金冷延续；④若农业/种业宽度缩回≤5→低切反抽证伪。</p></div>\n'
'</div>\n')

# 二 五路裁决
index_s2 = (
'<h2>二 五路裁决</h2>\n'
'<div class="routes">\n'
'<a class="rt" href="auction.html"><span class="rtn">01 / 第一路</span><span class="rtm">竞价·时机</span><b class="rtt s-mid">保留·B</b><span class="rtd">B62 · B档·回暖第1日轻仓进攻(温度+10.5+炸板率6.7%+跌停0+晋级全面修复)，仅轻仓窄窗1荐掌阅科技603533带闸门≤2成</span></a>\n'
'<a class="rt" href="lhb.html"><span class="rtn">02 / 第二路</span><span class="rtm">龙虎榜·席位</span><b class="rtt s-weak">采纳·C</b><span class="rtd">C68 · C档·防守空仓(资金温度42→27分位回落+单日脉冲第三次坐实+S档同向率1/4瓦解)</span></a>\n'
'<a class="rt" href="theme.html"><span class="rtn">03 / 第三路</span><span class="rtm">主线·题材</span><b class="rtt s-mid">保留·B</b><span class="rtd">B62 · B档·观察不铺开(无主线第6日，农业/种业+消费/零售低切承接但均未过宽≥13门槛)3观察</span></a>\n'
'<a class="rt" href="logic.html"><span class="rtn">04 / 第四路</span><span class="rtm">产业逻辑</span><b class="rtt s-weak">采纳·C</b><span class="rtd">C78 · C档·防守空仓(业绩腿静默第4次+T-1交叉2只零模板背书+存储环节0涨停)</span></a>\n'
'<a class="rt" href="limitup.html"><span class="rtn">05 / 第五路</span><span class="rtm">涨停复盘</span><b class="rtt s-weak">采纳·C</b><span class="rtd">C74 · C档·防守(负期望第12日执1max45.9%<50%+封单max3.53亿连续第3日下移)</span></a>\n'
'</div>\n')

# 三 检查四项
index_s3 = (
'<h2>三 检查四项</h2>\n'
'<div class="rowC">\n'
'<div class="card"><b>A档编造</b><p class="mut" style="margin:4px 0 0">无。五路荐票标的(掌阅科技603533/海鸥住工002084/万向德农600371/新赛股份600540/国芳集团601086/欢瑞世纪000892/一鸣食品605179)全部∈当日zt_pool，理由含量化证据(同类历史n·胜率·均收)，无凭空编造标的或阈值。</p></div>\n'
'<div class="card"><b>后视镜</b><p class="mut" style="margin:4px 0 0">无。五路判断只用≤20260901收盘数据；可证伪条件均写明日(20260902)验证，无引用未发生数据。</p></div>\n'
'<div class="card"><b>趋同盲区</b><p class="mut" style="margin:4px 0 0">有分歧但无盲区：auction(回暖第1日可轻仓进攻)与limitup(负期望第12日防守)对"回暖成色"判断分歧，总审采信防守侧(三维冷未跟进，情绪暖不足以进攻)。</p></div>\n'
'<div class="card"><b>数据缺口</b><p class="mut" style="margin:4px 0 0">温度表跌停数=null(东财summary跌停0为准)；昨日涨停溢价=null(分时库缺T+1腿)；T+1结算(20260831荐票)因spot故障全部0/0=数据缺口如实标注，未伪装正常结算。</p></div>\n'
'</div>\n')

# 四 总裁决 · 自主进化
index_s4 = (
'<h2>四 总裁决 · 自主进化</h2>\n'
'<div class="rowC">\n'
'<div class="card"><b>总裁决 C档·防守 置信72</b><p class="mut" style="margin:4px 0 0">定性=回暖第1日·中继分歧(情绪暖×三维冷分裂市)。仓位=防守为主不加仓不追高，仅auction轻仓窄窗(掌阅科技603533带闸门≤2成)可尝试。升B三前提未满足前维持防守：①lhb资金温度≥34分位且S档独立席位≥3且≥半同向且荐票不转净卖；②limitup全池执1胜率max≥50%且命中≥3只；③任一题材线宽≥13且立4板+且开板≤0.45。</p></div>\n'
'<div class="card"><b>环境加权裁决</b><p class="mut" style="margin:4px 0 0">当前温度档=中性63.1，各路历史战绩n<10样本不足不参与环境加权，分歧处采信保守侧(防守)。</p></div>\n'
'<div class="card"><b>回填窗口标注</b><p class="mut" style="margin:4px 0 0">资金温度/席位分桶库=单牛市周期窗口；iwencai六项存档=仅近期窗口；引用回填数据已带窗口偏差标注。</p></div>\n'
'</div>\n')

# 五 深挖与线索
index_s5 = (
'<h2>五 深挖与线索</h2>\n'
'<div class="rowC">\n'
'<div class="card"><b>综合深挖</b><p class="mut" style="margin:4px 0 0">①资金温度单日脉冲第三次坐实(42→27分位回落)，机构/北向/量化三方回流昨日为脉冲非趋势，今日未续=资金面证伪"回流启动"；②农业/种业(宽8高6环比+300%)为机械定性退坡线反抽陷阱，消费/零售(宽6高3环比+500%)新线首日爆量但脚本口径存疑，均未过主线门槛；③封板总额78.2亿-14.4%+单票封单max3.53亿连续第3日下移=广撒网式承接退潮，非质量型接力。</p></div>\n'
'<div class="card"><b>线索跟踪</b><p class="mut" style="margin:4px 0 0">①海鸥住工002084(7板孤高，明日断板则高标断层坐实)；②掌阅科技603533(auction唯一荐票，竞价落区间则轻仓尝试)；③农业/种业宽度次日是否缩回(反抽一日游验证)；④lhb资金温度次日是否≥34分位(资金冷延续/回暖验证)。</p></div>\n'
'</div>\n')

# 六 指派清单 · 认知迭代
index_s6 = (
'<h2>六 指派清单 · 认知迭代</h2>\n'
'<div class="rowC">\n'
'<div class="card"><b>指派清单</b><p class="mut" style="margin:4px 0 0">承接Master指派：①auction路—明日竞价掌阅科技603533落区间[-3,3]则轻仓尝试，越界弃单；②theme路—明日核实农业/种业宽度(≥13立4板+→真发酵；≤5→反抽一日游)；③limitup路—明日核实全池执1胜率max是否≥50%(负期望第12日是否终结)；④lhb路—明日核实资金温度是否≥34分位且S档同向率；⑤logic路—明日核实业绩腿T-1交叉是否出现≥1只模板背书标的。</p></div>\n'
'<div class="card"><b>认知迭代(最新)</b><p class="mut" style="margin:4px 0 0">①回暖第1日≠进攻信号：温度+10.5/炸板率6.7%/跌停0/晋级全面修复是"抛压枯竭式修复"，三维冷(质量+资金+主线)未跟进前，情绪暖不足以升级进攻，维持防守；②资金温度单日脉冲(8/29首现42分位)连续三次坐实"回流"为假信号，脉冲后必回落，不再因单日脉冲翻多；③负期望第12日+无主线第6日的退潮中后段，回暖第1日次日大概率分化(涨停广度收缩/晋级率回落/高标断板)，不追回暖首日的扩散票。</p></div>\n'
'</div>\n')

index_body = index_rowA + index_s1 + index_s2 + index_s3 + index_s4 + index_s5 + index_s6

# ============ cycle body ============
cycle_hero = (
'<div class="rowA">\n'
'<div class="hero"><div class="kick">Cycle · 周期与情绪 · 截至 2026-09-01 收盘</div><h1>回暖第1日：温度63.1升温+10.5,量能20334亿缩量,<em>炸板率6.7%极致修复×封板率93.3%重回80+</em></h1><p>量能台阶→先行指标三窗→情绪五阶段(五路投票)→连板梯队→攻防总开关,五件事定仓位。</p><div class="stance"><span class="pill warn">C · 防守（温度63.1中性回暖第1日+量能缩量-4.6% · 全池负期望第12日 · 五路3C2B取保守C）</span><span class="pill warn">升B需三信号齐：一进二率>10%+全池执1max≥50%+主线宽≥13</span></div></div>\n'
'<div class="kpi"><div class="top"><span class="l">两市量能</span><span class="v">20334亿</span></div><span class="chip2 c-half">缩量</span><span class="sub2">昨21310亿 · -4.6%缩量</span></div>\n'
'<div class="kpi"><div class="top"><span class="l">情绪温度</span><span class="v">63.1</span></div><span class="chip2 c-acc">中性</span><span class="sub2">昨52.6 → +10.5 升温</span></div>\n'
'<div class="kpi"><div class="top"><span class="l">最高板</span><span class="v">7板</span></div><span class="chip2 c-half">海鸥住工</span><span class="sub2">家居用品/控制权变更 · 梯队7-6-6-4-3-2-1</span></div>\n'
'<div class="kpi"><div class="top"><span class="l">周期投票</span><span class="v">1升3降1平</span></div><span class="chip2 c-acc">修复回暖(降)</span><span class="sub2">主判=修复回暖·降 · 反对路auction偏乐观</span></div>\n'
'</div>\n')

# 一 量能台阶
cycle_s1 = (
'<h2>一 量能台阶 · 我站在哪一阶</h2>\n'
'<div class="steps">\n'
'<div class="step dim"><span class="sr">≥3.8</span><span class="sn">主升2确认<small>放量突破</small></span><span class="sd"></span></div>\n'
'<div class="step dim"><span class="sr">3.5~3.8</span><span class="sn">突破压力<small>需增量</small></span><span class="sd"></span></div>\n'
'<div class="step dim"><span class="sr">3.3~3.5</span><span class="sn">强修<small>量能承接</small></span><span class="sd"></span></div>\n'
'<div class="step dim"><span class="sr">3.0~3.3</span><span class="sn">过渡<small>量能中枢</small></span><span class="sd"></span></div>\n'
'<div class="step cur"><span class="sr">&lt;3.0</span><span class="sn">弱修<small>缩量分歧</small></span><span class="sd"><span class="dayc now">09-01 2.03</span><span class="dayc">08-31 2.13</span><span class="dayc">08-28 2.10</span></span></div>\n'
'</div>\n'
'<div class="hint">量能20334亿=2.03万亿仍落"弱修"档(距3.0过渡档约0.97万亿),较昨21310亿缩量-976亿(-4.6%)——但情绪结构转暖(温度+10.5/炸板率6.7%/跌停0/封板率93.3%/最高板7),<b>量能台阶维持弱修档,量能缩但情绪结构修复(回暖第1日)</b>。A档:米开量能台阶换算。</div>\n')

# 二 先行指标
cycle_s2 = (
'<h2>二 先行指标 · 三窗触发器</h2>\n'
'<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">\n'
'<div class="kpi"><div class="top"><span class="l">一进二率</span><span class="v">18.4%</span></div><span class="chip2 c-acc">修复</span><span class="sub2">昨12.5% · 冰点线10%上方</span></div>\n'
'<div class="kpi"><div class="top"><span class="l">二进三率</span><span class="v">80.0%</span></div><span class="chip2 c-acc">高位</span><span class="sub2">昨25.0% · 大幅修复</span></div>\n'
'<div class="kpi"><div class="top"><span class="l">高度晋级率</span><span class="v">63.6%</span></div><span class="chip2 c-acc">修复</span><span class="sub2">昨35.7% · 高位接力</span></div>\n'
'<div class="kpi"><div class="top"><span class="l">昨日涨停溢价</span><span class="v">—</span></div><span class="chip2 c-half">数据缺口</span><span class="sub2">分时库缺T+1腿</span></div>\n'
'</div>\n'
'<div class="hint">先行指标三窗：一进二18.4%(>10%冰点线上方,修复)/二进三80%(高基数)/高度晋级63.6%(修复)——晋级率全面修复支持"回暖第1日"定性；但昨日涨停溢价缺(分时库T+1腿未回填)=承接质量无法机械验证,如实标注。三窗触发器未全部点亮(缺溢价窗),升B不成立。</div>\n')

# 三 情绪五阶段 · 五路周期投票
cycle_s3 = (
'<h2>三 情绪五阶段 · 五路周期投票</h2>\n'
'<div class="stages">\n'
'<div class="st"><b>冰点</b><span>—</span></div>\n'
'<div class="st"><b>修复</b><span class="on">回暖第1日</span></div>\n'
'<div class="st"><b>升温</b><span>—</span></div>\n'
'<div class="st"><b>高潮</b><span>—</span></div>\n'
'<div class="st"><b>退潮</b><span>中后段</span></div>\n'
'</div>\n'
'<div class="hint">主判=修复回暖·降(反对路auction偏乐观,加权反对份额0.207<0.60无复议)。五路投票：auction升(B档轻仓进攻)/lhb降(资金冷)/theme平(无主线低切)/logic平(业绩静默)/limitup降(负期望)。温度63.1中性回暖第1日=抛压枯竭式修复(炸板率6.7%+跌停0),但三维冷(质量停滞第12日+资金冷+无主线第6日)未跟进,明日大概率中继分化降温。</div>\n')

# 四 连板梯队
cycle_s4 = (
'<h2>四 连板梯队</h2>\n'
'<div class="ladder">\n'
'<div class="ld"><b class="l7">7板</b><span>海鸥住工002084(家居用品/控制权变更)</span></div>\n'
'<div class="ld"><b class="l6">6板</b><span>捷荣技术002855(消费电子) · 万向德农600371(农业)</span></div>\n'
'<div class="ld"><b class="l4">4板</b><span>新赛股份600540(农业/种业)</span></div>\n'
'<div class="ld"><b class="l3">3板</b><span>5只(2进3率80%高位)</span></div>\n'
'<div class="ld"><b class="l2">2板</b><span>9只(1进2率18.4%修复)</span></div>\n'
'<div class="ld"><b class="l1">1板</b><span>65只(首板78%占比,无主线扩散)</span></div>\n'
'</div>\n'
'<div class="hint">梯队7-6-6-4-3-2-1(83只)：最高板7海鸥住工孤高,6板双(捷荣技术+万向德农),4板1(新赛股份),3板5/2板9/1板65。二进三80%高位+高度晋级63.6%修复=高位接力修复；但首板65/83=78%占比=无主线扩散(次日易坍塌),海鸥住工7板孤高=高标断层风险。</div>\n')

# 五 攻防
cycle_s5 = (
'<h2>五 攻防 · 仓位总开关</h2>\n'
'<div class="posmeter"><div class="pm-track"><i class="pm-fill" style="width:20%"></i></div><div class="pm-lab">C档防守 · 仓位≤2成(仅auction轻仓窄窗)</div></div>\n'
'<div class="hint">攻防总开关=C档防守。温度63.1中性回暖第1日但三维冷未跟进,防守为主不加仓不追高；仅auction轻仓窄窗(掌阅科技603533带闸门≤2成)可尝试,其余四路空仓。升B三前提(①lhb资金温度≥34分位且S档同向≥3②全池执1max≥50%且命中≥3③题材线宽≥13立4板+且开板≤0.45)未满足前维持防守。</div>\n')

# 六 自主深挖
cycle_s6 = (
'<h2>六 自主深挖 · 指标与阈值孵化</h2>\n'
'<div class="hint">①资金温度单日脉冲假信号(42→27分位回落)连续三次坐实——孵化指标"资金温度连续≥34分位2日才计回流"待验证；②农业/种业宽度环比+300%为退坡线反抽陷阱——孵化"题材线宽≥13+立4板+且开板≤0.45"主线门槛(无主线第6日证伪旧阈值)；③封单max连续第3日下移(4.59→3.53亿)为广撒网承接退潮特征——孵化"封单max连续下移=质量型接力退潮"指标。详见自主拓展清单应答。</div>\n')

# 七 认知迭代
cycle_s7 = (
'<h2>七 我的认知迭代 · 最新</h2>\n'
'<div class="tli"><div class="d">2026-09-01</div><div class="h">回暖第1日≠进攻信号</div><div class="b">温度+10.5/炸板率6.7%/跌停0/晋级全面修复是"抛压枯竭式修复"；三维冷(质量停滞第12日+资金冷+无主线第6日)未跟进前,情绪暖不足以升级进攻,维持防守。</div></div>\n'
'<div class="tli"><div class="d">2026-09-01</div><div class="h">资金温度单日脉冲为假信号</div><div class="b">资金温度42→27分位回落,单日脉冲(8/29首现)连续三次坐实"回流"为假,脉冲后必回落,不再因单日脉冲翻多。</div></div>\n'
'<div class="tli"><div class="d">2026-09-01</div><div class="h">退潮中后段回暖首日次日分化</div><div class="b">负期望第12日+无主线第6日的退潮中后段,回暖第1日次日大概率分化(涨停广度收缩/晋级率回落/高标断板),不追回暖首日扩散票。</div></div>\n')

cycle_body = cycle_hero + cycle_s1 + cycle_s2 + cycle_s3 + cycle_s4 + cycle_s5 + cycle_s6 + cycle_s7

# ============ 读取五路 body ============
route_keys = {'auction':'auction','lhb':'lhb','theme':'theme','logic':'logic','limitup':'limitup'}
bodies = {'index': index_body, 'cycle': cycle_body}
for r in route_keys:
    p = os.path.join(BASE, L, '%s_body_%s.html' % (r, d))
    if os.path.exists(p):
        bodies[r] = open(p, encoding='utf-8').read()
    else:
        bodies[r] = '<div class="hint">%s路 body 缺失,待补</div>' % r

# ============ 写 judgment ============
judgment = {
    'date': d,
    '更新label': d + ' 复盘',
    '一句话': one_sentence,
    'ticker': ticker,
    'bodies': bodies,
    'archive_body': ''
}
out = os.path.join(BASE, L, 'judgment_%s.json' % d)
json.dump(judgment, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# 验证
print('judgment 已写:', out)
print('bodies keys:', list(bodies.keys()))
print('各body长度:')
for k, v in bodies.items():
    print('  %s: %d chars, div开=%d div闭=%d' % (k, len(v), v.count('<div'), v.count('</div>')))
print('一句话:', one_sentence)
print('ticker长度:', len(ticker))
