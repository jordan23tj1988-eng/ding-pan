# -*- coding: utf-8 -*-
"""候选页重出（2026-09-23）: 概览黄金骨架 + 能力进化两块, 不碰现网。

流程与生产同源:
  1) review_pages.build_site(root=市场数据, d=20260922, out=_tmp/golden_index_candidate)
  2) 生成盯盘台._sync_capability_blocks(site=candidate, date, root=市场数据)  # 部署后处理
  3) 自检: 段落/标记/组件计数/机器锚点/能力模块两块
"""
import sys, json
from pathlib import Path

MKT = Path("D:/股票数据/市场数据")
OUT = MKT / "_tmp" / "golden_index_candidate"
DATE = "20260922"
sys.path.insert(0, str(MKT))

import review_pages as rp
import importlib
gen = importlib.import_module("生成盯盘台")

result = rp.build_site(MKT, DATE, OUT)
print("build_site status:", result["status"], "errors:", result.get("errors"))
if result["status"] == "fail":
    raise SystemExit(1)

site_dir = Path("D:/股票数据/市场数据/_tmp/golden_full_site_%s" % DATE)
if site_dir.exists():
    import shutil
    shutil.rmtree(site_dir)
site_dir.mkdir(parents=True)
# 部署后处理需要七页齐全(index 是黄金锁页面; 其余六页从发布模型同源渲染)
for route in ("index", "intraday", "cycle", "auction", "lhb", "theme", "logic", "limitup", "history"):
    src = OUT / (route + ".html")
    if src.is_file():
        (site_dir / src.name).write_bytes(src.read_bytes())
print("staged pages:", sorted(p.name for p in site_dir.glob("*.html")))

report = gen._sync_capability_blocks(site_dir, DATE, root=MKT)
print("capability sync:", report)

idx = (site_dir / "index.html").read_text(encoding="utf-8")
stats = {
    "bytes": len(idx.encode("utf-8")),
    "h2": idx.count("<h2>"),
    "golden_markers": idx.count("<!--GOLDEN-INDEX:"),
    "citem": idx.count('class="citem"'),
    "reading_spine": idx.count('class="reading-spine"'),
    "obs": idx.count('class="obs"'),
    "rt": idx.count('class="routes'),
    "hb": idx.count('class="hb"'),
    "claim_anchor_bank": idx.count("claim-anchor-bank"),
    "evolution_blocks": idx.count('class="evolution"'),
    "anchors": {k: (idx.count("<!--%s-->" % k), idx.count("<!--/%s-->" % k))
                for k in ("CROSSPICK", "IDXTEMP", "IDXLEAD", "IDXVOTE", "ENGINEBOOKS")},
}
print(json.dumps(stats, ensure_ascii=False, indent=1))
print("CANDIDATE:", site_dir / "index.html")
