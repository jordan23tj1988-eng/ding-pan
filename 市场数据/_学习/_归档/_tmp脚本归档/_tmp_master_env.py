import json, io, os, re
B = r"D:\股票数据\市场数据\_学习"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

T = L(os.path.join(B, "_市场温度表.json"))
H = L(os.path.join(B, "子agent增强", "_战绩画像汇总_20260826.json"))

def wr(s):
    """'4/5' -> (4,5)"""
    if not isinstance(s, str) or "/" not in s: return None
    a, b = s.split("/")[:2]
    try: return int(a), int(b)
    except: return None

print("=" * 20, "环境加权:按荐票日温度档分组(温度表_市场温度表.json '温度档'字段)")
res = {}
for key, node in H["五路"].items():
    rows = node.get("按日", [])
    buckets = {}
    for r in rows:
        d = str(r.get("荐票日"))
        t = T.get(d, {})
        tier = t.get("温度档", "无温度表记录")
        temp = t.get("温度")
        w = wr(r.get("执行胜率"))
        ret = r.get("执行均收", r.get("均收"))
        gain = r.get("增益pp")
        b = buckets.setdefault(tier, {"win": 0, "n": 0, "rets": [], "gains": [], "days": 0, "dates": []})
        b["days"] += 1
        b["dates"].append(f"{d}({temp})")
        if w: b["win"] += w[0]; b["n"] += w[1]
        if isinstance(ret, (int, float)): b["rets"].append(ret)
        if isinstance(gain, (int, float)): b["gains"].append(gain)
    res[key] = buckets
    print(f"\n--- {key} ({node.get('路')}) 合计={node.get('合计')}")
    for tier, b in sorted(buckets.items()):
        avg = round(sum(b["rets"]) / len(b["rets"]), 2) if b["rets"] else None
        ag = round(sum(b["gains"]) / len(b["gains"]), 2) if b["gains"] else None
        rate = f"{b['win']}/{b['n']}={round(100*b['win']/b['n'],1)}%" if b["n"] else "n/a"
        print(f"  [{tier}] 荐票日数={b['days']} 票胜率={rate} 均收={avg} 均增益pp={ag}")
        print(f"      日期={b['dates']}")

print()
print("=" * 20, "偏冷档横向对比(n=票数;n<5不参与裁决)")
tbl = []
for key, b in res.items():
    c = b.get("偏冷")
    if not c: 
        print(f"{key}: 偏冷档无样本"); continue
    avg = round(sum(c["rets"]) / len(c["rets"]), 2) if c["rets"] else None
    ag = round(sum(c["gains"]) / len(c["gains"]), 2) if c["gains"] else None
    tbl.append((key, c["days"], c["win"], c["n"], round(100*c["win"]/c["n"],1) if c["n"] else None, avg, ag))
for t in sorted(tbl, key=lambda x: (x[6] if x[6] is not None else -99), reverse=True):
    print(f"{t[0]:9s} 偏冷荐票日={t[1]:2d} 票={t[3]:3d} 胜率={t[4]}% 均收={t[5]} 均增益pp={t[6]}  {'✅参与' if t[3]>=5 else '❌n<5不参与'}")

print()
print("=" * 20, "温度档全景(近30交易日)")
ds = sorted([d for d in T if re.fullmatch(r"20\d{6}", d)])[-30:]
for d in ds:
    print(d, T[d].get("温度"), T[d].get("温度档"), "涨停", T[d].get("涨停数"), "二板加", T[d].get("二板加"), "梯队1", T[d].get("梯队", {}).get("1"))
