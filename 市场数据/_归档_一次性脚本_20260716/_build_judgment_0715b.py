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
# ---------- LHB ----------
lhb_kpi=(
 kpi(ICO_T,'温(回升)','c-half','资金温度 · 70日分位','<span data-v="65">65</span>','含0714可得口径(0715榜未全发布)',gauge(65))+
 kpi(ICO_V,'在场34','c-mut','机构在场','<span data-v="34">34</span><small>只</small>','龙虎榜机构专用席34只')+
 kpi(ICO_S,'S·A出手10','c-half','S·A档出手','<span data-v="10">10</span><small>笔</small>','大钱试探未确认(昨7→今10)')+
 kpi(ICO_U,'T+1价源null','c-mut','昨判结算','<span class="big" style="font-size:20px">null</span>','席位路0714 Top5执行口径网络不可达')
)
lhb_deep='''<div class="card"><h3 style="margin:0 0 4px">清单应答 · lhb域</h3>
<p style="font-size:12.5px;line-height:1.6">扫描清单4项:①席位共现[国泰海通×高盛]②[中信上海×国泰海通]③[国泰海通×瑞银]④[瑞银×高盛]同向+新活跃席位[中泰济宁吴泰闸路净买≥5000万]。<b>应答:</b>2026-07-13用户拍板"中信上海×高盛共现≥3000万=加分项试运行(非独立荐票源)"——今日0715同日龙虎榜未全发布,共现金额无法核验,加分项<b>本晚悬置(数据缺)</b>,明日榜全后补算。在研孵化(新面孔降噪/东吴扬富路/国泰瑞银反向拥挤至0817):今日因榜数据不全无新增样本,孵化推进=维持在研、不改状态,可证伪判据不变(至0817窗口)。</p>
<div class="hint">收缩胜率K=10,n&lt;25标⚠小样本;席位胜率一律收缩估计值。</div></div>'''
lhb_tl='''<div class="tl"><div class="tli"><b>07-15</b> 同日龙虎榜未全publish=重大数据缺口(诚实记):席位路Top5(中国卫星[S]银河65.4%/豫能/儒意/铂力特/哈药)基于分析引擎已获席位动向(21条)出,但席位分档库/共现加分项因逐笔明细缺=部分悬置;资金温度65分位读数落0714可得口径。大钱回温(S/A出手7→10)但绝对偏少=试探非确认。
<div class="tli mut"><b>07-14</b> 修复日唯一跑赢的路(+5.82%),席位路买新有效;资金温度30→65回温。</div></div>'''
B['lhb']=f'''
<div class="rowA">
{hero('LHB · 龙虎榜/席位命门 · 第2路 · 截至 07-15','资金回温未确认:S/A出手10笔=大钱试探,席位Top1中国卫星[S]银河',[pill('资金温度','65分位(温)','warn','s-mid'),pill('机构','在场34只','',''),pill('数据','0715榜未全发布','warn','mut')],'对席位有根本认知+推演;全局扫描全市场席位,固定席位表仅作先验参照非白名单。')}
{lhb_kpi}
</div>
<h2>一 席位综合判断</h2>
<div class="card"><p style="font-size:12.5px;line-height:1.6">席位路Top5(综合分):①中国卫星600118 6.29 主席位[S]中国银河北京学院65.4%/2.42%(非小样本)②豫能控股001896 6.08 [A]华泰深圳彩田路⚠③儒意电影002739 6.04 [A]国联民生宁波⚠④铂力特688333 5.84 [A]华泰深圳彩田路⚠⑤哈药股份600664 5.59 共振2 [A]国盛杭州建设三路⚠。判断:S/A出手10笔较昨7笔小回升但绝对偏少=大钱试探非确认;Top5多⚠小样本(收缩胜率55-65%),仅中国卫星[S]样本足。诚实记:0715同日龙虎榜未全发布,以上基于分析引擎已获席位动向,共现加分项悬置待明日榜全。</p></div>
<!--FUNDTEMP--><div class="hint mut">资金温度.py 注入(段二"二 资金温度"自带h2,勿在锚前手写同名h2)。</div><!--/FUNDTEMP-->
<h2>三 龙虎榜台账</h2>
<!--LHBLEDGER--><div class="hint mut">龙虎榜台账.py --from-data 注入(最新在上、当日展开;含台账日块内SEATCARD荐票卡)。</div><!--/LHBLEDGER-->
<h2>四 席位分档库</h2>
<div class="hint">全市场席位滚动执行口径胜率S/A/B/C分档(收缩估计,n&lt;25标⚠)。★诚实记:今晚lhb席位区.py需逐笔明细(_席位动向/{d}.csv),因0715榜未全发布未能刷新,以下为最近可得(07-14)分档库快照。</div>
<details class="chain"><summary><b>席位分档库 · 最近快照(07-14)</b> <span class="chip cold">榜未全·待刷新</span></summary><div class="inner">{card('席位分档库.html')}</div></details>
<h2>五 自主深挖 · 席位孵化</h2>
{lhb_deep}
<h2>六 我的认知迭代 · 最新</h2>
{lhb_tl}
'''
# ---------- THEME ----------
th_kpi=(
 kpi(ICO_S,'6/6主流','c-hit','主流候选宽度','<span data-v="21">21</span><small>只</small>','医药/创新药(一字2·最高4板)')+
 kpi(ICO_U,'AI-50%/油煤-67%','c-miss','缩圈警报','<span class="big" style="font-size:20px">2线收缩</span>','AI算力5/6环比-50%·油气煤炭-67%')+
 kpi(ICO_V,'新线3','c-half','新线数','<span data-v="3">3</span><small>条</small>','中报预增/困境反转·消费·重组各首板')+
 kpi(ICO_T,'T+1价源null','c-mut','昨题材结算','<span class="big" style="font-size:20px">null</span>','0714题材Top执行口径网络不可达')
)
th_obs='''<div class="obs"><div class="obs-head"><span class="obs-nm">迪哲医药-U</span><span class="mut">688192</span><span class="obs-pos tag">业绩锚/正统龙候选</span></div>
<div class="obs-watch"><span class="obs-lab">身位逻辑</span> 创新药主线BD出海龙头:授权阿斯利康+EGFR(A档公告),2板早封开板0.0=承载核心,6/6主流线最硬身位。</div>
<div class="obs-rec"><span class="obs-lab2">荐票来源</span> 第3路发出版·不可覆盖;诚实:U股波动大、2板非高标,看明日能否领涨主线证龙头。</div></div>
<div class="obs"><div class="obs-head"><span class="obs-nm">哈药股份</span><span class="mut">600664</span><span class="obs-pos tag">正统龙候选(高位)</span></div>
<div class="obs-watch"><span class="obs-lab">身位逻辑</span> 当日唯一4板+中报预增/基药A档,医药主线最高标,9:30秒封封3.89%扎实。</div>
<div class="obs-rec"><span class="obs-lab2">荐票来源</span> 第3路;诚实:已4板高位缩圈龙,断承接/炸板不回封即高切,身位优先于空间。</div></div>
<div class="obs"><div class="obs-head"><span class="obs-nm">昭衍新药</span><span class="mut">603127</span><span class="obs-pos tag">业绩锚</span></div>
<div class="obs-watch"><span class="obs-lab">身位逻辑</span> CRO业绩锚:中报预增+实验猴涨价(A档),质量库抓龙率Top1(17.7%)。</div>
<div class="obs-rec"><span class="obs-lab2">荐票来源</span> 第3路;诚实:今日开板占比1.0(9:25开板回封封1.16%弱封)=分歧首板,做业绩锚不做龙。</div></div>'''
th_trow='''<div class="trow"><div class="tr1"><span class="tnm">医药/创新药</span><span class="d6"><i class="on"></i>×4<i class="on"></i>×2</span><span class="tjd tj-main">6/6·主流候选</span><div class="tbar"><i style="width:100%"></i></div><span class="tct">21只</span></div><div class="tds">GLP-1/CRO-CXO/IVD/器械多点开花;迪哲BD出海+哈药4板双龙头。<span class="mut">四维:宽度 5→21(+320%)【放宽】· 晋级率50% · 但开板占比0.48=宽而不硬 <b style="display:inline-block;width:6px;height:8px;background:#4a5666"></b><b style="display:inline-block;width:6px;height:11px;background:#4a5666"></b><b style="display:inline-block;width:6px;height:14px;background:#b8860b"></b> 序列2026-07-13起</span></div></div>
<div class="trow"><div class="tr1"><span class="tnm">AI算力/半导体</span><span class="d6"><i class="on"></i>×3<i class="on"></i>×2</span><span class="tjd tj-branch">5/6·大分支</span><div class="tbar"><i style="width:62%"></i></div><span class="tct">13只</span></div><div class="tds">AI应用游戏系预增+CPO+PCB+中昊芯英;<span class="mut">四维:环比-50%缩、晋级率14%——承载线退位,不做龙做中军</span></div></div>
<div class="trow"><div class="tr1"><span class="tnm">中报预增/困境反转</span><span class="d6"><i class="on"></i>×2<i></i></span><span class="tjd tj-minor">1/6·分支</span><div class="tbar"><i style="width:33%"></i></div><span class="tct">7只</span></div><div class="tds">醋酸/尿素/草酸/电力扭亏(A档业绩)★新线;<span class="mut">首板为主无梯队=困境反转防御画像</span></div></div>
<div class="trow"><div class="tr1"><span class="tnm">重组/跨界</span><span class="d6"><i class="on"></i>×3<i></i></span><span class="tjd tj-minor">3/6·分支</span><div class="tbar"><i style="width:45%"></i></div><span class="tct">6只</span></div><div class="tds">恒尚存储12天11板超高标(跨界重组驱动)+艾艾复牌5板;<span class="mut">个股驱动非板块效应</span></div></div>'''
th_deep='''<div class="card"><h3 style="margin:0 0 4px">清单应答 · theme域(【放宽】警报强制5问6有)</h3>
<p style="font-size:12.5px;line-height:1.6"><b>【放宽】医药/创新药 宽度5→21(+320%)——强制5问6有初判:</b><br>①有没有大方向?有(创新药BD出海/GLP-1减肥药全球放量,产业趋势A档)②有没有政策/事件催化?有(迪哲授权阿斯利康A档、多家中报预增A档)③有没有资金?部分(21只但开板0.48、S/A出手仅10笔=资金未大举确认)④有没有龙头?有候选(哈药4板/迪哲BD龙,但未确认接力)⑤有没有梯队?弱(4板1+3板2+2板...医药内2板≥2但首板普涨为主)⑥有没有持续性?未证(Day1爆发,警惕0709"宽度陷阱2.0"前科:42只宽而不硬后瓦解)。<b>生命周期起点判定:发酵Day1(未证主升)</b>——宽度到了、高度/梯队/资金确认没到。衰竭预判(必附高低切):若明日主线开板破封→高切业绩锚(哈药/迪哲)、低切GLP-1/CRO首板兑现。聚类口径守卫:医药归位对齐题材归位_0715.json(唯一真源),未用申万行业。</p>
<div class="hint">在研≤3/路;新线孵化推进=医药登记"发酵Day1"起点,可证伪=明日梯队是否重建。</div></div>'''
th_tl='''<div class="tl"><div class="tli"><b>07-15</b> 医药/创新药【放宽】+320%是唯一带4板梯队的承载线,但开板占比0.48=宽而不硬,与0709"宽度陷阱2.0"(42只宽而不硬)同构,故判"发酵Day1未证"而非确认主升,身位只做业绩锚(迪哲/哈药/昭衍)禁GLP-1/CRO首板接力。AI算力5/6却-50%、油气煤炭-67%=承载线退位,不做龙做中军。
<div class="tli mut"><b>07-14</b> 退潮中继反抽:只做业绩锚/新线龙首二板,禁接力人气身位。</div></div>'''
B['theme']=f'''
<div class="rowA">
{hero('Theme · 主线题材命门 · 第3路 · 截至 07-15','医药【放宽】+320%宽而不硬:发酵Day1未证,只做业绩锚',[pill('主流','医药6/6·21只','','s-mid'),pill('警报','AI-50%/油煤-67%缩','warn',''),pill('身位','业绩锚>接力','warn','')],'6有聚类口径;三级判定与生命周期引_题材四维.json;题材归属对齐12号归位唯一真源。')}
{th_kpi}
</div>
<h2>一 荐票卡</h2>
{th_obs}
<h2>二 三级判定</h2>
{th_trow}
<h2>三 主流生命周期</h2>
<div class="card"><p style="font-size:12.5px;line-height:1.6">医药/创新药=<b>发酵Day1(未证主升)</b>:宽度5→21爆发(6有4/6:大方向+催化+龙头候选到位,资金+梯队+持续性未证)。衰竭预判(高低切):若断承接→高切业绩锚(哈药4板/迪哲BD龙,基本面硬抗跌),低切GLP-1/CRO首板(睿智/博瑞/百花等纯概念先兑现)。AI算力=<b>退位中(5/6→环比-50%)</b>,群龙无首做中军不做龙。油气煤炭-67%=资源修复线退潮。</p></div>
<h2>四 龙头识别</h2>
<div class="card"><p style="font-size:12.5px;line-height:1.6">医药主线龙头候选:哈药(4板最高标,业绩驱动缩圈龙)vs 迪哲(BD出海2板早封,质地最硬)——两者身位互补,哈药看高度接力、迪哲看主线领涨。诚实:21只里19只首板/开板过半=龙头未真正确认,资金认不认看明日梯队能否重建。</p></div>
<h2>五 自主深挖 · 新线孵化</h2>
{th_deep}
<h2>六 我的认知迭代 · 最新</h2>
{th_tl}
'''
json.dump(B,open("_tmp_bodies_part2.json","w",encoding="utf-8"),ensure_ascii=False)
print("part2a(lhb/theme) built:",{k:len(v) for k,v in B.items()})
