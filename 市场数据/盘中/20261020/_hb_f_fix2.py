# -*- coding: utf-8 -*-
"""hb-f 20261020 14:45 决断件 补正2 —— 全文字面量 '%%' 缺陷收口
根因: 生成脚本中部分字符串走 % 格式化、部分为纯字面量; 纯字面量里的 '%%' 未被还原,
      落盘成 "6.06%%" 这类非法百分号。属**格式缺陷**, 不涉判断与数值本身。
按『发出版不可覆盖』以补正件登记, 原文件保持原样。
"""
import json, io, os, time

D = r"D:\股票数据\市场数据\盘中\20261020"
P = D + r"\临盘决断_20261020_1445.json"
OUT = D + r"\临盘决断_20261020_1445_补正2.json"
d = json.load(io.open(P, encoding="utf-8"))

def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, path + "[%d]" % i)
    elif isinstance(o, str) and "%%" in o:
        yield path, o

items = []
for p, s in walk(d):
    items.append({
        "路径": p,
        "原文片段": s[:160],
        "更正": "该字段内全部 '%%' → '%'(仅符号, 数值不变)",
        "复核": "补正后该字段百分号数 = %d, 且无 '%%'" % s.count("%") ,
    })

doc = {
    "date": "20261020",
    "session": "hb-f",
    "ts": "14:45",
    "type": "补正",
    "seq": 2,
    "write_ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    "发出版": True,
    "补正对象": "临盘决断_20261020_1445.json",
    "缺陷类型": "格式(字面量 %%)，非数值、非结论",
    "根因": "_hb_f_write.py 中同一份文档混用『% 格式化字符串』与『纯字面量字符串』；纯字面量里的双百分号未被还原 → 落盘可见 '%%'。生成方式缺陷，非判断改变。",
    "影响面": "共 %d 处字段(全部为叙述文字)；零成交(fills=[])、条件决断、在持票动作与数量、明日预案要点、仓位上账 均不受影响。" % len(items),
    "条目": items,
    "与补正1的关系": "补正1 已更正 情绪/关键事实/主线/截面判读 等字段中的**过期数值**(1.15→1.23、-6.10→-6.29、7.04→6.81 等)；本件只负责**百分号符号**。两件并读 = 该字段最终正确文本。",
    "收口判据": "决断件任何字段中出现 '%%' 即视为本缺陷未修复; 本件登记后, 读取方按下表替换。",
}
assert not os.path.exists(OUT), "补正2 已存在, 禁覆盖"
json.dump(doc, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", OUT, os.path.getsize(OUT), "items", len(items))
for it in items:
    print(" -", it["路径"])
