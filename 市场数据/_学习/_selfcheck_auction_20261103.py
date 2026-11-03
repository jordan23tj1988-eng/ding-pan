# -*- coding: utf-8 -*-
"""auction 20261103 三件产物收尾自检（可复跑）"""
import json, io, os, re, csv, sys

B = r"D:/股票数据/市场数据/_学习"
ZT = r"D:/股票数据/市场数据/20261103/zt_pool.csv"
fails = []
def chk(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)

# 1 三文件存在
A = os.path.join(B, "auction判断_20261103.json")
H = os.path.join(B, "auction_body_20261103.html")
P = os.path.join(B, "交易计划_auction_20261103.json")
for f in (A, H, P):
    chk(os.path.exists(f) and os.path.getsize(f) > 500, "existe %s (%d bytes)" % (os.path.basename(f), os.path.getsize(f) if os.path.exists(f) else -1))

# 2 JSON 可解析
j = json.load(io.open(A, encoding="utf-8")); plan = json.load(io.open(P, encoding="utf-8"))
chk(True, "json parse A/plan")

# 3 日期
chk(j.get("日期") == "20261103", "A.日期==20261103")
chk(plan.get("日期") == "20261103", "plan.日期==20261103")
chk(j.get("路") == "auction" and plan.get("路") == "auction", "路==auction")

# 4 荐票 ∈ zt_pool
zt = set()
with io.open(ZT, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f): zt.add(r["代码"])
codes = [s["代码"] for s in j["荐票"]["标的"]]
chk(all(c in zt for c in codes), "荐票/观察全部 ∈ zt_pool: %s" % codes)
chk(all(len(c) == 6 and c.isdigit() for c in codes), "代码为 6 位数字")
recs = [s for s in j["荐票"]["标的"] if s["类型"] == "荐票"]
chk(len(recs) <= 3, "荐票数量 %d <= 3" % len(recs))
chk(all(s["类型"] in ("荐票", "观察") for s in j["荐票"]["标的"]), "类型枚举合法")
chk(all("n=" in s["历史对照"] and "胜率" in s["历史对照"] for s in j["荐票"]["标的"]), "每只标的均带 n=/胜率 历史对照")

# 5 plan buys ⊆ zt_pool, 权重, gate
chk(all(b["代码"] in zt for b in plan["buys"]), "plan.buys ⊆ zt_pool")
chk(len(plan["buys"]) <= 5, "buys %d <= 5" % len(plan["buys"]))
chk(all(b["buy_gate"]["min_gap_pct"] < b["buy_gate"]["max_gap_pct"] for b in plan["buys"]), "buy_gate 上下界有序")
chk(len(plan.get("notes", "")) > 200, "notes 非空")

# 在持票表态：状态.json 每只在 sells 或 notes
st = json.load(io.open(os.path.join(B, "_模拟盘/auction/状态.json"), encoding="utf-8"))
held = [p2["code"] for p2 in (st.get("持仓") or [])]
sold = [s["代码"] for s in plan["sells"]]
for c in held:
    chk(c in sold or c in plan["notes"], "在持票 %s 已表态" % c)
chk(plan["buys"][0]["权重%"] == 0.5, "权重 0.5（冰点1%上限xP档0.5）")
hb = io.open(H, encoding="utf-8").read()
chk(("0.5%" in j["荐票"]["结论"]) and ("0.5%" in hb) and ("0.5%" in plan["buys"][0]["理由"]), "仓位 0.5% 三文件同源")
print("held=", held, "sells=", sold)

# 6 body div 配平 + h2 六段 + 无裸 null/None + 表内无空单元格
h = io.open(H, encoding="utf-8").read()
chk(h.count("<div") == h.count("</div>"), "<div %d == </div> %d" % (h.count("<div"), h.count("</div>")))
h2 = re.findall(r"<h2>(.*?)</h2>", h)
chk(len(h2) == 6, "h2 六段: %s" % h2)
chk(re.search(r"(?<![\w\"])null(?![\w\"])", h) is None and re.search(r"(?<![\w\"])None(?![\w\"])", h) is None, "body 无裸 null/None 字面量")
chk(h.count("<table") == h.count("</table>"), "table 配平")
chk("<td></td>" not in h, "无空表格单元格")

# 7 字段完整性
for k in ("结论", "证据", "档位", "置信度", "可证伪条件", "独立盲区声明"):
    chk(k in j["判断"], "判断.%s 存在" % k)
chk(j["判断"]["档位"] in ("A", "B", "C"), "档位 %s ∈ A/B/C" % j["判断"]["档位"])
chk(isinstance(j["判断"]["置信度"], int) and 0 <= j["判断"]["置信度"] <= 100, "置信度 %s ∈ 0~100" % j["判断"]["置信度"])
chk(j["能力使用"].get("status") == "no_eligible_capabilities" and j["能力使用"].get("records") == [], "能力使用 == no_eligible_capabilities")
chk("承接Master指派[MA-20261102-03]" in j["深挖"] and re.search(r"结果[:：]", j["深挖"]) is not None, "深挖含 Master 指派承接")
chk(len(j["认知迭代"]) >= 3, "认知迭代 %d 条" % len(j["认知迭代"]))

# 8 禁后视镜：正文不得出现 20261104 及以后的数据引用；不得出现 2026-11-04 以外的未来日期
future = re.findall(r"2026-(?:11-(?:0[4-9]|[12][0-9]|3[01])|12-[0-3][0-9])", h)
chk(not future, "body 无未来日期: %s" % future)
blob = json.dumps(j, ensure_ascii=False) + json.dumps(plan, ensure_ascii=False)
fut2 = re.findall(r"[_/]2026110[4-9]|2026110[4-9][_/]", blob)
chk(not fut2, "json 无 >20261103 的数据日期: %s" % fut2)

print("\n=== RESULT:", "ALL PASS" if not fails else ("%d FAIL" % len(fails)), "===")
sys.exit(1 if fails else 0)
