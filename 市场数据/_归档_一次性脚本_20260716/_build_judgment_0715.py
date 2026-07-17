# -*- coding: utf-8 -*-
import json,os,html
L="_学习"; d="20260715"; disp="07-15"
def card(fn):
    p=os.path.join(L,fn)
    return open(p,encoding="utf-8").read() if os.path.exists(p) else '<div class="hint mut">['+fn+' 缺,标null]</div>'
# ---- 通用KPI瓦片 ----
ICO_T='<svg viewBox="0 0 24 24"><path d="M12 3v10.3a4 4 0 1 0 2 0V3z"/><circle cx="13" cy="17" r="1.6"/></svg>'
ICO_V='<svg viewBox="0 0 24 24"><path d="M4 19h16M6 19V9m6 10V4m6 15v-7"/></svg>'
ICO_U='<svg viewBox="0 0 24 24"><path d="M12 4l6 7h-4v9h-4v-9H6z"/></svg>'
ICO_S='<svg viewBox="0 0 24 24"><path d="M3 12h4l2-7 4 14 2-7h6"/></svg>'
def kpi(ico,chip,chipcls,lab,big,sub,extra=''):
    return (f'<div class="kpi"><div class="top"><span class="ico">{ico}</span>'
            f'<span class="chip2 {chipcls}">{chip}</span></div>'
            f'<span class="lab">{lab}</span><span class="big">{big}</span>{extra}'
            f'<span class="sub2">{sub}</span></div>')
def gauge(v):
    return (f'<div class="gauge"><div class="gtrack"><i class="gmark" style="left:{v}%"></i></div>'
            f'<div class="gl"><span>0 冰点</span><span>45</span><span>65</span><span>85 过热</span></div></div>')
def hero(kick,h1,pills,intro=''):
    ph=''.join(pills)
    return (f'<div class="hero"><div class="kick">{kick}</div><h1>{h1}</h1>'
            f'<p>{intro}</p><div class="stance">{ph}</div></div>')
def pill(lab,val,cls='',bcls=''):
    return f'<span class="pill {cls}">{lab} · <b class="{bcls}">{val}</b></span>'

# 竞价评分池数
try:
    js=json.load(open(os.path.join(L,'竞价评分_%s.json'%d),encoding='utf-8')); pooln=len(js.get('明细',[]))
except: pooln=None

