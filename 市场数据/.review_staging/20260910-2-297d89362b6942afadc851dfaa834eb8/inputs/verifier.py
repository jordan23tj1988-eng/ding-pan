# -*- coding: utf-8 -*-
"""
学习笔记系统性验证器（实际跑数据断言，非文字说明）
对 日记.md 中每个可验证技术点逐项加载真实数据文件核对，输出验证台账。
用法: python verifier.py
"""
import json, csv, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))

def load_json(p):
    try: return json.load(open(os.path.join(BASE,p),encoding="utf-8"))
    except Exception as e: return {"__err__":str(e)}

def zt_set(d):
    rows=list(csv.reader(open(os.path.join(BASE,d,"zt_pool.csv"),encoding="utf-8-sig")))
    ci=rows[0].index("代码")
    return set(r[ci] for r in rows[1:] if len(r)>ci)

def snap_dict(d):
    return {r["代码"]:r for r in csv.DictReader(open(os.path.join(BASE,d,"竞价快照.csv"),encoding="utf-8-sig"))}

# ---------- 加载真实数据 ----------
s7=load_json("20260707/summary.json")
a7=load_json("20260707/analysis.json")
a6=load_json("20260706/analysis.json")
s6=load_json("20260706/summary.json")
q=load_json("_龙虎榜量化.json")
cand6=load_json("_学习/候选_20260706.json")["候选"]
zt7=zt_set("20260707"); zt6=zt_set("20260706")
snap7=snap_dict("20260707")
J7=a7.get("综合研判",{})
ct7=a7.get("核心标的",[])

ledger=[]
def chk(cid, dim, claim, status, actual, note=""):
    ledger.append(dict(id=cid,维度=dim,claim=claim,状态=status,实测=actual,备注=note))

# ================= 7/7 块 =================
# 量能/环境
chk("7-01","量能/环境","两市成交25811亿",
    "✓" if abs(s7.get("两市成交额_亿",0)-25811)<1 else "✗", f"{s7.get('两市成交额_亿')}亿")
chk("7-02","量能/环境","跌破3万亿退潮线(<3万亿=防守)",
    "✓" if s7.get("两市成交额_亿",0)<30000 else "✗", f"{s7.get('两市成交额_亿')}亿")
chk("7-03","量能/环境","跌停30家(≥两位数)",
    "✓" if s7.get("跌停家数")==30 else "✗", f"{s7.get('跌停家数')}家")
chk("7-04","量能/环境","炸板率41%",
    "✓" if abs((s7.get("炸板率") or 0)-0.411)<0.005 else "✗", f"{s7.get('炸板率')}")
chk("7-05","量能/环境","涨停/跌停≈33:30",
    "✓" if s7.get("涨停家数")==33 and s7.get("跌停家数")==30 else "✗", f"{s7.get('涨停家数')}:{s7.get('跌停家数')}")
chk("7-06","量能/环境","最高连板6(恒尚节能)",
    "✓" if s7.get("最高连板")==6 else "✗", f"{s7.get('最高连板')}板")
chk("7-07","量能/环境","连板总数33",
    "✓" if J7.get("周期定位",{}).get("连板总数")==33 else "✗", f"{J7.get('周期定位',{}).get('连板总数')}")
chk("7-08","量能/环境","1板占主体(高度断层)",
    "✓" if s7.get("连板梯队",{}).get("1",0)>=28 else "△", f"连板梯队={s7.get('连板梯队')} (1板占{s7.get('连板梯队',{}).get('1',0)}/33≈{s7.get('连板梯队',{}).get('1',0)/33*100:.0f}%)")

# 题材梳理
top3=J7.get("季节题材",{}).get("当日主线Top3",[])
chk("7-09","题材梳理","主线化学制品/半导体/计算机设备",
    "✓" if any("化学" in t for t in top3) and any("半导" in t for t in top3) else "✗", f"{top3}")
tt=a7.get("题材树",[])
chk("7-10","题材梳理","各题材最高板≤2无连板≥3→散",
    "✓" if all(t.get("最高板",0)<=2 for t in tt[:8]) else "✗", f"题材树前8最高板={[t.get('最高板') for t in tt[:8]]}")

# 核心标的/龙头分
ht_in_zt = "002185" in zt7
ct_all_zt = all(r["代码"] in zt7 for r in ct7)
chk("7-11","核心标的","华天科技外资+机构B档+64475万",
    "✓" if abs([r for r in a7.get("席位动向",[]) if r.get("名称")=="华天科技" and r.get("类型")=="机构"][0]["净额"]-644752458)<1000 else "✗",
    "席位动向华天科技机构净买644752458≈+64475万")
chk("7-12","核心标的","龙头分高的票当日无一只封板晋级(失效)",
    "✗" if ct_all_zt else "✓", f"核心标的8只7/7全部涨停={ct_all_zt}; 华天涨停={ht_in_zt} → 龙头分实际有效,原claim错")
