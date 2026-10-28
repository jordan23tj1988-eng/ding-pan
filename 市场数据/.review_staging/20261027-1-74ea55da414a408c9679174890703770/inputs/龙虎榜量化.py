# -*- coding: utf-8 -*-
"""
龙虎榜量化.py —— 补全"龙虎榜量化评分"待补项
从 lhb.csv(聚合层: 买/卖/净买/占比/换手) + analysis.json 席位动向(逐席位层: 均匀度/资金五分类)
算出每只上榜股的量化评分, 写入 _龙虎榜量化.json 与 analysis.json["龙虎榜量化"]。

量化维度(米氏资金五分类对齐):
  买力 = 龙虎榜买入额
  卖力 = 龙虎榜卖出额
  净买 = 龙虎榜净买额
  净买占比 = 净买额/总成交 (已含在csv)
  多空比 = 买力/卖力
  档(强/中/弱) = 由 净买符号 + 净买占比 + 多空比 推导
  均匀度 = 1 - 前3买席位净额占比(逐席位层; 无明细则"待席位明细")
  资金五分类买力分布 = 机构/量化/游资/外资/其他 的买力占比(逐席位层)
全部真实数据, 不编。
用法: python 龙虎榜量化.py [日期目录,默认今日]
"""
import os, json, glob, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "复盘")

def d2(x):
    try: return float(x)
    except: return 0.0

def classify(seat):
    """逐席位资金分类: 返回 机构/量化/游资/外资/其他"""
    游资 = seat.get("游资") or ""
    类型 = seat.get("类型") or ""
    name = (seat.get("营业部") or "")
    if "北向" in 游资 or "沪股通" in 游资 or "深股通" in 游资:
        return "外资"
    if 类型 == "机构":
        return "机构"
    if 类型 == "量化":
        return "量化"
    if 游资:  # 有游资标签(派神/紫阳东路等)
        return "游资"
    # 无名: 按营业部名粗判
    if "机构专用" in name:
        return "机构"
    if "量化" in name or "私募基金" in name:
        return "量化"
    return "其他"

def quant_dang(净买, 净买占比, 多空比):
    if 净买 <= 0:
        return "弱"  # 净卖=出货主导
    if 净买占比 >= 5 and 多空比 >= 1.5:
        return "强"  # 真金白银主买
    if 净买占比 >= 2:
        return "中"
    return "弱"

def main(day=None):
    if day is None:
        day = datetime.datetime.now().strftime("%Y%m%d")
    lhb = os.path.join(BASE, day, "lhb.csv")
    if not os.path.isfile(lhb):
        print("无 lhb.csv(%s), 跳过" % day); return
    ana_path = os.path.join(BASE, day, "analysis.json")
    ana = json.load(open(ana_path, encoding="utf-8")) if os.path.isfile(ana_path) else {}
    seats_all = ana.get("席位动向") or []

    # 逐席位按代码分组(买席位层)
    by_code = {}
    for s in seats_all:
        c = s.get("代码")
        by_code.setdefault(c, []).append(s)

    import csv
    rows = list(csv.DictReader(open(lhb, encoding="utf-8-sig")))
    res = []
    for r in rows:
        code = r["代码"]; name = r.get("名称", "")
        买力 = d2(r.get("龙虎榜买入额"))
        卖力 = d2(r.get("龙虎榜卖出额"))
        净买 = d2(r.get("龙虎榜净买额"))
        净买占比 = d2(r.get("净买额占总成交比"))
        换手 = d2(r.get("换手率"))
        多空比 = (买力 / 卖力) if 卖力 else 0
        档 = quant_dang(净买, 净买占比, 多空比)
        # 逐席位层
        seats = by_code.get(code, [])
        buys = [s for s in seats if d2(s.get("净额", 0)) > 0]
        total_buy = sum(d2(s.get("净额", 0)) for s in buys)
        均匀度 = None; 五分类 = None
        if total_buy > 0:
            top3 = sorted(buys, key=lambda s: -d2(s.get("净额", 0)))[:3]
            集中度 = sum(d2(s.get("净额", 0)) for s in top3) / total_buy
            均匀度 = round(1 - 集中度, 3)
            dist = {}
            for s in buys:
                c = classify(s)
                dist[c] = dist.get(c, 0) + d2(s.get("净额", 0))
            五分类 = {k: round(v / total_buy * 100, 1) for k, v in dist.items()}
        res.append(dict(
            代码=code, 名称=name, 买力=round(买力/1e4, 0), 卖力=round(卖力/1e4, 0),
            净买=round(净买/1e4, 0), 净买占比=round(净买占比, 2), 换手=round(换手, 2),
            多空比=round(多空比, 2), 档=档,
            均匀度=均匀度, 五分类=五分类,
            上榜原因=r.get("上榜原因", ""), 涨跌幅=d2(r.get("涨跌幅")),
            上榜后1日=r.get("上榜后1日", "") or "", 上榜后2日=r.get("上榜后2日", "") or "",
            上榜后5日=r.get("上榜后5日", "") or "", 上榜后10日=r.get("上榜后10日", "") or "",
        ))
    # 排序: 净买降序
    res.sort(key=lambda x: -x["净买"])
    # 写出
    json.dump(res, open(os.path.join(BASE, "_龙虎榜量化.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    # 并入 analysis.json
    ana["龙虎榜量化"] = res
    json.dump(ana, open(ana_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("龙虎榜量化: %d 只上榜股 | 强%d 中%d 弱%d | 有逐席位明细%d只" % (
        len(res),
        sum(1 for x in res if x["档"] == "强"),
        sum(1 for x in res if x["档"] == "中"),
        sum(1 for x in res if x["档"] == "弱"),
        sum(1 for x in res if x["均匀度"] is not None)))

if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