BODIES={}
# ============ INDEX ============
idx_kpi=(
 kpi(ICO_T,'偏冷 25–45','c-half','情绪温度 · 250日分位','<span class="big" data-v="33.4" data-dec="1">33.4</span>',
     '昨35.3→今33.4微降 · 三窗均未触发',gauge(33.4))+
 kpi(ICO_V,'偏冷','c-mut','两市量能','<span data-v="2.57" data-dec="2">2.57</span><small>万亿</small>',
     '资金温度 <b>65</b> 分位(温,含0714可得口径)',
     '<svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none"><polyline class="drawin" points="0,20 20,6 40,10 60,4 80,9 100,12" fill="none" stroke="#e8a33d" stroke-width="1.6" vector-effect="non-scaling-stroke" opacity=".9"/></svg>')+
 kpi(ICO_U,'分歧','c-miss','涨停 / 跌停','<span data-v="71">71</span><small> / </small><span class="dn">31</span>',
     '炸板21·炸板率22.8% · 最高4板(哈药)')+
 kpi(ICO_S,'回升未达标','c-half','1进2率(接力)','<span data-v="13.9" data-dec="1">13.9</span><small>%</small>',
     '昨2.5%极值→今13.9% · 2进3率14.3% · 高度晋级28.6%')
)
obs_index='''<div class="obs"><div class="obs-head"><span class="obs-nm">医药/创新药能否把"宽"转"高"</span><span class="obs-pos tag">主线·6/6主流</span></div>
<div class="obs-watch"><span class="obs-lab">身位逻辑</span> 21只承载但开板占比0.48=宽而不硬,仅哈药(4板)/迪哲(BD出海2板早封)为核心;明日看是否有2板→3板梯队接棒,只做业绩锚身位(哈药/迪哲/昭衍),禁GLP-1/CRO首板接力人气。</div>
<div class="obs-rec"><span class="obs-lab2">可证伪预测</span> 明日若医药主线出≥1只新3板+1进2率站上20%→升"混沌修复";若主线开板破封+跌停再扩(>35)→降"退潮",医药高切业绩锚(哈药/迪哲)低切GLP-1/CRO首板。</div></div>'''
pred_index='''<div class="obs"><div class="obs-head"><span class="obs-nm">明日三条可证伪命题</span><span class="obs-pos tag">给概率不给指令</span></div>
<div class="obs-watch"><span class="obs-lab">① 主线</span> 医药/创新药维持6/6主流概率高(~60%),但晋级出高标概率低(~30%);AI算力5/6环比-50%大概率继续退位。</div>
<div class="obs-rec"><span class="obs-lab2">② 情绪</span> 温度大概率维持偏冷25–45档(震荡分化),突破45进中性需1进2率站稳20%+新3板;③ 竞价:天安新材(评分Top1 44.1秒板首板)高开≥5则弃,低开≤0有肉。</div></div>'''
rail_index=f'''<div class="card"><h2 style="margin:0 0 2px;font-size:15px">三 拐点预警 · 命门温度背离</h2>
<div class="hint">三窗灯条(冰点进攻窗温度&lt;25 / 过热禁追窗≥85 / 洗出反弹窗溢价连负3日)</div>
{card('先行指标灯_%s.html'%d)}
<p style="margin:8px 0 0;font-size:12.5px;line-height:1.6">温度33.4(偏冷)未触任一窗;昨停溢价今晚实时源不可达标<b class="mut">null</b>,无法确认"洗出反弹窗"连负计数。背离观察:涨停71数量维持 × 1进2率13.9%(接力线较昨2.5%极值回升但绝对偏低)=数量与接力剪刀口收敛中、未见明确转向。资金温度65分位回温(0714可得口径)但S/A席位出手仅10笔=大钱试探未确认。</p></div>'''
routes_index=f'''<div class="routes">
<a class="rt" href="auction.html"><span class="rtn">01 / 第一路</span><span class="rtm">竞价·时机</span><b class="rtt s-mid">评分Top1 天安44.1</b><span class="rtd">秒板首板可追;高开≥5弃、低开有肉</span></a>
<a class="rt" href="lhb.html"><span class="rtn">02 / 第二路</span><span class="rtm">龙虎榜·席位</span><b class="rtt s-mid">资金温度65(温)</b><span class="rtd">Top1中国卫星[S]银河65.4%;0715榜同日未全发布</span></a>
<a class="rt" href="theme.html"><span class="rtn">03 / 第三路</span><span class="rtm">题材·主线</span><b class="rtt s-mid">医药6/6·21只</b><span class="rtd">【放宽】宽5→21但开板0.48宽而不硬</span></a>
<a class="rt" href="logic.html"><span class="rtn">04 / 第四路</span><span class="rtm">产业·逻辑</span><b class="rtt s-mid">困境反转新线7</b><span class="rtd">醋酸/尿素/草酸业绩底;A雷达网络未刷新</span></a>
<a class="rt" href="limitup.html"><span class="rtn">05 / 第五路</span><span class="rtm">涨停·质量</span><b class="rtt s-mid">质量Top1 昭衍17.7%</b><span class="rtd">首板56占79%普涨堆量;最高4板</span></a>
</div>'''
# 六账本 hb (累计%)
def hb_row(name,v):
    mag=abs(v)/1.66*48
    cls='pos' if v>=0 else 'neg'; side='right:50%' if v<0 else 'left:50%'
    vcls='up' if v>=0 else 'dn'
    return (f'<div class="hb"><span class="hbl">{name}</span><div class="hbt">'
            f'<i class="{cls}" style="width:{mag:.0f}%"></i></div>'
            f'<span class="hbv {vcls}">{v:+.2f}%</span><span class="hbs">本周累计</span></div>')
