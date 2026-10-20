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
s = json.dumps(zs, ensure_ascii=False)
import re
i = s.find("指派清单")
print("### 指派清单 idx", i)
print(s[i-200:i+3000] if i>0 else "NOT FOUND")
print()
print("### 顶层键", list(zs.keys()))

wp = L(os.path.join(B,"_学习/子agent增强/战绩画像_theme_20261020.json"))
print("### 战绩画像 顶层键", list(wp.keys()))
for k,v in wp.items():
    if k!="逐日":
        print("--",k,":", json.dumps(v, ensure_ascii=False)[:1500])
