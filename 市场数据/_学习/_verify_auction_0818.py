# -*- coding: utf-8 -*-
"""auction 20260818 三产物 schema/纪律验证(exit 0=全过)
用法: python _verify_auction_0818.py
核对: 判断json(档位/荐票代码∈涨停池/承接Master指派) + body html(div配平/6板块/POOLLEDGER锚) + 交易计划(持仓逐票表态)
"""
import json, csv, sys, re

L = r"D:\股票数据\市场数据\_学习"
R = r"D:\股票数据\市场数据"
fail = []

def chk(cond, msg):
    if not cond:
        fail.append(msg)

# ---------- 1. auction判断_20260818.json ----------
j = json.load(open(L + r"\auction判断_20260818.json", encoding="utf-8"))
chk(j["日期"] == "20260818" and j["路"] == "auction", "判断头错")
档位 = j["判断"]["档位"]
chk(档位 in ("A", "B", "C"), "档位非法:%s" % 档位)
chk(0 <= j["判断"]["置信度"] <= 100, "置信度越界")
chk(bool(j["判断"]["可证伪条件"] and j["判断"]["独立盲区声明"] and j["判断"]["框架引用"]), "判断字段缺失")
pool = set(r["代码"] for r in csv.DictReader(open(R + r"\20260818\zt_pool.csv", encoding="utf-8-sig")))
标 = j["荐票"]["标的"]
for x in 标:
    chk(len(x["代码"]) == 6 and x["代码"] in pool, "荐票代码不在涨停池:%s" % x["代码"])
    chk(x["类型"] in ("荐票", "观察"), "类型非法:%s" % x["类型"])
    chk("n=" in x["历史对照"], "历史对照缺n:%s" % x["代码"])
chk("AS-20260817-002" in j["深挖"] and "深挖结果" in j["深挖"], "未承接Master指派")

# ---------- 2. auction_body_20260818.html ----------
s = open(L + r"\auction_body_20260818.html", encoding="utf-8").read()
od, cd = s.count("<div"), s.count("</div>")
chk(od == cd, "div未配平:%d/%d" % (od, cd))
chk(s.count("<section") == 6 and s.count("</section") == 6, "section≠6")
chk(len(re.findall(r"<h2[^>]*>", s)) == 6, "h2板块≠6")
chk("<!--POOLLEDGER-->" in s and "<!--/POOLLEDGER-->" in s, "POOLLEDGER锚不成对")
chk(s.count('class="kpi"') == 4 and "hero" in s and "stance" in s, "头部agent卡缺")
chk("44.5" in s and "农业/种业粮食" in s, "body缺当日事实")

# ---------- 3. 交易计划_auction_20260818.json ----------
t = json.load(open(L + r"\交易计划_auction_20260818.json", encoding="utf-8"))
chk(t["日期"] == "20260818" and t["路"] == "auction", "交易计划头错")
chk(0 <= len(t["buys"]) <= 5, "buys越界")
chk(bool(t["notes"]), "空仓未写理由")
持仓 = ["603725"]
for c in 持仓:
    chk(any(x["代码"] == c for x in t["sells"]) or c in t["notes"], "持仓%s未表态" % c)
for x in t["sells"]:
    chk(x["腿"] in ("open", "close"), "sells腿非法:%s" % x.get("腿"))

if fail:
    print("FAIL:")
    for f in fail:
        print("  -", f)
    sys.exit(1)
print("PASS: 判断json(档位=%s 置信度=%s 荐票%d只=%s) | body(div %d=%d section6 h2_6 POOLLEDGER成对 hero+4kpi) | 交易计划(buys=%d sells=%d 603725已表态)" % (
    档位, j["判断"]["置信度"], len(标), [x["类型"] for x in 标], od, cd, len(t["buys"]), len(t["sells"])))
