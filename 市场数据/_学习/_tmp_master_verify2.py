import json, io, os, re, csv, glob
B = r"D:\股票数据\市场数据\_学习"
D = r"D:\股票数据\市场数据"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

print("=" * 20, "A) 情绪先行指标 20260826 (一进二率18.4%来源)")
cands = glob.glob(os.path.join(B, "*先行指标*"))
print("候选文件:", [os.path.basename(x) for x in cands][:8])
for c in cands[:2]:
    z = L(c)
    if isinstance(z, dict):
        k = "20260826"
        print(os.path.basename(c), "->", json.dumps(z.get(k, z), ensure_ascii=False)[:700])

print()
print("=" * 20, "B) 竞价池分桶库 '高开'口径(T日 or T+1?)")
p = os.path.join(B, "_竞价池分桶库.json")
z = L(p)
s = json.dumps(z, ensure_ascii=False)
print("顶层键:", list(z.keys())[:20] if isinstance(z, dict) else type(z))
for kw in ["口径", "高开", "T1", "T+1", "说明", "窗口"]:
    for m in list(re.finditer(r'"[^"]{0,25}' + kw + r'[^"]{0,25}"\s*:\s*("[^"]{0,220}"|[\d\.\-]+)', s))[:4]:
        print(f"  [{kw}]", m.group(0)[:300])

print()
print("=" * 20, "C) zt_pool 20260826 复核 theme/limitup 封单数字")
zp = glob.glob(os.path.join(D, "20260826", "*zt_pool*"))
print("文件:", [os.path.basename(x) for x in zp])
tgt = {"002084": "海鸥住工", "002418": "康盛股份", "000017": "深中华A", "003040": "楚天龙", "002963": "豪尔赛", "301630": "同宇新材"}
for f in zp:
    if f.endswith(".csv"):
        with io.open(f, encoding="utf-8-sig", newline="") as fh:
            rd = list(csv.DictReader(fh))
        print("csv行数", len(rd), "列", list(rd[0].keys()))
        for r in rd:
            code = (r.get("代码") or r.get("code") or "").zfill(6)
            if code in tgt:
                keep = {k: v for k, v in r.items() if k in ("代码","名称","首封时间","最后封板","开板次数","封板资金","流通市值","连板天数","high_days","换手率","涨跌幅","涨停原因","行业","封单比","首次封板时间")}
                print(" ", json.dumps(keep, ensure_ascii=False)[:400])
        # 封板资金 max
        def num(x):
            try: return float(x)
            except: return None
        fz = [(num(r.get("封板资金")), r.get("名称")) for r in rd if num(r.get("封板资金")) is not None]
        fz.sort(reverse=True)
        print("  封板资金Top5(元或亿?):", fz[:5])