six=''.join(hb_row(n,v) for n,v in [('总·master',0.35),('席位lhb',1.0),('题材theme',0.6),('竞价auction',-1.19),('涨停limitup',0.0),('产逻logic',-1.66)])
rowE_index=f'''<div class="rowE">
<div class="card"><h3 style="margin:0 0 6px">六账本 · 本周净值(出自引擎)</h3>{six}
<div class="hint">各100万独立账本;基准本周{'+' if -0.14>=0 else ''}-0.14%。今日六本全部有计划(逐票表态齐)。数字仅出自模拟盘引擎,agent不手算。</div></div>
<div class="card"><h3 style="margin:0 0 6px">总裁决 · 自主进化</h3>
<p style="font-size:12.5px;line-height:1.65">跨路裁决:今日五路周期票<b>全平一致</b>(主判启动/分歧·平,0反对,无复议)——★一致率100%触发<b class="s-mid">回声室警示</b>,已在cycle认知迭代记账(evidence均用私有数据自证非抄主判)。今日分派:medical主线三路共荐(题材迪哲/limitup昭衍/lhb哈药共振),master压6%迪哲对齐偏防守。自主拓展审计:audit回看0713打脸0条、tick无告警;横切面医药累计34毕业入链条纵深库。督办:昨日各路结算执行口径<b class="mut">全null</b>(T+1价源今晚网络不可达),明日补结算。</p></div>
</div>'''
tl_index='''<div class="tl"><div class="tli"><b>07-15</b> 数量繁荣延续(涨停71)但接力仍弱(1进2率13.9%);医药主线【放宽】+320%宽度爆发却开板0.48=宽而不硬,警惕"宽度陷阱2.0"(0709前科);五路票全平但一致率100%=回声室风险,强制各路用私有数据自证。今日重大数据缺口(诚实记):同日龙虎榜未全publish+实时spot源不可达→昨停溢价/各路执行口径结算/中报预增雷达刷新均标null,非系统判断而是环境网络限制。</div>
<div class="tli mut"><b>07-14</b> 冰点次日修复:涨停80、温度35.3落"诱多带",1进2率2.5%极值,买新不买旧。</div></div>'''
BODIES['index']=f'''
<div class="rowA">
{hero('Daily Overview · 我当前的判断 · 截至 2026-07-15 收盘','启动/分歧:数量维持 × 接力回升未达标,<em>偏冷诱多带</em>里只买医药业绩锚',[pill('情绪档','启动/分歧 · 温度33.4偏冷','warn','s-mid'),pill('周期','量能2.57万亿弱修档','',''),pill('攻防','混沌档执行≤4-5成 · 买业绩锚','warn',''),pill('三窗','全未触发','','mut')],'此刻我对市场的判断。明日观察点在第一屏;五路荐票按 ①竞价→②龙虎榜→③主线题材→④产业逻辑→⑤涨停复盘 深读。18:00更新,旧的进历史存档。')}
{idx_kpi}
</div>
<h2>一 明日核心观察点</h2>
<div class="hint">医药主线宽而不硬,明日看能否把"宽"转成"高"(梯队重建);给概率不给指令。</div>
<div class="rowC"><div>{obs_index}{pred_index}</div><aside class="rail">{rail_index}</aside></div>
<h2>二 五路看牌</h2>
{routes_index}
<h2>四 总裁决 · 自主进化</h2>
{rowE_index}
<h2>五 我的认知迭代 · 最新</h2>
{tl_index}
'''

