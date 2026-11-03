# -*- coding: utf-8 -*-
import json, os, csv, re, sys
B = r"D:/股票数据/市场数据/_学习"
zt = {r["代码"]: r for r in csv.DictReader(open(r"D:/股票数据/市场数据/20261103/zt_pool.csv", encoding="utf-8-sig"))}
ok = True
def chk(c, m):
    global ok
    print(("PASS " if c else "FAIL ") + m)
    if not c: ok = False

files = ["theme判断_20261103.json", "theme_body_20261103.html", "题材荐票_20261103.json",
         "题材龙头判断_20261103.json", "题材生命周期判断_20261103.json", "交易计划_theme_20261103.json",
         "题材线宽_20261102.json", "_tmp_医药AI应用启动逐笔_20261102.json"]
for f in files:
    p = os.path.join(B, f)
    chk(os.path.exists(p) and os.path.getsize(p) > 500, f"存在且非空 {f} ({os.path.getsize(p) if os.path.exists(p) else 0}B)")

J = {}
for f in files:
    if f.endswith(".json"):
        try:
            J[f] = json.load(open(os.path.join(B, f), encoding="utf-8"))
            chk(True, f"JSON 可解析 {f}")
        except Exception as e:
            chk(False, f"JSON 解析失败 {f}: {e}")

# 日期
tj = J["theme判断_20261103.json"]
chk(tj["日期"] == "20261103" and tj["路"] == "theme", "theme判断 日期/路 正确")
chk(tj["判断"]["档位"] in ("A", "B", "C") and isinstance(tj["判断"]["置信度"], int), "档位/置信度 合法")
chk(tj["判断"]["结论"].startswith("无主线"), "结论 明确给出「无主线」")
chk(tj.get("能力使用", {}).get("status") == "no_eligible_capabilities", "能力使用 status 正确")

# 荐票 ∈ zt_pool
codes = [x["代码"] for x in tj["荐票"]["标的"]]
for c in codes:
    chk(c in zt, f"荐票标的 ∈ zt_pool: {c} {zt.get(c,{}).get('名称','?')}")
chk(sum(1 for x in tj["荐票"]["标的"] if x["类型"] == "荐票") <= 3, "荐票数量≤3")
chk(len(codes) == len(set(codes)), "荐票无重复")

fs = J["题材荐票_20261103.json"]
chk(all(x["代码"] in zt for x in fs["标的"]), "题材荐票 标的均在 zt_pool")
chk([x["代码"] for x in fs["标的"]] == codes, "两个文件标的清单一致")

# 别名重复键
lg = J["题材龙头判断_20261103.json"]
chk(set(lg.keys()) == {"日期", "龙头标的", "判断"}, f"龙头判断 顶层仅 日期/龙头标的/判断 → {sorted(lg.keys())}")
chk("龙头" not in lg, "龙头判断 无别名键「龙头」")
lc = J["题材生命周期判断_20261103.json"]
chk(set(lc.keys()) == {"日期", "逐线判断", "高低切"}, f"生命周期判断 顶层仅 日期/逐线判断/高低切 → {sorted(lc.keys())}")
chk("逐线" not in lc, "生命周期判断 无别名键「逐线」")
chk(all(set(v.keys()) == {"定性", "判据"} for v in lc["逐线判断"].values()), "逐线判断 每条仅 定性/判据")

# 交易计划
tp = J["交易计划_theme_20261103.json"]
chk(0 <= len(tp["buys"]) <= 5, f"buys 0~5 ({len(tp['buys'])})")
chk(all(b["代码"] in zt for b in tp["buys"]), "buys 均在 zt_pool")
chk(sum(b["权重%"] for b in tp["buys"]) <= 100, f"buys 权重合计 {sum(b['权重%'] for b in tp['buys'])}%")
st = json.load(open(os.path.join(B, "_模拟盘/theme/状态.json"), encoding="utf-8"))
hold = st.get("持仓", [])
chk(all(any(h.get("代码") == s["代码"] for s in tp["sells"]) for h in hold) or not hold,
    f"在持票逐票表态（持仓 {len(hold)} 只，sells {len(tp['sells'])} 条）")
chk("持仓表态" in tp["notes"], "notes 含持仓表态")

# 无裸 null
def walk(o, path=""):
    bad = []
    if o is None: bad.append(path)
    elif isinstance(o, dict):
        for k, v in o.items(): bad += walk(v, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o): bad += walk(v, path + "/" + str(i))
    return bad
allnull = []
for f, d in J.items():
    allnull += [f + p for p in walk(d)]
chk(not allnull, f"JSON 无裸 null {allnull[:5]}")

h = open(os.path.join(B, "theme_body_20261103.html"), encoding="utf-8").read()
chk(re.search(r"(?<![A-Za-z])null(?![A-Za-z])|(?<![A-Za-z])None(?![A-Za-z])", h) is None, "body 无裸 null/None")
chk(h.count('<div class="card">') == 6, f"六段卡 {h.count('<div class=\"card\">')}")
h2 = re.findall(r"<h2>(.*?)</h2>", h)
chk(len(h2) == 6, f"h2 段标题 {len(h2)}: {h2}")
chk(h.count("<div") == h.count("</div>"), f"div 配平 {h.count('<div')}/{h.count('</div>')}")
chk(h.count("<table") == h.count("</table>") and h.count("<tr") == h.count("</tr>"), "table/tr 配平")
chk("theme-body" in h and "rowA" in h and "obslist" in h and "kpi" in h, "组件类名齐全")

# 逐笔 ≥40
ms = J["_tmp_医药AI应用启动逐笔_20261102.json"]
chk(ms["逐笔条数"] >= 40, f"逐笔条数 {ms['逐笔条数']} ≥40")
lw = J["题材线宽_20261102.json"]
chk(lw["消费系核对"]["族宽"] == 17 or lw["族口径"]["消费系"]["族宽"] == 17, "消费系族宽=17")

print("\n=== ALL PASS ===" if ok else "\n=== HAS FAILURES ===")
sys.exit(0 if ok else 1)
