import json, io, os
B = r"D:/股票数据/市场数据"
def L(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with io.open(p, encoding=enc) as f: return json.load(f)
        except UnicodeDecodeError: continue
        except Exception as e: return ("ERR", str(e))
    return None
zs = L(os.path.join(B,"_学习/总审_20261019.json"))
il = zs["指派清单"]
print(type(il), len(il) if isinstance(il,(list,dict)) else "")
if isinstance(il, dict):
    for k,v in il.items(): print("==",k, json.dumps(v, ensure_ascii=False, indent=1))
else:
    for e in il:
        print("==", json.dumps(e, ensure_ascii=False, indent=1))
print("### 页面合同 theme相关:")
pc = zs.get("页面合同")
print(json.dumps(pc, ensure_ascii=False)[:1200])
