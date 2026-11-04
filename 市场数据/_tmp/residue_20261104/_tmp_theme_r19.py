import json, csv, os, statistics
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
zw = L(B+"题材归位_20261030.json")["映射"]
rows = list(csv.DictReader(open(r"D:/股票数据/市场数据/20261030/zt_pool.csv", encoding='utf-8-sig')))
pool = {}
for r in rows:
    pool[r["代码"]] = r
lines = {}
for code, v in zw.items():
    r = pool.get(code)
    if not r: continue
    ln = v["大方向"]
    d = lines.setdefault(ln, {"家数":0,"封单":0.0,"剔一字封单":0.0,"一字":0,"早封":0,"开板家":0,
                              "炸次":0,"环节":{},"板":[],"封单比":[]})
    d["家数"] += 1
    feng = float(r["封板资金"])/1e8
    ratio = float(r["封板资金"])/float(r["流通市值"])*100
    fs = r["首次封板时间"]; ls = r["最后封板时间"]
    yz = (fs == "092500" or fs == "092501" or fs == "092502") and fs==ls
    d["封单"] += feng
    if yz: d["一字"] += 1
    else: d["剔一字封单"] += feng
    if fs <= "093100": d["早封"] += 1
    zha = int(r["炸板次数"]); d["炸次"] += zha
    if zha > 0: d["开板家"] += 1
    d["环节"][v["环节"]] = d["环节"].get(v["环节"],0)+1
    d["板"].append(int(r["连板数"]))
    d["封单比"].append(ratio)

tot_f = sum(d["封单"] for d in lines.values())
print(f"全场封板总额 {tot_f:.2f}亿  涨停47  一字合计 {sum(d['封单'] for d in lines.values() if False):.2f}")
for ln, d in sorted(lines.items(), key=lambda x:-x[1]["家数"]):
    eps = len(d["环节"]); maxep = max(d["环节"].values())
    print(f"{ln}: 家{d['家数']} 板最高{max(d['板'])} 封单{d['封单']:.2f}亿 剔一字{d['剔一字封单']:.2f}亿 "
          f"一字{d['一字']} 早封{d['早封']}/{d['家数']} 开板家{d['开板家']}/{d['家数']} 炸{d['炸次']} "
          f"封单比中位{statistics.median(d['封单比']):.2f}% 环节数{eps} 单环节最大{maxep} 离散度{eps/d['家数']:.2f}")
print()
# 族聚合 消费系
cons = ["消费/大消费","消费/白酒"]
c30 = sum(lines[x]["家数"] for x in cons if x in lines)
print("消费系(大消费+白酒) 今日合计", c30, "封单", round(sum(lines[x]["封单"] for x in cons if x in lines),2))
# 昨日
zw29 = L(B+"题材归位_20261029.json")["映射"]
c29 = sum(1 for v in zw29.values() if v["大方向"] in cons)
print("消费系 20261029(名称=消费/食品零售) 合计", c29)
zw28 = L(B+"题材归位_20261028.json")["映射"]
print("消费系 20261028", sum(1 for v in zw28.values() if v["大方向"] in cons), sorted(set(v["大方向"] for v in zw28.values())))
