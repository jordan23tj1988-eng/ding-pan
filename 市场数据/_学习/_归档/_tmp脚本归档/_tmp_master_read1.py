import json, io, os
B = r"D:\股票数据\市场数据\_学习"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

print("=" * 30, "昨日总审 顶层键+结构")
z = L(os.path.join(B, "总审_20260825.json"))
def walk(o, pre="", depth=0):
    if depth > 2: return
    if isinstance(o, dict):
        for k, v in o.items():
            t = type(v).__name__
            if isinstance(v, (dict, list)):
                print(f"{pre}{k}: {t}({len(v)})")
                walk(v, pre + "  ", depth + 1)
            else:
                s = str(v)
                print(f"{pre}{k}: {t} = {s[:120]}")
    elif isinstance(o, list):
        if o and isinstance(o[0], dict):
            print(f"{pre}[0].keys = {list(o[0].keys())}")
walk(z)
print()
print("=" * 30, "昨日总审 总裁决 全文")
print(json.dumps(z.get("总裁决"), ensure_ascii=False, indent=1)[:3000])
print()
print("=" * 30, "昨日总审 指派清单 全文")
print(json.dumps(z.get("指派清单"), ensure_ascii=False, indent=1)[:4000])
print()
print("=" * 30, "fact_20260826")
print(json.dumps(L(os.path.join(B, "fact_20260826.json")), ensure_ascii=False, indent=1)[:3500])
print()
print("=" * 30, "summary 20260826")
print(json.dumps(L(r"D:\股票数据\市场数据\20260826\summary.json"), ensure_ascii=False, indent=1)[:2500])
