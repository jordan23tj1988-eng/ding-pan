# -*- coding: utf-8 -*-
"""14:45 深场B: 主线(行业宽度)/龙头/炸板大面 定性输入"""
import json, csv, statistics

ZT = r"D:\股票数据\市场数据\20261020\zt_pool.csv"
SER = r"D:\股票数据\市场数据\盘中\20261021\_hb_f_series.json"
TICKS = r"D:\股票数据\市场数据\盘中\20261021\realtime_ticks.jsonl"

pool = {}
with open(ZT, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        pool[r["代码"]] = {
            "name": r["名称"], "ind": r["所属行业"], "lb": int(float(r["连板数"])),
            "stat": r["涨停统计"], "seal_amt": float(r["封板资金"] or 0),
            "first": r["首次封板时间"], "zb_cnt": int(float(r["炸板次数"] or 0)),
            "turn": float(r["换手率"] or 0),
        }

ser = json.load(open(SER, encoding="utf-8"))
last = ser["series"]["LAST"]
frames = [json.loads(l) for l in open(TICKS, encoding="utf-8") if l.strip()]
lastfr = frames[-1]
rows = {r["code"]: r for r in lastfr["rows"]}

print("=== 今日封板 16 只 × 昨日身位/行业 ===")
ind_cnt = {}
for code, name, pct in last["seal_list"]:
    p = pool.get(code, {})
    lb = p.get("lb")
    ind = p.get("ind", "?")
    ind_cnt[ind] = ind_cnt.get(ind, 0) + 1
    print(f"{code} {name:6s} 昨{lb}板->今{lb+1 if lb else '?'}板  行业={ind:8s} 昨封单={p.get('seal_amt',0)/1e8:.2f}亿 昨炸{p.get('zb_cnt')}次 昨换手{p.get('turn',0):.1f}%")
print("\n=== 行业宽度(封板数) ===")
for k, v in sorted(ind_cnt.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

print("\n=== 今日 大面/断板(池内 pct 最差 8) ===")
bad = sorted(((r["pct"], c, r["name"]) for c, r in rows.items()))[:8]
for pct, c, name in bad:
    p = pool.get(c, {})
    print(f"  {c} {name:6s} {pct:+7.2f}%  昨{p.get('lb')}板 昨炸{p.get('zb_cnt')}次 昨封单{p.get('seal_amt',0)/1e8:.2f}亿 今低→现 high={rows[c]['high']}")

print("\n=== 高位板(昨≥3板)今日表现 ===")
for c, r in rows.items():
    lb = pool.get(c, {}).get("lb")
    if lb and lb >= 3:
        print(f"  {c} {r['name']:6s} 昨{lb}板 今{r['pct']:+7.2f}% 现{r['latest']} 高{r['high']} 低{r['low']}")

print("\n=== 首板(昨1板)今日晋级率 ===")
first = [c for c in rows if pool.get(c, {}).get("lb") == 1]
sealed = {s[0] for s in last["seal_list"]}
promo = [c for c in first if c in sealed]
print(f"  昨首板 {len(first)} 只 → 今封板 {len(promo)} 只 = 晋级率 {len(promo)/len(first)*100:.1f}%")
print("  晋级:", [(c, rows[c]['name']) for c in promo])
print("  未晋级最差:", [(c, rows[c]['name'], round(rows[c]['pct'],1)) for c in sorted(first, key=lambda c: rows[c]['pct'])[:5]])
