import json, os, csv, re, sys
B = r"D:\股票数据\市场数据\_学习"
R = r"D:\股票数据\市场数据"
ok = True
def chk(cond, msg):
    global ok
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: ok = False

# 1 四文件存在可解析
pj = os.path.join(B,"limitup判断_20261030.json")
pt = os.path.join(B,"交易计划_limitup_20261030.json")
ph = os.path.join(B,"limitup_body_20261030.html")
pr = os.path.join(B,"能力使用回执_limitup_20261030.json")
for p in (pj,pt,ph,pr): chk(os.path.exists(p) and os.path.getsize(p)>0, "存在非空 %s (%d B)"%(os.path.basename(p), os.path.getsize(p) if os.path.exists(p) else 0))
J = json.load(open(pj,encoding='utf-8')); T = json.load(open(pt,encoding='utf-8')); RC = json.load(open(pr,encoding='utf-8'))
H = open(ph,encoding='utf-8').read()

# 2 结论非空
chk(bool(J["判断"]["结论"].strip()) and len(J["判断"]["结论"])>50, "判断.结论 非空且充实 (%d 字)"%len(J["判断"]["结论"]))
chk(bool(J["荐票"]["结论"].strip()), "荐票.结论 非空")
chk(len(J["判断"]["证据"])>=8, "证据条数 %d ≥8"%len(J["判断"]["证据"]))
chk(len(J["判断"]["可证伪条件"])>=3, "可证伪条件 %d ≥3"%len(J["判断"]["可证伪条件"]))
chk(bool(J["判断"]["独立盲区声明"].strip()), "独立盲区声明 非空")
chk(len(J["认知迭代"])>=3, "认知迭代 %d 条"%len(J["认知迭代"]))
chk(bool(str(J["深挖"]).strip()) and len(J["深挖"])>200, "深挖 非空 (%d 字)"%len(J["深挖"]))

# 3 置信度
c = J["判断"]["置信度"]; chk(isinstance(c,(int,float)) and 0<=c<=100, "置信度 %s ∈[0,100]"%c)
chk(J["判断"]["档位"] in ("A","B","C"), "档位=%s"%J["判断"]["档位"])

# 4 标的代码 ∈ zt_pool
with open(os.path.join(R,"20261030","zt_pool.csv"),encoding='utf-8-sig') as f:
    codes = {r["代码"] for r in csv.DictReader(f)}
tg = J["荐票"]["标的"]
chk(len(tg)<=3, "标的数 %d ≤3"%len(tg))
for t in tg:
    chk(t["代码"] in codes, "标的 %s %s ∈ zt_pool"%(t["代码"],t["名称"]))
    chk(t["类型"] in ("荐票","观察"), "  类型=%s 合法"%t["类型"])
    chk("n=" in t["历史对照"], "  %s 历史对照含量化 n="%t["代码"])

# 5 body 六个 h2 标题逐字
want = ["一 市场温度与涨停质量核心判断","二 连板梯队与归位台账","三 炸板与虚胖检测 · 质量库","四 全池期望与荐票","五 自主深挖","六 认知迭代"]
h2 = re.findall(r"<h2>(.*?)</h2>", H)
chk(len(h2)==6, "h2 数量 = %d"%len(h2))
chk(h2==want, "h2 标题逐字一致: %s"%("是" if h2==want else h2))
# 第一段含 市场温度
first_sec = H.split("<h2>")[1] if H.count("<h2>") else ""
chk("市场温度" in first_sec, "第一段(h2一)含关键词『市场温度』")

# 6 div 配平
op = len(re.findall(r"<div\b", H)); cl = len(re.findall(r"</div>", H))
chk(op==cl, "div 配平 open=%d close=%d"%(op,cl))
chk(len(re.findall(r'class="obslist"', H))>=1 and len(re.findall(r'class="obs"', H))>=1, "obs 组件存在 obs=%d obslist=%d"%(len(re.findall(r'class="obs"',H)),len(re.findall(r'class="obslist"',H))))
chk(len(re.findall(r'class="trow"', H))>=3, "trow 表格 %d 个"%len(re.findall(r'class="trow"', H)))

# 7 无裸 null/None
bad_html = [m for m in re.findall(r"[Nn](?:ull|one)", H)]
chk(len(bad_html)==0, "HTML 无 null/None (%d)"%len(bad_html))
def scan(o, path=""):
    out=[]
    if isinstance(o,dict):
        for k,v in o.items(): out += scan(v, path+"."+str(k))
    elif isinstance(o,list):
        for i,v in enumerate(o): out += scan(v, path+f"[{i}]")
    elif o is None: out.append(path)
    return out
nul = scan(J)+scan(T)+scan(RC)
chk(len(nul)==0, "JSON 无 None 值 (发现 %d: %s)"%(len(nul), nul[:5]))

# 8 交易计划 在持票无漏
st = json.load(open(os.path.join(B,"_模拟盘","limitup","状态.json"),encoding='utf-8'))
held = {p["code"]: p["name"] for p in st.get("持仓",[])}
sold = {s["代码"] for s in T["sells"]}
for c_,n_ in held.items():
    chk(c_ in sold, "在持票 %s %s 已在sells表态"%(c_,n_))
for s in T["sells"]:
    chk(s["腿"] in ("open","close"), "sell %s 腿=%s 合法"%(s["代码"],s["腿"]))
buy_codes = {b["代码"] for b in T["buys"]}
for b in T["buys"]:
    chk(b["代码"] in codes, "buy %s ∈ zt_pool"%b["代码"])
    g = b.get("buy_gate",{})
    chk(isinstance(g.get("min_gap_pct"),(int,float)) and isinstance(g.get("max_gap_pct"),(int,float)), "buy %s buy_gate 完整 [%s,%s]"%(b["代码"],g.get("min_gap_pct"),g.get("max_gap_pct")))
if not T["buys"]:
    chk(bool(T["notes"].strip()), "空仓 已写理由")
chk(bool(T["notes"].strip()), "notes 非空")

# 9 能力回执 schema
cap = json.load(open(os.path.join(B,"能力预加载_20261030.json"),encoding='utf-8'))
recs = [r["id"] for r in cap["routes"]["limitup"]["records"]]
chk(RC["route"]=="limitup", "回执 route=limitup")
chk(RC["status"] in ("applied","rejected_all","no_eligible_capabilities"), "回执 status=%s"%RC["status"])
considered = set(RC["considered_ids"]); applied = {a["id"] for a in RC["applied"]}; rej = {r["id"] for r in RC["rejected"]}
for rid in recs:
    chk(rid in considered and (rid in applied or rid in rej), "能力 %s 已逐条回应(%s)"%(rid, "applied" if rid in applied else "rejected"))
for a in RC["applied"]:
    chk(bool(a.get("effect")) and bool(a.get("source_locator")), "applied %s 有 effect+source_locator"%a["id"])

# 10 Master 指派承接
chk("MA-20261029-04" in J["深挖"], "深挖 含承接 Master 指派 MA-20261029-04")
chk("深挖结果" in J["深挖"], "深挖 含『深挖结果』段")

print("\n" + ("OK 全部自检通过" if ok else "NG 存在失败项"))
sys.exit(0 if ok else 1)
