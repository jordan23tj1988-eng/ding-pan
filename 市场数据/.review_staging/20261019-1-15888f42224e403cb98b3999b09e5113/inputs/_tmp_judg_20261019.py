# -*- coding: utf-8 -*-
"""20261019 judgment 组装: 7页 bodies + meta + archive (宿主替代缺失的 五路判断收集器.py)"""
import json, os, re
B = r"D:\股票数据\市场数据"
L = os.path.join(B, "_学习")
D = "20261019"

def rd(p):
    with open(os.path.join(L, p), encoding="utf-8") as f:
        return f.read()

meta = json.load(open(os.path.join(L, f"index_meta_{D}.json"), encoding="utf-8"))
bodies = {
    "index": rd(f"index_body_{D}.html"),
    "cycle": rd(f"cycle_body_{D}.html"),
    "auction": rd(f"auction_body_{D}.html"),
    "lhb": rd(f"lhb_body_{D}.html"),
    "theme": rd(f"theme_body_{D}.html"),
    "logic": rd(f"logic_body_{D}.html"),
    "limitup": rd(f"limitup_body_{D}.html"),
}
archive = rd(f"archive_{D}.html")

# 校验: div 配平 / h2 数 / 禁用字样 / 未来日期
BAN = ["待决断", "晚间复盘预案", "待13号确认", "—%~—%"]
for k, v in list(bodies.items()) + [("archive", archive)]:
    d1, d2 = v.count("<div"), v.count("</div>")
    h2 = len(re.findall(r"<h2", v))
    bad = [w for w in BAN if w in v]
    fut = re.findall(r"2026102\d|2026103\d|202611\d\d", v)
    print(f"{k}: len={len(v)} div={d1}/{d2} h2={h2} ban={bad} future_dates={len(fut)}")
    assert d1 == d2, f"{k} div 不配平"
    assert not bad, f"{k} 禁用字样 {bad}"
    assert h2 >= (6 if k in ("index", "cycle") else 4), f"{k} h2 太少"

jud = {
    "date": D,
    "更新label": meta["更新label"],
    "一句话": meta["一句话"],
    "ticker": meta["ticker"],
    "bodies": bodies,
    "archive_body": archive,
}
out = os.path.join(L, f"judgment_{D}.json")
tmp = out + ".tmp"
json.dump(jud, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
os.replace(tmp, out)
print("WROTE", out, os.path.getsize(out))
for k in ("LEDGER", "LHBLEDGER", "POOLLEDGER"):
    print("anchor", k, sum(v.count("<!--%s-->" % k) for v in bodies.values()))
