import json, io, os
B = r"D:\股票数据\市场数据\_学习"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)
for r in ["auction", "lhb", "theme", "logic", "limitup"]:
    d = L(os.path.join(B, f"{r}判断_20260826.json"))
    print("#" * 20, r, "可证伪条件")
    print(str(d["判断"].get("可证伪条件", ""))[:1600])
    print("--- 认知迭代(截断) ---")
    ci = d.get("认知迭代")
    print(json.dumps(ci, ensure_ascii=False)[:900] if not isinstance(ci, str) else ci[:900])
    print()
