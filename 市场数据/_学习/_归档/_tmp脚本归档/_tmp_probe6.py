import json, os, glob
B = r"D:/股票数据/市场数据"
L = os.path.join(B, "_学习")
for f in sorted(os.listdir(L)):
    if any(k in f for k in ("ths_zt","bars_cache","质量","甜点","盘中","尾盘","开盘验证","日内")):
        p = os.path.join(L,f)
        print(f, os.path.getsize(p) if os.path.isfile(p) else "<dir>")

print("\n=== _ths_zt_pool.json 结构 ===")
p = os.path.join(L,"_ths_zt_pool.json")
if os.path.exists(p):
    d = json.load(open(p, encoding="utf-8"))
    print(type(d))
    if isinstance(d, dict):
        ks = list(d.keys())
        print("n keys", len(ks), ks[:5], ks[-3:])
        k0 = ks[0]
        v = d[k0]
        print("sample", k0, type(v), json.dumps(v, ensure_ascii=False)[:800])
    elif isinstance(d, list):
        print("len", len(d), json.dumps(d[0], ensure_ascii=False)[:600])

print("\n=== bars_cache ===")
bc = os.path.join(L,"_bars_cache")
print(os.path.exists(bc), len(os.listdir(bc)) if os.path.exists(bc) else 0)
fs = sorted(os.listdir(bc))[:3] if os.path.exists(bc) else []
for f in fs:
    print(f, os.path.getsize(os.path.join(bc,f)))
    print(open(os.path.join(bc,f), encoding="utf-8", errors="replace").read()[:400])
