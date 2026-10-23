import json, io, os
B = r"D:\股票数据\市场数据\_学习"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)
z = L(os.path.join(B, "质量荐票结算_20260825.json"))
print("汇总:", json.dumps(z.get("汇总"), ensure_ascii=False))
for t in z.get("Top5", []):
    print(f"{t['名称']:8s} 连板{t.get('连板')} 命中{t.get('命中数')} 预测执1{t.get('预测执1胜率')} T1高开{t.get('T1高开')} 执行{t.get('执行收益')} 判定{t.get('判定')}")
print("反思:", str(z.get("反思"))[:400])
print()
c = L(os.path.join(B, "竞价池结算_20260825.json"))
print("竞价汇总:", json.dumps(c["汇总"], ensure_ascii=False))
print()
# 0825 lhb 荐票原文
l = L(os.path.join(B, "lhb判断_20260825.json"))
for t in l.get("荐票", {}).get("标的", []):
    print("lhb0825:", t.get("代码"), t.get("名称"), t.get("类型"))
