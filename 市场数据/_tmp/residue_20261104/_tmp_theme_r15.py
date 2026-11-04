import json, os
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
d29=L(B+"题材归位_20261029.json")
print("29 方向聚合", json.dumps(d29.get("方向聚合"), ensure_ascii=False))
print("29 counts", d29.get("counts"), d29.get("档计数"))
# 消费 in 29
for code,v in d29["映射"].items():
    if v["大方向"] in ("消费/食品零售","冰雪经济"):
        print(code, v["名称"], v["大方向"], v.get("环节"), v.get("连板口径"), v.get("首封"), v.get("开板次数"), v.get("来源档"))
print("---- 601188 today?")
d30=L(B+"题材归位_20261030.json")
print([v["名称"] for k,v in d30["映射"].items() if k in ("601188","000530","600576")])
print("---- 模拟盘状态")
p=B+"_模拟盘/theme/状态.json"
print(os.path.exists(p))
if os.path.exists(p):
    print(json.dumps(L(p), ensure_ascii=False, indent=1)[:3000])
