# -*- coding: utf-8 -*-
import json, os, csv, io, glob

BASE = "D:/股票数据/市场数据"
X = BASE + "/_学习"

def load(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with open(p, encoding=enc) as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except Exception:
            continue
    return "DECODE_FAIL"

files = {
 "题材归位": X+"/题材归位_20260826.json",
 "对链条": X+"/涨停对链条_20260826.json",
 "四维": X+"/_题材四维.json",
 "6有": X+"/主流题材6有_20260826.json",
 "生命周期": X+"/题材生命周期_20260826.json",
 "summary": BASE+"/20260826/summary.json",
 "战绩画像": X+"/子agent增强/战绩画像_theme_20260826.json",
 "认知库_theme": X+"/_认知库_theme.json",
 "总审0825": X+"/总审_20260825.json",
 "温度表": X+"/_市场温度表.json",
 "fact": X+"/fact_20260826.json",
 "模拟盘状态": X+"/_模拟盘/theme/状态.json",
}
for k,p in files.items():
    print("="*20, k, os.path.exists(p), p)

print("\n--- 子agent增强目录 ---")
d = X+"/子agent增强"
if os.path.isdir(d):
    for f in sorted(os.listdir(d)):
        if "theme" in f: print(" ", f)

print("\n--- _学习 下 theme/题材 相关 20260825/20260826 ---")
for f in sorted(os.listdir(X)):
    if ("theme" in f or "题材" in f) and ("2026082" in f or "_" == f[0]):
        print(" ", f)

print("\n--- 出版目录检查(荐票发出版是否已存在) ---")
for p in [X+"/题材荐票_20260826.json", X+"/theme判断_20260826.json", X+"/题材龙头判断_20260826.json", X+"/题材生命周期判断_20260826.json", X+"/交易计划_theme_20260826.json", X+"/theme_body_20260826.html"]:
    print(" ", os.path.exists(p), p)
