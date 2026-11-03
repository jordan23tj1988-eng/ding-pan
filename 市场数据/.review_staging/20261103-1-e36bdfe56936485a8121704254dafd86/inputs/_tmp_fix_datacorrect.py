# -*- coding: utf-8 -*-
"""两处客观数据修正（不改判断）：
1) limitup 荐票表 001219 青岛食品 板数 4板 -> 6板（zt_pool 连板数=6、涨停统计6/6）
2) theme 正文持仓回引 600838 -> 上海九百（哨兵只认 zt/dt 池内代码，持仓票不在池内）
"""
import json, shutil, sys, pathlib

BASE = pathlib.Path(r"D:\股票数据\市场数据")
L = BASE / "_学习"
JUDG = L / "judgment_20261102.json"

OLD_LIMIT = "<td>001219</td><td>青岛食品</td><td>观察</td><td>0</td><td>4板+"
NEW_LIMIT = "<td>001219</td><td>青岛食品</td><td>观察</td><td>0</td><td>6板+"

judg = json.loads(JUDG.read_text(encoding="utf-8"))
bak = JUDG.with_suffix(".json.bak_datacorrect_20261102")
if not bak.exists():
    shutil.copy(JUDG, bak)

lu = judg["bodies"]["limitup"]
n1 = lu.count(OLD_LIMIT)
print("limitup 命中", n1)
if n1 != 1:
    sys.exit("limitup 命中数异常，未写")
judg["bodies"]["limitup"] = lu.replace(OLD_LIMIT, NEW_LIMIT)

th = judg["bodies"]["theme"]
n2 = th.count("600838")
print("theme 600838 命中", n2)
judg["bodies"]["theme"] = th.replace("600838", "上海九百")

with JUDG.open("w", encoding="utf-8", newline="\n") as fh:
    json.dump(judg, fh, ensure_ascii=False, indent=1)

# 同步独立 body 文件（存在则改）
for route, old, new in (("limitup", OLD_LIMIT, NEW_LIMIT), ("theme", "600838", "上海九百")):
    p = L / ("%s_body_20261102.html" % route)
    if p.exists():
        t = p.read_text(encoding="utf-8")
        c = t.count(old)
        if c:
            shutil.copy(p, str(p) + ".bak_datacorrect_20261102")
            p.write_text(t.replace(old, new), encoding="utf-8", newline="\n")
        print(route, "body 文件替换", c)

j2 = json.loads(JUDG.read_text(encoding="utf-8"))
print("校验 limitup 残留4板串:", j2["bodies"]["limitup"].count(OLD_LIMIT))
print("校验 theme 残留600838:", j2["bodies"]["theme"].count("600838"))
print("校验 limitup 6板串:", j2["bodies"]["limitup"].count(NEW_LIMIT))
