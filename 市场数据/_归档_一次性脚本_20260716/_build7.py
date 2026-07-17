# -*- coding: utf-8 -*-
import json, os
J=json.load(open("_tmp_j.json",encoding="utf-8"))

archive = """
<div class="hero"><div class="kick">Daily Archive · 每日复盘总结(冻结存档)</div>
<h1>2026-07-08 复盘总结</h1>
<p>07-08 收盘后冻结的完整复盘,永久留存。含环境/周期/主线/核心标的/龙头/竞价/龙虎榜、明日观察点,以及对 07-07 预判的校准记分。</p>
<div class="stance"><span class="pill">情绪 · <b>退潮末期/结构分化</b></span><span class="pill warn">攻防 · <b>防守·仅算力主线内3-4成</b></span><span class="pill">一句话 · <b>涨停回升47跌停仍41,算力业绩兑现吸血,科技独强</b></span></div></div>

<h2>一、环境</h2>
<div class="strip">
<div class="kv"><div class="l">成交额</div><div class="v dn">2.56万亿</div></div>
<div class="kv"><div class="l">涨停/跌停</div><div class="v">47/41</div></div>
<div class="kv"><div class="l">炸板率</div><div class="v">23%</div></div>
<div class="kv"><div class="l">最高板</div><div class="v up">7板</div></div></div>
<div class="card"><p>量能2.56万亿与07-07(2.58万亿)持平、仍破3万亿退潮线;涨停回升33→47、炸板率41%→23%、算力赚钱效应回归,但跌停41不减反增、梯队7板孤悬后断层——<b>退潮末期的结构性分化:大盘退、单主线(算力)吸血独强</b>。攻防=防守,仅在算力主线内用3-4成仓。</p></div>

<h2>二、周期情绪 · 梯队断层加剧</h2>
<div class="card"><div class="ladder">
<div class="rung high"><div class="lv">7板</div><div class="nm">恒尚节能</div></div>
<div class="rung gap"><div class="lv">6/5/4板</div><div class="nm">空缺×3</div></div>
<div class="rung"><div class="lv">3板</div><div class="nm">大恒科技</div></div>
<div class="rung"><div class="lv">2板×6</div><div class="nm">威尔高/视源/大名城…</div></div>
<div class="rung"><div class="lv">首板×39</div><div class="nm">全场(含算力多只)</div></div></div>
<p style="margin-top:10px">恒尚7板独悬、中间4-6板三层皆空;但首板39只里算力占相当比例(浪潮/华勤/数据港/星网)=低位扩散、高位孤悬,结构分化的梯队画像。</p></div>

<h2>三、主线题材 · 算力(被行业字段拆散)</h2>
<div class="card"><p>表面软件开发5/计算机4/消费电子4分散,合并看是<b>算力线横跨5个行业字段吸血</b>:浪潮(计算机·整机)/华勤(消费电子·整机洼地)/星网(通信·互联)/数据港(通信服务·IDC)/浪潮软件(IT服务)——合并≥8只涨停。由浪潮H1业绩+226~288%(公告)点燃,是业绩兑现①档硬逻辑主线。<b>关键修正:连板/主线股必须穿透行业字段看产业归属(继恒尚存储后第二例)。</b></p></div>

<h2>四、核心标的 / 龙头</h2>
<div class="card"><table>
<tr><th>标的</th><th>身位</th><th>真实归属</th><th>点评</th></tr>
<tr><td>浪潮信息</td><td>首板一字</td><td class="dA">算力整机</td><td>业绩兑现准龙头,顶级资金爆买,成色高于昨日华天</td></tr>
<tr><td>恒尚节能</td><td>7板</td><td>存储重组</td><td>孤悬情绪高标,断层高危</td></tr>
<tr><td>大恒科技</td><td>3板</td><td>软件/机器人</td><td>身位次高但席位杂、封板晚,接力存疑</td></tr>
<tr><td>数据港/华勤</td><td>首板</td><td class="dA">算力IDC/整机洼地</td><td>高低切扩散第一梯队</td></tr>
<tr><td>华天科技</td><td>未板</td><td>半导体封测</td><td class="s-weak">封测到位,掩护出逃验证,规避</td></tr>
</table></div>

<h2>五、竞价</h2>
<div class="card"><p>算力一字/秒板占主导(浪潮一字54亿+华勤/威尔高秒板)+软件系秒板扩散;恒尚7板一字续命。07-07池T+1封板率约40-50%符合一字概率。学习:华勤(封单弱)因产业逻辑(整机洼地)反续板→<b>竞价需与产业逻辑共振使用,不能单用封单强弱</b>。</p></div>

<h2>六、龙虎榜</h2>
<div class="card"><p>顶级资金+外资+机构四方共振爆买浪潮(外资4亿+A档60%席1.74亿+机构0.85亿+多路&gt;18亿);顶级量化太华+知春派神进星网(算力互联)。方向情报连续三日拼图:算力(06)→半导体(07)→算力整机业绩兑现(08)——资金一直在科技里找有业绩兑现的洼地环节。半导体华天今日哑火=掩护出逃验证。</p></div>

<h2 class="hot">七、明日观察点(07-09)· 对应股票</h2>
<div class="card hotcard"><table>
<tr><th>标的</th><th>身位/逻辑</th><th>观察点</th><th>共振·类型</th></tr>
<tr><td><b>浪潮信息</b> 000977</td><td>算力整机·业绩288%·一字</td><td>2板确认龙头+带整机梯队(工业富联/曙光/紫光)</td><td>四维✓✓✓✓ 进攻观察</td></tr>
<tr><td><b>数据港/华勤</b> 603881/603296</td><td>算力IDC/整机洼地</td><td>洼地扩散能否续,盯润泽跟随</td><td>三维 进攻观察</td></tr>
<tr><td><b>星网锐捷</b> 002396</td><td>算力互联·顶级量化</td><td>量化续做否,通信线纳入算力</td><td>二维·席位强 观察</td></tr>
<tr><td><b>大恒科技</b> 600288</td><td>软件/机器人3板</td><td>4板续否,软件vs机器人</td><td>身位高·质量疑 高危观察</td></tr>
<tr><td><b>恒尚节能</b> 603137</td><td>存储7板孤悬</td><td>炸板/低开=情绪见顶信号弹</td><td>断层孤票 高危规避</td></tr>
<tr><td><b>华天科技</b> 002185</td><td>封测到位</td><td>掩护出逃,规避高位封测</td><td>位置到位 规避</td></tr>
</table></div>

<h2>八、认知迭代 · 退潮里的结构分化</h2>
<div class="card"><p><b>退潮≠一刀切空仓:</b>07-07判退潮空仓0-2成,今日涨停回升47+算力业绩兑现吸血——米开"混沌弱修复"一局占优,我一刀切退潮过保守。但跌停41+量能缩+断层证明这是<b>科技吸血的结构分化</b>而非健康修复。<b>迭代结论:退潮要区分"全面退潮(空仓)"与"结构性分化(单主线吸血,主线内做3-4成、主线外空仓)"</b>,不用退潮教条误杀单主线机会;浪潮288%业绩给了算力硬逻辑,产业逻辑维度(高低切扩散)今日大胜。</p></div>

<h2>九、校准记分卡 · 对 07-07 预判的结算</h2>
<div class="card"><table>
<tr><th>07-07 我的预判</th><th>07-08 真实</th><th>判定</th></tr>
<tr><td>华天2板确认+带半导体梯队(带不出=首板套利)</td><td>未涨停未入强势池,冲高回落</td><td class="dA">✓ 命中(首板套利/未带梯队)</td></tr>
<tr><td>恒尚炸板/低开=退潮加速信号弹</td><td>一字7板续封未炸</td><td class="dB">◐ 高危未触发</td></tr>
<tr><td>万通3板补断层</td><td>收+4.84%未涨停,3板未补</td><td class="dA">✓ 命中(断层未补)</td></tr>
<tr><td>宜宾纸业高位孤标看弱</td><td>收-4.96%</td><td class="dA">✓ 命中</td></tr>
<tr><td>紫光规避(除非竞价转强)</td><td>今晨打脸重新点火,收+6.80%未封板</td><td class="dC">✗ 打脸(算力方向对/规避判错)</td></tr>
<tr><td>周期=退潮空仓0-2成 <span class="mut">(vs米开混沌4-5成)</span></td><td>涨停回升47/算力赚钱,但跌停41/量能缩</td><td class="dB">◐ 米开占优/我过保守</td></tr>
<tr><td>主线锚半导体 <span class="mut">(vs米开锚机器人)</span></td><td>半导体哑火,真主线=算力(浪潮业绩)</td><td class="dC">✗ 锚错(米开泼冷水华天=对)</td></tr>
<tr><td>产业逻辑:数据港IDC洼地/浪潮整机=高低切候选</td><td>浪潮一字+数据港+华勤全在算力低位环节点火</td><td class="dA">✓✓ 大胜</td></tr>
</table>
<p style="margin-top:10px"><b>自评(四维记账):</b><b class="s-ok">产业逻辑✓✓大胜</b>(高低切扩散全兑现)、<b class="s-ok">席位✓</b>(方向情报浪潮爆买准)、<b class="s-mid">题材△</b>(方向科技对/载体锚错半导体)、<b class="s-mid">竞价△</b>(回暖判对/修复启动打折)、<b class="s-weak">周期✗需修正</b>(退潮空仓教条过保守)。核心教训:①退潮要区分全面退潮与结构分化;②主线判断穿透行业字段;③产业逻辑量化位置法是我的强项维度,继续强化。</p></div>

<div class="foot"><b>本页为 07-08 冻结存档</b>,只加不删。数据取自真实盘后,A档可验证/C档只能实盘。为 Claude 训练产物,非买卖指令。</div>"""
J["archive_body"]=archive

# 最终落盘
out="_学习/judgment_20260708.json"
json.dump(J, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("archive ok", len(archive))
print("bodies keys:", list(J["bodies"].keys()))
print("saved ->", out)
