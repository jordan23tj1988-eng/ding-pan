# -*- coding: utf-8 -*-
"""hb-e 14:30 补正2(最终成稿): 修正补正1的格式缺陷(字面%% / 列表repr / 回落负号),
不改任何数据与结论。1430 与 补正1 均留档不覆盖。"""
import json, os, datetime, re

D = r"D:\股票数据\市场数据\盘中\20261023"
SRC = os.path.join(D, "临盘决断_20261023_1430_补正1.json")
TARGET = os.path.join(D, "临盘决断_20261023_1430_补正2.json")
if os.path.exists(TARGET):
    raise SystemExit("发版不可覆盖: 已存在 -> " + TARGET)

doc = json.load(open(SRC, encoding="utf-8"))

def walk(o):
    if isinstance(o, str):
        s = o.replace("%%", "%").replace("[30.14]", "30.14")
        s = s.replace("距今高回落 -0.10%", "距今日高回落 0.10%")
        s = s.replace("距今高 30.16 仅回落 -0.10%", "距今高 30.16 仅回落 0.10%")
        return s
    if isinstance(o, list):
        return [walk(x) for x in o]
    if isinstance(o, dict):
        return {k: walk(v) for k, v in o.items()}
    return o

doc = walk(doc)
doc["版本"] = ("v3 · 14:30 尾盘前哨【最终成稿】——取代 临盘决断_20261023_1430.json(v1) 与 _1430_补正1.json(v2)，"
              "两者仅留档、不删改。本件修正：①防守三查③/权限分级B 中字面『%%』格式残留；②现价项池帧值列表repr（[30.14]→30.14）；"
              "③『距今高回落 -0.10%』负号语义歧义。数据与结论均未改动。")
doc["★成稿声明"] = "本件为 20261023 hb-e(14:30 尾盘前哨)最终成稿，14:45 深场B 与晚间链请以本件为准；v1/补正1 保留完整留档以存更正痕迹。"
doc["更正记录"]["补正2"] = {
 "产生原因": "补正1 出件后格式自审：fix_3 文本未走 % 运算，字面量『%%』未被转义还原；现价项把池帧查值以列表形式写入（[30.14]）；『距今高回落 -0.10%』中负号与『回落』语义重复，易被读成上涨。",
 "修正内容": ["字面『%%』→『%』（全文扫描替换）", "池帧现价列表 repr → 数值 30.14", "『距今日高回落 -0.10%』→『距今日高回落 0.10%』（括号内保留 px/high-1 的负值口径说明）"],
 "是否动数据/结论": "否。涨停 73、炸板 12、跌停 8、炸板率 0.1412、603370 现价 30.13(+4.95%)、浮盈 +7.19%、A/B/C 均 0 笔、fills 空 —— 全部与 v1 一致。",
 "发版纪律": "v2 不覆盖，另出 v3（本件）；三件并存可追溯。"
}

json.dump(doc, open(TARGET, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
s = json.dumps(doc, ensure_ascii=False)
print("written", TARGET, os.path.getsize(TARGET))
print("残留%%计数:", s.count("%%"), "| 残留[30.14]:", s.count("[30.14]"), "| 残留-0.10%:", s.count("回落 -0.10%"))
