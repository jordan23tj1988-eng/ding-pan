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

q = load(os.path.join(L, "_涨停质量库.json"))
print("质量库 keys:", list(q.keys()))
for k,v in q.items():
    if isinstance(v, dict):
        print(" -", k, "dict keys:", list(v.keys())[:15])
    elif isinstance(v, list):
        print(" -", k, "list len", len(v), "first:", json.dumps(v[0], ensure_ascii=False)[:300] if v else "")
    else:
        print(" -", k, "=", v)

print("\n=== 基准 ===")
for k in ("更新","样本","窗口","基准","环境规则","口径"):
    if k in q:
        print(k, json.dumps(q[k], ensure_ascii=False)[:1200])
