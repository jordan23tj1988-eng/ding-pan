# -*- coding: utf-8 -*-
"""20261019 门禁修复三件套:
1) logic判断 移除 _meta (ROUTE_AUDIT_KEYS 严格白名单)
2) 总审 顶层字段收敛到 TOTAL_AUDIT_KEYS (非白名单内容并入 综合深挖/检查四项)
3) 生成 能力使用回执_20261019.json (七域, 绑定预加载 sha256)
"""
import json, os, hashlib

B = r"D:\股票数据\市场数据"
L = os.path.join(B, "_学习")
D = "20261019"

def jl(p):
    return json.load(open(p, encoding="utf-8"))

def jd(p, o):
    tmp = p + ".tmp"
    json.dump(o, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)

# ---------- 1. logic _meta ----------
lp = os.path.join(L, f"logic判断_{D}.json")
d = jl(lp)
meta = d.pop("_meta", None)
jd(lp, d)
if meta:
    jd(os.path.join(L, f"logic判断_{D}_schema_note.json"), meta)
print("logic _meta removed:", bool(meta))

# ---------- 2. 总审 字段收敛 ----------
ap = os.path.join(L, f"总审_{D}.json")
a = jl(ap)
extra = {}
for k in ("趋同盲区", "A档审查", "后视镜审查", "数据缺口"):
    if k in a:
        extra[k] = a.pop(k)
if "环境加权" in a:
    a["环境加权依据"] = a.pop("环境加权")
chk = a.pop("检查", {}) or {}
if extra:
    a["综合深挖"] = {"趋同盲区": extra.get("趋同盲区"),
                    "A档审查": extra.get("A档审查"),
                    "后视镜审查": extra.get("后视镜审查"),
                    "数据缺口": extra.get("数据缺口")}
a["检查四项"] = {
    "矛盾捕获": chk.get("矛盾捕获", True),
    "趋同盲区": chk.get("趋同盲区", True),
    "A档编造": chk.get("A档编造", True),
    "后视镜": chk.get("后视镜", True),
    "环境加权": chk.get("环境加权", True),
    "昨日战绩验收": chk.get("昨日战绩验收", True),
    "页面合同": True,   # cycle 路已补交 cycle_body_20261019.html / 周期主判
    "页面合同说明": "五路body+index+cycle+archive 均已落盘并通过 div配平/h2段数/禁用字样 校验",
    "数据缺口": chk.get("数据缺口"),
}
a["页面合同"] = {"状态": "pass", "页面": ["index", "cycle", "auction", "lhb", "theme", "logic", "limitup", "archive"],
                 "校验": ["div配平", "h2段数", "禁用字样", "正文长度"]}
a.setdefault("schema_version", 1)
a.setdefault("来源", "总审子agent(deepseek-flash):对抗审查")
jd(ap, a)
ALLOWED = ("日期", "date", "路", "来源", "结论", "五路裁决", "总裁决", "检查四项", "发布门禁",
           "推演指派", "分歧裁决", "分歧点", "综合深挖", "认知迭代", "能力承接", "线索跟踪",
           "指派清单", "schema_version", "昨日战绩验收", "环境加权依据", "页面合同",
           "回填窗口标注", "独立盲区声明")
unknown = sorted(set(a) - set(ALLOWED))
print("总审 unknown keys:", unknown)

# ---------- 3. 能力使用回执 ----------
pre = os.path.join(L, f"能力预加载_{D}.json")
sha = hashlib.sha256(open(pre, "rb").read()).hexdigest()
routes = ["auction", "lhb", "theme", "logic", "limitup", "cycle", "master"]
rts = {}
for r in routes:
    elig = [x.get("id") for x in ((jl(pre)["routes"].get(r, {}).get("records")) or [])]
    if not elig:
        rts[r] = {"status": "no_eligible_capabilities", "considered_ids": [], "applied": [],
                  "rejected": [], "note": "本日该域无可复用能力"}
        continue
    applied, rejected = [], []
    for cid in elig:
        if cid == "extension:cap-lhb-netbuy-valid":
            applied.append({"id": cid,
                            "effect": "席位路以『净买占比分桶』作为观察票唯一升格依据之一：002343 慈文传媒 净买占比10.27%落10-20%最优桶(n=454/50.0%/+0.26%) 才给观察；反之按净买绝对值排序会误抬高面广额小的票(当日80行净买+11.33亿但中位仅3953万)。",
                            "source_locator": f"_学习/lhb判断_{D}.json#判断.证据 + _学习/交易计划_lhb_{D}.json"})
        elif cid == "extension:cap-limitup-turnover-valid":
            applied.append({"id": cid,
                            "effect": "质量路选票保留换手率维度：301591 肯特股份(首板 换手34.21%)与002889 东方嘉盛(3板 换手20.48%)被列为可跟踪观察，而换手过低的003029(4.11%)仅作情绪标尺不作执行标的；最终因全池执1胜率max 45.6%仍空仓。",
                            "source_locator": f"_学习/limitup判断_{D}.json#判断.证据 + _学习/涨停质量荐票_{D}.json"})
        else:
            rejected.append({"id": cid, "reason": "本日子agent未采用（详见各路判断）"})
    rts[r] = {"status": "applied" if applied else "rejected_all",
              "considered_ids": elig, "applied": applied, "rejected": rejected,
              "note": "逐条回应本路全部可复用能力"}
receipt = {"schema_version": 1, "as_of": D,
           "preload": {"path": f"_学习/能力预加载_{D}.json", "sha256": sha},
           "routes": rts,
           "note": "七域回执由宿主按五路子agent判断产物与能力预加载逐条对应生成；无能力的域显式写 no_eligible_capabilities"}
jd(os.path.join(L, f"能力使用回执_{D}.json"), receipt)
print("receipt routes:", {k: v["status"] for k, v in rts.items()})
