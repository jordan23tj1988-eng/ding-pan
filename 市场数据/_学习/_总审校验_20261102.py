import json, io, sys, os, re
base = r"D:\股票数据\市场数据\_学习"
P = os.path.join(base, "总审_20261102.json")
d = json.load(io.open(P, encoding="utf-8-sig"))
errs, warns = [], []

REQ = ["date","日期","来源","schema_version","五路裁决","分歧点","趋同盲区","编造与后视镜审查",
       "环境加权依据","昨日战绩验收","总裁决","指派清单","线索跟踪","能力承接","检查","检查四项",
       "回填窗口标注","独立盲区声明","矛盾捕获","综合深挖","认知迭代","票池"]
missing = [k for k in REQ if k not in d]
if missing: errs.append("缺键: %s" % missing)
extra = [k for k in d if k not in REQ]
print("顶层键数 %d（要求 22：指定 21 + Master 增补『票池』）" % len(d))
if extra: warns.append("额外键: %s" % extra)

# 1 五路裁决
routes = ["auction","lhb","theme","logic","limitup"]
wr = d.get("五路裁决", [])
if len(wr) != 5: errs.append("五路裁决条数=%d" % len(wr))
got = [x.get("路") for x in wr]
if got != routes: errs.append("五路顺序/名称错: %s" % got)
for x in wr:
    for f in ["路","档位","置信度","荐票数","结论摘要","采信/降权及理由"]:
        if f not in x: errs.append("五路裁决[%s] 缺字段 %s" % (x.get("路"), f))
    if x.get("档位") not in ("A","B","C"): errs.append("档位非法 %s" % x.get("路"))
    if not isinstance(x.get("置信度"), int) or not (0 <= x["置信度"] <= 100): errs.append("置信度非法 %s" % x.get("路"))

# 2 总裁决
zj = d.get("总裁决", {})
for f in ["档位","依据","置信度","攻防纪律","仓位区间","次日验证点","结论","票池"]:
    if f not in zj: errs.append("总裁决缺字段 %s" % f)
if zj.get("档位") not in ("A","B","C"): errs.append("总裁决档位非法")
if not isinstance(zj.get("置信度"), int): errs.append("总裁决置信度非整数")
if not zj.get("次日验证点"): errs.append("次日验证点空")
if "明日(20261103)" not in (zj.get("结论") or ""): errs.append("总裁决.结论 未以『明日(20261103)』开头表述")
pool = zj.get("票池") or []
if not pool: errs.append("总裁决.票池 空")
tot = 0.0
for p in pool:
    for f in ["代码","名称","来自路","裁定","总裁定权重%","执行闸门","理由","题材（以 题材归位_20261102.json 为准）"]:
        if f not in p: errs.append("票池[%s] 缺 %s" % (p.get("代码"), f))
    if p.get("来自路") not in routes: errs.append("票池[%s] 来自路非法" % p.get("代码"))
    tot += float(p.get("总裁定权重%") or 0)
print("票池(总裁决) %d 只，权重合计 %.1f%%" % (len(pool), tot))
if tot > 7.01: errs.append("票池权重合计 %.2f 超上限" % tot)
# 顶层票池索引须与 总裁决.票池 一致
idx = d.get("票池")
if not isinstance(idx, dict) or "明细" not in idx: errs.append("顶层 票池 结构非法（应为 {合计,明细}）")
else:
    codes_a = [p.get("代码") for p in pool]
    codes_b = [p.get("代码") for p in idx["明细"]]
    if codes_a != codes_b: errs.append("顶层票池与总裁决.票池 代码不一致 %s vs %s" % (codes_b, codes_a))
    wa = sum(float(p.get("总裁定权重%") or 0) for p in idx["明细"])
    if abs(wa - tot) > 1e-9: errs.append("顶层票池权重和 %.2f != 总裁决 %.2f" % (wa, tot))
    for p in idx["明细"]:
        for f in ["代码","名称","来自路","总裁定权重%","执行闸门","详情指针"]:
            if f not in p: errs.append("票池索引[%s] 缺 %s" % (p.get("代码"), f))
    print("顶层票池索引 一致: %d 只 / %.1f%%" % (len(codes_b), wa))

# 3 指派清单
ap = d.get("指派清单")
if not isinstance(ap, list): errs.append("指派清单不是数组")
else:
    if not ap: warns.append("指派清单为空（需给理由）")
    for a in ap:
        for f in ["指派ID","指派给","深挖任务","理由","可机械验证","截止","状态"]:
            if f not in a: errs.append("指派[%s] 缺 %s" % (a.get("指派ID"), f))
        if a.get("指派给") not in routes: errs.append("指派[%s] 指派给非法: %s" % (a.get("指派ID"), a.get("指派给")))
        if a.get("截止") != "20261103": errs.append("指派[%s] 截止非 20261103" % a.get("指派ID"))
        if not re.match(r"^MA-20261102-\d{2}$", str(a.get("指派ID"))): errs.append("指派ID 命名错 %s" % a.get("指派ID"))
    covered = set(a.get("指派给") for a in ap)
    if covered != set(routes): warns.append("指派未覆盖五路: 缺 %s" % (set(routes)-covered))
    print("指派 %d 条 → %s" % (len(ap), sorted(covered)))

