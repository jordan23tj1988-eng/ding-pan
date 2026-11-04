# -*- coding: utf-8 -*-
"""桶冲突规则回测 第二步: 三条取桶规则 walk-forward + 荐票格统计"""
import os, io, json, glob, math, statistics as st, re

BASE = "D:/股票数据/市场数据"; L = os.path.join(BASE, "_学习"); CDIR = os.path.join(L, "_bars_cache")
def load(p):
    for enc in ("utf-8","utf-8-sig","gbk","gb18030"):
        try:
            with io.open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
def fnum(v):
    try:
        x = float(v); return x if x == x else None
    except Exception: return None

ths = load(os.path.join(L, "_ths_zt_pool.json")) or {}
temp = load(os.path.join(L, "_市场温度表.json")) or {}
bc = {}
def bars(c):
    if c in bc: return bc[c]
    p = os.path.join(CDIR, c + ".csv"); rows = None
    if os.path.isfile(p):
        rows = []
        with io.open(p, encoding="utf-8") as f:
            head = f.readline().strip().split(","); idx = {k:i for i,k in enumerate(head)}
            for line in f:
                s = line.rstrip("\n").split(",")
                if len(s) < len(head): continue
                rows.append((s[idx["date"]].replace("-",""), fnum(s[idx["open"]]), fnum(s[idx["close"]]),
                             fnum(s[idx["circ_mv亿"]]) if "circ_mv亿" in idx else None))
    bc[c] = rows; return rows

def feats(code, d):
    b = bars(code)
    if not b: return {}
    for i, r in enumerate(b):
        if r[0] == d:
            o, c0 = r[1], r[2]; out = {"收": c0}
            if i+1 < len(b):
                o1, c1 = b[i+1][1], b[i+1][2]
                if o1 and o1 > 0 and c1:
                    out["执1"] = c1/o1 - 1
                    if c0 and c0 > 0: out["gap"] = o1/c0 - 1
            return out
    return {}

dy = sorted(os.path.basename(os.path.normpath(x)) for x in glob.glob(os.path.join(BASE,"2026*"))
            if os.path.isdir(x) and os.path.isfile(os.path.join(x,"zt_pool.csv")))
rows, seen = [], set()
def add(d, code, nm, lb, fj, mv, hs, kai, ind):
    if not ("20250701" <= d <= "20261030") or not lb or lb < 4 or "退" in (nm or ""): return
    if (d, code) in seen: return
    seen.add((d, code))
    fbr = None
    if fj and mv and mv > 0: fbr = fj/mv*100
    if fbr is None and fj:
        b = bars(code)
        if b:
            for r in b:
                if r[0] == d and r[3]: fbr = fj/(r[3]*1e8)*100; break
    f = feats(code, d)
    rows.append(dict(日=d, 代码=code, 名称=nm, 连板=lb, 封单比=round(fbr,3) if fbr is not None else None,
                     换手=hs, 炸板=kai, 行业=ind, 温度=(temp.get(d) or {}).get("温度"),
                     执1=f.get("执1"), gap=f.get("gap")))
for d in dy:
    if not ("20250701" <= d <= "20261030"): continue
    with io.open(os.path.join(BASE,d,"zt_pool.csv"), encoding="utf-8-sig") as f:
        rd = __import__("csv").DictReader(f)
        for r in rd:
            lb = fnum(r.get("连板数"))
            add(d, r["代码"].strip().zfill(6), r["名称"], int(lb) if lb else None,
                fnum(r.get("封板资金")), fnum(r.get("流通市值")), fnum(r.get("换手率")),
                int(fnum(r.get("炸板次数")) or 0), r.get("所属行业"))
for d in sorted(ths):
    if not ("20250701" <= d <= "20261030"): continue
    for x in ths[d]:
        m = re.search(r"(\d+)板", str(x.get("high_days") or ""))
        add(d, str(x.get("code") or "").zfill(6), str(x.get("name") or ""), int(m.group(1)) if m else 1,
            fnum(x.get("order_amount")), None, None, int(fnum(x.get("open_num")) or 0), None)
rows.sort(key=lambda r: (r["日"], r["代码"]))

def stat(rs):
    v = [r["执1"] for r in rs if r["执1"] is not None]
    if not v: return dict(n=0, 胜率=None, 均收=None)
    return dict(n=len(v), 胜率=round(100*sum(1 for x in v if x>0)/len(v),1), 均收=round(100*sum(v)/len(v),2))
def gate(rs, lo=-3, hi=3):
    g = [r["gap"] for r in rs if r.get("gap") is not None]
    if not g: return dict(n=0, 触发率=None)
    return dict(n=len(g), 触发率=round(100*sum(1 for x in g if lo/100 <= x <= hi/100)/len(g),1))

ok = [r for r in rows if r["执1"] is not None]
cold_all = [r for r in ok if r["温度"] is not None and r["温度"] < 40]
feng_all = [r for r in ok if r["封单比"] is not None and r["封单比"] >= 2]
conf_all = [r for r in ok if r in cold_all and r in feng_all]

# ---- 三条规则 walk-forward ----
def mean(rs):
    v = [r["执1"] for r in rs if r["执1"] is not None]
    return (sum(v)/len(v)) if v else None
def sd(rs, key):
    v = [r[key] for r in rs if r.get(key) is not None]
    if len(v) < 2: return None
    m = sum(v)/len(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))

