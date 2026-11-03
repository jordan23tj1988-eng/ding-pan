import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
d=L(B+"_涨停质量库.json")
print("窗口", d["窗口"], "样本", d["样本"])
print("基准", json.dumps(d["基准"], ensure_ascii=False))
for k,v in d["分板胜率"].items():
    print("#####", k)
    for kk,vv in v.items():
        print(f"   {kk}: n={vv.get('n')} 执1胜率={vv.get('执1胜率')} 执1均涨={vv.get('执1均涨')} 抓龙率={vv.get('抓龙率')} T1均涨={vv.get('T1均涨')}")
print("##### 因子 keys", list(d["因子"].keys()))
for f in ("封单比","板位x温度","温度","连板 x 环境"):
    if f in d["因子"]:
        print("=====", f, json.dumps(d["因子"][f], ensure_ascii=False)[:2000])
