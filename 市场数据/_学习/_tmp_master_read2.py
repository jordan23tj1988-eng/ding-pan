import json, io, os
B = r"D:\股票数据\市场数据\_学习"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

for r in ["auction", "lhb", "theme", "logic", "limitup"]:
    p = os.path.join(B, f"{r}判断_20260826.json")
    d = L(p)
    print("=" * 40, r, "顶层键")
    def walk(o, pre="", depth=0):
        if depth > 1: return
        if isinstance(o, dict):
            for k, v in o.items():
                t = type(v).__name__
                if isinstance(v, (dict, list)):
                    print(f"{pre}{k}: {t}({len(v)})")
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        print(f"{pre}  [0].keys={list(v[0].keys())}")
                    elif isinstance(v, dict):
                        walk(v, pre + "  ", depth + 1)
                else:
                    print(f"{pre}{k}: {t} = {str(v)[:200]}")
    walk(d)
    print()