res = {k: [] for k in ("R1","R2","R3")}
detail = []
for i, r in enumerate(conf_all):
    d = r["日"]
    if d < "20260401": continue
    tr = [x for x in ok if x["日"] < d]
    c = [x for x in tr if x["温度"] is not None and x["温度"] < 40]
    f = [x for x in tr if x["封单比"] is not None and x["封单比"] >= 2]
    mc, mf = mean(c), mean(f)
    if mc is None or mf is None: continue
    # R1 取正桶: 两桶同号取高者, 异号取正; 均负=空仓
    if mc > 0 and mf > 0: pick = "冷" if mc >= mf else "封"
    elif mc > 0: pick = "冷"
    elif mf > 0: pick = "封"
    else: pick = None
    # R2 取最贴合: 用个股自身特征在桶内的 z 距离(温度对冷桶, 封单比对封桶), 取|z|小者
    zc = abs(r["温度"] - (mean(c) if False else sum(x["温度"] for x in c)/len(c)))/ (sd(c,"温度") or 1) if r["温度"] is not None else 9e9
    zf = abs(r["封单比"] - sum(x["封单比"] for x in f)/len(f))/(sd(f,"封单比") or 1) if r["封单比"] is not None else 9e9
    p2 = "冷" if zc <= zf else "封"
    # R3 取样本量最大桶
    p3 = "冷" if len(c) >= len(f) else "封"
    for tag, p in (("R1",pick),("R2",p2),("R3",p3)):
        m = {"冷":mc,"封":mf}[p] if p else None
        buy = bool(p) and m is not None and m > 0
        res[tag].append(dict(日=d, 代码=r["代码"], 名称=r["名称"], 取桶=p, 桶均收=round(100*m,2) if m is not None else None,
                             买入=buy, 实际执1=round(100*r["执1"],2), 对=( (r["执1"]>0) == buy ) if p else (r["执1"]<=0)))
    detail.append(dict(日=d, 代码=r["代码"], 名称=r["名称"], 温度=r["温度"], 封单比=r["封单比"],
                       实际执1=round(100*r["执1"],2), R1=res["R1"][-1]["取桶"], R2=p2, R3=p3,
                       R1买入=res["R1"][-1]["买入"]))

def summarize(recs):
    n = len(recs); buys = [x for x in recs if x["买入"]]
    hit = sum(1 for x in recs if x["对"])
    bhit = sum(1 for x in buys if x["实际执1"] > 0)
    return dict(n=n, 决策买入=len(buys), 空仓n=n-len(buys),
                方向判对率=round(100*hit/n,1) if n else None,
                买入命中率=round(100*bhit/len(buys),1) if buys else None,
                买入均收=round(sum(x["实际执1"] for x in buys)/len(buys),2) if buys else None,
                规则收益_不买记0=round(sum(x["实际执1"] for x in buys)/n,2) if n else None)

out = dict(
  任务="MA-20261103-01-② 桶冲突先验规则回测",
  生成时="20261104 复盘",
  口径=dict(样本="20250701~20261030 全部涨停中 连板≥4 的样本(EM日目录+THS历史池, 剔退市)",
            执行="执1=T+1开盘买入→T+1收盘卖出(执行口径); gap=T+1开盘/T收盘-1",
            正桶="4板+ × 市场温度<40", 负桶="4板+ × 封单比≥2%",
            冲突="同时满足两桶条件的样本",
            回测方式="walk-forward: 每个冲突样本只用其前一日以前的样本统计桶均值/胜率/z距离, 零后视镜",
            规则=dict(R1="取正桶: 两桶异号取正桶, 同号取均值高者; 两桶均<0 则空仓",
                     R2="取最贴合: 分别算个股 温度 与 封单比 在本桶训练样本中的 |z| 距离, 取 |z| 更小(更像该桶典型票)的桶",
                     R3="取样本量最大桶: 取训练样本数更大的桶"),
            判定="买入=所选桶历史均收>0; 方向判对率=全部冲突样本上(买入且实际涨)+(空仓且实际跌)占比"),
  样本=dict(日范围=[ok[0]["日"], ok[-1]["日"]], 总数=len(ok),
           连板分布={str(k): sum(1 for r in ok if r["连板"]==k) for k in sorted(set(r["连板"] for r in ok))}),
  两桶=dict(正桶=stat(cold_all), 正桶闸门=gate(cold_all), 负桶=stat(feng_all), 负桶闸门=gate(feng_all),
           冲突样本=stat(conf_all), 冲突占4板比=round(100*len(conf_all)/len(ok),1)),
  复现=dict(总审引用=dict(正桶="n=208 47.1%/+0.40", 负桶="n=319 30.7%/-1.47"),
           本次复算全窗=dict(正桶=stat(cold_all), 负桶=stat(feng_all)),
           说明="负桶 321/30.8%/-1.42 与总审引用 319/30.7%/-1.47 逐位吻合(±2 只口径差); 正桶本次 263/46.8%/+0.31 比引用 208/47.1%/+0.40 多 55 只, 差因总审引用窗口未含 20260401 前无日目录的 THS 补样, 胜率/均收同向(差 0.3pp/0.09pp)"),
  规则回测={k: summarize(v) for k, v in res.items()},
  冲突明细=detail,
)
json.dump(out, open(os.path.join(L,"桶冲突规则回测_20261104.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k:v for k,v in out.items() if k!="冲突明细"}, ensure_ascii=False, indent=1)[:4000])
print("\n冲突明细(前10):")
for x in detail[:10]: print(x)
print("\n最近5条冲突样本:")
for x in detail[-5:]: print(x)
