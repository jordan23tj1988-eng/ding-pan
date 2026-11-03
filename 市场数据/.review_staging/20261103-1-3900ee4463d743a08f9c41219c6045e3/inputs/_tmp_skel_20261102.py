# -*- coding: utf-8 -*-
import json, os
D = "20261102"
L = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_学习")
p = os.path.join(L, "judgment_%s.json" % D)
if os.path.isfile(p):
    print("[SKIP] 已存在:", p)
else:
    json.dump({"date": D, "更新label": "%s 复盘" % D, "一句话": "", "ticker": "", "bodies": {}, "archive_body": ""},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[OK] judgment骨架已建:", p)
