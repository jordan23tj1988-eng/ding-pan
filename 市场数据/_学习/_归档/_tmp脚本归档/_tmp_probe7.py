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

y = load(os.path.join(L, "limitup判断_20261022.json"))
print("=== limitup判断_20261022 keys ===", list(y.keys()))
print(json.dumps(y, ensure_ascii=False, indent=1)[:9000])
