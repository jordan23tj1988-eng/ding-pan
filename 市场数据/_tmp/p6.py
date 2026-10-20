# -*- coding: utf-8 -*-
import sys, io, json, re, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r"D:/股票数据/市场数据"; L = B + "/_学习"
rad = json.load(open(B + "/_tmp/radar_parsed.json", encoding='utf-8'))
zt = list(csv.DictReader(open(B + "/20261020/zt_pool.csv", encoding='utf-8-sig')))
ztmap = {r["代码"]: r for r in zt}

def collect(key):
    return {x["代码"]: x for x in rad[key]}
poolA = collect("A共振池(重要度排序)")
poolC = collect("概念叠加候选")
poolP = collect("纯预增未叠加")
poolF = collect("已发酵对照Top12")
poolE = collect("预期已兑现(年内已翻倍,不入候选)")
poolI = collect("刚点火(有涨停未透支)")
allc = {}
for p in (poolC, poolP, poolF, poolE):
    allc.update(p)

print("中报池(候选类)代码数:", len(allc), "| A池:", len(poolA))
# intersect with zt
def inter(pool):
    return [(c, pool[c], ztmap[c]) for c in pool if c in ztmap]

print("\n== 中报池 ∩ 今日涨停 ==")
for c, r, z in inter(allc):
    print(f"  {c} {r['名称']} 涨停{z['连板数']}板 类型={r['预告类型']} 幅度={r['变动幅度%']} 成色={r.get('成色','-')} 主类={r.get('主类','-')} 公告={r.get('公告日期')}")
print("  n=", len(inter(allc)))

print("\n== A共振池 ∩ 今日涨停 ==")
a = inter(poolA)
for c, r, z in a:
    print(f"  {c} {r['名称']} {z['连板数']}板 重要度{r['重要度分']} 成色依据={r['成色依据']} 叠加={r['叠加线']}")
print("  n=", len(a))

# template codes
tpl = json.load(open(B + "/产业链模板.json", encoding='utf-8'))
tplmap = {}
for plate, v in tpl.items():
    if not isinstance(v, dict) or "环节" not in v: continue
    for step, arr in v["环节"].items():
        for it in arr:
            tplmap[it[0]] = (plate, step, it[1])
print("\n模板代码数:", len(tplmap))
t_inter = [(c, tplmap[c], ztmap[c]) for c in tplmap if c in ztmap]
print("== 模板 ∩ 今日涨停 ==")
for c, t, z in t_inter:
    print(f"  {c} {t[2]} {t[0]}/{t[1]} {z['连板数']}板 封板{z['封板资金']} 首封{z['首次封板时间']} 炸{z['炸板次数']} 换手{z['换手率']}")
print("  n=", len(t_inter))

# 三交叉 template ∩ radar ∩ zt
print("\n== 三交叉(中报池∩模板∩涨停) ==")
tri = [c for c in allc if c in tplmap and c in ztmap]
for c in tri:
    print("  ", c, allc[c]["名称"], tplmap[c], "成色", allc[c].get("成色"))
print("  n=", len(tri))