# 4 线索跟踪
xs = d.get("线索跟踪")
if not isinstance(xs, list) or not xs: errs.append("线索跟踪空")
else:
    srcs = set()
    for x in xs:
        for f in ["线索ID","来源路","内容","状态","判定条件","下次验证点"]:
            if f not in x: errs.append("线索[%s] 缺 %s" % (x.get("线索ID"), f))
        if x.get("状态") not in ("待验证","观察中","已证伪","已证实","待指派"): errs.append("线索[%s] 状态非法: %s" % (x.get("线索ID"), x.get("状态")))
        srcs.add(x.get("来源路"))
    print("线索 %d 条，来源覆盖 %s" % (len(xs), sorted(srcs)))
    for r in routes:
        if not any(r in str(s) for s in srcs): errs.append("线索未覆盖路 %s" % r)

# 5 能力承接
c = d.get("能力承接", {})
if c.get("可复用能力数") != 2: errs.append("可复用能力数 != 2")
applied = sum(1 for x in c.get("逐路", []) if x.get("采用或拒绝") == "采用")
if c.get("复用合计") != applied: errs.append("复用合计 %s != applied %s" % (c.get("复用合计"), applied))
if c.get("新增能力化") != 0: errs.append("新增能力化 != 0")
print("能力承接: 可复用 %s / 复用合计 %s / applied %s / 新增 %s" % (c.get("可复用能力数"), c.get("复用合计"), applied, c.get("新增能力化")))

# 6 昨日战绩验收
ys = d.get("昨日战绩验收", [])
ids = [x.get("指派ID") for x in ys]
need = ["MA-20261030-0%d" % i for i in range(1,6)]
if ids != need: errs.append("昨日验收 ID 不齐: %s" % ids)
for x in ys:
    if not x.get("证据路径"): errs.append("昨日验收[%s] 无证据路径" % x.get("指派ID"))
    if x.get("判定") not in ("已完成","部分完成","未完成"): errs.append("昨日验收[%s] 判定非法" % x.get("指派ID"))
print("昨日验收: %s" % ["%s=%s" % (x["指派ID"][-2:], x["判定"]) for x in ys])

# 7 分歧/深挖/认知条数
for k, n in [("分歧点",4),("趋同盲区",4),("综合深挖",3),("认知迭代",3),("矛盾捕获",3)]:
    v = d.get(k)
    if not isinstance(v, list) or len(v) < n: errs.append("%s 条数 %s < %s" % (k, len(v) if isinstance(v,list) else "非数组", n))
    else: print("%s %d 条" % (k, len(v)))

# 8 后视镜: 未来日期只能出现在 判定/验证/截止 语境
bad = []
for k in routes:
    txt = io.open(os.path.join(base, "%s判断_20261102.json" % k), encoding="utf-8-sig").read()
    for m in re.finditer(r"2026(11(0[3-9]|1\d|2\d|3[01])|\d{2}(0[1-9]|1\d|2\d|3[01]))", txt):
        if m.group(0) <= "20261102": continue
        ctx = txt[max(0, m.start()-60):m.end()+40]
        if not re.search(r"可证伪|验证|判定|截止|条件|明日|次日|待|预期|将|若|缺口|不估值|无一落在", ctx):
            bad.append((k, m.group(0), ctx.replace("\n"," ")))
if bad:
    for b in bad[:10]: warns.append("后视镜存疑 %s" % (b,))
else:
    print("后视镜扫描: 五路无『未来日期作为证据』语境")

# 9 编造落盘校验: 提取声称落盘的文件名并检查存在
for k in routes:
    txt = io.open(os.path.join(base, "%s判断_20261102.json" % k), encoding="utf-8-sig").read()
    for fn in set(re.findall(r"[_A-Za-z0-9\u4e00-\u9fa5\-]{2,40}_20261102\.(?:json|csv)", txt)):
        if not os.path.exists(os.path.join(base, fn)):
            warns.append("%s 提及但 _学习 下不存在: %s" % (k, fn))

# 10 回执
rc = json.load(io.open(os.path.join(base, "能力使用回执_master_20261102.json"), encoding="utf-8-sig"))
print("master 回执:", rc.get("route"), rc.get("日期"), rc.get("status"), "applied=%d" % len(rc.get("applied", [])))
if rc.get("applied") and rc.get("status") == "no_eligible_capabilities": errs.append("回执状态与 applied 矛盾")

print("\n=== 结果 ===")
print("ERRORS:", len(errs))
for e in errs: print("  E:", e)
print("WARN:", len(warns))
for w in warns: print("  W:", w)
sys.exit(1 if errs else 0)
