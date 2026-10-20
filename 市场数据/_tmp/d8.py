import json, io, os, csv
B = r"D:/股票数据/市场数据"
def L(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with io.open(p, encoding=enc) as f: return json.load(f)
        except UnicodeDecodeError: continue
        except Exception as e: return ("ERR", str(e))
    return None
ch = L(os.path.join(B,"_学习/涨停对链条_20261020.json"))
print("### 题材线概要 (家数/最高板/最早封/早封占比/开板占比)")
for t in ch["题材线"]:
    print(f'{t["大方向"]:8s} n={t["家数"]:2d} h={t["最高连板"]} 早封={t["最早封板"]} 早封占比={t.get("早封占比")} 开板={t.get("开板占比")} | {t.get("强度画像","")[:80]}')
print()
print("### 机器人线 逐票")
with io.open(os.path.join(B,"20261020/zt_pool.csv"), encoding="utf-8-sig") as f:
    pool = {r["代码"]:r for r in csv.DictReader(f)}
gw = L(os.path.join(B,"_学习/题材归位_20261020.json"))["映射"]
for c in L(os.path.join(B,"_学习/题材归位_20261020.json"))["方向聚合"]["机器人"]:
    m=gw[c]; p=pool.get(c,{})
    print(c, m["名称"], "|", m["连板口径"], "| 首封",m["首封"],"| 环节:", m["环节"], "| 封单亿", round(float(p.get("封板资金",0))/1e8,2), "| 成交亿", round(float(p.get("成交额",0))/1e8,2), "| 换手",round(float(p.get("换手率",0)),2), "| 炸",p.get("炸板次数"), "| 流通亿", round(float(p.get("流通市值",0))/1e8,1), "| 价",p.get("最新价"))
print()
print("### 其余关键票")
for c in ["003029","600178","600148","002724","002835","001323","603236","603068","603893","301313","002881","001388","600267","300244","605177","002940","002929"]:
    m=gw.get(c,{}); p=pool.get(c,{})
    print(c, m.get("名称"), m.get("大方向"), "|", m.get("连板口径"),"| 首封",m.get("首封"),"| 环节:",m.get("环节"), "| 封单亿", round(float(p.get("封板资金",0))/1e8,2),"| 换手",round(float(p.get("换手率",0)),2),"| 炸",p.get("炸板次数"),"| 流通亿",round(float(p.get("流通市值",0))/1e8,1),"| 价",p.get("最新价"))