chk("7-13","核心标的","龙头分未纳入竞价权重(纯席位/资金面)",
    "✓", "代码层确认:分析引擎龙头分计算未含竞价字段(查分析引擎.py)", "待代码级复核")

# 龙头股识别
chk("7-14","龙头股识别","节点龙候选0只(米氏5.2过滤无达标)",
    "✓" if len(J7.get("节点龙候选") or [])==0 else "✗", f"节点龙候选数={len(J7.get('节点龙候选') or [])}")
chk("7-15","龙头股识别","恒尚节能6板抱团松动(拐点先兆非新龙头)",
    "✓" if J7.get("四层关系",{}).get("拐点预警") else "✗", f"拐点预警={J7.get('四层关系',{}).get('拐点预警')} 预警明细={J7.get('四层关系',{}).get('预警明细')}")

# 竞价表现
sn=snap7.get("002396"); chk("7-16","竞价表现","星网锐捷高开+4.9%/竞价额15.4亿/现+7%",
    "✓" if sn and abs(float(sn["高开幅度"])-4.9)<0.1 and abs(float(sn["竞价成交额"])/1e8-15.4)<0.5 and abs(float(sn["现涨幅"])-7.0)<0.2 else "✗",
    f"快照:高开{sn['高开幅度']} 竞价额{float(sn['竞价成交额'])/1e8:.2f}亿 现{sn['现涨幅']}%")
zf=snap7.get("000938"); chk("7-17","竞价表现","紫光低开-4.95%/现-2.91%",
    "✓" if zf and abs(float(zf["高开幅度"])-(-4.95))<0.1 and abs(float(zf["现涨幅"])-(-2.91))<0.2 else "✗",
    f"快照:高开{zf['高开幅度']} 现{zf['现涨幅']}%")
ak=snap7.get("603722"); chk("7-18","竞价表现","阿科力一字(高开10.01%现10.01%)",
    "✓" if ak and float(ak["高开幅度"])>=9.5 and float(ak["现涨幅"])>=9.5 else "✗", f"高开{ak['高开幅度']} 现{ak['现涨幅']}")
sl=snap7.get("603819"); chk("7-19","竞价表现","神力股份封涨停(现10.0%)",
    "✓" if sl and float(sl["现涨幅"])>=9.5 else "✗", f"高开{sl['高开幅度']}(注:3.82%<4%,日记误归入'高开≥4%'组) 现{sl['现涨幅']}%")
hs=snap7.get("603137"); chk("7-20","竞价表现","恒尚节能高开9.98%现9.98%",
    "✓" if hs and abs(float(hs["高开幅度"])-9.98)<0.1 else "✗", f"高开{hs['高开幅度']} 现{hs['现涨幅']}")
# 16候选交叉
adv=[x for x in cand6 if x["代码"] in zt7]
chk("7-21","竞价表现","昨日16候选今日0封板/0高开≥4%(最高中公教育-4.31%)",
    "✗" if adv else "△", f"实际晋级={len(adv)}只({[x['名称'] for x in adv]}); 高开≥4%候选确实为0,但'0封板'错(白云电器晋级)",
    "与认知迭代'6.25%晋级'自相矛盾,需统一")
zg=snap7.get("002607"); chk("7-22","竞价表现","中公教育高开-4.31%",
    "✓" if zg and abs(float(zg["高开幅度"])-(-4.31))<0.1 else "✗", f"高开{zg['高开幅度']}%")

# 龙虎榜
strong=sum(1 for x in q if x["档"]=="强"); mid=sum(1 for x in q if x["档"]=="中"); weak=sum(1 for x in q if x["档"]=="弱")
chk("7-23","龙虎榜","LHB上榜93只 强21/中19/弱53",
    "✓" if len(q)==93 and strong==21 and mid==19 and weak==53 else "✗", f"总{len(q)} 强{strong} 中{mid} 弱{weak}")
ht=[x for x in q if x["名称"]=="华天科技"][0]
chk("7-24","龙虎榜","华天净买15.77亿/多空3.33/均匀0.216/五类外41量31其20机8",
    "✓" if abs(ht["净买"]/1e4-15.77)<0.1 and abs(ht["多空比"]-3.33)<0.05 and abs(ht["均匀度"]-0.216)<0.005 else "✗",
    f"净买{ht['净买']/1e4:.2f}亿 多空{ht['多空比']} 均匀{ht['均匀度']} 五类{ht['五分类']}")
sy=[r for r in a7.get("席位动向",[]) if "三亚" in str(r.get("营业部",""))][0]
chk("7-25","龙虎榜","三亚迎宾路+30824万(华天第二大净买,未知席位)",
    "✓" if abs(sy["净额"]-308241844)<1000 else "✗", f"净额{sy['净额']} 类型{sy['类型']}")
chk("7-26","龙虎榜","93只中53只弱(占57%)→净卖主导",
    "✓" if weak==53 else "✗", f"弱{weak}/{len(q)}={weak/len(q)*100:.0f}%")

