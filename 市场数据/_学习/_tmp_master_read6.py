import json, io, os
B = r"D:\股票数据\市场数据\_学习"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

for r in ["auction", "lhb", "theme", "logic", "limitup"]:
    d = L(os.path.join(B, f"{r}判断_20260826.json"))
    print("#" * 25, r)
    print("--荐票.结论--")
    print(str(d.get("荐票", {}).get("结论", ""))[:1800])
    print("--荐票.标的--")
    print(json.dumps(d.get("荐票", {}).get("标的", []), ensure_ascii=False, indent=1)[:2500])
    print()
