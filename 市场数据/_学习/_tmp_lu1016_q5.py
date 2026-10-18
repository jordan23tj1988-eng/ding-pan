# -*- coding: utf-8 -*-
import json, os
B=r"D:\股票数据\市场数据\_学习"
z=json.load(open(os.path.join(B,"涨停原因_20261016.json"),encoding="utf-8"))
mp=z["映射"]
for c in ["000530","300045","301586","002917","600802","600825","920006","603168","600860"]:
    print(c, json.dumps(mp.get(c),ensure_ascii=False)[:400])
