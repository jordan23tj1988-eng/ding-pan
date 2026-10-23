import json, io, os, re, csv, glob
B = r"D:\股票数据\市场数据\_学习"
D = r"D:\股票数据\市场数据"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

print("=" * 20, "A) 一进二率分母核验")
p = os.path.join(B, "_情绪先行指标.json")
z = L(p)
print("顶层键类型:", list(z.keys())[:8] if isinstance(z, dict) else type(z))
if "20260826" in z:
    for d in ["20260824", "20260825", "20260826"]:
        print(d, json.dumps(z[d].get("晋级"), ensure_ascii=False))
else:
    print("单日文件(无日期键), 内容=", json.dumps(z, ensure_ascii=False)[:400])
    b = L(os.path.join(B, "_情绪先行指标.json.bak_0812"))
    print("bak无0825")
T = L(os.path.join(B, "_市场温度表.json"))
print("温度表0825梯队1(首板)=", T["20260825"]["梯队"]["1"], " 温度表0826梯队2=", T["20260826"]["梯队"]["2"])
print("若分母=49 -> 9/49 =", round(9/49, 4), " 若分母=56 -> 9/56 =", round(9/56, 4), " 10/56 =", round(10/56, 4))

print()
print("=" * 20, "B) 题材线复核(涨停对链条_20260826)")
p = os.path.join(B, "涨停对链条_20260826.json")
if os.path.exists(p):
    c = L(p)
    print("类型", type(c).__name__, "顶层键", list(c.keys())[:12] if isinstance(c, dict) else len(c))
    lines = c.get("题材线") or c.get("lines") or c
    if isinstance(lines, dict):
        w = sorted(((k, len(v) if isinstance(v, list) else v) for k, v in lines.items()), key=lambda x: -(x[1] if isinstance(x[1], int) else 0))
        print("线数", len(lines), "最宽Top8", w[:8])
    elif isinstance(lines, list):
        print("列表长度", len(lines), "样例", json.dumps(lines[0], ensure_ascii=False)[:300])
else:
    print("候选:", [os.path.basename(x) for x in glob.glob(os.path.join(B, "*链条*20260826*"))])

print()
print("=" * 20, "C) logic复核 模板153/A池186")
for pat in ["*中报预增雷达_20260826*", "*产业链*模板*", "*纵深*"]:
    print(pat, "->", [os.path.basename(x) for x in glob.glob(os.path.join(B, pat))][:6])
p = os.path.join(B, "中报预增雷达_20260826.json")
if os.path.exists(p):
    z = L(p)
    print("雷达顶层键", list(z.keys())[:12] if isinstance(z, dict) else len(z))
    for k in list(z.keys())[:6] if isinstance(z, dict) else []:
        v = z[k]
        if isinstance(v, list):
            print(f"  {k}: list({len(v)})")
        elif isinstance(v, dict):
            print(f"  {k}: dict({len(v)})")
        else:
            print(f"  {k}: {str(v)[:120]}")
