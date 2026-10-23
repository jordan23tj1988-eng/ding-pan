# -*- coding: utf-8 -*-
import json, os
L = r"D:/股票数据/市场数据/_学习"
q = json.load(open(os.path.join(L, "涨停质量荐票_20261023.json"), encoding="utf-8"))
print("top5:")
print(json.dumps(q["top5"], ensure_ascii=False, indent=1)[:3500])
print("\n明细[0]:")
print(json.dumps(q["明细"][0], ensure_ascii=False, indent=1))
print("\n活跃因子:", q["活跃因子"])
