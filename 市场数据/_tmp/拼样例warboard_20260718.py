# -*- coding: utf-8 -*-
"""一次性v2: 按真实规模(19只)拼 warboard 样例——0717涨停池真名+master真实持仓, 状态合成标SAMPLE。"""
import os, json, csv, glob, random
BASE = glob.glob("/sessions/*/mnt/股票数据/市场数据")[0] if not os.path.isdir(r"D:\股票数据\市场数据") else r"D:\股票数据\市场数据"
d = "20260717"
S = json.load(open(os.path.join(BASE, "_学习/_模拟盘/master/状态.json"), encoding="utf-8"))
hold = S["持仓"][0]
sm = json.load(open(os.path.join(BASE, d, "summary.json"), encoding="utf-8"))
cr = list(csv.DictReader(open(os.path.join(BASE, d, "concept_rank.csv"), encoding="utf-8-sig")))
zt = list(csv.DictReader(open(os.path.join(BASE, d, "zt_pool.csv"), encoding="utf-8-sig")))
random.seed(17)

def A(gap, verdict, note): return {"gap_pct": gap, "verdict": verdict, "note": note}
def tl(*a): return [list(x) for x in a]

cards = [
 # ── 已成交 2
 {"code":"603580","name":"艾艾精工","theme":"工程胶带·高度","sources":["竞价"],"status":"已成交","px":43.1,"chg_pct":-4.1,
  "why":"4板唯一高度板,低开进肉桶(竞价分桶:低开-3~0%桶T+1执行+2.1pp)","trigger":"低开-4%~0% → 开盘价买 12%",
  "abort":"低开<-4% / 高开>3%","sell":"破前日分时低点-2%离场(显式声明)",
  "auction":A(-2.4,"超预期","4板低开进trigger区,低开有肉"),
  "fill":{"time":"09:30:20","px":43.85,"rule":"trigger达成·下一tick"},
  "timeline":tl(("09:25","竞价-2.4%进trigger区"),("09:30","成交 ¥43.85"),("10:00","回落-4%,未触卖条件"))},
 {"code":"002766","name":"索菱股份","theme":"车路云","sources":["题材","质量"],"status":"已成交","px":4.02,"chg_pct":2.0,
  "why":"车路云+低价首板双共振,质量分A档,题材路主线荐票#2","trigger":"gap -1%~+4% → 开盘价买 8%",
  "abort":"高开>4% / 一字禁追","sell":"当日炸板即卖(显式);否则晚间表态",
  "auction":A(1.2,"符合预案","温和高开,封单预期内"),
  "fill":{"time":"09:30:20","px":3.99,"rule":"trigger达成·下一tick"},
  "timeline":tl(("09:25","竞价+1.2%符合"),("09:30","成交 ¥3.99"))},
 # ── 持有中 3
 {"code":hold["code"],"name":hold["name"],"theme":"医药BD出海","sources":["题材","总"],"status":"持有中","px":68.9,"chg_pct":1.2,
  "why":hold["reason"][:80],"trigger":"已于%s成交 ¥%s"%(hold["buy_date"],hold["buy_px"]),"abort":"—",
  "sell":"未声明盘中止损=持有,晚间表态","auction":A(1.8,"符合预案","高开温和,持有腿不动"),
  "hold":{"days":2,"pnl_pct":4.4},
  "timeline":tl(("07-16","开盘买 ¥66.00"),("09:25","盘点:符合预案"),("10:05","心跳:医药线走强,持有"))},
 {"code":"600816","name":"建元信托","theme":"金融防守","sources":["席位","总"],"status":"持有中","px":3.31,"chg_pct":0.9,
  "why":"(在持)金融权重防守仓,席位路机构3席+档(57.1%/+1.52%)","trigger":"已于07-16成交 ¥3.25","abort":"—",
  "sell":"跌破3.20撤(显式声明)","auction":A(0.3,"符合预案","平开缩量,防守仓稳"),
  "hold":{"days":2,"pnl_pct":1.8},"timeline":tl(("09:25","盘点:符合"),("10:00","心跳:缩量横盘"))},
 {"code":"300436","name":"广生堂","theme":"创新药BD","sources":["逻辑"],"status":"持有中","px":31.6,"chg_pct":-1.9,
  "why":"(在持)创新药BD链#3低位,logic路A池","trigger":"已于07-15成交 ¥32.4","abort":"—",
  "sell":"晚间表态;医药线批量转弱触B级评估","auction":A(-1.1,"恶化","低开破位感,给到预警观察"),
  "hold":{"days":3,"pnl_pct":-2.5},
  "timeline":tl(("09:25","盘点:恶化,挂预警"),("09:50","心跳:同链迪哲走强,对冲信号,再看30分钟"))},
 # ── 顺延 1
 {"code":"600343","name":"航天动力","theme":"商业航天","sources":["逻辑"],"status":"卖出顺延","px":12.06,"chg_pct":-10.0,
  "why":"(在持)商业航天链低位补涨,07-15买入","trigger":"已于07-15成交 ¥13.40","abort":"—",
  "sell":"今日开盘卖(昨晚指令);跌停封死→顺延","auction":A(-9.8,"恶化","竞价近跌停"),
  "fill":{"time":"09:30:00","px":None,"rule":"跌停封死·挂单顺延次日开盘"},
  "hold":{"days":3,"pnl_pct":-10.0},
  "timeline":tl(("09:25","竞价-9.8%恶化"),("09:30","跌停封死,顺延"),("10:10","封单4.2万手未开板"))},
 # ── 竞价新增观察 3
 {"code":"002677","name":"浙江美大","theme":"并购重组","sources":["竞价场新增"],"status":"观察","px":7.95,"chg_pct":4.6,
  "why":"3板梯队核心,竞价额2.4亿放量2.8倍居两市前列,昨烂板今竞价回封预期强(9:25决断)",
  "trigger":"开盘10分钟内回封且封单>8000万 → 下一tick买 ≤10%(C级帽)","abort":"9:40未回封 / 一字禁追",
  "sell":"当日炸板即卖(显式)","auction":A(4.6,"超预期","放量异动,两市竞价额前列"),
  "timeline":tl(("09:25","竞价场决断:放量异动入册"))},
 {"code":"600892","name":"大晟文化","theme":"传媒·疑新线","sources":["竞价场新增"],"status":"观察","px":4.71,"chg_pct":5.1,
  "why":"传媒超跌+竞价抢筹(gap+5.1%,竞价额1.1亿=昨全天1/4),疑似新题材首日点火(9:25决断)",
  "trigger":"仅观察,今日不参与(单日证据不足)","abort":"—","sell":"—",
  "auction":A(5.1,"超预期","竞价抢筹,观察是否新线"),
  "timeline":tl(("09:25","竞价场决断:疑似点火,只看不动"))},
 {"code":"301005","name":"超捷股份","theme":"商业航天","sources":["竞价场新增","逻辑"],"status":"观察","px":28.8,"chg_pct":3.2,
  "why":"商业航天紧固件,链上洼地环节,竞价放量+逻辑路昨晚watch共振(9:25决断升级)",
  "trigger":"10:00前站稳+3%且量比>3 → 下一tick买 ≤10%","abort":"回落<+1%",
  "sell":"T+2起看链条位置","auction":A(3.2,"超预期","watch票竞价共振"),
  "timeline":tl(("09:25","watch升级候选"))},
 # ── 待触发 7
 {"code":"300577","name":"开润股份","theme":"出口链","sources":["席位"],"status":"待触发","px":20.41,"chg_pct":0.2,
  "why":"紫阳东路净买1.2亿(≥1亿唯一跟随友好档65%/+0.65%),出口链首板",
  "trigger":"回踩开盘价±1%企稳且量比>2 → 下一tick买 8%","abort":"10:30未触发过期 / 跌破-3%",
  "sell":"T+2按席位撤退信号","auction":A(0.6,"符合预案","平开等回踩"),
  "timeline":tl(("09:25","符合,挂条件单"))},
 {"code":"003001","name":"中岩大地","theme":"雅下水电","sources":["质量"],"status":"待触发","px":19.6,"chg_pct":0.2,
  "why":"质量分Top3,基建+雅下水电标签,换手因子强","trigger":"gap 0~+3%回封 → 下一tick买 6%",
  "abort":"高开>5% / 竞价一字","sell":"晚间表态","auction":A(0.4,"符合预案","平开,封单一般"),
  "timeline":tl(("09:25","符合,等回封"))},
 {"code":"002097","name":"山河智能","theme":"军工装备","sources":["题材"],"status":"待触发","px":8.66,"chg_pct":-0.8,
  "why":"军工装备+湖南国资,题材路二梯队,等首阴低吸位","trigger":"回踩5日线(8.42)企稳 → 下一tick买 6%",
  "abort":"跌破8.30","sell":"反弹+5%止盈半仓(显式)","auction":A(-0.8,"符合预案","小低开,等低吸位"),
  "timeline":tl(("09:25","符合,等回踩"))},
 {"code":"601606","name":"长城军工","theme":"军贸","sources":["题材","质量"],"status":"待触发","px":22.15,"chg_pct":-1.2,
  "why":"军贸核心前龙,题材路+质量路双荐,等分歧转一致","trigger":"翻红且分时量能突增 → 下一tick买 10%",
  "abort":"全天未翻红过期","sell":"炸板即卖(显式)","auction":A(-1.5,"符合预案","低开分歧,按剧本"),
  "timeline":tl(("09:25","符合,等翻红"))},
 {"code":"002432","name":"九安医疗","theme":"器械出海","sources":["质量","题材"],"status":"待触发","px":80.1,"chg_pct":1.1,
  "why":"医疗器械+出海,昨首板质量S档;高开触abort后回落重新入区,10:00心跳恢复条件单",
  "trigger":"回踩+1%~+3%区企稳 → 下一tick买 8%","abort":"再冲+5%不追",
  "sell":"晚间表态","auction":A(6.2,"恶化","高开>5%曾触abort,已回落重挂"),
  "timeline":tl(("09:25","高开6.2%触abort"),("10:00","心跳:回落入区,重挂条件单"))},
 {"code":"600893","name":"航发动力","theme":"军工发动机","sources":["逻辑"],"status":"待触发","px":38.9,"chg_pct":0.5,
  "why":"军工发动机链主,logic纵深库焦点链#1,低位量化位置-38%距高","trigger":"放量突破39.8 → 下一tick买 8%",
  "abort":"缩量磨盘不动","sell":"T+3链条位置评估","auction":A(0.5,"符合预案","平开,等突破"),
  "timeline":tl(("09:25","符合,等突破"))},
 {"code":"688981","name":"中芯国际","theme":"半导体权重","sources":["总"],"status":"待触发","px":88.2,"chg_pct":-0.6,
  "why":"半导体权重锚,总裁决防守配置候选,等大盘企稳信号","trigger":"炸板率回落<25%且本票翻红 → 买 6%",
  "abort":"炸板率>35%全天禁开新仓","sell":"—","auction":A(-0.9,"符合预案","随大盘低开"),
  "timeline":tl(("09:25","符合,等环境信号"))},
 # ── 已卖出 2 / 已放弃 2
 {"code":"601127","name":"赛力斯","theme":"智能车","sources":["心跳新增"],"status":"已卖出","px":51.2,"chg_pct":-2.8,
  "why":"(在持)07-16题材路买入;10:00心跳:汽车线批量转弱+跌破预警线,B级防守卖出",
  "trigger":"已于07-16成交 ¥53.10","abort":"—","sell":"B级防守:跌破-2.5%预警线离场(10:00决断)",
  "auction":A(-0.8,"符合预案","中性开盘"),
  "fill":{"time":"10:00:40","px":51.55,"rule":"B级防守·下一tick","batches":2},
  "timeline":tl(("09:25","中性"),("10:00","心跳:题材批量转弱"),("10:00:40","卖出 ¥51.55 分2批"))},
 {"code":"000818","name":"航锦科技","theme":"军工电子","sources":["逻辑"],"status":"已卖出","px":12.6,"chg_pct":-2.9,
  "why":"(在持)军工电子,昨晚开盘卖指令","trigger":"已于07-15成交 ¥13.2","abort":"—",
  "sell":"今日开盘卖(昨晚指令)","auction":A(-1.9,"符合预案","按指令开盘走"),
  "fill":{"time":"09:30:10","px":12.88,"rule":"开盘卖指令·开盘价"},
  "timeline":tl(("09:25","按指令待开盘卖"),("09:30","卖出 ¥12.88"))},
 {"code":"002432","name":"九安医疗(早盘腿)","theme":"器械出海","sources":["质量"],"status":"已放弃","px":82.3,"chg_pct":3.9,
  "why":"质量分Top1,开盘腿计划;高开6.2%>5%触abort弃单","trigger":"gap -2%~+5% → 开盘价买 10%",
  "abort":"高开>5%弃(高开套分桶-1.9pp)","sell":"—","auction":A(6.2,"恶化","高开触abort"),
  "fill":{"time":"09:25:10","px":None,"rule":"abort:高开6.2%>5%"},
  "timeline":tl(("09:25","弃单"),("10:00","验证:冲高回落,弃单正确"))},
 {"code":"600759","name":"*ST洲际","theme":"ST过滤","sources":["竞价"],"status":"已放弃","px":2.1,"chg_pct":4.9,
  "why":"竞价异动扫描命中,但ST禁买名单硬过滤","trigger":"—","abort":"禁买:ST/退/N/C(全站口径)",
  "sell":"—","auction":A(4.9,"恶化","ST硬过滤,不入池仅记录"),
  "fill":{"time":"09:25:05","px":None,"rule":"硬过滤:ST禁买"},
  "timeline":tl(("09:25","硬过滤弃"))},
]
# 账户: master真实净值曲线
try:
    nv = json.load(open(os.path.join(BASE, "_学习/_模拟盘/master/净值.json"), encoding="utf-8"))
    if isinstance(nv, dict):
        curve = [[k, float(v["nav"] if isinstance(v, dict) else v)] for k, v in sorted(nv.items())]
    else:
        curve = [[str(r.get("date")), float(r.get("nav"))] for r in nv]
