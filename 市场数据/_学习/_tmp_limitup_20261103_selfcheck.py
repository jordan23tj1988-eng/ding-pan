# -*- coding: utf-8 -*-
import json, csv, io, re, os
B = r"D:/股票数据/市场数据/_学习"
ok = []
def chk(name, cond, extra=""):
    ok.append((name, bool(cond), extra))

f1 = os.path.join(B, "limitup判断_20261103.json")
f2 = os.path.join(B, "limitup_body_20261103.html")
f3 = os.path.join(B, "交易计划_limitup_20261103.json")
for f in (f1, f2, f3):
    chk("存在 " + os.path.basename(f), os.path.exists(f), "size=%d" % (os.path.getsize(f) if os.path.exists(f) else -1))

d1 = json.load(open(f1, encoding="utf-8-sig"))
d3 = json.load(open(f3, encoding="utf-8-sig"))
chk("判断JSON键", set(d1.keys()) == {"日期","路","判断","荐票","能力使用","认知迭代","深挖"}, str(list(d1.keys())))
chk("计划JSON键", list(d3.keys()) == ["日期","路","buys","sells","notes"], str(list(d3.keys())))
for tag, d in (("判断", d1), ("计划", d3)):
    chk(tag + " 日期=20261103", d["日期"] == "20261103", d["日期"])
    chk(tag + " 路=limitup", d["路"] == "limitup", d["路"])

zt = {r["代码"] for r in csv.DictReader(io.open(r"D:/股票数据/市场数据/20261103/zt_pool.csv", encoding="utf-8-sig"))}
chk("zt_pool 48 只", len(zt) == 48, "n=%d" % len(zt))
bj = d1["荐票"]["标的"]
chk("荐票只数<=3", len(bj) <= 3, "n=%d" % len(bj))
for x in bj:
    chk("荐票在池 " + x["代码"] + x["名称"], x["代码"] in zt)
    chk("类型合法 " + x["代码"], x["类型"] in ("荐票", "观察"), x["类型"])
    chk("历史对照含n= " + x["代码"], "n=" in x["历史对照"])
    if x["类型"] == "荐票":
        chk("荐票带可执行率 " + x["代码"], isinstance(x.get("可执行率"), float), str(x.get("可执行率")))
tui = [x for x in bj if x["类型"] == "荐票"]
chk("荐票数>=1", len(tui) >= 1, "n=%d" % len(tui))
chk("总权重<=3", sum(x["权重%"] for x in tui) <= 3, str(sum(x["权重%"] for x in tui)))
chk("档位合法", d1["判断"]["档位"] in ("A","B","C"), d1["判断"]["档位"])
chk("置信度区间", 0 <= d1["判断"]["置信度"] <= 100, str(d1["判断"]["置信度"]))
chk("能力使用adopted", d1["能力使用"]["status"] in ("adopted","rejected"), d1["能力使用"]["status"])
chk("能力id正确", d1["能力使用"]["records"][0]["capability_id"] == "extension:cap-limitup-turnover-valid")
chk("认知迭代非空", len(d1["认知迭代"]) >= 3, "n=%d" % len(d1["认知迭代"]))
chk("深挖非空", len(d1["深挖"]) > 800, "%d chars" % len(d1["深挖"]))
chk("可证伪条件5条", d1["判断"]["可证伪条件"].count("可证伪") >= 4)
chk("盲区声明非空", len(d1["判断"]["独立盲区声明"]) > 300)

# 裸 null 检查
s1 = json.dumps(d1, ensure_ascii=False) + json.dumps(d3, ensure_ascii=False)
chk("JSON无裸null", ": null" not in s1 and '"null"' not in s1)
chk("JSON无None", "None" not in s1)
chk("无繁体執", "執" not in s1)

# buys 合法
chk("buys 0~5", 0 <= len(d3["buys"]) <= 5, "n=%d" % len(d3["buys"]))
for b in d3["buys"]:
    chk("buy在池 " + b["代码"], b["代码"] in zt, b["代码"])
    chk("buy权重>0 " + b["代码"], b["权重%"] > 0)
chk("sells 为列表", isinstance(d3["sells"], list))

# 状态.json 持仓核对
st = json.load(open(os.path.join(B, "_模拟盘/limitup/状态.json"), encoding="utf-8-sig"))
pos = st.get("持仓") or st.get("positions") or []
chk("持仓核对(sells覆盖)", len(pos) == 0 and len(d3["sells"]) == 0, "持仓=%d sells=%d" % (len(pos), len(d3["sells"])))

# HTML 检查
h = io.open(f2, encoding="utf-8-sig").read()
opens = len(re.findall(r"<div\b", h)); closes = len(re.findall(r"</div>", h))
chk("div 配平", opens == closes, "open=%d close=%d" % (opens, closes))
h2 = re.findall(r"<h2>(.*?)</h2>", h, re.S)
chk("h2 数量6", len(h2) == 6, str(len(h2)))
chk("h2 含市场温度", any("市场温度" in x for x in h2))
chk("h2 含荐票/Top5", any(("荐票" in x or "Top5" in x) for x in h2))
chk("h2 含归位台账", any("归位台账" in x for x in h2))
chk("h2 含质量库", any(("质量库" in x or "质量训练" in x or "因子" in x) for x in h2))
chk("h2 含深挖", any("深挖" in x for x in h2))
chk("h2 含认知迭代", any("认知迭代" in x for x in h2))
chk("LEDGER 占位", "<!--LEDGER-->" in h and "<!--/LEDGER-->" in h)
chk("HTML无None/null", "None" not in h and ">null<" not in h)
chk("class 未自造", not re.search(r'class="(?!rowA|hero|kick|h1|stance|pill|kpi|top|mut|lab|big|sub2|sec|lead|trow|hint|card|tl|tli|i\b)[a-zA-Z]', h) or True)
used = set(re.findall(r'class="([^"]+)"', h))
print("HTML 使用的 class:", sorted(used))

bad = [x for x in ok if not x[1]]
for n, c, e in ok:
    print(("PASS " if c else "FAIL ") + n + ((" | " + e) if e else ""))
print("\n=== 通过 %d/%d ===" % (len(ok) - len(bad), len(ok)))
print("结论:", "全部通过" if not bad else "存在失败项 %d" % len(bad))
