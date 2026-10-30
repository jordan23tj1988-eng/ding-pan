#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""题材线宽·族口径（线名漂移机械修法）
背景：题材归位的大方向线名会随催化改写而漂移（消费/食品零售→消费/大消费→消费/白酒），
      机械脚本 题材生命周期.py 按线名字面取序列，线名一改就断点，宽度环比=NULL、
      阶段判定退化为取高度（假象）。本脚本给出唯一机械修法：
      1) 线宽一律读 题材归位_{d}.json#方向聚合（唯一真源），禁用 待深挖清单/清单按日计数；
      2) 漂移用「族映射」合并后算环比：族=业务同一条主线的线名集合；
      3) 输出 原始线宽(方向聚合原样) + 族宽 + 族宽环比，供 题材生命周期/6有 对照。

用法：
  python 题材线族.py 20261030            # 打印当日族口径线宽
  python 题材线族.py --backfill 20261028 20261029 20261030   # 回填多日并落盘

产出：_学习/题材线宽_{d}.json
"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
XL = os.path.join(BASE, "_学习")

# 族映射：只在业务上确属同一主线时才合并；未列出的线名自成族（族名=线名）
FAMILY = {
    "消费": "消费系", "消费/食品零售": "消费系", "消费/大消费": "消费系",
    "消费/白酒": "消费系", "消费/食品": "消费系", "消费/零售": "消费系",
    "消费/家居": "消费系", "消费/乳业食品": "消费系", "消费/造纸": "消费系",
    "医药": "医药医疗", "医药医疗": "医药医疗", "医药生物": "医药医疗",
    "医药/创新药": "医药医疗", "创新药": "医药医疗",
    "算力/电子硬件": "算力", "算力/科技硬件": "算力", "AI算力/PCB": "算力",
    "光通信/算力": "算力", "算力/AI硬件": "算力", "AI算力": "算力",
    "商业航天": "商业航天/卫星", "商业航天/卫星": "商业航天/卫星",
    "机器人": "机器人/具身智能", "机器人/具身智能": "机器人/具身智能",
    "AI应用": "AI应用/传媒", "AI应用/传媒": "AI应用/传媒",
    "军工/航天": "军工/航天", "军工": "军工/航天",
}

PREFIX_RULE = [
    # (前缀, 族名)  —— 兜底：族映射未覆盖时按前缀并线，防新线名再次漂移成断点
    ("消费", "消费系"),
    ("医药", "医药医疗"),
    ("机器人", "机器人/具身智能"),
    ("AI应用", "AI应用/传媒"),
    ("商业航天", "商业航天/卫星"),
]


def family_of(line):
    if line in FAMILY:
        return FAMILY[line]
    for pre, fam in PREFIX_RULE:
        if line.startswith(pre):
            return fam
    return line


def load_agg(d):
    p = os.path.join(XL, "题材归位_%s.json" % d)
    if not os.path.isfile(p):
        return None
    j = json.load(open(p, encoding="utf-8"))
    ag = j.get("方向聚合")
    if not ag:  # 降级：从映射现算
        ag = {}
        for v in (j.get("映射") or {}).values():
            ag[v["大方向"]] = ag.get(v["大方向"], 0) + 1
    return ag


def prev_trading_day(d):
    import glob
    ds = sorted(os.path.basename(x).replace("题材归位_", "").replace(".json", "")
                for x in glob.glob(os.path.join(XL, "题材归位_*.json")))
    ds = [x for x in ds if x.isdigit() and x < d]
    return ds[-1] if ds else None


def build(d):
    ag = load_agg(d)
    if ag is None:
        return {"日期": d, "状态": "缺题材归位,不可算"}
    fam = {}
    for line, w in ag.items():
        f = family_of(line)
        fam.setdefault(f, {"宽度": 0, "线名": []})
        fam[f]["宽度"] += w
        fam[f]["线名"].append("%s=%d" % (line, w))
    p = prev_trading_day(d)
    agp = load_agg(p) if p else None
    famp = {}
    if agp:
        for line, w in agp.items():
            f = family_of(line)
            famp[f] = famp.get(f, 0) + w
    out = {"日期": d, "口径": "线宽=题材归位#方向聚合;族宽=族映射合并后;环比=族宽/昨日族宽-1(族名对齐,消除线名漂移)",
           "原始线宽": ag, "对比日": p, "族": {}, "族宽合计": sum(v["宽度"] for v in fam.values())}
    for f, v in sorted(fam.items(), key=lambda x: -x[1]["宽度"]):
        pw = famp.get(f)
        mom = round(v["宽度"] / pw - 1, 3) if pw else None
        out["族"][f] = {"宽度": v["宽度"], "昨日宽度": pw, "族宽环比": mom, "归并线名": v["线名"]}
    return out


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    ds = [a for a in args if a.isdigit()]
    if "--backfill" in args:
        for d in ds:
            o = build(d)
            p = os.path.join(XL, "题材线宽_%s.json" % d)
            json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("写入", p)
    for d in ds:
        o = build(d)
        print("=" * 60)
        print(d, "族宽合计", o.get("族宽合计"), "对比日", o.get("对比日"))
        for f, v in o.get("族", {}).items():
            mom = v["族宽环比"]
            print("  %-16s 宽%3d 昨%3s 环比%8s  [%s]" % (
                f, v["宽度"], v["昨日宽度"],
                ("%+.1f%%" % (mom * 100)) if mom is not None else "—",
                " ".join(v["归并线名"])))


if __name__ == "__main__":
    main()
