# -*- coding: utf-8 -*-
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r"D:/股票数据/市场数据"; L = B + "/_学习"

# template
tpl = json.load(open(B + "/产业链模板.json", encoding='utf-8'))
print("== 模板盘数:", len(tpl))
for plate, v in tpl.items():
    codes = re.findall(r'"(\d{6})"', json.dumps(v, ensure_ascii=False))
    print(f"  {plate}: 环节{len(v) if isinstance(v,dict) else '?'} 代码{len(codes)}")

# 涨停对链条 题材线
c = json.load(open(L + "/涨停对链条_20261020.json", encoding='utf-8'))
print("\n== 题材线", len(c["题材线"]))
for t in c["题材线"]:
    print("  ", json.dumps(t, ensure_ascii=False)[:400])

# risk events
ev = json.load(open(L + "/风险事件_20261020.json", encoding='utf-8'))
print("\n== 风险事件 metrics:", json.dumps(ev["metrics"], ensure_ascii=False))
print("sources:", json.dumps(ev["sources"], ensure_ascii=False)[:600])
print("事件 sample:", json.dumps(ev["事件"][0], ensure_ascii=False, indent=1))
cal = json.load(open(L + "/风险日历_20261020.json", encoding='utf-8'))
print("\n== 风险日历 metrics:", json.dumps(cal["metrics"], ensure_ascii=False))
print("sources:", json.dumps(cal["sources"], ensure_ascii=False)[:800])
