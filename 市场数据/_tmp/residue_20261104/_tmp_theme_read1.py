import json, os
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try:
            return json.load(open(p,encoding=enc))
        except Exception as e:
            last=e
    raise last

def show(name, d, depth=0, maxlen=900):
    s = json.dumps(d, ensure_ascii=False)
    print(f"### {name}  len={len(s)}")
    print(s[:maxlen])
    print()

# 1 战绩画像
p = B+"子agent增强/战绩画像_theme_20261030.json"
print("EXISTS 战绩画像", os.path.exists(p))
if os.path.exists(p):
    d=L(p); show("战绩画像_theme_20261030", d, maxlen=3000)

# 2 认知库
for cand in [B+"_认知库_theme.json", B+"子agent增强/认知库_theme_20261030.json"]:
    print("EXISTS", cand, os.path.exists(cand))
