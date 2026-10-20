# -*- coding: utf-8 -*-
import sys, io, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r"D:/股票数据/市场数据"
L = B + "/_学习"

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

# 1. radar structure
p = L + "/中报预增雷达_20261020.json"
raw = open(p, 'rb').read()
print("RADAR bytes:", len(raw))
try:
    d = json.loads(raw.decode('utf-8', errors='replace'))
    print("RADAR json OK, keys:")
    for k, v in d.items():
        print("  ", k, type(v).__name__, (len(v) if hasattr(v, '__len__') else ''))
    json.dump(d, open(B + "/_tmp/radar_parsed.json", 'w', encoding='utf-8'), ensure_ascii=False)
except Exception as e:
    print("RADAR parse FAIL:", e)

# 2. risk cal / events
for name in ["风险日历_20261020.json", "风险事件_20261020.json"]:
    try:
        x = load(L + "/" + name)
        print("\n==", name, "keys:", list(x.keys())[:30] if isinstance(x, dict) else type(x))
        s = json.dumps(x, ensure_ascii=False)
        print("  size:", len(s))
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, (list, dict)):
                    print("   ", k, type(v).__name__, len(v))
                else:
                    print("   ", k, "=", str(v)[:120])
    except Exception as e:
        print(name, "FAIL", e)

# 3. 题材归位 keys
try:
    t = load(L + "/题材归位_20261020.json")
    print("\n== 题材归位 keys:", list(t.keys())[:10])
    m = t.get("映射") or t
    print("  映射数:", len(m))
    items = list(m.items())[:3]
    print("  sample:", json.dumps(items, ensure_ascii=False)[:600])
except Exception as e:
    print("题材归位 FAIL", e)

# 4. 涨停对链条
try:
    c = load(L + "/涨停对链条_20261020.json")
    print("\n== 涨停对链条 keys:", list(c.keys())[:20])
    for k, v in c.items():
        if isinstance(v, (list, dict)):
            print("   ", k, type(v).__name__, len(v))
        else:
            print("   ", k, "=", str(v)[:100])
except Exception as e:
    print("涨停对链条 FAIL", e)

# 5. 开盘验证维
try:
    o = load(L + "/开盘验证维_20261020.json")
    print("\n== 开盘验证维:", json.dumps(o, ensure_ascii=False)[:1500])
except Exception as e:
    print("开盘验证维 FAIL", e)
