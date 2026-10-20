import json, io, os, csv
B = r"D:/股票数据/市场数据"
def L(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with io.open(p, encoding=enc) as f: return json.load(f)
        except UnicodeDecodeError: continue
        except Exception as e: return ("ERR", str(e))
    return None

# zt_pool
print("### zt_pool 20261020")
with io.open(os.path.join(B,"20261020/zt_pool.csv"), encoding="utf-8-sig") as f:
    r = list(csv.DictReader(f))
print("cols:", list(r[0].keys()), "n=", len(r))
for row in r:
    print("|".join(str(row.get(k,"")) for k in r[0].keys()))
