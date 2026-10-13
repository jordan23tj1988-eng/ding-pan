# -*- coding: utf-8 -*-
import json, os, re, csv
R = r"D:\股票数据\市场数据\_学习"
B = r"D:\股票数据\市场数据"
ok = True
def chk(c, msg):
    global ok
    print(("PASS " if c else "FAIL ") + msg)
    if not c: ok = False

# 1 判断JSON可load且日期一致
j = json.load(open(os.path.join(R,"auction判断_20261012.json"), encoding='utf-8'))
chk(j.get("日期")=="20261012" and j.get("路")=="auction", "1) 判断JSON可load且日期=20261012/路=auction")
chk(isinstance(j["判断"]["证据"], list) and len(j["判断"]["证据"])>=8 and j["判断"]["档位"] in "ABC", "1b) 证据为list(%d条)/档位=%s/置信度=%s" % (len(j["判断"]["证据"]), j["判断"]["档位"], j["判断"]["置信度"]))

# 2 荐票类型代码 ∈ 当日zt_pool
rows = list(csv.DictReader(open(os.path.join(B,"20261012","zt_pool.csv"), encoding='utf-8-sig')))
codes = {r["代码"] for r in rows}
rec = [t for t in j["荐票"]["标的"] if t["类型"]=="荐票"]
obs = [t for t in j["荐票"]["标的"] if t["类型"]=="观察"]
allok = all(t["代码"] in codes for t in rec)
chk(allok and len(rec)<=3, "2) 荐票%d只全部∈zt_pool(%d只)；观察%d只" % (len(rec), len(codes), len(obs)))
chk(all(("n=" in t["历史对照"] and "胜率" in t["历史对照"] and "均收" in t["历史对照"]) for t in j["荐票"]["标的"]), "2b) 每票历史对照含量化(n=/胜率/均收)")

# 3 body div平衡 + 去标签>=2000
h = open(os.path.join(R,"auction_body_20261012.html"), encoding='utf-8').read()
op, cl = h.count("<div"), h.count("</div>")
txt = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
txt = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
txt = re.sub(r"<[^>]+>", "", txt)
txt = re.sub(r"\s+", " ", txt).strip()
chk(op==cl, "3) body <div>=%d == </div>=%d" % (op, cl))
chk(len(txt)>=2000, "3b) body去标签后 %d 字符 (>=2000)" % len(txt))
chk(all(m in h for m in ["<!--SCORECARD--><!--/SCORECARD-->","<!--POOLLEDGER--><!--/POOLLEDGER-->","<!--MACHSIG--><!--/MACHSIG-->"]), "3c) 三标记区(SCORECARD/POOLLEDGER/MACHSIG)完整")
chk(h.count('class="obs"')>=5 and "obslist" in h, "3d) obs荐票卡 %d 张 + obslist" % h.count('class="obs"'))
chk(len(re.findall(r"<h2>", h))==6 and "三 昨日" in h, "3e) 六板块(%d个h2)、含『三 昨日』锚点" % len(re.findall(r"<h2>", h)))

# 4 交易计划 buys<=5 且 sells 覆盖全部在持票
p = json.load(open(os.path.join(R,"交易计划_auction_20261012.json"), encoding='utf-8'))
st = json.load(open(os.path.join(R,"_模拟盘","auction","状态.json"), encoding='utf-8-sig'))
held = [x.get("code") or x.get("代码") for x in (st.get("持仓") or [])]
sold = [s["代码"] for s in p.get("sells", [])]
chk(len(p["buys"])<=5, "4) buys=%d (<=5)" % len(p["buys"]))
chk(set(held) <= set(sold), "4b) sells覆盖在持票：持仓=%s / sells=%s（空仓合法，notes须表态）" % (held, sold))
chk(("持仓=[]" in p["notes"]) or set(held)<=set(sold), "4c) notes逐票表态（持仓为空已写明，无漏票）")
chk(all("buy_gate" in b and b["buy_gate"]["max_gap_pct"] < 5 for b in p["buys"]), "4d) 每只buy_gate均<5%（闸门纪律落到计划）")

# 5 能力回执 considered_ids == 预加载本路id集合
pre = json.load(open(os.path.join(R,"能力预加载_20261012.json"), encoding='utf-8-sig'))
a = pre["routes"]["auction"]
ids = [r.get("id") for r in (a.get("records") or [])]
rc = json.load(open(os.path.join(R,"能力回执_auction_20261012.json"), encoding='utf-8'))
chk(set(rc["considered_ids"])==set(ids), "5) 回执considered_ids=%s == 预加载auction id集合=%s（status=%s/eligible=%s）" % (rc["considered_ids"], ids, rc.get("status"), a.get("eligible_count")))
chk(rc["status"]=="no_eligible_capabilities" and rc["applied"]==[] and rc["rejected"]==[], "5b) 无能力：status/两个数组均为空")

# 附：关键数字复算（不进判定，只做证据一致性）
s = json.load(open(os.path.join(R,"竞价池结算_20261009.json"), encoding='utf-8-sig'))
gate=[d for d in s["明细"] if d["T1高开"]<5]; hi=[d for d in s["明细"] if d["T1高开"]>=5]
gm=round(sum(d["执行收益"] for d in gate)/len(gate),2); hm=round(sum(d["执行收益"] for d in hi)/len(hi),2)
chk(gm==4.77 and hm==-2.88, "附) 昨日池闸门复算 闸门内%.2f%%/%d只 vs 高开≥5档%.2f%%/%d只" % (gm, len(gate), hm, len(hi)))

print("\n==== 总判定:", "PASS" if ok else "FAIL", "====")
