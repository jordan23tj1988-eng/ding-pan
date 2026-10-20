# -*- coding: utf-8 -*-
"""第9步：把五路 body HTML 注入 judgment_20261020.json bodies。"""
import json, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = os.path.join(BASE, "_学习")
D = "20261020"
jp = os.path.join(L, "judgment_%s.json" % D)
j = json.load(open(jp, encoding="utf-8"))
bodies = j.get("bodies") or {}
rep = {}
for r in ("auction", "lhb", "theme", "logic", "limitup"):
    p = os.path.join(L, "%s_body_%s.html" % (r, D))
    s = open(p, encoding="utf-8").read()
    assert s.count("<div") == s.count("</div>"), (r, "div imbalance")
    assert s.count("<script") == 0 and s.count("<style") == 0, (r, "script/style")
    assert len(re.findall(r"<h2", s)) >= 6, (r, "h2<6")
    bodies[r] = s
    rep[r] = len(s)
j["bodies"] = bodies
json.dump(j, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("injected", rep, "bodies keys:", list(bodies))
