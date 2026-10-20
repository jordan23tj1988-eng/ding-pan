# -*- coding: utf-8 -*-
"""把 index/cycle LLM 板块 HTML 注入 judgment_20261020.json bodies（带三条断言）"""
import json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = os.path.join(BASE, "_学习")
D = "20261020"
jp = os.path.join(L, "judgment_%s.json" % D)

def plain(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", "", s)

j = json.load(open(jp, encoding="utf-8"))
bodies = j.setdefault("bodies", {})
for route, path, minchars in (("index", "index_body_%s.html" % D, 3200), ("cycle", "cycle_body_%s.html" % D, 2600)):
    p = os.path.join(L, path)
    s = open(p, encoding="utf-8").read()
    assert s.count("<div") == s.count("</div>"), "%s div 不配平 %d/%d" % (route, s.count("<div"), s.count("</div>"))
    assert "<script" not in s and "<style" not in s, "%s 含 script/style" % route
    n = len(plain(s))
    assert n >= minchars, "%s 纯文本 %d < %d" % (route, n, minchars)
    assert re.search(r"<h2", s), "%s 缺 h2" % route
    bodies[route] = s
    print(route, "injected chars=%d plain=%d" % (len(s), n))

json.dump(j, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
j2 = json.load(open(jp, encoding="utf-8"))
print("bodies keys:", list(j2["bodies"]), {k: len(v) for k, v in j2["bodies"].items()})
