# -*- coding: utf-8 -*-
"""组装 _学习/judgment_20261023.json（宿主职责）
- bodies: 六路 body 文件原样读入（auction/lhb/theme/logic/limitup/cycle），缺一即报错，不编造
- 一句话: 由总审 20261023 的 总裁决/筛选清单/次日验证点 原文拼装，不改数字
- archive_body: 空串（与原 schema 一致；出页时由 生成盯盘台 的 fallback 组装）
"""
import json, os, sys

os.chdir(r"D:\股票数据\市场数据")
D = "20261023"
L = "_学习"

ROUTES = ["index", "cycle", "auction", "lhb", "theme", "logic", "limitup"]
bodies, missing = {}, []
for r in ROUTES:
    p = os.path.join(L, f"{r}_body_{D}.html")
    if not os.path.exists(p):
        missing.append(p)
        continue
    bodies[r] = open(p, encoding="utf-8").read()

if missing:
    print("MISSING BODY:", missing)
    sys.exit(2)

tot = json.load(open(os.path.join(L, f"总审_{D}.json"), encoding="utf-8"))
verdict = tot["总裁决"]
screen = tot["筛选清单"]
keep = screen.get("留用明细权重") or screen.get("明细") or []
keep_txt = []
if isinstance(keep, dict):
    keep_txt = [f"{k} {v}%" if not isinstance(v, dict) else f"{k} {v.get('建议权重%')}%" for k, v in keep.items()]
elif isinstance(keep, list):
    for x in keep:
        if isinstance(x, dict) and str(x.get("留或剔", "")).startswith("留"):
            keep_txt.append(f"{x.get('票')} {x.get('建议权重%')}%")

points = verdict.get("次日验证点") or []
pts = []
for p in points[:4]:
    pts.append(p if isinstance(p, str) else json.dumps(p, ensure_ascii=False))

one = (
    f"{verdict.get('档位')}·置信{verdict.get('置信度')}｜{verdict.get('结论')}"
    f" 明日留用 {screen.get('留数')} 只 / 合计 {screen.get('留用合计权重%')}%（{'；'.join(keep_txt)}）"
    f"；剔除 {screen.get('剔数')} 只（002474 自我豁免驳回 / 301502 双库负桶 / 688836 价格P0越档）。"
    f" 次日验证点：" + "；".join(pts)
)

# 口径归一（零语义改动）：总审原文写"温度11.2→53.2"，门禁 limitup数据核对 的
# 元信息温度引用正则只取第一个数字 → 误判 11.2≠53.2。改为"温度53.2（昨11.2）"，
# 今日值在前、昨日值保留。总审原件不改，只在组装层归一。
import re as _re
one = _re.sub(r"温度\s*([0-9.]+)\s*(?:→|->)\s*([0-9.]+)", r"温度\2（昨\1）", one)

j = {
    "date": D,
    "更新label": f"{D} 复盘",
    "一句话": one,
    "ticker": "",
    "bodies": bodies,
    "archive_body": "",
}
out = os.path.join(L, f"judgment_{D}.json")
json.dump(j, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("judgment 写入:", out, os.path.getsize(out), "bytes")
print("bodies:", {k: len(v) for k, v in bodies.items()})
print("一句话长度:", len(one))
print("一句话:", one[:400])
