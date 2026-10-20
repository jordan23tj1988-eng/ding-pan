# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r"D:/股票数据/市场数据"; L = B + "/_学习"
rad = json.load(open(B + "/_tmp/radar_parsed.json", encoding='utf-8'))
print("日期", rad["日期"], "报告期", rad["报告期"])
print("口径:", rad["口径"])
print("\n统计:", json.dumps(rad["统计"], ensure_ascii=False, indent=1))
print("\n活跃线 keys:", list(rad["活跃线"].keys()))
print("活跃线:", json.dumps(rad["活跃线"], ensure_ascii=False)[:1200])
print("\nA池 n=", len(rad["A共振池(重要度排序)"]))
print("A池 sample[0]:", json.dumps(rad["A共振池(重要度排序)"][0], ensure_ascii=False, indent=1))
print("\n按题材归类 keys:", list(rad["按题材归类"].keys()))
for k, v in rad["按题材归类"].items():
    print("  ", k, len(v) if hasattr(v, '__len__') else v)
print("\n刚点火 n=", len(rad["刚点火(有涨停未透支)"]))
print(json.dumps(rad["刚点火(有涨停未透支)"], ensure_ascii=False, indent=1)[:4000])
