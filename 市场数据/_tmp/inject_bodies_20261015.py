# -*- coding: utf-8 -*-
"""宿主注入: 五路 body -> judgment bodies[route] (收集器脚本本机缺失的替代)
含注入前校验: h2段数 / div配平 / LEDGER类锚成对 / 非空。"""
import json, os, re, sys

R = r"D:\股票数据\市场数据"
os.chdir(R)
D = sys.argv[1] if len(sys.argv) > 1 else "20261015"
JP = "_学习/judgment_%s.json" % D
MAP = {"auction": "_学习/auction_body_%s.html" % D,
       "lhb": "_学习/lhb_body_%s.html" % D,
       "theme": "_学习/theme_body_%s.html" % D,
       "logic": "_学习/logic_body_%s.html" % D,
       "limitup": "_学习/limitup_body_%s.html" % D}
j = json.load(open(JP, encoding="utf-8"))
bd = j.setdefault("bodies", {})
fails = []
for route, p in MAP.items():
    if not os.path.exists(p):
        fails.append("%s: 文件缺失 %s" % (route, p)); continue
    s = open(p, encoding="utf-8").read()
    h2 = re.findall(r"<h2[^>]*>", s)
    nopen, nclose = len(re.findall(r"<div[\s>]", s)), len(re.findall(r"</div>", s))
    anchors = {}
    for a in ("LEDGER", "LHBLEDGER", "POOLLEDGER", "QT卡", "SEATCARD", "SCORECARD", "JUDGE"):
        c = len(re.findall(r"<!--/?%s" % re.escape(a), s))
        if c: anchors[a] = c
    bad_anchor = [k for k, v in anchors.items() if v % 2 != 0]
    ins = ("洞察" in s) or ("agent" in s.lower())
    prob = []
    if len(h2) < 6: prob.append("h2段数=%d<6" % len(h2))
    if nopen != nclose: prob.append("div不平 %d/%d" % (nopen, nclose))
    if bad_anchor: prob.append("锚不成对 %s" % bad_anchor)
    if len(s) < 1500: prob.append("过短 %d" % len(s))
    bd[route] = s
    print("%-8s len=%-7d h2=%-2d div=%d/%d anchors=%s 洞察卡=%s %s"
          % (route, len(s), len(h2), nopen, nclose, anchors or "-", ins,
             ("[问题] " + "; ".join(prob)) if prob else "OK"))
    if prob: fails.append("%s: %s" % (route, "; ".join(prob)))
json.dump(j, open(JP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("注入完成 -> %s | bodies keys=%s | 总字符=%d"
      % (JP, list(bd.keys()), sum(len(v) for v in bd.values())))
if fails:
    print("FAIL: " + " | ".join(fails)); sys.exit(1)
print("PASS: 五路 body 注入校验全通过")
