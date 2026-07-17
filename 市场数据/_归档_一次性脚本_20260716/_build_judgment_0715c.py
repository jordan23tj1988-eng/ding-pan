# -*- coding: utf-8 -*-
import json,os
L="_学习"; d="20260715"; disp="07-15"
def card(fn):
    p=os.path.join(L,fn); return open(p,encoding="utf-8").read() if os.path.exists(p) else '<div class="hint mut">['+fn+' 缺]</div>'
ICO_T='<svg viewBox="0 0 24 24"><path d="M12 3v10.3a4 4 0 1 0 2 0V3z"/><circle cx="13" cy="17" r="1.6"/></svg>'
ICO_V='<svg viewBox="0 0 24 24"><path d="M4 19h16M6 19V9m6 10V4m6 15v-7"/></svg>'
ICO_U='<svg viewBox="0 0 24 24"><path d="M12 4l6 7h-4v9h-4v-9H6z"/></svg>'
ICO_S='<svg viewBox="0 0 24 24"><path d="M3 12h4l2-7 4 14 2-7h6"/></svg>'
def kpi(ico,chip,chipcls,lab,big,sub,extra=''):
    return (f'<div class="kpi"><div class="top"><span class="ico">{ico}</span><span class="chip2 {chipcls}">{chip}</span></div>'
            f'<span class="lab">{lab}</span><span class="big">{big}</span>{extra}<span class="sub2">{sub}</span></div>')
def gauge(v):
    return (f'<div class="gauge"><div class="gtrack"><i class="gmark" style="left:{v}%"></i></div>'
            f'<div class="gl"><span>0 冰点</span><span>45</span><span>65</span><span>85 过热</span></div></div>')
def hero(kick,h1,pills,intro=''):
    return f'<div class="hero"><div class="kick">{kick}</div><h1>{h1}</h1><p>{intro}</p><div class="stance">{"".join(pills)}</div></div>'
