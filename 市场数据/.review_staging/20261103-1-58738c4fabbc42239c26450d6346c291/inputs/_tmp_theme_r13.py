import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
print("======== theme判断_20261029")
print(json.dumps(L(B+"theme判断_20261029.json"), ensure_ascii=False, indent=1)[:7000])
