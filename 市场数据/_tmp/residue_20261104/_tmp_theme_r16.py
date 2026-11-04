import json, os
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
print("==== 能力预加载 routes.theme")
d=L(B+"能力预加载_20261030.json")
print("TOP", list(d.keys()))
r = d.get("routes",{}).get("theme",{})
print(json.dumps(r, ensure_ascii=False, indent=1)[:3000])
print("==== 待深挖清单_20261030")
print(json.dumps(L(B+"待深挖清单_20261030.json"), ensure_ascii=False, indent=1)[:2500])
print("==== 涨停质量荐票_20261030")
print(json.dumps(L(B+"涨停质量荐票_20261030.json"), ensure_ascii=False, indent=1)[:2500])
