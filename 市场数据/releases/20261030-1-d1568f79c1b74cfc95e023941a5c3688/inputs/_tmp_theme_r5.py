import json, os
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
for f in ["题材归位_20261030.json","主流题材6有_20261030.json","_题材四维.json","fact_20261030.json",
          "涨停对链条_20261030.json","日内轮动图谱_20261030.json","待深挖清单_20261030.json",
          "能力预加载_20261030.json","横切面扫描_20261030.json"]:
    p=B+f
    print(f"{f}: exists={os.path.exists(p)} size={os.path.getsize(p) if os.path.exists(p) else 0}")
