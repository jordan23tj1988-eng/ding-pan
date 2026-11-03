# -*- coding: utf-8 -*-
"""theme 20261103 现场复算：逐线强度体检 + MA-20261102-01 三数同口径重算"""
import json, statistics, re, os
B = r"D:/股票数据/市场数据/_学习"

def load(p):
    with open(os.path.join(B, p), encoding="utf-8") as f:
        return json.load(f)

zt = {}
import csv
with open(r"D:/股票数据/市场数据/20261103/zt_pool.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        zt[r["代码"]] = r

gw = load("题材归位_20261103.json")
mp = gw["映射"]
print("归位条数", len(mp), "大方向数", len(gw["方向聚合"]))
print(json.dumps(gw["方向聚合"], ensure_ascii=False))

# 词典：关键词 -> 主环节（同口径，可复算）
DICT = [
    ("碳纤维", "碳纤维芯/线缆"), ("电线电缆", "碳纤维芯/线缆"), ("电缆", "碳纤维芯/线缆"),
    ("光伏", "光伏边框/铝箔"), ("铝箔", "光伏边框/铝箔"),
    ("固态电池", "固态电池/储能"), ("液冷", "固态电池/储能"), ("储能", "固态电池/储能"),
    ("锂电池", "锂电材料"), ("正极", "锂电材料"), ("磷酸铁锂", "锂电材料"), ("电解液", "锂电材料"),
    ("电池", "电池制造"),
    ("短剧", "短剧族"), ("漫剧", "漫剧"), ("微短剧", "短剧族"),
    ("出版", "出版IP"), ("IP", "出版IP"),
    ("营销", "AI营销"), ("AIGC", "AI营销"),
    ("影视", "影视院线"), ("院线", "影视院线"), ("电影", "影视院线"),
    ("游戏", "游戏"),
    ("白酒", "白酒"), ("乳品", "乳品饮料"), ("饮料", "乳品饮料"), ("乳业", "乳品饮料"),
    ("零售", "商超零售"), ("百货", "商超零售"), ("超市", "商超零售"),
    ("服装", "服装纺织"), ("纺织", "服装纺织"), ("家纺", "服装纺织"),
    ("机器人", "机器人"), ("减速器", "机器人"), ("丝杠", "机器人"),
    ("水泥", "水泥建材"), ("建材", "水泥建材"), ("玻璃", "水泥建材"),
    ("民爆", "民爆/矿"), ("矿", "民爆/矿"), ("铜", "民爆/矿"), ("锂", "民爆/矿"),
    ("医药", "医药"), ("创新药", "医药"), ("医疗器械", "医药"),
    ("卫星", "卫星航天"), ("航天", "卫星航天"), ("商业航天", "卫星航天"),
]

def zhu(env):
    if not env:
        return "未标环节"
    hits = []
    for kw, z in DICT:
        if kw in env and z not in hits:
            hits.append(z)
    return hits[0] if hits else "其他/" + env.split("/")[0]

def stats_20261103():
    lines = {}
    for code, m in mp.items():
        line = m["大方向"]
        r = zt.get(code)
        if not r:
            continue
        lb = int(r["连板数"]); fs = r["首次封板时间"]; zb = int(r["炸板次数"])
        fd = float(r["封板资金"]); lt = float(r["流通市值"]) or 1.0
        d = lines.setdefault(line, {"家数": 0, "板": [], "一字": 0, "早封": 0, "开板": 0,
                                    "封单": 0.0, "封比": [], "换手": [], "环节": [],
                                    "末封": [], "成交": 0.0, "股": []})
        d["家数"] += 1; d["板"].append(lb)
        if fs <= "092500" and zb == 0:
            d["一字"] += 1
        if fs <= "093100":
            d["早封"] += 1
        if zb > 0:
            d["开板"] += 1
        d["封单"] += fd
        d["封比"].append(fd / lt * 100)
        d["换手"].append(float(r["换手率"]))
        d["成交"] += float(r["成交额"])
        d["环节"].append(m.get("环节") or "")
        d["末封"].append(r["最后封板时间"])
        d["股"].append((code, r["名称"], lb, fs, zb, round(fd / 1e8, 2), round(fd / lt * 100, 2)))

    out = []
    for line, d in sorted(lines.items(), key=lambda x: -x[1]["家数"]):
        n = d["家数"]; hs = d["环节"]
        zs = [zhu(e) for e in hs]
        zc = {}
        for z in zs:
            zc[z] = zc.get(z, 0) + 1
        out.append({
            "线": line, "家数": n, "最高板": max(d["板"]), "一字": d["一字"],
            "早封_0931前": d["早封"], "早封占比": round(d["早封"] / n, 2),
            "开板家数": d["开板"], "开板占比": round(d["开板"] / n, 2),
            "封单亿": round(d["封单"] / 1e8, 2),
            "封单比中位%": round(statistics.median(d["封比"]), 2),
            "换手中位%": round(statistics.median(d["换手"]), 2),
            "环节原文数": len(set(hs)), "主环节数": len(zc),
            "主环节离散度": round(len(zc) / n, 2),
            "同主环节≥5只": sum(1 for v in zc.values() if v >= 5),
            "最大主环节聚集": max(zc.values()) if zc else 0,
            "主环节分布": dict(sorted(zc.items(), key=lambda x: -x[1])),
            "成交亿": round(d["成交"] / 1e8, 1),
        })
    return out

def san_shu(date, line):
    g = load(f"题材归位_{date}.json")["映射"]
    hs = [v.get("环节") or "" for k, v in g.items() if v["大方向"] == line]
    zs = [zhu(e) for e in hs]
    zc = {}
    for z in zs:
        zc[z] = zc.get(z, 0) + 1
    return {"线": line, "家数": len(hs), "环节原文数": len(set(hs)),
            "主环节数": len(zc), "主环节离散度": round(len(zc) / len(hs), 2),
            "同主环节≥5只": sum(1 for v in zc.values() if v >= 5),
            "最大聚集": max(zc.values()), "分布": dict(sorted(zc.items(), key=lambda x: -x[1]))}

if __name__ == "__main__":
    st = stats_20261103()
    print("\n== 20261103 逐线强度体检 ==")
    for s in st:
        print(f"{s['线']:<16} 宽{s['家数']:>2} 高{s['最高板']} 一字{s['一字']} 早封{s['早封_0931前']}({s['早封占比']}) "
              f"开板{s['开板占比']} 封{s['封单亿']}亿 封比中{s['封单比中位%']}% 换手中{s['换手中位%']}% "
              f"| 环节原文{s['环节原文数']} 主{s['主环节数']} 离散{s['主环节离散度']} ≥5只{s['同主环节≥5只']}")
    print("\n== 20261102 AI应用/传媒 三数（同词典重算）==")
    print(json.dumps(san_shu("20261102", "AI应用/传媒"), ensure_ascii=False, indent=1))
    print("\n== 20261102 AI应用/软件 + 传媒 合并 ==")
    g = load("题材归位_20261102.json")["映射"]
    hs = [v.get("环节") or "" for v in g.values() if v["大方向"] in ("AI应用/传媒", "AI应用/软件")]
    zs = [zhu(e) for e in hs]
    zc = {}
    for z in zs:
        zc[z] = zc.get(z, 0) + 1
    print("族家数", len(hs), "原文环节", len(set(hs)), "主环节", len(zc),
          "离散", round(len(zc) / len(hs), 2), dict(sorted(zc.items(), key=lambda x: -x[1])))
    json.dump({"逐线": st, "AI传媒_20261102_三数": san_shu("20261102", "AI应用/传媒")},
              open(os.path.join(B, "_tmp_theme_calc_20261103.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
