import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
c = L(B+"_认知库_theme.json")
items = c["条目"]
print("n=", len(items))
for i,it in enumerate(items):
    print(f"[{i}] {it.get('日期')} | {str(it.get('标题'))[:120]}")
