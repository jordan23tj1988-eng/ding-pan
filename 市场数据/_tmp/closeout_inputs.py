import sys,json,re,pathlib,importlib.util,shutil,datetime,html,hashlib
R=pathlib.Path(r'D:\股票数据\市场数据'); L=R/'_学习'; D='20260911';sys.path.insert(0,str(R))
B=R/'_tmp'/'codex_closeout_backup';B.mkdir(exist_ok=True)
def rd(n):return json.loads((L/n).read_text(encoding='utf-8-sig'))
def put(n,v):
 p=L/n
 if p.exists() and not (B/n).exists(): (B/n).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,B/n)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2) if not isinstance(v,str) else v,encoding='utf-8')
def mod(name):
 spec=importlib.util.spec_from_file_location(name,R/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
j=rd('judgment_'+D+'.json');e=mod('情绪先行指标'); t=e.load_out(); old=json.dumps({k:v for k,v in t.items() if k!=D},sort_keys=True)
t[D]={'日':D,'晋级':e.promo(D,'20260910',e.load_ths()),'核按钮':e.nuke(D,'20260910'),'昨日涨停溢价':t[D].get('昨日涨停溢价')};t[D]['触发器']=e.triggers(D,t)
put('_情绪先行指标.json',t);e.card(D,t)
assert old==json.dumps({k:v for k,v in e.load_out().items() if k!=D},sort_keys=True)
# Correct false missing-source statements; independent continuous ticks remain unavailable.
a=rd('auction判断_'+D+'.json');a['判断']['证据'][-1]='[实证] 竞价快照存档/20260911_meta.json：ifind_rt于09:26采集5461行静态快照；可核验静态成交额，不能据此还原09:25之前逐笔大单或连续变化。';a['判断']['独立盲区声明'][0]='静态竞价快照存在；未完成09:25精确排名复核，且连续逐笔与撤单轨迹不足。';put('auction判断_'+D+'.json',a)
lo=rd('logic判断_'+D+'.json');lo['判断']['证据'][0]=lo['判断']['证据'][0].replace('炸板22只','炸板18只');put('logic判断_'+D+'.json',lo)
# Actual-source narrative fills previously empty fixed sections.
def add(rt,title,text):
 j['bodies'][rt]+=f'\n<h2>{title}</h2><div class="card"><p>{html.escape(text)}</p></div>\n'
add('index','五路看牌','[实证] 五路目标日判断：竞价仅观察评分池；席位路不主动买入；题材、逻辑和涨停质量均无正式荐票。机械跨路筛选卡展示机器候选，不能替代五路自主交易计划。六路模拟盘收盘状态及指令由引擎看板直出。')
add('auction','今日竞价温度','[实证] 市场温度12.7；静态竞价快照09:26采集5461行。评分卡衡量池内历史执行差异，未完成精确09:25排名复核，因此保持观察，不升级实际买入。')
add('auction','竞价信号胜率追踪','[原文] 历史分桶高开≥5%执行均收-1.74%、胜率21.5%；这是评分库历史统计，不能替代目标日样本或个股胜率。样本窗口和分桶详见同日机器评分库卡，继续保留高开过滤。')
add('logic','中报预增雷达','[实证] 同日雷达：预增扭亏798、未发酵606、成色A共振65、行情缺失34。以上是研究候选统计，尚未逐票完成公告与当日产业催化双源复核，不进入正式荐票。')
# Rebuild seven canonical cycle sections: module renderer slices literal 一..七 boundaries.
temp=rd('_市场温度表.json')[D];v=t[D]['晋级'];n=t[D]['核按钮']; mc=mod('module_render_cycle')
head='<div class="hero"><div class="kick">周期主判 · 20260911收盘</div><h1>冰点防守，等待承接质量改善</h1><p class="stance">[原文] C档防守，实际以空仓观察为主；研究观察上限0至2成不构成买入指令。</p></div>'
parts=[head]
def c(title,body):parts.append('<h2>'+title+'</h2>'+body)
def p(text):return '<div class="card"><p>'+html.escape(text)+'</p></div>'
c('一 量能台阶',p('[实证] 成交额19719亿元，与09-10同口径值持平；成交额单项不能证明资金主动扩张。温度由11.7至12.7，仍在冰点区。'))
c('二 先行指标',p(f"[实证] 明确以09-10为前一交易日：一进二率{v['一进二率']:.1%}，二进三率{v['二进三率']:.1%}，高度晋级率{v['高度晋级率']:.1%}；核按钮{n['今日跌停回杀']}/{n['昨日涨停数']}={n['核按钮率']:.1%}。连续板口径与普通连板数分布不同；有间断涨停不按连续晋级计。指标提示与C档防守并存，不单独触发开仓。"))
votes=[]
for rt in ['auction','lhb','theme','logic','limitup']:
 z=rd('周期投票_'+rt+'_'+D+'.json');votes.append(rt+' '+z['stage']+'·'+z['direction'])
stages=['冰点','启动','发酵','高潮','退潮']
c('三 情绪五阶段 · 周期投票',p('[原文] 主判冰点·降；实际投票：'+'；'.join(votes)+'。平票保留为中性分歧。')+'<div class="stages">'+''.join('<div class="stage'+(' on' if x=='冰点' else '')+'">'+x+'</div>' for x in stages)+'</div>')
c('四 连板梯队',p('[实证] 涨停40，普通连板统计：首板33、二板4、三板2、四板1；瑞尔特为最高4板。元件9只但最高2板，行业聚集不能代替经公告核实的主线。'))
c('五 攻防 · 仓位总开关',p('[原文] C档防守：空仓为主，研究观察上限0至2成；不追高开、不接孤立最高板。封板率68.97%、炸板率31.0%、跌停21。只有封板质量、晋级率与可核实题材宽度同步改善后再复议。')+'<div class="posmeter"><i style="width:20%"></i><em style="left:20%"></em></div><div class="posml"><span>0成</span><span>观察上限0至2成</span><span>10成</span></div>')
c('六 自主深挖',p('[实证] 09:26静态竞价快照存在；连续盘中tick缺失。40只题材归位全部为B行业兜底，催化尚未验证。[原文] 后续若封板率≥80%、炸板率<20%，且至少一条可核实题材有3只以上及二板承载，再复议；目前不满足。'))
c('七 认知迭代','<div class="tl"><div class="tli"><b>09-11</b><p>晋级必须对齐紧邻交易日。此次补跑显式使用09-10，纠正默认THS缓存日期缺口导致跨日错配；静态快照与连续轨迹分别核验，不再将有快照写成无数据。</p></div></div>')
j['bodies']['cycle']='\n'.join(parts)
# Produce dated ledger blocks from authoritative builders; histories are read-only.
for rt,name,anchor,title in [('limitup','涨停复盘台账','LEDGER','涨停台账'),('lhb','龙虎榜台账','LHBLEDGER','龙虎榜台账')]:
 m=mod(name);summary,inner=m.build_from_data(D);m.save(D,summary,inner)
 # exact day and historical original blocks, filtered to no future dates
 files=sorted([f for f in pathlib.Path(m.STORE).glob('20*.json') if f.stem<=D],reverse=True)
 block=''
 for i,f in enumerate(files):
  x=json.loads(f.read_text(encoding='utf-8')); dd=x['date']; block+=f'<details class="chain"'+(' open' if i==0 else '')+f'><summary><b>{dd[4:6]}-{dd[6:8]}</b> <span class="chip">'+('最新' if i==0 else '存档')+'</span> '+html.escape(x['summary'])+'</summary><div class="inner">'+x['html']+'</div></details>'
 raw=j['bodies'][rt]; raw=re.sub('<!--'+anchor+'-->.*?<!--/'+anchor+'-->','',raw,flags=re.S)
 j['bodies'][rt]=raw+'<h2>'+title+'</h2><p>[实证] 当日日块按权威数据生成，历史原文保留。机器排序不等于自主买入。</p><!--'+anchor+'-->'+block+'<!--/'+anchor+'-->'
m=mod('竞价池结算归档'); block=m.build(); assert '09-10池终结算' in block and '09-11池终结算' not in block
j['bodies']['auction']=re.sub(r'<!--POOLLEDGER-->.*?<!--/POOLLEDGER-->','',j['bodies']['auction'],flags=re.S)+'<h2>二 昨日池结算</h2>'+block
# Correct residual false-source statements in dated bodies.
for rt,b in j['bodies'].items():
 b=b.replace('目标日无真实竞价快照','目标日有09:26静态竞价快照，连续逐笔轨迹未补齐').replace('缺少目标日竞价快照','目标日静态竞价快照存在，尚缺连续轨迹').replace('炸板22只','炸板18只')
 j['bodies'][rt]=b;put(rt+'_body_'+D+'.html',b)
put('judgment_'+D+'.json',j)
print('repaired source facts, seven cycle sections, missing fixed narratives and three ledger injections')
