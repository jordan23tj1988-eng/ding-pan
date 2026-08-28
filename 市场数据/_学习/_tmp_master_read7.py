import json, io, os, re
B = r"D:\股票数据\市场数据\_学习"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

T = L(os.path.join(B, "_市场温度表.json"))
print("--- 温度表 20260826 记录 ---")
print(json.dumps(T["20260826"], ensure_ascii=False)[:900])
print()
print("--- 温度表 20260825 记录 ---")
print(json.dumps(T["20260825"], ensure_ascii=False)[:900])
print()
# 档定义扫描
dl = set()
for d, v in T.items():
    if isinstance(v, dict):
        for k in v:
            if "档" in k or "温度" in k or "一进二" in k:
                dl.add(k)
print("含'档/温度/一进二'的字段:", sorted(dl))
