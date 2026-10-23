# -*- coding: utf-8 -*-
"""hb-e 成稿修正2: 603278/002724 今日走势表述错误(非"全天封板", 实为深水反包/地天板) + filled/fills 笔误。
数据零改动, 结论方向不变(修正后实际强化"修复"判断)。"""
import json, os, datetime, urllib.request

D = r"D:\股票数据\市场数据\盘中\20261023"
F = os.path.join(D, "临盘决断_20261023_1430_补正2.json")
doc = json.load(open(F, encoding="utf-8"))

# 现取两只6板股今日 低/高 佐证(取数时点必早于14:45, 属盘后留档范围)
u = "https://qt.gtimg.cn/q=sh603278,sz002724"
raw = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"}), timeout=15).read().decode("gbk", "replace")
info = {}
for seg in raw.strip().split(";"):
    seg = seg.strip()
    if not seg.startswith("v_"):
        continue
    f = seg.partition("=")[2].strip().strip('"').split("~")
    if len(f) < 40:
        continue
    info[f[2]] = {"name": f[1], "px": float(f[3]), "pre": float(f[4]), "pct": float(f[32]),
                  "hi": float(f[33]), "lo": float(f[34]), "t": f[30]}
print(json.dumps(info, ensure_ascii=False))

b = info["603278"]
h = info["002724"]
txt = ("②高位双钉验证：603278 大业股份（6板，今 %.2f %+.2f%%，今低 %.2f = %+.2f%% 深水反包涨停，非全天封板）与 "
       "002724 海洋王（6板，今 %.2f %+.2f%%，今低 %.2f = %+.2f%% 触跌停后拉至涨停＝地天板，14:01 前后曾一度回落至 +0.80%% 再回封）"
       "是唯一高位梯子，4~5 板全空档。两只均属『深水拉板』型硬资金行为，说明高位未溃散；明日若两只均续板 → 情绪进入上升段，可做 2 板接力；"
       "若同时断板 → 判定修复一日游，转防守、C 档零新增。") % (
    b["px"], b["pct"], b["lo"], (b["lo"] / b["pre"] - 1) * 100,
    h["px"], h["pct"], h["lo"], (h["lo"] / h["pre"] - 1) * 100)

plan = doc["为14:45深场B备料"]["明日预案要点草稿"]
idx = [i for i, s in enumerate(plan) if s.startswith("②")][0]
old_txt = plan[idx]
plan[idx] = txt

# 笔误
doc["就地重写记录"]["未改动"] = doc["就地重写记录"]["未改动"].replace("filled/fills", "fills")
doc["就地重写记录"]["改写2"] = {
 "时点": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
 "发现": "自审备料②时用腾讯 quote 复核两只 6 板股日内低点：603278 今低 13.23(-8.82%)、002724 今低 10.09(-9.99% 跌停)，原写『全天封板』与行情矛盾。",
 "原表述（错误，留档）": old_txt,
 "更正后": txt,
 "证据": "腾讯 qt.gtimg.cn 取数 t=%s(603278) / %s(002724)，字段 high/low 直读；另 002724 池帧 13:57:59 +6.16%% → 14:01:59 +0.80%% → 14:31:04 +9.90%% 三段留档。" % (b["t"], h["t"]),
 "影响": "结论方向不变且强化：两只 6 板均『深水/地天』拉回涨停 → 高位未溃散，修复更实；仍不改任何动作(A/B/C 0 笔)。"
}
json.dump(doc, open(F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("updated", os.path.getsize(F))
print(plan[idx][:160])
