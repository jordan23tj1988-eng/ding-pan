import json, io, os
B = r"D:\股票数据\市场数据\_学习"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

print("=" * 30, "战绩画像汇总_20260826 顶层结构")
h = L(os.path.join(B, "子agent增强", "_战绩画像汇总_20260826.json"))
def walk(o, pre="", depth=0, maxd=2):
    if depth > maxd: return
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, dict):
                print(f"{pre}{k}: dict({len(v)}) keys={list(v.keys())[:12]}")
                walk(v, pre + "  ", depth + 1, maxd)
            elif isinstance(v, list):
                print(f"{pre}{k}: list({len(v)})")
                if v and isinstance(v[0], dict):
                    print(f"{pre}  [0]={json.dumps(v[0], ensure_ascii=False)[:300]}")
            else:
                print(f"{pre}{k}: {str(v)[:150]}")
walk(h)
print()
print("=" * 30, "温度档关键词扫描")
s = json.dumps(h, ensure_ascii=False)
for kw in ["温度档", "偏冷", "冰点", "偏热", "温度"]:
    print(kw, "出现", s.count(kw), "次")
print()
print("=" * 30, "各路合计/归因")
for r in ["auction", "lhb", "theme", "logic", "limitup"]:
    node = h.get(r) or h.get("路") or {}
    print("--", r, json.dumps(h.get(r, {}), ensure_ascii=False)[:1200] if isinstance(h.get(r), (dict, list)) else h.get(r))
