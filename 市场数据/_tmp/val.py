import io, json, re, os
B = r"D:/股票数据/市场数据/_学习"
jsons = ["theme判断_20261020.json","题材荐票_20261020.json","题材龙头判断_20261020.json",
         "题材生命周期判断_20261020.json","交易计划_theme_20261020.json"]
for f in jsons:
    p=os.path.join(B,f)
    raw=io.open(p,"rb").read()
    try:
        j=json.loads(raw.decode("utf-8"))
        print("OK", f, len(raw), "keys=", list(j.keys())[:8])
    except Exception as e:
        print("BAD", f, e)
# cross checks
tp=json.loads(io.open(os.path.join(B,"题材荐票_20261020.json"),encoding="utf-8").read())
plan=json.loads(io.open(os.path.join(B,"交易计划_theme_20261020.json"),encoding="utf-8").read())
print("荐票codes", tp["荐票"], "| 标的类型", [(x["代码"],x["类型"],x["负面过滤"]["命中维度数"]) for x in tp["标的"]])
print("buys", [(b["代码"],b["权重%"],b["buy_gate"]) for b in plan["buys"]])
print("sells", [(s["代码"],s["腿"]) for s in plan["sells"]])
print("003029 in buys?", any(b["代码"]=="003029" for b in plan["buys"]))
# html checks
h=io.open(os.path.join(B,"theme_body_20261020.html"),encoding="utf-8").read()
print("HTML len", len(h))
print("open div", h.count("<div"), "close div", h.count("</div>"))
print("script/style", "<script" in h, "<style" in h)
print("认知迭代：", "认知迭代：" in h)
print("h2", re.findall(r"<h2>(.*?)</h2>", h))
print("LEDGER", h.count("<!--LEDGER-->"))
