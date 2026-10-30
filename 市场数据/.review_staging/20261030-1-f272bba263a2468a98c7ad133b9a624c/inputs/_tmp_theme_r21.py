import json, collections
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
d=L(B+"日内轮动图谱_20261030.json")
g=d["graph"]
def half(ts):
    t=ts[11:16]
    return "am" if t<="11:30" else "pm"
agg=collections.defaultdict(lambda: {"am":[], "pm":[]})
for r in g:
    agg[r["theme"]][half(r["ts"])].append((r["ts"],r["n"],r["mean_pct"]))
for th,v in agg.items():
    am=v["am"]; pm=v["pm"]
    am_avg=sum(x[2] for x in am)/len(am) if am else None
    pm_avg=sum(x[2] for x in pm)/len(pm) if pm else None
    am_last=am[-1][2] if am else None
    pm_last=pm[-1][2] if pm else None
    print(f"{th}: am_avg={am_avg:.2f} am末={am_last:.2f} pm_avg={pm_avg:.2f} pm末={pm_last:.2f} 变化={pm_last-am_last:+.2f} 点数am{len(am)}/pm{len(pm)}")
