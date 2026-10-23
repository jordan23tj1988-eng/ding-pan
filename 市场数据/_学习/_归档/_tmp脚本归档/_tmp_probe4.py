import json, os
B = r"D:/股票数据/市场数据"
L = os.path.join(B, "_学习")
def load(p):
    for enc in ("utf-8-sig","utf-8","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    return None

m = load(os.path.join(L, "总审_20261022.json"))
print("=== 综合深挖 ===")
print(json.dumps(m.get("综合深挖"), ensure_ascii=False, indent=1)[:5000])
print("\n=== 矛盾捕获 ===")
print(json.dumps(m.get("矛盾捕获"), ensure_ascii=False, indent=1)[:2500])
