# -*- coding: utf-8 -*-
import json, os
B = r"D:\股票数据\市场数据\_学习"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
w = load_any(os.path.join(B,"子agent增强","战绩画像_limitup_20261016.json"))
print("#### 战绩画像 keys", list(w.keys()))
print(json.dumps(w,ensure_ascii=False)[:4500])
print("\n\n#### 交易计划_limitup_20261015")
print(json.dumps(load_any(os.path.join(B,"交易计划_limitup_20261015.json")),ensure_ascii=False)[:2500])
print("\n\n#### 模拟盘状态")
print(json.dumps(load_any(os.path.join(B,"_模拟盘","limitup","状态.json")),ensure_ascii=False)[:2500])
