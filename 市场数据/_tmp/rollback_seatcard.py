# -*- coding: utf-8 -*-
"""回滚 SEATCARD 搬运：把 bodies.lhb 恢复到 .bak_seatcard_20261104（= revision 2 出页成功时的状态）。

理由：SEATCARD 是 artifact 型锚（渲染器按 section 注入卡片），body 位置不影响归属；
搬运后台账段结构变化导致渲染期 `<!--/LHBLEDGER-->` 丢失、sentinel exit=1、golden anchor pair 失败。
index 的 h2→h3 改动保留（revision 2 已含且出页成功）。
"""
import json
import shutil
from pathlib import Path

L = Path(r"D:\股票数据\市场数据\_学习")
p = L / "judgment_20261103.json"
bak = L / "judgment_20261103.json.bak_seatcard_20261104"
assert bak.exists(), "缺备份"

with open(bak, encoding="utf-8") as f:
    old = json.load(f)
with open(p, encoding="utf-8") as f:
    cur = json.load(f)

cur["bodies"]["lhb"] = old["bodies"]["lhb"]
shutil.copy2(p, L / "judgment_20261103.json.bak_before_seatcard_rollback")
with open(p, "w", encoding="utf-8") as f:
    json.dump(cur, f, ensure_ascii=False)
print("已恢复 lhb body：", len(cur["bodies"]["lhb"]), "字符")
print("index body 保持 h2→h3 版：", "检查四项与发布门禁" in cur["bodies"]["index"])
