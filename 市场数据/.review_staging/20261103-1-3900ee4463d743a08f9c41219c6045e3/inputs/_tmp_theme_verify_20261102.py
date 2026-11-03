# -*- coding: utf-8 -*-
import json, csv, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
XL = r"D:/股票数据/市场数据/_学习/"
D = "20261102"
ok = True
def chk(cond, msg):
    global ok
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: ok = False

# 1) JSON 键集
lt = json.load(open(XL+f"题材龙头判断_{D}.json", encoding="utf-8"))
chk(list(lt.keys()) == ["龙头标的","判断"], f"题材龙头判断 顶层键={list(lt.keys())} 必须=['龙头标的','判断']")
lc = json.load(open(XL+f"题材生命周期判断_{D}.json", encoding="utf-8"))
chk(list(lc.keys()) == ["龙头标的","逐线判断","高低切"], f"题材生命周期判断 顶层键={list(lc.keys())}")
chk(all(set(v.keys())=={"定性","判据"} for v in lc["逐线判断"].values()), "逐线判断 每条={定性,判据}")
chk(all(("→" in v["判据"] or "＝" in v["判据"] or "=" in v["判据"]) and ("明日" in v["判据"]) for v in lc["逐线判断"].values()), "每条判据含可机械结算阈值+明日时点")

# 2) 荐票/龙头 ∈ zt_pool 且 名称一致
rows = {r["代码"]: r for r in csv.DictReader(open(r"D:/股票数据/市场数据/20261102/zt_pool.csv", encoding="utf-8-sig"))}
gw = json.load(open(XL+f"题材归位_{D}.json", encoding="utf-8"))["映射"]
tj = json.load(open(XL+f"题材荐票_{D}.json", encoding="utf-8"))
picks = [x for x in tj["标的"] if x["类型"]!="观察"]
chk(len(picks) <= 3, f"正式荐票 {len(picks)} 只 ≤3")
for x in picks + [y for y in tj["标的"] if y["类型"]=="观察"]:
    chk(x["代码"] in rows, f"{x['代码']} {x['名称']} ∈ zt_pool")
    chk(gw.get(x["代码"],{}).get("名称")==x["名称"], f"{x['代码']} 名称与归位真源一致")
for x in lt["龙头标的"]:
    chk(x["代码"] in rows, f"龙头 {x['代码']} {x['名称']} ∈ zt_pool")
    chk(gw.get(x["代码"],{}).get("名称")==x["名称"], f"龙头 {x['代码']} 名称一致")

# 3) 11 条 6有 线 == 判断键集
s6 = json.load(open(XL+f"主流题材6有_{D}.json", encoding="utf-8"))["题材_聚类口径"]
lines = [r["题材(题材聚类口径)"] for r in s6]
print("6有行:", lines)
chk(set(lt["判断"].keys()) == set(lines), f"龙头判断键集==6有线集 ({len(lt['判断'])} vs {len(lines)})")
chk(set(lc["逐线判断"].keys()) <= set(lines), "生命周期逐线 ⊆ 6有线集")

# 4) HTML
h = open(XL+f"theme_body_{D}.html", encoding="utf-8").read()
chk(h.count("<div") == h.count("</div>"), f"div 配平 {h.count('<div')}/{h.count('</div>')}")
chk(h.count('class="rowA"')==1, "rowA 恰好1个")
seg = h[h.index('<div class="rowA">'): h.index('<div class="card">')]
chk(seg.count('class="hero"')==1, "rowA 含 1 hero")
chk(seg.count('class="kpi"')==4, f"rowA 含 4 kpi（实际 {seg.count('class=\"kpi\"')}）")
need = ["一 荐票卡 · 题材综合判断","二 三级判定 · 方向宽度与六有","三 主流生命周期 · 逐线判定",
        "四 龙头识别 · 谁是真龙","五 自主深挖 · 新线孵化","六 认知迭代"]
pos = [h.find("<h2>%s</h2>"%t) for t in need]
chk(all(p>0 for p in pos), "六个 h2 标题齐全且逐字匹配")
chk(pos == sorted(pos), "六个板块顺序正确")
for bad in ("null","None","NaN","undefined"):
    chk(bad not in h, f"HTML 无裸 {bad}")
allowed = {"theme-body","rowA","hero","kick","stance","pill","kpi","top","chip2","c-hit","c-warn","c-half","c-miss",
           "lab","big","sub2","card","trow","obs","obslist","obs-head","obs-nm","obs-pos","obs-watch","obs-rec","obs-lab","obs-lab2","mut"}
used = set(re.findall(r'class="([^"]+)"', h))
extra = {c for grp in used for c in grp.split()} - allowed
chk(not extra, f"无自造 class（多余={sorted(extra)}）")

# 5) 交易计划
tp = json.load(open(XL+f"交易计划_theme_{D}.json", encoding="utf-8"))
st = json.load(open(XL+"_模拟盘/theme/状态.json", encoding="utf-8"))
held = {x["code"] for x in st["持仓"]}
sold = {x["代码"] for x in tp["sells"]}
chk(held <= sold | {x["代码"] for x in tp["buys"]}, f"在持票逐票表态: 在持{sorted(held)} 表态{sorted(sold|{x['代码'] for x in tp['buys']})}")
chk(all(x["腿"] in ("open","close") for x in tp["sells"]), "sells 腿∈{open,close}")

# 6) 回执
cr = json.load(open(XL+f"能力使用回执_theme_{D}.json", encoding="utf-8"))
chk(cr["status"]=="no_eligible_capabilities" and cr["considered_ids"]==[] and cr["applied"]==[], "回执 status/空列表合规")

print("\n=== 总判定:", "ALL PASS" if ok else "有 FAIL")
