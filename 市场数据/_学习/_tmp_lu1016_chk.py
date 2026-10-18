# -*- coding: utf-8 -*-
import json, os, re, csv
B=r"D:\股票数据\市场数据\_学习"; M=r"D:\股票数据\市场数据"
# 1 JSON 校验
for f in ["limitup判断_20261016.json","交易计划_limitup_20261016.json","能力回执_limitup_20261016.json"]:
    d=json.load(open(os.path.join(B,f),encoding="utf-8"))
    print(f,"OK keys=",list(d.keys()))
j=json.load(open(os.path.join(B,"limitup判断_20261016.json"),encoding="utf-8"))
print("档位",j["判断"]["档位"],"置信度",j["判断"]["置信度"])
tp=[x for x in j["判断"]["荐票"]["标的"] if x["类型"]=="荐票"]
ob=[x for x in j["判断"]["荐票"]["标的"] if x["类型"]=="观察"]
print("荐票",len(tp),[x["代码"] for x in tp],"观察",len(ob),[x["代码"] for x in ob])
print("证据条数",len(j["判断"]["证据"]),"可证伪",len(j["判断"]["可证伪条件"]),"盲区",len(j["判断"]["独立盲区声明"]),"认知迭代",len(j["认知迭代"]),"深挖",len(j["深挖"]))
zt={r["代码"] for r in csv.DictReader(open(os.path.join(M,"20261016","zt_pool.csv"),encoding="utf-8-sig"))}
print("zt池",len(zt),"荐票全在池内:",all(x["代码"] in zt for x in tp+ob))
p=json.load(open(os.path.join(B,"交易计划_limitup_20261016.json"),encoding="utf-8"))
w=[b["权重"] for b in p["buys"]]
print("buys",len(p["buys"]),w,"合计",sum(w),"sells",len(p["sells"]),"在池内",all(b["代码"] in zt for b in p["buys"]))
print("buy_gate齐全:",all(k in b for b in p["buys"] for k in ("buy_gate","理由","结算口径")))
# 2 HTML 检查
h=open(os.path.join(B,"limitup_body_20261016.html"),encoding="utf-8").read()
print("\nHTML len",len(h))
print("h2数",len(re.findall(r"<h2>",h)),[x for x in re.findall(r"<h2>(.*?)</h2>",h)])
print("div开",h.count("<div"),"div闭",h.count("</div>"),"配平",h.count("<div")==h.count("</div>"))
print("table开",h.count("<table"),"闭",h.count("</table>"),"tr",h.count("<tr"),"td",h.count("<td"))
print("doctype",h.startswith("<!doctype"),"end",h.strip()[-14:])
print("类名复用:",[c for c in ["rowA","hero","kpi","pill","insight","card","obs","obslist","obs-head","obs-nm","obs-pos","obs-lab","obs-lab2","mut"] if ('class="'+c) in h])
