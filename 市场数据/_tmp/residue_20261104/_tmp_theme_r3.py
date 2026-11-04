import json, os
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try:
            return json.load(open(p,encoding=enc))
        except Exception as e:
            last=e
    raise last
def P(k, n=6000):
    print("="*20, k)
    print(json.dumps(k, ensure_ascii=False)[:n] if not isinstance(k,str) else k[:n])

# 认知库
c = L(B+"_认知库_theme.json")
print("认知库 keys", list(c.keys()) if isinstance(c,dict) else type(c))
if isinstance(c,dict):
    for kk in list(c.keys())[:15]:
        print(" -",kk, type(c[kk]), (len(c[kk]) if hasattr(c[kk],'__len__') else ''))
print(json.dumps(c, ensure_ascii=False)[:4000])