def pill(lab,val,cls='',bcls=''): return f'<span class="pill {cls}">{lab} · <b class="{bcls}">{val}</b></span>'
B={}
# ---------- LOGIC ----------
lo_kpi=(
 kpi(ICO_S,'沿0714','c-half','A共振池','<span class="big" style="font-size:20px">未刷新</span>','中报预增雷达今晚网络不可达')+
 kpi(ICO_V,'新线1','c-half','新线链数','<span data-v="1">1</span><small>条</small>','中报预增/困境反转(醋酸/尿素/草酸)')+
 kpi(ICO_U,'覆铜板+139.8%','c-miss','透支警示','<span class="big" style="font-size:20px">严重</span>','AI承载环节均60日透支(沿0714)')+
 kpi(ICO_T,'T+1价源null','c-mut','昨产逻结算','<span class="big" style="font-size:20px">null</span>','0714逻辑Top执行口径网络不可达')
)
lo_obs='''<div class="obs"><div class="obs-head"><span class="obs-nm">明泰铝业</span><span class="mut">601677</span><span class="obs-pos tag">埋伏观察</span></div>
<div class="obs-watch"><span class="obs-lab">链条</span> AI算力×电解铝双线(A池,沿0714):覆铜板上游材料替代位(铝基覆铜板/液冷铝材放量,预增+51.5%)。</div>
<div class="obs-rec"><span class="obs-lab2">类型</span> 埋伏观察;温度偏冷埋伏不追,逻辑硬情绪弱→观察(0714持仓,逻辑未破)。</div></div>
<div class="obs"><div class="obs-head"><span class="obs-nm">江苏索普</span><span class="mut">600746</span><span class="obs-pos tag">卡位兑现</span></div>
<div class="obs-watch"><span class="obs-lab">链条</span> 中报预增/困境反转★新线(醋酸华东龙头,尿素-甲醇一体化)。</div>
<div class="obs-rec"><span class="obs-lab2">类型</span> 卡位兑现;硬度=①A档中报预增公告②醋酸价格弹性;困境反转防御属性非进攻龙。</div></div>'''
lo_radar='''<div class="card"><h3 style="margin:0 0 4px">中报预增·概念叠加雷达(A共振)</h3>
<p style="font-size:12.5px;line-height:1.6">★诚实记:中报预增雷达.py 今晚因业绩预告数据源网络不可达(挂起>15min后中止),A共振池<b>未刷新</b>,沿用0714成色判定(A池含明泰铝业AI×电解铝双线等)。今日从题材归位识别的中报预增/困境反转线7只(江苏索普醋酸2板/赤天化尿素2板/金煤草酸2板/世茂热电2板+湖南发展/东方新能/璞源材料)均A档业绩实锤但首板无梯队=业绩底非进攻。A池=第四路候选来源之一(可选非必须),今日选江苏索普(唯一带2板梯队)。</p>
<div class="hint">漏斗末层=卡数;不混入r250≥100%透支票或B/C票。今日A池刷新失败标null,明日网络恢复补跑。</div></div>'''
lo_deep='''<div class="card"><h3 style="margin:0 0 4px">清单应答 · logic域(横切面"神")</h3>
<p style="font-size:12.5px;line-height:1.6">横切面扫描待深挖清单:①医药/创新药累计34(已毕业入链条纵深库,今21只)②中报预增(业绩)累计15毕业③油气/煤炭累计12孵化中(今仅3=收缩)④★新:中报预增/困境反转7、消费7、重组/跨界6。<b>答"神"(10答形11答神):</b>医药34毕业=形已成,神=BD出海(迪哲授权阿斯利康首付款)+GLP-1全球放量的真产业趋势承接,但当前是"业绩预增普涨"驱动多于"产业逻辑纵深"驱动——真纵深仅创新药BD/GLP-1两支,其余IVD/器械/中药是业绩搭车。深挖专题台账推进:困境反转新线(醋酸/尿素/草酸)=供给收缩+价格弹性逻辑,可证伪判据=若醋酸/尿素现货价明日续涨则逻辑硬,截止入台账观察至下周。</p>
<div class="hint">logic域走横切面扫描.py+深挖专题台账.json(与其他五域自主拓展扫描.py错开)。</div></div>'''
lo_tl='''<div class="tl"><div class="tli"><b>07-15</b> 周期票昨投"升"被裁判(平)打脸,今修正为"平"——产逻硬度够(困境反转+医药BD真趋势)但情绪高度不足,逻辑领先情绪时要压身位等确认。中报预增雷达网络不可达=A池未刷新(诚实标null,非judgment)。医药34毕业入链条纵深库但辨"神":真纵深仅创新药BD/GLP-1,其余业绩搭车。
<div class="tli mut"><b>07-14</b> A共振预增+51.5%明泰铝业(AI×电解铝双线)埋伏观察;电解铝★新线Day1。</div></div>'''
B['logic']=f'''
<div class="rowA">
{hero('Logic · 产业逻辑 · 第4路 · 截至 07-15','逻辑领先情绪:困境反转是业绩底非进攻龙,压身位等确认',[pill('A共振','沿0714(今未刷新)','warn','s-mid'),pill('新线','困境反转7只','',''),pill('透支','覆铜板+139.8%','warn','')],'挖未启动的产业逻辑与前置预期;埋伏观察/未启动挖掘/卡位兑现三类。')}
{lo_kpi}
</div>
<h2>一 荐票卡</h2>
{lo_obs}
<h2>二 链条深度地图库</h2>
<details class="chain" open><summary><b>医药/创新药链</b> <span class="chip hot">焦点 07-15</span></summary><div class="inner"><p style="font-size:12.5px;line-height:1.6">创新药BD出海(迪哲授权阿斯利康)→GLP-1减肥药(博瑞/美诺华/四川双马原料+制剂)→CRO/CXO(凯莱英/昭衍/睿智/百花,实验猴涨价+订单)→IVD/器械(基蛋POCT/蓝帆手套)。纵深核=BD/GLP-1真趋势,CRO是订单弹性,IVD/器械业绩搭车。</p></div></details>
<details class="chain"><summary><b>AI算力/覆铜板链</b> <span class="chip cold">透支·退位</span></summary><div class="inner"><p style="font-size:12.5px;line-height:1.6">覆铜板/PCB(贤丰2板)→CPO/光通信(华盛昌)→AI芯片(天普中昊芯英)→AI应用(巨人/恺英游戏预增)。承载环节均60日+139.8%严重透支(沿0714),环比-50%退位,上游材料替代位=明泰铝业埋伏。</p></div></details>
<details class="chain"><summary><b>困境反转/化工链</b> <span class="chip hot">新线 07-15</span></summary><div class="inner"><p style="font-size:12.5px;line-height:1.6">醋酸(江苏索普2板)→尿素/甲醇(赤天化2板)→草酸/煤化工(金煤2板)→热电(世茂2板)。逻辑=供给收缩+价格弹性+中报预增A档,防御业绩底属性。</p></div></details>
<h2>三 逻辑硬度 · 消息溯源</h2>
<div class="card"><p style="font-size:12.5px;line-height:1.6">硬度分级:①最硬=创新药BD(迪哲授权阿斯利康,公告A档实锤有真金白银首付)②硬=困境反转价格弹性(醋酸/尿素/草酸现货涨价+中报预增A档)③中=GLP-1减肥药全球放量(产业趋势A档但个股多原料/CDMO间接受益)④软=IVD/器械/中药业绩搭车(蹭医药主线情绪)。溯源纪律:题材归属对齐12号归位唯一真源,不自立题材。</p></div>
<h2>四 前置预期雷达</h2>
<div class="card"><p style="font-size:12.5px;line-height:1.6">到期校准:①电解铝(0714埋伏)——铝价+中报预增逻辑,明泰持仓观察,逻辑未破。②困境反转化工——醋酸/尿素现货价为兑现锚点,明日续涨则硬。③A池雷达0715刷新失败,预期事件跟踪顺延至网络恢复。</p></div>
<h2>五 中报预增 · 概念叠加雷达</h2>
{lo_radar}
<h2>六 自主深挖 · 专题孵化</h2>
{lo_deep}
<h2>七 我的认知迭代 · 最新</h2>
{lo_tl}
'''
# ---------- LIMITUP ----------
li_kpi=(
 kpi(ICO_U,'剔ST退','c-mut','涨停家数','<span data-v="71">71</span><small>只</small>','跌停31·炸板21·炸板率22.8%')+
 kpi(ICO_S,'哈药','c-half','最高连板','<span data-v="4">4</span><small>板</small>','3板2·2板12·首板56(占79%)')+
 kpi(ICO_T,'偏冷','c-half','温度档','<span data-v="33.4" data-dec="1">33.4</span>','250日分位',gauge(33.4))+
 kpi(ICO_V,'T+1价源null','c-mut','昨Top5结算','<span class="big" style="font-size:20px">null</span>','0714质量Top5执行口径网络不可达')
)
li_deep='''<div class="card"><h3 style="margin:0 0 4px">清单应答 · limitup域(因子孵化+归位)</h3>
<p style="font-size:12.5px;line-height:1.6">扫描清单3项:因子[开板次数/封单比/股价档]近5日3次成为套票主导——失效复盘/降权候补。<b>应答:</b>今日质量Top5(昭衍/华盛昌/天安/爱旭/云中马)命中0规则、纯靠抓龙率排序,其中"封单比:弱&lt;0.5%(+2.2)"仍是最强正因子(爱旭/云中马)、"开板次数:开2次+(+1.6)"次之——与清单"这三因子近5日反复主导"一致,提示套票因子可能过拟合。<b>立项:因子孵化观察</b>——首步结论=封单比/开板次数在偏冷普涨环境区分度可能虚高(首板普涨拉低样本质量),可证伪判据=若明日Top5执行口径均涨为负则确认因子偏冷失效、提请降权。待核清账:题材归位1只待核(72涨停vs71归位,差1为退市股口径),同股连2日无。线名守卫:医药/创新药线名今日无改名断裂。</p>
<div class="hint">质量库=统计训练非策略回测,守零后视镜;非16因子特征小样本≥3pp才提请拍板。</div></div>'''
li_tl='''<div class="tl"><div class="tli"><b>07-15</b> 涨停71但首板56占79%=普涨堆量、最高仅4板(哈药)——数量繁荣高度不足的典型分歧混沌结构。质量Top5全命中0规则=偏冷普涨环境下规则榜(扛出型)失灵,只能靠抓龙率排序,昭衍17.7%居首(业绩锚CRO)。★诚实记:质量库v6今晚为0714 fit(9活跃因子)——本晚fetch/prep阶段沙箱网络挂起未能重训,用T-1权重打标(因子权重日间稳定,不影响当日打标口径),明日网络恢复补重训。
<div class="tli mut"><b>07-14</b> 修复日质量Top5跑输-2.24pp,规则榜扛出型在弱环境失效。</div></div>'''
B['limitup']=f'''
<div class="rowA">
{hero('Limit-up · 涨停复盘/质量 · 第5路 · 截至 07-15','数量繁荣高度不足:首板56占79%,质量Top1昭衍(业绩锚)',[pill('涨停','71(剔ST退)','',''),pill('最高','4板哈药','','s-mid'),pill('质量Top1','昭衍17.7%','','')],'16因子质量分打标全部涨停,Top5作第5路荐票;零后视镜,当日因子只用≤当日数据。')}
{li_kpi}
</div>
<h2>一 Top5 荐票卡</h2>
{card('涨停质量荐票卡_%s.html'%d)}
<h2>二 市场温度 · 涨停生态</h2>
{card('市场温度卡_%s.html'%d)}
<h2>三 归位台账</h2>
<!--LEDGER--><div class="hint mut">涨停复盘台账.py --from-data 注入(最新在上、当日展开、旧日折叠;三层归位表+待归位兜底)。</div><!--/LEDGER-->
<h2>四 训练库</h2>
<details class="chain"><summary><b>涨停质量库 v6 · 因子权重</b> <span class="chip cold">0714 fit(网络限重训)</span></summary><div class="inner"><p style="font-size:12.5px;line-height:1.6">质量库v6(窗口一年,9活跃因子):封单比/开板次数/股价档/流通市值/首封时间/换手率/题材共振/连板桶/市场温度。★今晚fetch/prep沙箱网络挂起,用0714 fit权重打标今日71只(因子权重日间稳定),明日补重训。目标变量=执行口径收益+抓龙率P(执2≥+8%)。</p></div></details>
<h2>五 自主深挖 · 因子与归位孵化</h2>
{li_deep}
<h2>六 我的认知迭代 · 最新</h2>
{li_tl}
'''
json.dump(B,open("_tmp_bodies_part3.json","w",encoding="utf-8"),ensure_ascii=False)
print("part3(logic/limitup) built:",{k:len(v) for k,v in B.items()})
