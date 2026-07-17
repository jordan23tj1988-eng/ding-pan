# -*- coding: utf-8 -*-
import json, os
L="_学习"
D="20260708"
J={"date":D,"更新label":"2026-07-08 收盘",
"一句话":"退潮末期·结构分化 · 涨停回升47/跌停仍41、量能2.56万亿未破线;算力线业绩兑现吸血(浪潮288%一字爆买)、科技独强、其余杀跌"}

# ========== INDEX ==========
index = """
<div class="hero"><div class="kick">Daily Overview · 我当前的判断</div>
<h1>复盘概览 · 截至 2026-07-08 收盘</h1>
<p>此刻我对市场的判断。明日观察点与对应股票在下面第一屏;周期/情绪、主线、产业逻辑、龙虎榜、竞价点导航深入看我的认知迭代。每天 18:00 更新,旧的进历史存档。</p>
<div class="stance"><span class="pill">情绪档 · <b>退潮末期/结构分化</b></span><span class="pill">周期 · <b>退潮末期(混沌苗头)</b></span><span class="pill warn">攻防 · <b>防守·仅算力主线内进攻 3-4成</b></span></div></div>

<h2 class="hot">明日核心观察点(07-09)· 对应股票</h2>
<div class="hint">操盘手"看牌":盯谁、看什么触发、什么算强算弱。给观察点不给买卖指令。每只注明四维共振数(产业逻辑/题材/席位/竞价)与缺失维。★荐票制:观察点=题材页核心标的∪两命门发现∪高危情绪标(含规避型),口径不同属正常。</div>
<div class="card hotcard"><table>
<tr><th>标的</th><th>身位 / 逻辑</th><th>明日(07-09)观察点</th><th>共振·类型</th></tr>
<tr><td><b>浪潮信息</b><br><span class="mut">000977</span></td><td>算力·服务器整机首板·<b>H1业绩+226~288%</b><br>一字54亿强封+顶级资金/外资/机构爆买</td><td><b>算力主线核心</b>。看竞价能否高开+封2板确认龙头身位,能否带出整机梯队(工业富联/中科曙光/紫光股份)。带得出=算力主升成形;带不出=业绩兑现一日游。</td><td><b class="s-ok">四维✓✓✓✓</b><br><span class="tag2 t-attack">进攻观察</span></td></tr>
<tr><td><b>数据港</b><br><span class="mut">603881</span><br><span class="mut">华勤 603296</span></td><td>算力洼地环节(IDC/整机)·首板<br>数据港IDC-38/距高-44深洼地、华勤整机-21/距高-37</td><td>高低切扩散第一梯队。看洼地环节能否续板、<b>盯润泽科技(300442)跟随</b>;数据港今日10:31封较晚,看明日能否早封转强。续=扩散确认,趴=资金只认核心。</td><td><span class="s-ok">三维✓✓·竞价待验</span><br><span class="tag2 t-attack">进攻观察</span></td></tr>
<tr><td><b>星网锐捷</b><br><span class="mut">002396</span></td><td>通信设备·算力互联·首板<br>顶级量化(太华路+知春派神)净买近2亿</td><td>席位驱动。看顶级量化明日是否续做、通信设备(算力互联)能否成算力线又一分支。量化撤退=纯博弈一日。</td><td><span class="s-mid">二维✓·产逻/题材待验</span><br><span class="tag2 t-watch">观察</span></td></tr>
<tr><td><b>大恒科技</b><br><span class="mut">600288</span></td><td>软件开发/机器人·<b>3板(全场连板次高)</b><br>外资3.1亿+华泰2.3亿大买但席位胜率B/C·封板晚11:16</td><td>全场身位最高的接力票(仅次恒尚)。看4板能否续、是软件(信创/AI)还是机器人属性主导资金。封板晚+胜率杂=接力质量存疑,高位分歧风险。</td><td><span class="s-mid">身位✓·席位质量弱</span><br><span class="tag2 t-watch">高危观察</span></td></tr>
<tr><td><b>恒尚节能</b><br><span class="mut">603137</span></td><td>存储跨界重组·<b>7板孤悬</b>·题材情绪高标<br>梯队断层(7/断/断/断/3/2)</td><td><b>异动红线区、7板极高危。</b>看竞价与首封;一旦炸板/低开=情绪见顶信号弹,高位抱团瓦解。不追。</td><td><span class="s-weak">情绪孤票·断层</span><br><span class="tag2 t-avoid">高危规避</span></td></tr>
<tr><td><b>华天科技</b><br><span class="mut">002185</span></td><td>半导体封测·首板套利已证伪</td><td>封测环节60日+78%距前高仅-4%已到位,今日冲高回落未2板——<b>米开"高辨识度标单独走强=掩护出逃"07-08验证</b>。规避高位封测。</td><td><span class="s-weak">位置到位</span><br><span class="tag2 t-avoid">规避</span></td></tr>
</table></div>

<h2>环境 · 退潮末期·结构分化</h2>
<div class="strip">
<div class="kv"><div class="l">两市成交额</div><div class="v dn">2.56万亿</div></div>
<div class="kv"><div class="l">涨停 / 跌停</div><div class="v">47 <span class="mut">/</span> 41</div></div>
<div class="kv"><div class="l">炸板率</div><div class="v">23%</div></div>
<div class="kv"><div class="l">最高板</div><div class="v up">7板</div></div></div>

<h2>四层关系 · 结构分化(局部共振)</h2>
<div class="card"><div class="gate">
<div class="g"><div class="t">环境·量能</div><div class="s s-weak">弱</div></div>
<div class="g"><div class="t">周期·高度</div><div class="s s-weak">断层</div></div>
<div class="g"><div class="t">题材·主线</div><div class="s s-mid">算力成形中</div></div>
<div class="g"><div class="t">情绪·赚亏</div><div class="s s-mid">分化</div></div></div>
<p style="margin-top:12px"><b>拐点预警:</b>量能仍缩(2.56万亿破线)、跌停41不减反增、连板梯队7板孤悬后直接断到3板——大盘退潮特征未消;但涨停回升47、算力线业绩兑现吸血(浪潮288%)+顶级资金爆买=<b>结构性分化,不是全面退潮空仓、也不是健康修复</b>。<br><b style="color:#b45309">★命门反推校验(07-08收盘):</b>昨晚设可证伪条件"若今日涨停回60+且跌停缩个位数→上修修复/启动"。实际涨停47(回升未到60)、跌停41(未缩)——<b>条件未满足,周期不上修为修复启动,定为"退潮末期结构分化/单主线吸血"</b>。三命门(席位/竞价/题材)齐指算力=局部共振唱多,与大盘退潮背离已收敛为"科技吸血"结论。转向条件:明日量能重回3万亿上方+跌停缩至20内+浪潮2板带整机梯队→升级科技主导修复;若量能续缩+算力断板→退潮加速。</p></div>

<h2>四维 · 操盘手看牌 <span class="badge bA">07-08更</span></h2><div class="hint">四张卡=四维共振选股的四问:该不该涨(产业逻辑)/有持续性吗(题材)/聪明钱认吗(席位)/点火了吗(竞价)。末行=温度读数,与周期判定背离时看拐点预警。</div><div class="two"><a class="mith" href="logic.html"><h3>产业逻辑·该不该涨 <span class="arw">→</span></h3><p><b class="s-ok">算力高低切扩散兑现</b>:浪潮(整机业绩288%一字)+华勤(整机洼地)+数据港(IDC深洼地)全在低位环节点火,昨判"高低切第一脚印"大胜;封测华天已到位掩护出逃。资金路径:已到位(封测/存储)→洼地(整机/IDC),盯润泽/液冷跟随。<br><span class="mut">链条温度:洼地环节涨停≥3起(扩散加速);涨停入库4/47,浪潮为业绩兑现①档硬逻辑</span></p></a><a class="mith" href="theme.html"><h3>题材·方向gate <span class="arw">→</span></h3><p><b>无题材过6有=分支轮动市</b>,但算力线被拆进4个行业字段(计算机/消费电子/通信/通信服务)被低估。名义最高:软件开发4/6(信创/AI软件5只涨停)。算力靠业绩兑现硬逻辑升级为"成形中主线"。<br><span class="mut">题材温度:全场最高6有分 4(持平);算力真实成色>行业字段显示</span></p></a><a class="mith" href="lhb.html"><h3>席位·钱在买什么 <span class="arw">→</span></h3><p><b>顶级资金爆买浪潮</b>(A档60%席位1.74亿+外资4亿+机构)=算力整机业绩兑现方向;<b>顶级量化(太华+知春派神A档60.8%)进星网锐捷</b>=通信/算力互联。方向高度共振指算力,无S档撤退。<br><span class="mut">席位温度:S/A真金净买集中算力(浪潮/星网)≥6笔——偏暖偏强,方向明确</span></p></a><a class="mith" href="auction.html"><h3>竞价·今晨最强信号 <span class="arw">→</span></h3><p><b>浪潮9:25一字54亿强封</b>(算力业绩兑现引领)+恒尚7板一字续命+软件系秒板。涨停回升47但跌停仍41=回暖伴分化。一字=三口径通吃信号(T+1封板41.6%/T+2跟随53.1%)。<br><span class="mut">竞价温度:一字≥2(浪潮/恒尚)+软件系秒板——回暖,但跌停未缩=结构性</span></p></a></div>

<h2>我的认知迭代 · 最新</h2>
<div class="card"><p><b>07-07 → 07-08 退潮里的结构分化:</b>昨判"退潮空仓0-2成",今日涨停回升47+算力线业绩兑现吸血——<span style="color:var(--half);font-weight:700">米开"混沌弱修复"一局占优,我一刀切退潮空仓过保守</span>。但跌停41+量能缩+断层证明这不是健康修复而是<b>科技吸血的结构分化</b>。→ 认知升级:退潮要区分"全面退潮(空仓)"与"结构性分化(单主线吸血,主线内做、主线外空)";浪潮288%业绩兑现给了算力硬逻辑,产业逻辑维度(高低切扩散)今日大胜。<a href="history.html" style="color:var(--accent)">查看历史存档 →</a></p></div>

<div class="foot"><b>说明:</b>本站为 Claude 认知/推演训练产物,给用户作参考、非买卖指令。数据取自真实盘后,拿不到即标 null。A档=可数据验证;C档=只能实盘、历史不可复现。</div>"""
J.setdefault("bodies",{})["index"]=index
json.dump(J, open("_tmp_j.json","w",encoding="utf-8"), ensure_ascii=False)
print("index ok len", len(index))
