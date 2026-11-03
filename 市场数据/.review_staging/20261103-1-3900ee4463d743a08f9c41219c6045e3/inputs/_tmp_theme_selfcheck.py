# -*- coding: utf-8 -*-
"""theme 20261030 收尾自检"""
import json, os, csv, re, sys

XL = r"D:/股票数据/市场数据/_学习/"
D = "20261030"
ok = []
err = []

def chk(cond, msg):
    (ok if cond else err).append(msg)

def L(p):
    return json.load(open(p, encoding="utf-8"))

files = ["theme判断_%s.json" % D, "theme_body_%s.html" % D, "题材荐票_%s.json" % D,
         "题材龙头判断_%s.json" % D, "题材生命周期判断_%s.json" % D,
         "交易计划_theme_%s.json" % D, "能力使用回执_theme_%s.json" % D]
for f in files:
    p = os.path.join(XL, f)
    chk(os.path.isfile(p) and os.path.getsize(p) > 0, "文件存在且非空: " + f)

# 1 判断
j = L(XL + "theme判断_%s.json" % D)
chk(bool(j["判断"]["结论"].strip()), "结论非空")
c = j["判断"]["置信度"]
chk(isinstance(c, int) and 0 <= c <= 100, "置信度0-100: %s" % c)
chk(j["判断"]["档位"] in ("A", "B", "C"), "档位A/B/C: %s" % j["判断"]["档位"])
chk(len(j["判断"]["证据"]) >= 8, "证据条数>=8: %d" % len(j["判断"]["证据"]))
chk(len(j["判断"]["可证伪条件"]) >= 4, "可证伪条件>=4: %d" % len(j["判断"]["可证伪条件"]))
chk(bool(j["判断"]["独立盲区声明"].strip()), "独立盲区声明非空")
chk(bool(j["深挖"].strip()) and "MA-20261029-05" in j["深挖"], "深挖含承接Master指派[MA-20261029-05]")
chk(len(j["认知迭代"]) >= 3, "认知迭代>=3: %d" % len(j["认知迭代"]))
chk(len(j["判断"]["生命周期"]["逐线"]) >= 5, "生命周期逐线>=5")
chk(bool(j["判断"]["生命周期"]["高低切"].strip()), "高低切非空")

# 2 标的 ∈ zt_pool
pool = {r["代码"] for r in csv.DictReader(open(r"D:/股票数据/市场数据/20261030/zt_pool.csv", encoding="utf-8-sig"))}
cands = [(x["代码"], x["名称"], x["类型"]) for x in j["荐票"]["标的"]]
chk(len(cands) <= 3, "荐票标的<=3: %d" % len(cands))
for code, nm, typ in cands:
    chk(code in pool, "标的代码∈zt_pool: %s %s" % (code, nm))
    chk(typ in ("荐票", "观察"), "类型∈{荐票,观察}: %s" % typ)

# 3 body
html = open(XL + "theme_body_%s.html" % D, encoding="utf-8").read()
h2 = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.S)
want = ["一 荐票卡 · 题材综合判断", "二 三级判定 · 方向宽度与六有", "三 主流生命周期 · 逐线判定",
        "四 龙头识别 · 谁是真龙", "五 自主深挖 · 新线孵化", "六 认知迭代"]
chk(len(h2) == 6, "body恰好6个h2: %d" % len(h2))
chk([x.strip() for x in h2] == want, "h2标题逐字一致: %s" % [x.strip() for x in h2])
chk(html.count("<div") == html.count("</div>"), "div配平: open=%d close=%d" % (html.count("<div"), html.count("</div>")))
chk("null" not in html.lower().replace("null(", ""), "body无裸null")
chk("None" not in html, "body无裸None")
chk('class="trow"' in html, "使用 table.trow")
chk('class="obs"' in html and 'class="obs-head"' in html and 'class="obs-rec"' in html, "使用统一obs组件")
chk('class="obslist"' in html, "多卡外套obslist")

# 4 龙头/逐线 无重复平键
ld = L(XL + "题材龙头判断_%s.json" % D)
chk(sorted(ld.keys()) == ["判断", "龙头标的"], "龙头判断顶层键只允许 龙头标的+判断: %s" % sorted(ld.keys()))
name_keys = [k for k in ld.keys() if "龙头" in k]
chk(len(name_keys) == 1, "龙头不存在双写平键: %s" % name_keys)
lc = L(XL + "题材生命周期判断_%s.json" % D)
chk(sorted(lc.keys()) == sorted(["逐线判断", "高低切"]), "生命周期顶层键只允许 逐线判断+高低切: %s" % sorted(lc.keys()))
line_keys = [k for k in lc.keys() if "逐线" in k]
chk(len(line_keys) == 1, "逐线不存在双写平键: %s" % line_keys)
for t, v in ld["龙头标的"].items():
    for x in v:
        chk(bool(x["名称"]) and bool(x["身位"]), "龙头条目字段完整: %s" % x["名称"])
chk(set(ld["判断"].keys()) == set(ld["龙头标的"].keys()), "龙头/判断题材键对齐")

# 5 交易计划在持票无漏
plan = L(XL + "交易计划_theme_%s.json" % D)
chk(plan["路"] == "theme" and plan["日期"] == D, "交易计划路/日期正确")
for b in plan["buys"]:
    chk("buy_gate" in b and "min_gap_pct" in b["buy_gate"] and "max_gap_pct" in b["buy_gate"], "buys含buy_gate")
held = []
sp = r"D:/股票数据/市场数据/_学习/_模拟盘/theme/状态.json"
if os.path.isfile(sp):
    st = L(sp)
    held = [h["code"] for h in st.get("持仓", [])]
    sold = {s["代码"] for s in plan["sells"]}
    miss = [h for h in held if h not in sold]
    chk(not miss, "在持票逐票表态无漏: 持仓%s 已表态%s" % (held, sorted(sold)))
    for s in plan["sells"]:
        chk(s["腿"] in ("open", "close"), "sells腿∈{open,close}: %s" % s["腿"])
        chk(bool(s["理由"].strip()), "sells理由非空: %s" % s["代码"])
    if not plan["buys"]:
        chk(bool(plan["notes"].strip()), "空仓已写理由")

# 6 回执
rc = L(XL + "能力使用回执_theme_%s.json" % D)
chk(rc["route"] == "theme", "回执route=theme")
chk(rc["status"] in ("applied", "rejected_all", "no_eligible_capabilities"), "回执status合法: %s" % rc["status"])
if rc["status"] == "applied":
    chk(all(x.get("effect") and x.get("source_locator") for x in rc["applied"]), "applied含effect+source_locator")

# 7 发出版与判断一致
rb = L(XL + "题材荐票_%s.json" % D)
chk(rb["日期"] == D, "发出版日期正确")
chk(len(rb["荐票"]) == 0, "发出版正式荐票=0（空仓）")
chk([x["代码"] for x in rb["观察"]] == [x[0] for x in cands], "发出版观察与判断一致")

# 8 族口径产物
chk(os.path.isfile(XL + "题材线宽_%s.json" % D), "族口径产物存在: 题材线宽_%s.json" % D)
fw = L(XL + "题材线宽_%s.json" % D)
chk("消费系" in fw["族"] and fw["族"]["消费系"]["宽度"] == 14, "消费系族宽=14")
chk(fw["族"]["消费系"]["族宽环比"] is not None, "消费系族宽环比非null")

print("OK %d 项" % len(ok))
for e in err:
    print("FAIL:", e)
print("ALL PASS" if not err else "HAS FAILURES(%d)" % len(err))
if not err:
    print("OK")
sys.exit(0 if not err else 1)
