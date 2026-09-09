import json, os, re
root='D:/股票数据/市场数据'; L=os.path.join(root,'_学习'); d='20260908'
J=os.path.join(L,'judgment_'+d+'.json')
j=json.load(open(J,encoding='utf-8-sig'))
# Consume the five independently written body files; retain their evidence verbatim.
bodies={}
for r in ['auction','lhb','theme','logic','limitup']:
 p=os.path.join(L,f'{r}_body_{d}.html')
 s=open(p,encoding='utf-8-sig').read() if os.path.exists(p) else '<div class="obs"><div class="obs-nm">'+r+' body unavailable</div></div>'
 # Ledger anchors are fixed contract anchors, not invented content.
 if r=='auction' and 'POOLLEDGER' not in s: s+='\n<div><!--POOLLEDGER--></div>'
 if r=='lhb' and 'LHBLEDGER' not in s: s+='\n<div><!--LHBLEDGER--></div>'
 if r=='limitup' and '<!--LEDGER-->' not in s: s+='\n<div><!--LEDGER--></div>'
 bodies[r]=s
T=json.load(open(os.path.join(L,'_市场温度表.json'),encoding='utf-8-sig'))[d]
S=json.load(open(os.path.join(root,d,'summary.json'),encoding='utf-8-sig'))
A=json.load(open(os.path.join(L,'总审_'+d+'.json'),encoding='utf-8-sig'))
P=json.load(open(os.path.join(L,'推演_'+d+'.json'),encoding='utf-8-sig'))
obs='''<div class="obs"><div class="obs-head"><span class="obs-nm">空仓为主</span><span class="mut">20260908</span><span class="obs-pos">C档防守</span></div><div class="obs-watch"><span class="obs-lab">环境</span>温度42.3·偏冷；涨停73、炸板37、封板率66.4%、最高4板。</div><div class="obs-rec"><span class="obs-lab2">触发/证伪</span>仅当宽度、晋级、高度、封板质量同步改善，才复议升档；当前不构成买入或成交指令。</div></div>'''
index=f'''<div class="rowA"><div class="hero"><div class="kick">REVIEW / {d}</div><h1>情绪复盘：偏冷环境，C档防守</h1><p>总审裁决：局部竞价强度与B档席位放量不足以推翻质量、主线和资金确认缺口。</p><span class="stance pill warn">C档防守</span></div><div class="kpi"><div><b>42.3</b><span>温度·偏冷</span></div><div><b>73</b><span>涨停</span></div><div><b>37</b><span>炸板</span></div><div><b>4</b><span>最高板</span></div></div></div>
<h2>一 总裁决 <span class="hint">环境→周期→题材→情绪</span></h2>{obs}
<h2>二 环境与量能 <span class="hint">真实收盘数据</span></h2><p>两市成交额19603.0亿；跌停0；炸板率33.6%。成交额为客观盘面字段，昨日溢价等缺失项不补造。</p>
<h2>三 周期与攻防 <span class="hint">周期主判：退潮·降</span></h2><p>周期主判为退潮·降。五路共识偏防守，竞价与席位存在局部强度但未形成可执行修复。</p>
<h2>四 五路看牌 <span class="hint">独立判断与对抗总审</span></h2><p>竞价C、席位原判B后裁决C、题材C、产业逻辑C、涨停质量C；席位B→C为本日主要分歧。</p>
<h2>五 明日观察 <span class="hint">条件先行，非交易指令</span></h2><p>观察出版、农化制品等分支是否形成宽度与晋级共振；观察S档是否回归；观察封板率与质量执1是否同步修复。</p>
<h2>六 拐点预警 <span class="hint">可证伪条件</span></h2><p>若题材宽度、至少2只晋级、最高板和封板质量同时改善，防守判断进入复议；若炸板率继续升高或高开闸门再度触发，防守强化。</p>
<h2>七 我的认知迭代 <span class="hint">最新在上</span></h2><p>今日把“竞价强度、席位放量、封板质量、产业题材”分开验收：局部强度不等于整体进攻环境。</p>'''
cycle=f'''<div class="rowA"><div class="hero"><div class="kick">CYCLE / {d}</div><h1>退潮·降：偏冷周期，防守优先</h1><p>温度42.3，封板率66.4%，主线未确认；先等修复证据。</p><span class="stance pill warn">退潮·降</span></div><div class="kpi"><div><b>42.3</b><span>温度</span></div><div><b>19603</b><span>成交额·亿</span></div><div><b>66.4%</b><span>封板率</span></div><div><b>0</b><span>跌停</span></div></div></div>
<h2>一 量能台阶 <span class="hint">两市成交额</span></h2><p>两市成交额19603.0亿，量能数据真实可追溯；不以单日量能替代情绪修复。</p>
<h2>二 情绪先行指标 <span class="hint">晋级与溢价</span></h2><p>涨停73、首板55、二板12、一进二率0.15；二进三率、高度晋级率、昨停溢价为null/unavailable。</p>
<h2>三 周期五阶段 <span class="hint">主判</span></h2><p>主判：退潮。局部竞价一字9只与B档净买是结构强点，但炸板37、质量执1最高45.9%未过门槛。</p>
<h2>四 三态攻防 <span class="hint">C档防守</span></h2>{obs}
<h2>五 梯队与高度 <span class="hint">连板结构</span></h2><p>梯队：1板55、2板12、3板3、4板3；最高连板4，未出现可确认的高度突破。</p>
<h2>六 五路周期投票 <span class="hint">主判与投票台账</span></h2><p>周期主判退潮·降；auction降、lhb平、theme降、logic降、limitup降，分歧未达当日复议阈值。</p>
<h2>七 我的认知迭代 <span class="hint">最新在上</span></h2><p>周期判断优先看可执行质量：数量回升、局部强度和成交额不能单独构成升档依据。</p>'''
bodies['index']=index; bodies['cycle']=cycle
j['date']=d; j['更新label']=d+' 复盘·C档防守'; j['一句话']='温度42.3偏冷，涨停73但炸板37、封板率66.4%，题材主线与高质量资金未确认，C档防守、空仓为主。'; j['ticker']='量能19603亿｜涨停73｜跌停0｜炸板率33.6%｜最高4板｜一进二15%｜主线未确认'; j['bodies']=bodies; j['archive_body']='<h2>20260908收盘存档</h2><p>温度42.3偏冷；涨停73、炸板37、最高4板、成交额19603.0亿；总审C档防守。缺失字段按null/unavailable留档。</p>'
tmp=J+'.tmp'
with open(tmp,'w',encoding='utf-8') as f: json.dump(j,f,ensure_ascii=False,indent=1)
os.replace(tmp,J)
print('judgment assembled',[(k,len(v)) for k,v in bodies.items()])
