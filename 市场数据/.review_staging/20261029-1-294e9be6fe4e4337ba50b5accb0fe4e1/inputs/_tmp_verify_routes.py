# -*- coding: utf-8 -*-
"""核验五路产物 schema/日期 + 写运行状态"""
import json, os, io

BASE = r"D:\股票数据\市场数据"
D = "20261029"
routes = ["auction", "lhb", "theme", "logic", "limitup"]
ok = True
res = {}
for r in routes:
    p = os.path.join(BASE, "_学习", "%s判断_%s.json" % (r, D))
    b = os.path.join(BASE, "_学习", "%s_body_%s.html" % (r, D))
    pl = os.path.join(BASE, "_学习", "交易计划_%s_%s.json" % (r, D))
    rc = os.path.join(BASE, "_学习", "_能力回执片段_%s_%s.json" % (r, D))
    info = {}
    try:
        j = json.load(io.open(p, encoding="utf-8"))
        info["date"] = j.get("日期")
        info["route"] = j.get("路")
        jd = j.get("判断") or {}
        info["tier"] = jd.get("档位")
        info["conf"] = jd.get("置信度")
        picks = ((j.get("荐票") or {}).get("标的") or [])
        info["picks"] = len(picks)
        info["types"] = [x.get("类型") for x in picks]
        info["has_falsify"] = bool(jd.get("可证伪条件"))
        info["has_blind"] = bool(jd.get("独立盲区声明"))
        info["cog"] = len(j.get("认知迭代") or [])
        info["deep"] = len(j.get("深挖") or [])
        info["json_ok"] = True
    except Exception as e:
        info["json_ok"] = False
        info["err"] = repr(e)
        ok = False
    info["body"] = os.path.getsize(b) if os.path.isfile(b) else 0
    if not info["body"]:
        ok = False
    try:
        t = json.load(io.open(pl, encoding="utf-8"))
        info["buys"] = len(t.get("buys") or [])
        info["sells"] = len(t.get("sells") or [])
    except Exception as e:
        info["buys"] = info["sells"] = None
        info["plan_err"] = repr(e)
    info["receipt"] = os.path.isfile(rc)
    res[r] = info

    st = {"route": r, "date": D,
          "status": "pass" if info.get("json_ok") and info.get("body") else "fail",
          "attempts": 1, "model": "deepseek-flash", "provider": "deepseek",
          "error_class": None,
          "updated_at": "2026-10-29T19:40:00+08:00",
          "artifact_paths": [p, b, pl, rc]}
    json.dump(st, open(os.path.join(BASE, "_学习", "_运行状态", "%s_%s.json" % (r, D)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

print(json.dumps(res, ensure_ascii=False, indent=1))
print("ALL_OK", ok)