except Exception:
    curve = []
if not curve:
    curve = [["20260713",1.0],["20260714",0.988],["20260715",0.995],["20260716",1.004],["20260717",1.0161]]
acct = {"nav": S.get("nav", 1.0), "week_pct": S.get("本周pct"), "bench_week_pct": S.get("基准本周pct"),
        "cash_pct": round(S.get("现金", 0)/1e6*100), "pos_pct": round(100 - S.get("现金", 0)/1e6*100),
        "n_pos": len(S.get("持仓", [])), "curve": curve}
judg = {"date": "07-16晚", "stage": "退潮初段", "pos_band": "0-3成",
 "line": "高位板批量分歧+量能失速,判退潮初段:禁新开进攻仓,防守腿优先;医药BD为唯一独立线可留观察",
 "checks": [
  {"name": "炸板率", "expect": ">30%恶化", "now": "23.8%", "ok": False},
  {"name": "跌停家数", "expect": ">60家确认", "now": "192家", "ok": True},
  {"name": "1进2率", "expect": "<15%", "now": "9.4%", "ok": True},
  {"name": "医药独立性", "expect": "逆势红盘", "now": "板块+1.9%", "ok": True}],
 "response": {"ts": "10:00心跳", "verdict": "成立",
  "note": "3/4检查项确认退潮:跌停192家极端化,晋级率坍塌;炸板率暂可控不改结论。执行:全天禁开新仓,防守腿已执行2笔(赛力斯/航锦)"}}
W = {"date": d, "mode": "sample", "ts": "10:12:40", "account": acct, "judgment": judg,
 "pipeline": {"last_tick": "10:12:31", "fresh_sec": 9, "quota": {
   "实时行情": {"used": 21.4, "cap": 300}, "日内快照": {"used": 9.6, "cap": 200},
   "高频序列": {"used": 1.1, "cap": 150}, "历史行情": {"used": 3.9, "cap": 100}}},
 "pulse": {"zt": sm["涨停家数"], "dt": sm["跌停家数"], "zb": sm["炸板家数"],
   "zb_rate": round(sm["炸板率"]*100, 1), "top_lb": sm["最高连板"],
   "concept_top": [[r["名称"], float(r["涨幅"])] for r in cr[:6] if r.get("涨幅")]},
 "auction_review": {"ts": "09:25", "summary": "整体偏弱:恶化5/19,新增3只均放量型,ST过滤1"},
 "cards": cards}
out = os.path.join(BASE, "盘中", d); os.makedirs(out, exist_ok=True)
json.dump(W, open(os.path.join(out, "warboard.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("sample v2 OK:", len(cards), "cards")