# ============ CYCLE ============
steps='''<div class="steps">
<div class="step dim"><span class="sr">≥3.8</span><span class="sn">主升2确认<small>放量突破</small></span><span class="sd"></span></div>
<div class="step dim"><span class="sr">3.5~3.8</span><span class="sn">突破压力<small>需增量</small></span><span class="sd"></span></div>
<div class="step dim"><span class="sr">3.3~3.5</span><span class="sn">强修<small>量能承接</small></span><span class="sd"></span></div>
<div class="step dim"><span class="sr">3.0~3.3</span><span class="sn">过渡<small>量能中枢</small></span><span class="sd"></span></div>
<div class="step cur"><span class="sr">&lt;3.0</span><span class="sn">弱修<small>缩量分歧</small></span><span class="sd"><span class="dayc now">07-15 2.57</span><span class="dayc">07-14 2.70</span></span></div>
</div>
<div class="hint">量能2.57万亿落"弱修"档(连2日回落,昨2.70→今2.57)——数量繁荣靠情绪堆而非增量资金,是弱修复而非放量突破。A档:米开量能台阶换算。</div>'''
stages5='''<div class="stages">
<div class="st">冰点<small>0713兑现</small></div>
<div class="st on">启动/分歧<small>宽度维持·高度不足</small></div>
<div class="st">发酵·主升<small>未至</small></div>
<div class="st">高潮<small>—</small></div>
<div class="st">退潮<small>—</small></div></div>'''
posmeter='''<div class="stages" style="margin-top:8px"><div class="st">主升<small>8-10成</small></div><div class="st on">启动混沌<small>4-5成</small></div><div class="st">退潮<small>0-2成</small></div></div>
<div class="posmeter"><i style="width:42%"></i><em style="left:50%"></em></div>
<div class="posml"><span>0成</span><span>执行≤4-5成(偏防守)▲</span><span>10成</span></div>'''
ladder='''<div class="cols">
<div class="col hotc"><i style="height:12%"></i><b>1</b><span>4板</span></div>
<div class="col"><i style="height:24%"></i><b>2</b><span>3板</span></div>
<div class="col"><i style="height:100%"></i><b>12</b><span>2板</span></div>
<div class="col"><i style="height:100%"></i><b>56</b><span>首板</span></div>
</div><div class="colsub"><span>最高4板=哈药股份(医药,中报预增业绩)</span><span>2板12只(梯队略厚于0714)</span><span>首板56占79%=普涨堆量</span></div>'''
cyc_kpi=(
 kpi(ICO_V,'弱修档','c-mut','两市量能','<span data-v="2.57" data-dec="2">2.57</span><small>万亿</small>','连2日回落 · 缩量分歧')+
 kpi(ICO_S,'宽度维持','c-half','情绪阶段','<span class="big" style="font-size:20px">启动/分歧</span>','高度不足·未证发酵')+
 kpi(ICO_T,'偏冷','c-half','市场温度','<span data-v="33.4" data-dec="1">33.4</span>','250日分位',gauge(33.4))+
 kpi(ICO_U,'混沌偏防守','c-miss','仓位上限','<span class="big" style="font-size:20px">4-5成</span>','三态开关:启动混沌档')
)
cyc_deep='''<div class="card"><h3 style="margin:0 0 4px">清单应答 · cycle域(先行指标/温度分量250日极值)</h3>
<p style="font-size:12.5px;line-height:1.6">① 温度分量250日分位极值扫描:今日温度33.4=250日中位偏下,未见≥95或≤5极值(0713温度8.7曾近冰点极值,今已回);1进2率13.9%较昨2.5%(250日分位约2%极值)明显回升脱离极值区。<b>应答:今日无250日极值触发,不立项。</b>可证伪:若明日温度分量任一指标进≤5或≥95分位,cycle段二判读card专门应答并登记孵化窗。② 三窗:全未触发(温度33.4未破25/85;溢价连负因今晚溢价null无法计数=悬置,非确认)。</p>
<div class="hint">cycle孵化=阈值/口径年检类;在研≤3/路。今日孵化窗:无新登记(极值未触发)。</div></div>'''
cyc_tl='''<div class="tl">
<div class="tli"><b>07-15</b> ★回声室警示:五路周期票全平、一致率100%——虽主判"平"有据(温度偏冷+接力回升未达标+主线宽而不硬),但全票一致本身是风险信号,已要求各路evidence用私有数据自证(auction用高开档执行分布/lhb用席位出手笔数/theme用开板占比/logic用困境反转画像/limitup用梯队结构),非互相抄。周期投票复议判定:tally 0反对未触发复议,主判维持"启动/分歧·平"。A档:量能2.57万亿弱修+1进2率13.9%。
<div class="tli mut"><b>07-14</b> 定档"启动(未证)平":冰点后修复日,宽度回来高度没回来,买新不买旧。</div></div>'''
BODIES['cycle']=f'''
<div class="rowA">
{hero('Cycle · 环境周期总开关 · 第0路(总闸) · 截至 07-15','量能弱修 × 情绪启动/分歧:总闸锁"混沌偏防守4-5成"',[pill('量能','2.57万亿弱修档','',''),pill('阶段','启动/分歧(未证)','warn','s-mid'),pill('攻防','执行≤4-5成','warn','')],'环境/周期是总开关,直接锁总仓位与攻防基调(非四层平权)。')}
{cyc_kpi}
</div>
<h2>一 量能台阶 · 我站在哪一阶</h2>
{steps}
<h2>二 先行指标 · 三窗触发器</h2>
{card('先行指标卡_%s.html'%d)}
<div class="card"><h3 style="margin:0 0 4px">今日读数判读</h3><p style="font-size:12.5px;line-height:1.6">剪刀口:涨停71(数量维持) × 1进2率13.9%(接力线较0714的2.5%极值回升但绝对偏低)=数量与接力的背离在收敛、未见明确转向。昨停溢价今晚实时源不可达=<b class="mut">null</b>,"洗出反弹窗(溢价连负3日)"无法计数,悬置不判。三窗结论:<b>全未触发</b>——温度33.4未破冰点&lt;25也未破过热≥85。已证伪口径不用:"连负3日=退潮确认"/复合转机分量。</p></div>
<h2>三 情绪五阶段 · 五路周期投票</h2>
{stages5}
<!--VOTEBOARD-->
{card('周期投票牌_%s.html'%d)}
<!--/VOTEBOARD-->
<div class="hint">当日主判=启动/分歧·平;五路全平一致(0反对),tally未触发复议——★一致率100%回声室警示已记账。</div>
<h2>四 连板梯队</h2>
{ladder}
<h2>五 攻防 · 仓位总开关</h2>
<div class="card"><p style="font-size:12.5px;line-height:1.65">总开关驱动:量能2.57万亿弱修档 + 情绪启动/分歧(未证)→ 锁<b class="s-mid">混沌偏防守,执行仓位上限4-5成</b>。退潮敢喊防守、冰点敢喊进攻的纪律下,今日=偏冷诱多带里的谨慎试错:只做医药业绩锚身位(哈药/迪哲/昭衍),禁接力人气与高开≥5追板。三窗未触发=无冰点进攻窗加分、无过热禁追窗压制。</p>{posmeter}</div>
<h2>六 自主深挖 · 指标与阈值孵化</h2>
{cyc_deep}
<h2>七 我的认知迭代 · 最新</h2>
{cyc_tl}
'''

