import json, io, os
B = r"D:\股票数据\市场数据\_学习"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

for f in ["竞价池结算_20260825.json", "席位荐票结算_20260825.json", "题材荐票结算_20260825.json",
          "逻辑荐票结算_20260825.json", "质量荐票结算_20260825.json"]:
    p = os.path.join(B, f)
    print("=" * 30, f)
    try:
        print(json.dumps(L(p), ensure_ascii=False, indent=1)[:2600])
    except Exception as e:
        print("ERR", e)
    print()
