# -*- coding: utf-8 -*-
import json, os, re, csv, statistics
B = r"D:\股票数据\市场数据\_学习"
M = r"D:\股票数据\市场数据"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
ql = load_any(os.path.join(B,"_涨停质量库.json"))
print("基准:", json.dumps(ql["基准"],ensure_ascii=False))
fb = ql["分板胜率"]
print("分板胜率 keys:", list(fb.keys()))
for k,v in fb.items():
    print("\n--",k)
    if isinstance(v,dict):
        for kk,vv in v.items():
            print("   ",kk,"=",json.dumps(vv,ensure_ascii=False)[:260])
print("\n=== 规则榜 全部 ===")
for r in ql["规则榜"]:
    print(r["规则"], "| n=%s 执1胜%s 执1均%s 执2胜%s 执2均%s 抓龙%s 可执行=%s"%(r["n"],r["执1胜率"],r["执1均涨"],r["执2胜率"],r["执2均涨"],r["抓龙率"],r["可执行"]))
