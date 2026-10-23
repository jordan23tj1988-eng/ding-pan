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
    return "LOAD_FAIL"

def show(name, p, n=3000):
    print("\n=== %s ===" % name)
    if not os.path.exists(p):
        print("MISSING", p); return
    d = load(p)
    s = json.dumps(d, ensure_ascii=False, indent=1)
    print(s[:n])

show("情绪先行指标", os.path.join(L, "_情绪先行指标.json"), 2500)
show("总审20261022", os.path.join(L, "总审_20261022.json"), 4000)
show("能力预加载", os.path.join(L, "_学习" if False else L, "能力预加载_20261023.json"), 2500)
show("模拟盘状态", os.path.join(L, "_模拟盘", "limitup", "状态.json"), 2500)
