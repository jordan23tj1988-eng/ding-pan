import json, io, os
B = r"D:/股票数据/市场数据"
def L(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with io.open(p, encoding=enc) as f: return json.load(f)
        except UnicodeDecodeError: continue
        except Exception as e: return ("ERR", str(e))
    return None

# 1 four-dim today + yesterday
fd = L(os.path.join(B,"_学习/_题材四维.json"))
print("### 四维 keys tail:", [k for k in fd.keys()][-6:])
for k in ("20261017","20261019","20261020"):
    if k in fd:
        print("### 四维", k)
        print(json.dumps(fd[k], ensure_ascii=False, indent=1))

# 2 6you
print("### 6有 20261020")
print(json.dumps(L(os.path.join(B,"_学习/主流题材6有_20261020.json")), ensure_ascii=False, indent=1))

# 3 temp table
t = L(os.path.join(B,"_学习/_市场温度表.json"))
print("### 温度表 type", type(t), (list(t.keys())[:5] if isinstance(t,dict) else len(t)))
if isinstance(t, dict):
    for k in list(t.keys()):
        if k.startswith("202610"): print(k, json.dumps(t[k], ensure_ascii=False))
else:
    for r in t[-8:]: print(json.dumps(r, ensure_ascii=False))
