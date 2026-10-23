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

# 总审 指派清单
m = load(os.path.join(L, "总审_20261022.json"))
print("总审顶层键:", list(m.keys()))
for k in m.keys():
    if "指派" in k:
        print("\n=== %s ===" % k)
        print(json.dumps(m[k], ensure_ascii=False, indent=1)[:6000])

# 先行指标 今日/昨日
si = load(os.path.join(L, "_情绪先行指标.json"))
for d in ("20261022","20261023"):
    print("\n=== 先行指标 %s ===" % d)
    print(json.dumps(si.get(d), ensure_ascii=False, indent=1))

# limitup 能力预加载完整
cap = load(os.path.join(L, "能力预加载_20261023.json"))
print("\n=== 能力预加载 limitup ===")
print(json.dumps(cap["routes"]["limitup"], ensure_ascii=False, indent=1))