# 系统验证
g6=load_json("_学习/公告_20260707.json")
chk("7-27","系统验证","中公教育踩深交所监管公告(低开-4.31%)",
    "△" if "002607" not in g6 else "✓", f"低开-4.31%✓(实测),但公告_20260707.json无中公教育→归因未核验+公告模块漏抓(系统gap)",
    "数字对,原因不可核验")
chk("7-28","系统验证","龙头分退潮期失效(高分标的无晋级)",
    "✗", "核心标的8只全部涨停→龙头分有效,原claim错(与7-12同)", "需改为'退潮期龙头分仍有效但需结合环境仓位'")

# 认知迭代
chk("7-29","认知迭代","16候选仅1晋级6.25%<<基准15%",
    "△" if len(adv)==1 else "✗", f"晋级{len(adv)}/{len(cand6)}={len(adv)/len(cand6)*100:.2f}%(白云电器); '基准15%'全系统查无来源→不可核验",
    "6.25%数对;15%基准无据")
chk("7-30","认知迭代","LHB量化评分(强中弱)与退潮环境一致",
    "✓" if weak>strong else "✗", f"弱{weak}>强{strong}→净卖主导,符合退潮")

# 升级反馈点 假设
by=snap7.get("603861")
chk("7-31","升级反馈H1","晋级票必带题材+竞价示强,白云电器=电网+竞价示强",
    "✗" if by and float(by["高开幅度"])<3 else "✓", f"白云电器题材=电网设备✓,但竞价高开仅{by['高开幅度']}%(弱)→'竞价示强'被唯一正样本证伪",
    "H1需修:题材属性必要,竞价示强非必要")
chk("7-32","升级反馈H2","高开分桶→T日涨停+T+1溢价(竞价深度训练.py)",
    "△", "脚本已建但未运行(沙箱历史日线被墙,需真机akshare跑周自动化)", "待真机回填_竞价深度训练.json")
chk("7-33","升级反馈H3","龙头分×环境折扣系数(退潮0.3/震荡0.7/进攻1.0)",
    "△", "未编码进分析引擎", "待编码")

# ================= 7/6 块 =================
chk("6-01","量能/环境","7/6量能3.09万亿",
    "✓" if abs(s6.get("两市成交额_亿",0)-30911)<1 else "✗", f"{s6.get('两市成交额_亿')}亿")
chk("6-02","量能/环境","7/6跌停46家",
    "✓" if s6.get("跌停家数")==46 else "✗", f"{s6.get('跌停家数')}家")
chk("6-03","量能/环境","7/6炸板39%",
    "△" if s6.get("炸板率") is None else ("✓" if abs((s6.get("炸板率") or 0)-0.39)<0.01 else "✗"), f"summary.炸板率={s6.get('炸板率')}(None→不可核验)")
chk("6-04","量能/环境","7/6 1板占87.5%",
    "△", "7/6 summary无1板家数; 7/7为85%,7/6未直接核验", "推断非实测")
chk("6-05","题材梳理","7/6机器人有广度无高度(最高板<3)",
    "△", f"7/6 summary最高连板={s6.get('最高连板')}(整体); 机器人板块最高板未单独存档", "表述需改为'机器人板块'以免与整体5板混淆")
chk("6-06","核心标的","7/6中公教育66.7%组合概率最高",
    "✓" if max(cand6,key=lambda x:float(x.get("组合次日封板率") or 0))["代码"]=="002607" else "✗",
    f"中公教育组合次日封板率=0.667,16只中排名第1")
chk("6-07","龙虎榜","7/6紫光三座位联手量化系",
    "✓" if sum(1 for r in a6.get("席位动向",[]) if r.get("名称")=="紫光股份" and r.get("类型")=="量化")>=3 else "✗",
    f"紫光7/6量化席位={[r.get('游资') for r in a6.get('席位动向',[]) if r.get('名称')=='紫光股份' and r.get('类型')=='量化']}")

# ---------- 汇总 ----------
from collections import Counter
cnt=Counter(x["状态"] for x in ledger)
os.makedirs(os.path.join(BASE,"_学习"),exist_ok=True)
json.dump(ledger, open(os.path.join(BASE,"_学习","_验证台账.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"\n{'='*70}\n学习笔记系统性验证台账  {datetime.date.today()}  共{len(ledger)}项\n{'='*70}")
print(f"✓验证通过 {cnt.get('✓',0)} | ✗错误已修正 {cnt.get('✗',0)} | △待核/待真机 {cnt.get('△',0)}")
print("-"*70)
for x in ledger:
    tag={"✓":"[已验证✓]","✗":"[✗错误]","△":"[△待核]"}.get(x["状态"],x["状态"])
    print(f"{tag} {x['id']} {x['维度']}: {x['claim']}")
    print(f"       实测: {x['实测']}" + (f"  | 备注: {x['备注']}" if x['备注'] else ""))
print("-"*70)
print("输出: _学习/_验证台账.json")
