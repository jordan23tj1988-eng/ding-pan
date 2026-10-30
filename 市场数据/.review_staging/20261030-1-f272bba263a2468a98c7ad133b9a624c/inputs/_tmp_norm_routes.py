# -*- coding: utf-8 -*-
"""规范化五路判断JSON: 顶层荐票/认知迭代/深挖/独立盲区声明齐备 + 档位字母化"""
import json, io, os

BASE = r"D:\股票数据\市场数据"
D = "20261029"


def load(p):
    return json.load(io.open(p, encoding="utf-8"))


def save(p, o):
    json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ---- theme: 判断 内嵌 荐票/认知迭代/深挖 上提为顶层(移动非复制) ----
p = os.path.join(BASE, "_学习", "theme判断_%s.json" % D)
j = load(p)
jd = j["判断"]
moved = {}
for k in ("荐票", "认知迭代", "深挖"):
    if k in jd and k not in j:
        moved[k] = jd.pop(k)
j.update(moved)
# 盲区: 采用本路自报的数据缺口(原文照录, 不新增判断)
if not jd.get("独立盲区声明"):
    jd["独立盲区声明"] = ("本路自报盲区(照录, 未加工): 线名漂移第三天未修——清单按日计数把今日写成"
                        "「算力/电子硬件0、消费0」, 与题材归位实际计数(商业航天/卫星10、消费/食品零售7)不一致; "
                        "一级数据缺口=无竞价额/撤单差/无卡位纯度文件, 「各自为战」目前用环节离散度(0.90)代理, "
                        "属代理指标非直接证据。")
save(p, j)
print("theme normalized:", list(j.keys()), "| moved:", list(moved.keys()))

# ---- lhb: 档位字母化(说明保留在原字段) ----
p = os.path.join(BASE, "_学习", "lhb判断_%s.json" % D)
j = load(p)
t = j["判断"].get("档位", "")
if len(t) > 1:
    j["判断"]["档位说明"] = t
    j["判断"]["档位"] = t[0] if t[0] in "ABC" else "B"
save(p, j)
print("lhb tier:", j["判断"]["档位"], "| note:", j["判断"].get("档位说明", "")[:40])

# ---- 全路 schema 复核 ----
for r in ["auction", "lhb", "theme", "logic", "limitup"]:
    j = load(os.path.join(BASE, "_学习", "%s判断_%s.json" % (r, D)))
    jd = j.get("判断") or {}
    miss = [k for k in ("结论", "证据", "档位", "置信度", "可证伪条件", "独立盲区声明") if k in jd is False or not jd.get(k)]
    miss2 = [k for k in ("荐票", "认知迭代", "深挖") if k not in j]
    print(r, "tier=%s conf=%s" % (jd.get("档位"), jd.get("置信度")), "缺判断项:", miss, "缺顶层:", miss2,
          "荐票数=%d" % len((j.get("荐票") or {}).get("标的") or []))
