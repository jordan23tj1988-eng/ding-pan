# -*- coding: utf-8 -*-
"""20261019 五路产物核验 + 运行状态落盘(契约: 断点续跑门)"""
import json, os, time
B = r"D:\股票数据\市场数据"
L = os.path.join(B, "_学习")
D = "20261019"
routes = ["auction", "lhb", "theme", "logic", "limitup"]
os.makedirs(os.path.join(L, "_运行状态"), exist_ok=True)
summary = []
for r in routes:
    jp = os.path.join(L, f"{r}判断_{D}.json")
    bp = os.path.join(L, f"{r}_body_{D}.html")
    tp = os.path.join(L, f"交易计划_{r}_{D}.json")
    vp = os.path.join(L, f"周期投票_{r}_{D}.json")
    cp = os.path.join(L, f"能力回执_{r}_{D}.json")
    errs = []
    data = None
    if not os.path.isfile(jp):
        errs.append("判断json缺失")
    else:
        try:
            data = json.load(open(jp, encoding="utf-8"))
        except Exception as e:
            errs.append("json解析失败:%s" % e)
    if data:
        if str(data.get("日期", "")) != D:
            errs.append("日期不符:%s" % data.get("日期"))
        j = data.get("判断") or {}
        for k in ("结论", "证据", "档位", "置信度", "可证伪条件", "独立盲区声明"):
            if k not in j or j.get(k) in (None, ""):
                errs.append("判断缺字段:%s" % k)
        tj = data.get("荐票") or {}
        if "标的" not in tj:
            errs.append("荐票缺标的")
        else:
            for it in tj.get("标的", []):
                if not it.get("代码") or not it.get("名称"):
                    errs.append("标的缺代码/名称")
                if it.get("类型") not in ("荐票", "观察"):
                    errs.append("标的类型非法:%s" % it.get("类型"))
    for tag, p in (("body", bp), ("交易计划", tp), ("周期投票", vp), ("能力回执", cp)):
        if not os.path.isfile(p):
            errs.append("%s缺失" % tag)
    # body div 配平
    if os.path.isfile(bp):
        s = open(bp, encoding="utf-8").read()
        if s.count("<div") != s.count("</div>"):
            errs.append("body div不配平 %d/%d" % (s.count("<div"), s.count("</div>")))
        if s.count("<h2") < 4:
            errs.append("body h2不足(%d)" % s.count("<h2"))
    status = "pass" if not errs else "fail"
    rec = {"route": r, "date": D, "status": status, "attempts": 1,
           "model": "deepseek-flash", "provider": "deepseek",
           "error_class": None if status == "pass" else "schema",
           "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "artifact_paths": [jp, bp, tp, vp, cp], "errors": errs}
    json.dump(rec, open(os.path.join(L, "_运行状态", f"{r}_{D}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    band = ((data or {}).get("判断") or {}).get("档位")
    conf = ((data or {}).get("判断") or {}).get("置信度")
    rec_n = len((((data or {}).get("荐票") or {}).get("标的") or []))
    summary.append(f"{r}: {status} 档={band} 置信={conf} 标的={rec_n} errs={errs}")
print("\n".join(summary))
