# -*- coding: utf-8 -*-
import json,re
idx=open('/tmp/idx.txt').read(); cyc=open('/tmp/cyc.txt').read(); thm=open('/tmp/thm.txt').read()
J=json.load(open('_学习/judgment_20260708.json',encoding='utf-8'))
def grab(t,a,b=None):
    i=t.find(a)
    if i<0: return ''
    if b is None: return t[i:]
    j=t.find(b,i+len(a))
    return t[i:j] if j>=0 else t[i:]
# ---- 复用块 ----
hero=grab(idx,'<div class="hero">','<h2')
gate=grab(idx,'<h2>四层关系','<h2>四维')            # 四层gate+拐点预警
kanpai=grab(idx,'<h2>四维 · 操盘手看牌','<h2>我的认知迭代')
idx_die=grab(idx,'<h2>我的认知迭代','<div class="foot"')
foot=grab(idx,'<div class="foot"')
huanjing=grab(idx,'<h2>环境','<h2>四层关系')         # 环境strip → 下沉cycle
# 观察点表(原文)+荐票源注入
gtable=grab(idx,'<h2 class="hot">明日核心观察点','<h2>环境')
rep=[
 ('四维✓✓✓✓</b><br><span class="tag2 t-attack">进攻观察</span>','四维✓✓✓✓</b><br><span class="mut">荐票:5路全荐(产业·题材·席位·竞价·质量)</span><br><span class="tag2 t-attack">进攻观察</span>'),
 ('三维✓✓·竞价待验</span><br><span class="tag2 t-attack">进攻观察</span>','三维✓✓·竞价待验</span><br><span class="mut">荐票:产业逻辑+题材(2路)</span><br><span class="tag2 t-attack">进攻观察</span>'),
 ('二维✓·产逻/题材待验</span><br><span class="tag2 t-watch">观察</span>','二维✓·产逻/题材待验</span><br><span class="mut">荐票:席位+涨停质量Top5(2路)</span><br><span class="tag2 t-watch">观察</span>'),
 ('身位✓·席位质量弱</span><br><span class="tag2 t-watch">高危观察</span>','身位✓·席位质量弱</span><br><span class="mut">荐票:涨停质量(身位·3板)</span><br><span class="tag2 t-watch">高危观察</span>'),
 ('情绪孤票·断层</span><br><span class="tag2 t-avoid">高危规避</span>','情绪孤票·断层</span><br><span class="mut">荐票:无(题材情绪监控·规避)</span><br><span class="tag2 t-avoid">高危规避</span>'),
 ('位置到位</span><br><span class="tag2 t-avoid">规避</span>','位置到位</span><br><span class="mut">荐票:无(规避)</span><br><span class="tag2 t-avoid">规避</span>'),
]
for a,b in rep: gtable=gtable.replace(a,b)
# 表头加"荐票·共振·类型",hint改五路
gtable=gtable.replace('<th>共振·类型</th>','<th>荐票源·共振·类型</th>')
gtable=re.sub(r'(<h2 class="hot">明日核心观察点.*?</h2>)\s*<div class="hint">.*?</div>',
  r'\1<div class="hint">五路荐票综合(竞价/席位/题材/产业逻辑/涨停复盘质量)→总agent裁决。每只标荐票来源(几路荐)+四维共振数+类型。给观察点不给买卖指令;含规避型。</div>',gtable,flags=re.S)

# ================= INDEX v2(判断+看牌,瘦身) =================
J['bodies']['index']=hero+'\n'+gtable+'\n'+gate+'\n'+kanpai+'\n'+idx_die+'\n'+foot

# ================= CYCLE v2(环境下沉+攻防总开关) =================
huanjing2=huanjing.replace('<h2>环境 · 退潮末期·结构分化</h2>','<h2>环境 · 量能台阶与涨跌停(四层顶层)</h2>')
gongfang=('<h2>攻防仓位总开关(量能台阶→仓位映射)</h2>'
 '<div class="card"><div class="gate">'
 '<div class="g"><div class="t">量能档</div><div class="s s-weak">2.56万亿·缩</div></div>'
 '<div class="g"><div class="t">周期阶段</div><div class="s s-weak">退潮末期</div></div>'
 '<div class="g"><div class="t">情绪三态</div><div class="s s-mid">结构分化</div></div>'
 '<div class="g"><div class="t">★仓位档</div><div class="s s-mid">防守·仅算力主线内3-4成</div></div></div>'
 '<p style="margin-top:12px"><b>总开关逻辑:</b>量能缩(破3万亿)+跌停41+连板断层=退潮末期→米开映射本应0-2成空仓;但算力单主线业绩兑现吸血=结构性分化,故<b>非全面空仓,改"主线内3-4成、主线外空"</b>。转向:量能重回3万亿上方+跌停缩至20内+算力上3板→升攻;量能续缩+算力断板→退潮加速回0-2成。</p></div>')
J['bodies']['cycle']=huanjing2+'\n'+gongfang+'\n'+cyc

# ================= THEME v2(判定+生命周期+龙头,删全表) =================
t_pandin=grab(thm,'<h2>〇 主流判定','<h2 class="hot">一 三层')
t_zhuxian=grab(thm,'<h2>二 我的主线判断','<h2>三 核心标的与龙头')
t_hexin=grab(thm,'<h2>二、核心标的分析','<h2>三、龙头识别')
t_longtou=grab(thm,'<h2>三、龙头识别','<h2>我的认知迭代')
t_die=grab(thm,'<h2>我的认知迭代')
link=('<div class="card"><p class="mut">全量47只涨停的三层题材归位表(大方向→环节→个股+质量分)见 '
      '<a href="limitup.html" style="color:var(--accent)"><b>涨停复盘页</b></a>——题材归属唯一真源在那里,本页只做方向判定与龙头。</p></div>')
t_zhuxian=t_zhuxian.replace('<h2>二 我的主线判断(操盘手读法)</h2>','<h2>主流生命周期与主线判断</h2>')
J['bodies']['theme']=t_pandin+'\n'+link+'\n'+t_zhuxian+'\n'+t_hexin+'\n'+t_longtou+'\n'+t_die

json.dump(J,open('_学习/judgment_20260708.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('重建完成 lens:',{k:len(v) for k,v in J['bodies'].items()})
