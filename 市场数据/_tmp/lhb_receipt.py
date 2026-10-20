# -*- coding: utf-8 -*-
import json,os
os.chdir(r"D:/股票数据/市场数据")
d='20261020'
# 1) 战绩画像 归因 补位
p=f'_学习/子agent增强/战绩画像_lhb_{d}.json'
img=json.load(open(p,encoding='utf-8'))
zero=[x['荐票日'] for x in img['按日'] if x['执行胜率']=='0/0']
win=[x for x in img['按日'] if x['执行胜率'] not in ('0/0',)]
def wr(s):
    a,b=s.split('/');return int(a),int(b)
tw=sum(wr(x['执行胜率'])[0] for x in win); tn=sum(wr(x['执行胜率'])[1] for x in win)
best=sorted([x for x in win if x['均收'] is not None],key=lambda x:-x['均收'])[:3]
worst=sorted([x for x in win if x['均收'] is not None],key=lambda x:x['均收'])[:3]
img['归因']={
 "样本":[{"口径":"含空仓日的全部荐票日","日数":len(img['按日']),"笔数":"41/95"},
        {"口径":"剔除0/0空仓日后的有效日","日数":len(win),"笔数":f"{tw}/{tn}","胜率":"%.1f%%"%(tw/tn*100) if tn else None}],
 "空仓段":{"日数":len(zero),"起":zero[0] if zero else None,"止":zero[-1] if zero else None,
          "说明":"0/0 为『当日发出版只有不到1只可执行』或『口径缺段』造成，非策略主动空仓；该段占全部日数 %d/%d，会稀释合计胜率的解释力"%(len(zero),len(img['按日']))},
 "最赚三日":[{"荐票日":x['荐票日'],"胜率":x['执行胜率'],"均收":x['均收']} for x in best],
 "最亏三日":[{"荐票日":x['荐票日'],"胜率":x['执行胜率'],"均收":x['均收']} for x in worst],
 "主导归因":"发出版口径(买入前五明细S/A席净额加总)存在买侧偏置，导致无源1/双源分歧的不可核票进入Top5；20261019(3/3,+0.77)与20261020(0/5可用)均复现该模式",
 "本路处置":"20261020起在人工判断层加双源前置过滤(一致 ∧ 源1净买>0)，机械层修法已给出一行补丁规格(见 lhb判断_20261020.json#认知迭代[2])",
 "写入":{"路":"lhb","日期":d,"来源":"本路席位判官"}}
json.dump(img,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('画像归因已写', len(zero), tw, tn)

# 2) 能力使用回执片段
rc={"日期":d,"路由":"lhb","路名":"席位命门(龙虎榜)",
 "能力":[{"id":"extension:cap-lhb-netbuy-valid","名称":"龙虎榜质量库·净买占比因子有效",
          "来源":"_学习/_龙虎榜质量库.json#因子.净买占比","状态":"applied",
          "effect":"①否决>20%最差桶3只(600178 28.14%/300466 28.62%/603696 24.39%，桶内n=136/36.0%/-0.59%)，其中600178为3板封单292%的强封票，若不接该能力必入选；②以10-20%最优桶(n=454/50.0%/+0.26%)抬升600267(14.27%)/300115(11.03%)进观察池；③与双源负面过滤互为冗余(6只强矛盾票净买占比全在≤0桶)",
          "证据定位":"_学习/lhb判断_20261020.json#判断.证据[8]; #荐票.标的[0..2]; _学习/lhb_body_20261020.html 板块一『净买占比分桶』卡 + 板块五能力回执卡",
          "边界":"库mtime 2026-07-10(停更102天)、近窗rho=-0.5，只作否决与优先级，不作期望收益；不用该库T1读数"}],
 "说明":"本路本日无 rejected 项；能力预加载清单中 lhb 域仅此1条，已显式消费并写入判断.深挖。"}
json.dump(rc,open(f'_学习/能力回执_lhb_{d}.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('回执已写')
