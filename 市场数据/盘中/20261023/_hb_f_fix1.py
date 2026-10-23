# -*- coding: utf-8 -*-
"""1445 件 补正1: 仅修 2 处百分号重复转义（呈现），数据与结论零改动。
   发版纪律: v1 留档不覆盖，本件为 v2 全量成稿。"""
import json, os, copy, datetime

D = r"D:\股票数据\市场数据\盘中\20261023"
V1 = os.path.join(D, "临盘决断_20261023_1445.json")
OUT = os.path.join(D, "临盘决断_20261023_1445_补正1.json")
assert os.path.exists(V1), "v1 必须存在"
assert not os.path.exists(OUT), "发版不可覆盖: %s" % OUT

v1 = json.load(open(V1, encoding="utf-8"))
d = copy.deepcopy(v1)
fixed = []
for k in ("指数(14:46:42~14:46:45)", "高位结构"):
    old = d["市场读数"][k]
    new = old.replace("%%", "%")
    if old != new:
        fixed.append({"字段": "市场读数/%s" % k, "原": old, "改后": new})
        d["市场读数"][k] = new

d["版本"] = ("v2 · 14:45 尾盘深场B【最终成稿】——取代 临盘决断_20261023_1445.json(v1)，v1 留档不删改。"
         "本件仅修正 v1 的 1 类呈现缺陷：『市场读数』两项内百分号重复转义（写入时格式化运算被双重转义，显示为两个连续的百分号）；"
         "数据、结论、fills、闸门判定、在持票表态全部与 v1 逐字一致。")
d["write_ts"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
d["更正记录"] = {
 "产生原因": "出件后自审（哨兵前后各扫一遍全文）发现写入脚本中对含百分号的字符串同时使用了 % 格式化与字面 %，导致两个百分号双写残留，落在 2 个字段；属呈现缺陷（铁律③ 真实数据自审未过）。",
 "修正内容": fixed,
 "是否动数据/结论": "否。涨停 81/炸板 12/跌停 8/炸板率 0.129/603370 现价 30.28(+5.47%)/浮盈 +7.72%/A档 leg=close 排队 1 笔/B·C 档 0 笔/fills=[] —— 与 v1 完全一致（哨兵 C25/C26 逐项校验）。",
 "发版纪律": "v1 原样留档、不删不改；本件 v2 为本场唯一最终成稿。收盘腿成交仍见 临盘决断_20261023_1500_收盘了结.json（不回填本件）。",
 "口径影响": "无。百分号仅影响可读性，不影响任何数值解释。"
}
# 保证除版本/写件时间/更正记录外与 v1 完全一致
chk = copy.deepcopy(v1)
for k in ("版本", "write_ts", "更正记录", "市场读数"):
    chk.pop(k, None)
chk2 = copy.deepcopy(d)
for k in ("版本", "write_ts", "更正记录", "市场读数"):
    chk2.pop(k, None)
assert json.dumps(chk, ensure_ascii=False, sort_keys=True) == json.dumps(chk2, ensure_ascii=False, sort_keys=True), "数据被改动，禁止发版"
_chkdoc = copy.deepcopy(d)
_chkdoc.pop("更正记录", None)   # 更正记录里"原"字段按留档要求原样引用缺陷文本
assert "%%" not in json.dumps(_chkdoc, ensure_ascii=False), "百分号残留"

json.dump(d, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", OUT, os.path.getsize(OUT))
print("fixed fields:", [f["字段"] for f in fixed])
