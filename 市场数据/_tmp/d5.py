import json, io, os, csv
B = r"D:/股票数据/市场数据"
def L(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with io.open(p, encoding=enc) as f: return json.load(f)
        except UnicodeDecodeError: continue
        except Exception as e: return ("ERR", str(e))
    return None

re20 = L(os.path.join(B,"_学习/风险事件_20261020.json"))
ev = re20["事件"]
# per-code counts by 维度
from collections import defaultdict
agg = defaultdict(lambda: defaultdict(list))
for e in ev:
    c = e.get("代码")
    if c: agg[c][e.get("维度","?")].append(e)
print("### 全池54只 负面三维命中")
with io.open(os.path.join(B,"20261020/zt_pool.csv"), encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
hitcodes=[]
for r in rows:
    c=r["代码"]; d=agg.get(c)
    if d:
        hitcodes.append((c,r["名称"],r["连板数"],{k:len(v) for k,v in d.items()}))
for h in hitcodes: print(h)
print("命中票数:", len(hitcodes), "/", len(rows))

print("### 风险日历 20261020")
cal = L(os.path.join(B,"_学习/风险日历_20261020.json"))
print(json.dumps(cal, ensure_ascii=False)[:2500])
