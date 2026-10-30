# -*- coding: utf-8 -*-
"""组装 judgment_20261029.json: bodies(7页) + 一句话 + ticker + archive_body"""
import io, json, os

BASE = r"D:\股票数据\市场数据"
L = os.path.join(BASE, "_学习")
D = "20261029"
ROUTES = ["index", "cycle", "auction", "lhb", "theme", "logic", "limitup"]
jp = os.path.join(L, "judgment_%s.json" % D)

j = json.load(io.open(jp, encoding="utf-8"))
bodies = {}
for r in ROUTES:
    p = os.path.join(L, "%s_body_%s.html" % (r, D))
    if not os.path.isfile(p):
        raise SystemExit("MISS body: " + p)
    bodies[r] = io.open(p, encoding="utf-8").read()

j["date"] = D
j["更新label"] = "20261029 复盘"
j["一句话"] = ("温度11.0（昨28.9）极冰点换挡日：C档·防守·总仓2.5%——宽度塌（涨停39，昨71）、跌停潮41家"
            "（其中38家当日首次跌停）、一进二率腰斩至9.5%，但核按钮率0.0%（昨日71只涨停今日无一回杀）说明"
            "跌停潮未伤接力链条；只做席位格601188 1.5%＋结构格600592 1.0%，其余全降观察。")
j["ticker"] = ("温度11.0 · 涨停39 · 跌停41 · 炸板率39.1% · 最高4板001219 · 量能15565亿 · "
               "1进2 9.5% · 2进3 40.0% · 总仓上限2.5%")
j["bodies"] = bodies
if not (j.get("archive_body") or "").strip():
    j["archive_body"] = ("<p>2026-10-29 极冰点换挡日：温度 11.0（昨 28.9）、涨停 39（昨 71）、跌停 41（首日 38）、"
                         "炸板率 39.1%、最高 4 板双峰（001219 一字 / 002708 假一字）、成交 15565 亿、一进二 9.5%。"
                         "总裁决 C 档 · 总仓 2.5%：601188 1.5% + 600592 1.0%，其余观察 0%。</p>")

json.dump(j, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("bodies:", {k: len(v) for k, v in bodies.items()})
print("一句话:", j["一句话"][:80])
print("total bytes:", os.path.getsize(jp))
