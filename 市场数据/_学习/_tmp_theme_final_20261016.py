# -*- coding: utf-8 -*-
import json, os, glob
from datetime import datetime
L = r"D:/股票数据/市场数据/_学习"
d = json.load(open(os.path.join(L,"题材生命周期判断_20261016.json"), encoding="utf-8"))
print("逐线:", list(d["逐线"].keys()))

# 清理探针临时脚本（保留生成/校验脚本）
rm = []
for f in glob.glob(os.path.join(L,"_tmp_theme_probe*.py")) + [os.path.join(L,"_tmp_theme_ctx_20261016.json")]:
    try:
        os.remove(f); rm.append(os.path.basename(f))
    except Exception as e:
        print("skip", f, e)
print("removed:", len(rm))

artifacts = [
 "theme判断_20261016.json",
 "theme_body_20261016.html",
 "题材荐票_20261016.json",
 "题材龙头判断_20261016.json",
 "题材生命周期判断_20261016.json",
 "交易计划_theme_20261016.json",
 "能力回执_theme_20261016.json",
]
missing = [a for a in artifacts if not os.path.exists(os.path.join(L,a))]
assert not missing, missing
run = {
 "status": "pass",
 "attempts": 1,
 "model": "deepseek-flash",
 "provider": "deepseek",
 "artifact_paths": [os.path.join(L,a).replace("\\","/") for a in artifacts],
 "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
}
p = os.path.join(L, "_运行状态", "theme_20261016.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(run, open(p,"w",encoding="utf-8",newline="\n"), ensure_ascii=False, indent=1)
print("runstatus:", p, os.path.getsize(p))
print(json.dumps(run, ensure_ascii=False, indent=1))
print("\n最终自检:")
for a in artifacts:
    print("  %-32s %7d bytes" % (a, os.path.getsize(os.path.join(L,a))))
