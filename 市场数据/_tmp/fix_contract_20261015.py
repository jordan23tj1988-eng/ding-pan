# -*- coding: utf-8 -*-
"""宿主契约对齐修复(仅键名/版本号归一，不改内容):
 1) 总审_{d}.json schema_version: 字符串 'master-audit-v1' -> int 1
 2) theme判断_{d}.json 认知迭代条目: 补 标题/正文 键(内容原样保留)以匹配 ROUTE_AUDIT_KEYS 收集器
修复前备份 .bak_contractfix；修复后跑 review_contract.validate_schema_version 断言。"""
import json, os, shutil, sys
R = r"D:\股票数据\市场数据"; os.chdir(R)
sys.path.insert(0, R)
from review_contract import validate_schema_version, TOTAL_AUDIT_KEYS, ROUTE_AUDIT_KEYS

D = sys.argv[1] if len(sys.argv) > 1 else "20261015"
chg = []

# 1) 总审 schema_version
p = "_学习/总审_%s.json" % D
j = json.load(open(p, encoding="utf-8"))
if j.get("schema_version") != 1:
    shutil.copyfile(p, p + ".bak_contractfix")
    j["schema_version"] = 1
    json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    chg.append("总审 schema_version -> 1")
assert validate_schema_version(j, p) is None, validate_schema_version(j, p)
unknown = set(j) - set(TOTAL_AUDIT_KEYS)
print("总审 顶层非白名单字段:", sorted(unknown) or "无")

# 2) theme 认知迭代
p = "_学习/theme判断_%s.json" % D
t = json.load(open(p, encoding="utf-8"))
if t.get("schema_version") not in (None, 1):
    t["schema_version"] = 1
items = t.get("认知迭代") or []
fixed = 0
for it in items:
    if not isinstance(it, dict):
        continue
    if it.get("正文") or it.get("claim") or it.get("认知点"):
        continue
    txt = it.get("条目") or it.get("标题") or ""
    if not txt:
        continue
    shutil.copyfile(p, p + ".bak_contractfix")
    it.setdefault("标题", str(txt)[:60])
    it["正文"] = txt
    it.setdefault("日期", D)
    fixed += 1
if fixed:
    json.dump(t, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    chg.append("theme 认知迭代 补 正文 键 x%d" % fixed)
assert validate_schema_version(t, p) is None, validate_schema_version(t, p)
print("theme 顶层非白名单字段:", sorted(set(t) - set(ROUTE_AUDIT_KEYS)) or "无")
print("修复项:", chg or "无需修复")
