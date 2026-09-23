# -*- coding: utf-8 -*-
"""hb-e 20260918 本场自纠: 待批清单 ⑤ iFinD 项由『iFinDPy.pth 缺失』改为 cron 原文引用(零编造纪律, 同一场次内自纠)。"""
import json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\股票数据\市场数据\盘中\20260918"
OLD = "⑤【iFinD】保活体检 17:34 FAIL(login/取数失败, iFinDPy.pth 缺失)"
NEW = ("⑤【iFinD】保活体检 17:34 FAIL —— cron 错误原文: 『ALARM [2026-09-18 17:34:08] iFinD保活体检失败: / "
       "login/取数失败: D:\\股票数据\\.venv312\\Lib\\site-packages\\iFinDPy.pth / login_rc=-2』(exit code 1); "
       "本场未独立核实缺失件明细, 仅引原文, 不推定")
p = os.path.join(D, "临盘决断_20260918_1430.json")
d = json.load(open(p, encoding="utf-8"))
a = d["收市后待批清单"]
assert OLD in a, "原文不匹配"
d["收市后待批清单"] = a.replace(OLD, NEW)
d["本场自纠"] = ("本场为同一执行实例内的自纠(非覆盖他场发出版): 收市后待批清单⑤ iFinD 项原写『iFinDPy.pth 缺失』系沿用同批他场表述, "
                "本场未独立核实; 已改为 cron 错误原文逐字引用, 避免越证。其余结论不变。 自纠时间=%s" %
                __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

ap = os.path.join(D, "报警_20260918.jsonl")
lines = open(ap, encoding="utf-8").read().splitlines()
n = 0
out = []
for ln in lines:
    o = json.loads(ln)
    if o.get("session") == "hb-e_1430" and "iFinDPy.pth 缺失" in json.dumps(o, ensure_ascii=False):
        o["收市后待批清单"] = o["收市后待批清单"].replace(OLD, NEW)
        o["本场自纠"] = d["本场自纠"]
        ln = json.dumps(o, ensure_ascii=False)
        n += 1
    out.append(ln)
open(ap, "w", encoding="utf-8").write("\n".join(out) + "\n")

# 复核
d2 = json.load(open(p, encoding="utf-8"))
assert "iFinDPy.pth 缺失" not in json.dumps(d2, ensure_ascii=False), "决断件残留"
rows = [json.loads(x) for x in open(ap, encoding="utf-8") if x.strip()]
assert all("iFinDPy.pth 缺失" not in json.dumps(r, ensure_ascii=False) for r in rows), "报警件残留"
mine = [r for r in rows if r.get("session") == "hb-e_1430"]
print("自纠行数:", n, "| 报警件总行:", len(rows), "| 本场条数:", len(mine))
print("本场 level=", mine[0]["level"], "fills=", mine[0]["fills"])
print("决断件 JSON 复核 OK, size=", os.path.getsize(p), "| 报警件 size=", os.path.getsize(ap))
print("⑤段:", [x for x in mine[0]["收市后待批清单"].split("; ") if "iFinD" in x])