# ============ AUCTION ============
au_kpi=(
 kpi(ICO_U,'早封占比','c-mut','一字/早封占比','<span data-v="9.9" data-dec="1">9.9</span><small>%</small>','7只≤09:31未炸 / 71涨停')+
 kpi(ICO_S,'评分池','c-mut','竞价评分池数',f'<span data-v="{pooln or 0}">{pooln if pooln else "null"}</span><small>只</small>','SCORECARD打分池(排序+闸门用)')+
 kpi(ICO_T,'秒板首板','c-hit','评分Top1','<span class="big" style="font-size:20px">天安44.1</span>','秒板·首板=可追档(非高开≥5)')+
 kpi(ICO_V,'T+1价源null','c-mut','昨池结算','<span class="big" style="font-size:20px">null</span>','0714池11只次日封板5;执行口径网络不可达')
)
au_deep='''<div class="card"><h3 style="margin:0 0 4px">清单应答 · auction域</h3>
<p style="font-size:12.5px;line-height:1.6">扫描清单3项(连续3日同向):①信号[一字]连续3日均收[-4.2/-0.9/-3.8]、②高开档[低开≤0]连续3日、③高开档[高开≥5]连续3日均收负。<b>应答:</b>三项均指向"追一字/追高开≥5在偏冷环境连续吃面"——与分桶库口径一致(高开≥5档执行-1.72%/胜率21.9%,一字信号次日封板率高但执行口径为负=开盘买进当天套)。<b>立项深挖(在研·07-15拍板):秒板失效复盘按温度档拆样本</b>——首步结论:偏冷档(温度&lt;45)下秒板/一字执行口径普遍为负,今日评分Top1天安新材虽秒板但需gate5防高开;孵化区推进=下一步按温度档分桶统计秒板执行胜率,可证伪判据=偏冷档秒板执行胜率若≥50%则证伪"秒板偏冷失效"。</p>
<div class="hint">铁律:池原样追开盘非alpha,竞价分=排序+闸门用;agent只写洞察card,SCORECARD/POOLLEDGER标记区脚本管。</div></div>'''
au_tl='''<div class="tl"><div class="tli"><b>07-15</b> 分桶库回填确认"低开有肉高开套":低开≤0档执行+0.57%/胜率47.6%、高开0~5档+0.21%/胜率54%、高开≥5档-1.72%/胜率21.9%(n=1394)。今日评分Top1天安新材=秒板首板(非高开≥5)可追档,gate5防高开。昨池执行口径结算null(T+1价源网络不可达),仅信号口径次日封板5/11。</div>
<div class="tli mut"><b>07-14</b> 修复日竞价池追开盘跑输(-5.33pp),验证池非alpha、分=排序闸门用。</div></div>'''
BODIES['auction']=f'''
<div class="rowA">
{hero('Auction · 集合竞价命门 · 第1路 · 截至 07-15','偏冷竞价:低开有肉高开套,评分Top1天安秒板首板可追(gate5)',[pill('温度','偏冷33.4','warn','s-mid'),pill('评分Top1','天安44.1(秒板首板)','',''),pill('闸门','高开≥5弃','warn','')],'第一式是C档只能实盘;竞价分=A档代理(高开幅度/开盘位置/信号→次日)。')}
{au_kpi}
</div>
<h2>一 竞价选股池 · 当日</h2>
<div class="hint">SCORECARD评分卡(竞价评分.py产,排序+闸门用;池追开盘非alpha,禁trow池行表)。</div>
<!--SCORECARD-->
{card('竞价评分卡_%s.html'%d)}
<!--/SCORECARD-->
<h2>二 今日竞价温度</h2>
<div class="card"><p style="font-size:12.5px;line-height:1.6">竞价温度=偏冷(市场温度33.4同步)。分桶库(窗口20250701~20260710,n=2905)口径:<b>低开≤0档</b>执行胜率47.6%/均涨+0.57%(有肉)、<b>高开0~5档</b>54.0%/+0.21%、<b>高开≥5档</b>21.9%/均涨-1.72%(追高即套,n=1394)——"低开有肉高开套"稳。今日盯:天安新材(评分Top1 44.1,秒板首板)高开≥5弃、低开≤0进。</p></div>
<h2>三 昨日池 · 今日终结算</h2>
<!--POOLLEDGER--><div class="hint mut">竞价池结算归档.py --inject 注入(段三,归档脚本管;昨池执行口径T+1价源今晚不可达标null)。</div><!--/POOLLEDGER-->
<h2>四 竞价信号胜率追踪</h2>
<details class="chain"><summary><b>评分库卡 · 信号胜率追踪</b> <span class="chip">分桶库</span></summary><div class="inner">{card('竞价评分库卡_%s.html'%d)}</div></details>
<h2>五 自主深挖 · 信号孵化</h2>
{au_deep}
<h2>六 我的认知迭代 · 最新</h2>
{au_tl}
'''
json.dump(BODIES,open("_tmp_bodies_part1.json","w",encoding="utf-8"),ensure_ascii=False)
print("part1(index/cycle/auction) built, sizes:",{k:len(v) for k,v in BODIES.items()})
