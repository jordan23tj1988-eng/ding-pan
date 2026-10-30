# -*- coding: utf-8 -*-
"""收尾自检: 四件存在/可解析 + 结论非空 + 置信度 + 代码∈zt_pool + body 6个h2标题逐字 + div配平 + 无裸null + 在持票无漏"""
import json, os, re, csv, sys
B = r"D:\股票数据\市场数据\_学习"
D = r"D:\股票数据\市场数据"
err = []

def chk(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond: err.append(msg)

JA = os.path.join(B, "auction判断_20261030.json")
HB = os.path.join(B, "auction_body_20261030.html")
JT = os.path.join(B, "交易计划_auction_20261030.json")
JR = os.path.join(B, "能力使用回执_auction_20261030.json")

print("== 1. 四文件存在且可json解析 ==")
objs = {}
for p, need_json in ((JA, True), (HB, False), (JT, True), (JR, True)):
    ex = os.path.isfile(p)
    chk(ex, "存在 %s" % os.path.basename(p))
    if ex and need_json:
        try:
            objs[p] = json.load(open(p, encoding='utf-8')); chk(True, "json可解析 %s" % os.path.basename(p))
        except Exception as e:
            chk(False, "json解析 %s: %s" % (os.path.basename(p), e))

print("== 2. 判断.结论非空 / 置信度 0-100 / 档位 ==")
j = objs.get(JA, {})
d = j.get("判断", {})
chk(bool(str(d.get("结论", "")).strip()), "判断.结论非空 (len=%d)" % len(str(d.get("结论", ""))))
chk(isinstance(d.get("置信度"), int) and 0 <= d["置信度"] <= 100, "置信度整数且0-100 = %r" % d.get("置信度"))
chk(d.get("档位") in ("A", "B", "C"), "档位∈A/B/C = %r" % d.get("档位"))
chk(bool(str(d.get("可证伪条件", "")).strip()), "可证伪条件非空")
chk(bool(str(d.get("独立盲区声明", "")).strip()), "独立盲区声明非空")
chk(isinstance(d.get("证据"), list) and len(d["证据"]) >= 5, "证据条数 = %d" % len(d.get("证据") or []))
chk(j.get("日期") == "20261030" and j.get("路") == "auction", "日期/路字段")
chk(isinstance(j.get("认知迭代"), list) and len(j["认知迭代"]) >= 2, "认知迭代条数 = %d" % len(j.get("认知迭代") or []))
chk("MA-20261029-03" in str(j.get("深挖", "")) and "承接Master指派" in str(j.get("深挖", "")), "深挖含Master指派承接格式")

print("== 3. 所有标的代码 ∈ 当日 zt_pool ==")
zp = {r["代码"].zfill(6) for r in csv.DictReader(open(os.path.join(D, r"20261030\zt_pool.csv"), encoding='utf-8-sig'))}
codes = [t["代码"] for t in j.get("荐票", {}).get("标的", [])]
chk(len(codes) <= 3, "荐票只数<=3 = %d" % len(codes))
for c in codes:
    chk(c in zp, "推荐代码 %s ∈ zt_pool" % c)
for t in j.get("荐票", {}).get("标的", []):
    chk(t.get("类型") in ("荐票", "观察"), "%s 类型合法 = %r" % (t["代码"], t.get("类型")))
    chk("同类历史" in t.get("历史对照", "") and "n=" in t.get("历史对照", ""), "%s 历史对照含量化n" % t["代码"])
for b in objs.get(JT, {}).get("buys", []):
    chk(b["代码"] in zp, "买单 %s ∈ zt_pool" % b["代码"])
    chk(isinstance(b.get("权重%"), int), "买单 %s 权重%%为整数 = %r" % (b["代码"], b.get("权重%")))
    chk(isinstance(b.get("buy_gate"), dict) and "min_gap_pct" in b["buy_gate"] and "max_gap_pct" in b["buy_gate"], "买单 %s buy_gate完整" % b["代码"])

print("== 4. body: 恰好6个h2且标题逐字一致 ==")
h = open(HB, encoding='utf-8').read()
h2 = re.findall(r"<h2>(.*?)</h2>", h, re.S)
want = ["一 竞价选股池 · 核心判断", "二 竞价温度与闸门对账", "三 竞价池兑现与信号胜率",
        "四 明日竞价预案 · 当日池处置", "五 自主深挖", "六 认知迭代"]
chk(len(h2) == 6, "h2 数量 = %d" % len(h2))
for i, w in enumerate(want):
    got = h2[i].strip() if i < len(h2) else "<缺>"
    chk(got == w, "h2[%d] 逐字一致: %r" % (i, got))

print("== 5. div 配平 / 裸 null / obs 组件 / trow ==")
o_div = len(re.findall(r"<div\b", h)); c_div = len(re.findall(r"</div>", h))
chk(o_div == c_div, "<div> 配平 open=%d close=%d" % (o_div, c_div))
bare_null = re.findall(r"(?<![A-Za-z_\u4e00-\u9fa5])null(?![A-Za-z_\u4e00-\u9fa5])|(?<![A-Za-z_\u4e00-\u9fa5])None(?![A-Za-z_\u4e00-\u9fa5])", h)
chk(len(bare_null) == 0, "无裸 null/None 字面量 (%d)" % len(bare_null))
chk('<table class="trow"' in h, "使用 <table class=\"trow\"> 家族")
n_obs = len(re.findall(r'<div class="obs">', h))
chk(n_obs >= len(codes), "obs 组件数 %d >= 标的数 %d" % (n_obs, len(codes)))
chk('<div class="obslist">' in h, "多卡外套 obslist")
for cls in ("obs-head", "obs-nm", "obs-pos", "obs-watch", "obs-lab", "obs-rec", "obs-lab2"):
    chk(('class="%s"' % cls) in h, "obs 子组件 %s 在页" % cls)
for bad in ("待决断", "晚间复盘预案"):
    chk(bad not in h, "无自造字样『%s』" % bad)

print("== 6. 交易计划: 在持票无漏 ==")
st = json.load(open(os.path.join(B, r"_模拟盘\auction\状态.json"), encoding='utf-8'))
held = [x["code"] for x in st.get("持仓", [])]
jt = objs.get(JT, {})
sold = [s["代码"] for s in jt.get("sells", [])]
miss = [c for c in held if c not in sold]
chk(len(miss) == 0, "在持票 %s 全部表态 (sells=%s)" % (held, sold))
for s in jt.get("sells", []):
    chk(s.get("腿") in ("open", "close"), "卖单 %s 腿合法 = %r" % (s["代码"], s.get("腿")))
chk(bool(str(jt.get("notes", "")).strip()), "notes 非空 (len=%d)" % len(str(jt.get("notes", ""))))

print("== 7. 能力回执 ==")
rc = objs.get(JR, {})
chk(rc.get("route") == "auction", "回执 route=auction")
pl = json.load(open(os.path.join(B, "能力预加载_20261030.json"), encoding='utf-8'))
recs = pl.get("routes", {}).get("auction", {}).get("records", [])
if not recs:
    chk(rc.get("status") == "no_eligible_capabilities", "无records ⇒ status=no_eligible_capabilities")
    chk(rc.get("considered_ids") == [] and rc.get("applied") == [] and rc.get("rejected") == [], "三列表全空")
else:
    chk(len(rc.get("considered_ids", [])) == len(recs), "逐条回应 records=%d" % len(recs))

print("\n== 结果: %s ==" % ("OK  全部通过" if not err else "FAIL %d 项" % len(err)))
for e in err: print("  -", e)
sys.exit(0 if not err else 1)
