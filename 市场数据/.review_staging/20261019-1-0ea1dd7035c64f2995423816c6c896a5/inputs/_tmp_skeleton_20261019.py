import json, os
BASE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(BASE, "_学习", "judgment_20261019.json")
sk = {"date": "20261019", "更新label": "20261019 复盘", "一句话": "", "ticker": "", "bodies": {}, "archive_body": ""}
json.dump(sk, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("judgment骨架已建", p, os.path.getsize(p))
