import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
d=L(B+"_涨停质量库.json")
print("TOP", list(d.keys()) if isinstance(d,dict) else type(d))
if isinstance(d,dict):
    for k,v in d.items():
        print("--",k, type(v), (len(v) if hasattr(v,'__len__') else ''))
        if isinstance(v,(dict,list)):
            print("   sample:", json.dumps(v if not isinstance(v,list) else v[:2], ensure_ascii=False)[:800])
