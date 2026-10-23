# -*- coding: utf-8 -*-
import json, os
L = r"D:/股票数据/市场数据/_学习"
def load(p):
    for enc in ("utf-8-sig","utf-8","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
print("=== 交易计划_limitup_20261022 ===")
print(json.dumps(load(os.path.join(L,"交易计划_limitup_20261022.json")), ensure_ascii=False, indent=1)[:3000])
print("\n=== 质量荐票结算_20261023 ===")
print(json.dumps(load(os.path.join(L,"质量荐票结算_20261023.json")), ensure_ascii=False, indent=1)[:4000])
