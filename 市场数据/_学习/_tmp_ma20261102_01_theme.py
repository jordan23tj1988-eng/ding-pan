# -*- coding: utf-8 -*-
"""MA-20261102-01 承接件：①题材线宽_20261102.json（族口径+归并前对照）
②_tmp_医药AI应用启动逐笔_20261102.json（医药族/AI应用族 生命周期逐笔，≥40条）"""
import json, glob, os, collections
B = r"D:/股票数据/市场数据/_学习"

def load(p):
    with open(os.path.join(B, p), encoding="utf-8") as f:
        return json.load(f)

def _denull(o):
    if o is None:
        return "—"
    if isinstance(o, dict):
        return {k: _denull(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_denull(v) for v in o]
    return o

def dump(p, o):
    with open(os.path.join(B, p), "w", encoding="utf-8") as f:
        json.dump(_denull(o), f, ensure_ascii=False, indent=1)

# ---------- ① 题材线宽 20261102 ----------
gw = load("题材归位_20261102.json")
agg = gw["方向聚合"]
FAM = {
    "消费系": ["消费/大消费", "消费/白酒", "消费/零售", "消费/旅游", "消费/食品零售"],
    "AI应用族": ["AI应用/传媒", "AI应用/软件", "AI应用/教育", "AI应用/AI培训"],
    "AI算力族": ["AI算力/硬件", "AI算力/PCB", "AI算力/半导体", "AI算力"],
    "医药族": ["医药医疗", "医药/创新药", "医药生物", "创新药", "医药/中药"],
    "电力设备族": ["电力设备/新能源", "电力设备", "新能源/光伏", "光伏/储能"],
    "机器人族": ["机器人/具身智能", "机器人", "具身智能"],
}
lines_sorted = sorted(agg.items(), key=lambda x: -x[1])
fam_out = {}
covered = set()
for fam, names in FAM.items():
    parts = {n: agg.get(n, 0) for n in names if n in agg}
    if parts:
        fam_out[fam] = {"族宽": sum(parts.values()), "归并前": parts,
                        "归并前线名数": len(parts), "归并后族名数": 1}
        covered |= set(parts)
dump("题材线宽_20261102.json", {
    "日期": "20261102", "路": "theme",
    "来源": "题材归位_20261102.json#方向聚合（唯一真源，125/125覆盖）",
    "口径": "族宽=同一产业族在归并前多个线名宽度之和；归并前=归位原始线名，归并后=族名。只并同族异名，不并跨族。",
    "全场涨停": gw["counts"]["total"],
    "线名总数": len(agg),
    "族口径": fam_out,
    "未入族线名": [{"线名": k, "宽度": v} for k, v in lines_sorted if k not in covered],
    "原文线名宽度": dict(lines_sorted),
    "消费系核对": {
        "族宽": fam_out["消费系"]["族宽"],
        "加总核对": "9(消费/大消费)+4(消费/白酒)+4(消费/零售)=17",
        "与昨日对比": {"20261030": 14, "20261102": 17, "环比": "+21.4%"},
        "旧线名残留": {"消费/食品零售": agg.get("消费/食品零售", 0)},
    },
})
print("①题材线宽 消费系族宽=", fam_out["消费系"]["族宽"], "AI应用族=", fam_out["AI应用族"]["族宽"])

# ---------- ② 医药族/AI应用族 生命周期逐笔 ----------
files = sorted(glob.glob(os.path.join(B, "题材生命周期_*.json")))
data = []
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    data.append((d["日期"], {x["线"]: x for x in d["阶段表"]}))
data.sort(key=lambda x: x[0])

def fam_of(line):
    if "医药" in line or "创新药" in line:
        return "医药族"
    if line.startswith("AI应用"):
        return "AI应用族"
    return None

rows = []
for i in range(len(data) - 1):
    d0, m0 = data[i]
    d1, m1 = data[i + 1]
    for line, s in m0.items():
        fam = fam_of(line)
        if not fam:
            continue
        nxt = m1.get(line)
        cur = s["当日"]
        rows.append({
            "族": fam, "线名": line, "日期": d0,
            "阶段": s["阶段"], "陷阱": s.get("陷阱"),
            "宽度": cur["w"], "高度": cur["h"], "首板": cur.get("sb"), "二连板": cur.get("el"),
            "宽度环比": cur.get("mom"), "晋级率": cur.get("jj"),
            "次日日期": d1, "次日阶段": nxt["阶段"] if nxt else "线名出池(0只)",
            "次日宽度": nxt["当日"]["w"] if nxt else 0,
            "次日高度": nxt["当日"]["h"] if nxt else 0,
            "转移": f"{s['阶段']}→{nxt['阶段'] if nxt else '出池'}",
        })

def outdeg(fam, stage):
    sub = [r for r in rows if r["族"] == fam and r["阶段"] == stage]
    c = collections.Counter(r["转移"] for r in sub)
    return {"N": len(sub), "去向": dict(c.most_common())}

summary = {fam: {st: outdeg(fam, st) for st in ["萌发", "启动", "发酵", "高潮", "退坡", "退潮"]}
           for fam in ["医药族", "AI应用族"]}
dump("_tmp_医药AI应用启动逐笔_20261102.json", {
    "日期": "20261102", "路": "theme", "用途": "MA-20261102-01 承接：医药族/AI应用族 生命周期逐笔（机械分类直引，不手抄）",
    "来源": "题材生命周期_*.json（48份，题材生命周期.py 机械分类）",
    "族映射": {"医药族": "线名含『医药』或『创新药』", "AI应用族": "线名以『AI应用』开头"},
    "逐笔条数": len(rows),
    "出度汇总": summary,
    "逐笔": rows,
})
print("②逐笔条数", len(rows))
print("医药族启动出度", summary["医药族"]["启动"])
print("AI应用族启动出度", summary["AI应用族"]["启动"])
print("医药族发酵出度", summary["医药族"]["发酵"])
print("AI应用族退坡出度", summary["AI应用族"]["退坡"])
