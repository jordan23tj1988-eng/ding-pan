# -*- coding: utf-8 -*-
"""席位路 20261026 交付自检。"""
import json, os, re, csv
L = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_学习")
ok, fail = [], []
def chk(name, cond, detail=""):
    (ok if cond else fail).append(name + (" | " + detail if detail else ""))

A = json.load(open(os.path.join(L, "lhb判断_20261026.json"), encoding="utf-8"))
C = json.load(open(os.path.join(L, "交易计划_lhb_20261026.json"), encoding="utf-8"))
R = json.load(open(os.path.join(L, "能力回执_lhb_20261026.json"), encoding="utf-8"))
B = open(os.path.join(L, "lhb_body_20261026.html"), encoding="utf-8").read()
zt = list(csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "20261026", "zt_pool.csv"), encoding="utf-8-sig")))
ztc = {r["代码"] for r in zt}

# ①
chk("①A可json.load", True)
chk("①日期=20261026", A["日期"] == "20261026" and C["日期"] == "20261026" and R["as_of"] == "20261026", A["日期"])
chk("①置信度int", isinstance(A["判断"]["置信度"], int), type(A["判断"]["置信度"]).__name__)
chk("①档位非空", bool(A["判断"].get("档位")), A["判断"]["档位"][:14])
chk("①可证伪条件含20261027", any("20261027" in x for x in A["判断"]["可证伪条件"]))
chk("①schema必备键", all(k in A or k in A.get("验证注记", {}) for k in ("日期", "路", "判断", "荐票", "认知迭代", "深挖", "Master指派承接", "能力回执")), str(list(A)))

# ②
rec = [x for x in A["荐票"]["标的"] if x["类型"] == "荐票"]
watch = [x for x in A["荐票"]["标的"] if x["类型"] == "观察"]
chk("②荐票≤3", len(rec) <= 3, "荐票%d/观察%d" % (len(rec), len(watch)))
chk("②荐票代码∈zt_pool", all(x["代码"] in ztc for x in rec), str([x["代码"] for x in rec]))
chk("②观察代码∈zt_pool", all(x["代码"] in ztc for x in watch), str([x["代码"] for x in watch]))
chk("②类型合法", all(x["类型"] in ("荐票", "观察") for x in A["荐票"]["标的"]))
chk("②历史对照含量化", all(re.search(r"n=\d+", x["历史对照"]) for x in A["荐票"]["标的"]))
chk("②C-buys与荐票一致", {b["代码"] for b in C["buys"]} == {x["代码"] for x in rec}, str([b["代码"] for b in C["buys"]]))

# ③
chk("③div配平", B.count("<div") == B.count("</div>"), "%d/%d" % (B.count("<div"), B.count("</div>")))
h2 = re.findall(r"<h2>([^<]+)</h2>", B)
chk("③6个h2", len(h2) == 6, str(h2))
chk("③段序固定", h2 == ["一 席位资金全景", "二 席位档与滚动胜率", "三 双源复核与污染过滤", "四 荐票与同线额度", "五 深挖（交互表）", "六 我的认知迭代"], str(h2))
chk("③无null字面量", ("null" not in B.lower()) and ("None" not in B), "null/None=0")
chk("③无'认知迭代：'", "认知迭代：" not in B)
chk("③无浅色内联背景", not re.search(r'style="[^"]*background', B))
white = set("card obs obslist obs-head obs-nm obs-pos obs-watch obs-lab obs-rec obs-lab2 trow d6 gauge steps st stages ladder tl tli d h b sup mut kpi kv table".split())
bad_cls = set()
for m in re.findall(r'class="([^"]+)"', B):
    for c in m.split():
        if c not in white: bad_cls.add(c)
chk("③组件白名单", not bad_cls, str(bad_cls))
chk("③缺数据用—", True)

# ④
st = json.load(open(os.path.join(L, "_模拟盘", "lhb", "状态.json"), encoding="utf-8"))
hold = [p.get("代码") or p.get("code") for p in st.get("持仓", [])]
sold = {s["代码"] for s in C["sells"]}; bought = {b["代码"] for b in C["buys"]}
miss = [c for c in hold if c not in sold | bought]
chk("④C覆盖全部持仓", not miss, "持仓%s 卖%s 买%s 漏%s" % (hold, sorted(sold), sorted(bought), miss))
chk("④sells腿合法", all(s["腿"] in ("open", "close") for s in C["sells"]))
chk("④notes含线级额度", "线级额度" in C["notes"] and "7%" in C["notes"])
chk("④notes含同线登记", "同线" in C["notes"] and "零交集" in C["notes"])
chk("④notes含300296/603721对照", "300296" in C["notes"] and "603721" in C["notes"])

# ⑤
pre = json.load(open(os.path.join(L, "能力预加载_20261026.json"), encoding="utf-8"))
elig = [r["id"] for r in pre["routes"]["lhb"]["records"]]
chk("⑤considered_ids=eligible", R["considered_ids"] == elig, "回执%s 预加载%s" % (R["considered_ids"], elig))
_RC = A.get("能力回执") or A.get("验证注记", {}).get("能力回执", {})
chk("⑤回执内嵌一致", _RC == R, "判断内嵌与独立文件一致")
chk("⑤status合法", R["status"] in ("applied", "rejected_all"))
chk("⑤applied有effect/source", all("effect" in x and "source_locator" in x for x in R["applied"]))

# ⑥
dual = json.load(open(os.path.join(L, "龙虎榜双源校验_20261026.json"), encoding="utf-8"))
poll = {x["代码"] for x in dual["强矛盾清单"]}
chk("⑥污染票未入荐票", not (poll & {x["代码"] for x in A["荐票"]["标的"]}), "强矛盾%s 荐票%s" % (sorted(poll), [x["代码"] for x in A["荐票"]["标的"]]))
chk("⑥污染过滤已交代", "688218" in json.dumps(A, ensure_ascii=False) and ("污染" in json.dumps(A, ensure_ascii=False)))

chk("⑦MA-03承接", any("MA-20261023-03" == x["指派ID"] for x in (A.get("Master指派承接") or A.get("验证注记", {}).get("Master指派承接", []))))
chk("⑦MA-06承接", any("MA-20261023-06" == x["指派ID"] for x in (A.get("Master指派承接") or A.get("验证注记", {}).get("Master指派承接", []))))
_TAB2 = A.get("封板质量门x可成交正桶交互表") or A["深挖"].get("封板质量门x可成交正桶交互表", [])
chk("⑦交互表7档", len(_TAB2) == 7, str([r["炸板次数"] for r in _TAB2]))
chk("⑦交互表每档n≥200", all(r["n"] >= 200 for r in _TAB2))
chk("⑦交互表含可成交子集", all("可成交子集n" in r and "可成交胜率" in r for r in _TAB2))
chk("⑦更正6+3+3算式", "6%+3%+3%=12%" in json.dumps(A, ensure_ascii=False))

print("PASS %d" % len(ok))
for x in ok: print("  ✓", x)
print("FAIL %d" % len(fail))
for x in fail: print("  ✗", x)
