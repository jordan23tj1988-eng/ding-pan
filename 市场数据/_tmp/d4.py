import json, io, os
B = r"D:/股票数据/市场数据"
def L(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with io.open(p, encoding=enc) as f: return json.load(f)
        except UnicodeDecodeError: continue
        except Exception as e: return ("ERR", str(e))
    return None

re20 = L(os.path.join(B,"_学习/风险事件_20261020.json"))
print("### 风险事件 keys", list(re20.keys()) if isinstance(re20,dict) else type(re20))
print(json.dumps({k:(v if not isinstance(v,list) else f"list[{len(v)}]") for k,v in re20.items()}, ensure_ascii=False, indent=1)[:3000])
# find any event mentioning our codes
codes = {"003029","603197","603278","600178","605488","002164","600860","002724","600148","002835"}
s = json.dumps(re20, ensure_ascii=False)
import re
for c in sorted(codes):
    idxs = [m.start() for m in re.finditer(c, s)]
    print(c, "hits:", len(idxs))
    for i in idxs[:6]:
        print("   ...", s[max(0,i-260):i+260].replace("\n"," "))
