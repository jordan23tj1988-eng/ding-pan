# -*- coding: utf-8 -*-
import json,re
J=json.load(open('_学习/judgment_20260708.json',encoding='utf-8'))
b=J['bodies']['index']

# ---------- ① 删"今晨竞价兑现"卡片 ----------
DIV=re.compile(r'<div\b|</div>')
def match_div(s,start):
    depth=0
    for m in DIV.finditer(s,start):
        if m.group()=='</div>':
            depth-=1
            if depth==0: return m.end()
        else: depth+=1
    return len(s)
i=b.find('今晨竞价兑现')
cs=b.rfind('<div class="card',0,i)
ce=match_div(b,cs)
b=b[:cs]+b[ce:]

# ---------- ② 观察点表:固定布局+缩短荐票文案(修出格) ----------
b=b.replace('<div class="card hotcard"><table>',
  '<div class="card hotcard"><table style="table-layout:fixed;width:100%"><colgroup><col style="width:13%"><col style="width:29%"><col style="width:36%"><col style="width:22%"></colgroup>')
short=[('荐票:5路全荐(产业·题材·席位·竞价·质量)','荐票·5路全荐'),
 ('荐票:产业逻辑+题材(2路)','荐票·产业+题材'),
 ('荐票:席位+涨停质量Top5(2路)','荐票·席位+质量'),
 ('荐票:涨停质量(身位·3板)','荐票·质量(3板)'),
 ('荐票:无(题材情绪监控·规避)','荐票·无(规避)'),
 ('荐票:无(规避)','荐票·无')]
for a,c in short: b=b.replace(a,c)

# ---------- ③ 看牌→5路荐票,每框=荐的票+一句说明 ----------
newcards=('<h2>五路荐票 · 各子agent荐的票 <span class="badge bA">07-08</span></h2>'
 '<div class="hint">五个子agent各自维度独立荐票→总agent综合裁决上首页观察点。每框=这个agent荐的是谁+一句为什么。点卡进对应页看深读。</div>'
 '<div class="two">'
 '<a class="mith" href="logic.html"><h3>产业逻辑 · 该不该涨 <span class="arw">→</span></h3>'
 '<p>荐票:<b>浪潮信息</b>(整机业绩+288%硬逻辑)、<b>数据港</b>(IDC深洼地扩散)。<br><span class="mut">高低切扩散兑现,低位环节点火;封测华天已到位掩护出逃。</span></p></a>'
 '<a class="mith" href="theme.html"><h3>题材 · 方向gate <span class="arw">→</span></h3>'
 '<p>荐票:<b>算力线</b>(聚类口径6/6主流,27只跨6环节)。<br><span class="mut">方向明确但高度弱(最高3板);题材归属以涨停复盘为准。</span></p></a>'
 '<a class="mith" href="lhb.html"><h3>席位 · 钱在买什么 <span class="arw">→</span></h3>'
 '<p>荐票:<b>浪潮信息</b>(顶级资金1.74亿+外资4亿)、<b>星网锐捷</b>(顶级量化2亿)。<br><span class="mut">真金集中算力,无S档撤退;方向高度共振。</span></p></a>'
 '<a class="mith" href="auction.html"><h3>竞价 · 点没点火 <span class="arw">→</span></h3>'
 '<p>荐票:<b>浪潮信息</b>(9:25一字54亿强封)。<br><span class="mut">一字=三口径通吃信号(T+1 77.8%);恒尚7板续命,软件系秒板。</span></p></a>'
 '<a class="mith" href="limitup.html"><h3>涨停复盘 · 质量分 <span class="arw">→</span></h3>'
 '<p>荐票:质量Top5#1 <b>浪潮信息</b>(质量分100·一字×封单≥2%)。<br><span class="mut">纯机械因子打分,预测T1 90%/+8.6%;有利空/末端由总agent压。</span></p></a>'
 '</div>')
b=re.sub(r'<h2>四维 · 操盘手看牌.*?(?=<h2>我的认知迭代)',newcards+'\n\n',b,flags=re.S)

J['bodies']['index']=b
json.dump(J,open('_学习/judgment_20260708.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('index修完,',len(b),'字符 | 残留今晨竞价兑现卡?',('今晨竞价兑现' in b),'| 看牌卡数:',b.count('class="mith"'))
