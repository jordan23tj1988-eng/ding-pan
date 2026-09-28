# -*- coding: utf-8 -*-
"""题材生命周期.py {d} [--settle {dprev}] —— 主线题材七段生命周期状态机 + 次日预判 + 机械化结算。

★动机(2026-08-15 用户拍板): 题材路的"生命周期"此前只是对当日事实贴标签(爆量启动段/退潮退位段),
  是事后归因不是事前预判。本脚本把它升级为"状态机+次日预判": 每条线判当前阶段(萌发/启动/发酵/
  高潮/退坡/退潮/消亡), 并给"明日最可能转移 + 确认条件 + 证伪条件 + 仓位含义", 次日机械化结算。

★七段锚定米开手册3.1(细化版八段 混沌启动→加速→分化→再加速→高潮→分歧转一致→强分歧→退潮):
  七段=米开八段去掉两个细分分歧、前补"萌发"、后补"消亡"。陷阱(宽度陷阱/反抽)是【标记】不占七段。

★数据: _学习/_题材四维.json(题材四维.py产出, 全历史逐日逐线) —— 全部T日收盘可知, 零后视镜。

★零后视镜: 对日期d分类+预判, 只用 <=d 的四维序列; 结算用 dprev 的预判 + dnext 的实际四维。

★阈值=假设(可被证伪/弃用): 宽度≥8爆量/≥15峰值、高度≥4双峰、环比±20%/±100%、晋级率=0, 均非铁律,
  打脸进认知库降权。七段判定仅凭宽度/高度/环比/晋级率, 缺一字/封单/炸板等强度证据(四维不含),
  强度修正由题材命门agent在判断层补(见10_题材命门agent.md)。

★线名归一: 跨日线名漂移会造成序列断裂(题材四维.py如实呈现不拼接)。本脚本内置 LINE_ALIAS 做
  "脚本级兜底归一"(仅回测中已验证的核心主线改名), 但线名归一真源=12号涨停复盘(题材归位_{d}.json),
  冲突以归位为准。归一后仍断裂的, prev=None 按序列首日处理并如实标注。

用法:
  python 题材生命周期.py 20260814            # 当日七段分类 + 次日预判
  python 题材生命周期.py 20260814 --settle    # 结算 20260814 的预判(需下一交易日四维)

产出:
  _学习/题材生命周期_{d}.json             (当日阶段表+预判)
  _学习/题材生命周期结算_{dprev}.json      (预判兑现/证伪)
  _学习/_题材生命周期结算.jsonl           (累计结算, 供转移概率归因)
  _学习/_题材生命周期反思.jsonl           (累计反思)
"""
import os, sys, json

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")
OUT4 = os.path.join(L, "_题材四维.json")

# 七段(顺序即生命周期推进方向)
STAGES = ["萌发", "启动", "发酵", "高潮", "退坡", "退潮", "消亡"]

# 线名归一(脚本级兜底假设;真源=12号题材归位,冲突以归位为准)
LINE_ALIAS = {
    "AI算力/半导体": "AI算力", "AI算力/液冷存储": "AI算力",
    "机器人/人形机器人": "机器人", "机器人/自动化": "机器人", "汽车/机器人": "机器人",
    "创新药/医药": "医药/创新药",
    "存储/半导体重组": "存储/半导体",
    "消费/乳业食品": "消费", "消费/造纸": "消费",
    "军工/商业航天": "商业航天",
}

# 仓位含义(米开3.2/3.3"每阶段定仓位"的定性映射, 方向性提示非指令)
POS_MEAN = {
    "萌发": "观察不介入",
    "启动": "低吸铺·轻仓试错",
    "发酵": "最佳上车点·第1次分歧可加",
    "高潮": "减仓·不追高",
    "退坡": "兑现·防御",
    "退潮": "空仓·低切防御",
    "消亡": "剔除·等新催化",
}


def norm(name):
    return LINE_ALIAS.get(name, name)


def _num(v):
    try:
        f = float(v)
        return f if f == f else None  # NaN->None
    except Exception:
        return None


def _gap_break(dt_a, dt_b):
    """日期差>7天=序列断裂(长休市/数据缺口), 断裂处 prev 视为不存在, 不跨段拼接。"""
    from datetime import datetime
    return (datetime.strptime(dt_b, "%Y%m%d") - datetime.strptime(dt_a, "%Y%m%d")).days > 7


def _prev_of(series_line, dts, i):
    """返回 (prev_row, prev_stage)。dts[i] 与前一交易日断裂则 (None, None)。"""
    if i <= 0:
        return None, None
    if _gap_break(dts[i - 1], dts[i]):
        return None, None
    prev = series_line[dts[i - 1]]
    prev2 = None
    if i > 1 and not _gap_break(dts[i - 2], dts[i - 1]):
        prev2 = series_line[dts[i - 2]]
    prev_stage, _ = classify(prev, prev2, None)
    return prev, prev_stage


def load_series(d):
    """读四维, 返回 {line: {dt: row}}, 只含<=d, 归一后线名。row含 w/h/sb/el/mom/jj。"""
    if not os.path.isfile(OUT4):
        return {}, []
    raw = json.load(open(OUT4, encoding="utf-8"))
    days = sorted(k for k in raw.keys() if k.isdigit() and k <= d)
    series = {}
    for dt in days:
        for name, info in raw[dt].items():
            if name == "_警报" or not isinstance(info, dict):
                continue
            line = norm(name)
            series.setdefault(line, {})[dt] = {
                "w": info.get("宽度") or 0,
                "h": info.get("高度") or 0,
                "sb": info.get("首板") or 0,
                "el": info.get("二连板") or 0,
                "mom": info.get("宽度环比"),
                "jj": info.get("题材晋级率"),
            }
    return series, days


def classify(row, prev, prev_stage):
    """七段分类 + 陷阱标记。返回 (stage, trap)。trap∈{None,'宽度陷阱','反抽'}。"""
    w, h, el = row["w"], row["h"], row["el"]
    mom = row["mom"]
    pw, ph = (prev["w"], prev["h"]) if prev else (None, None)

    # 陷阱标记(不占七段): 宽度先行高度未立 = 宽≥8高≤2, 或 宽≥15高≤3(爆量但高度滞后)
    trap = None
    if (w >= 8 and h <= 2) or (w >= 15 and h <= 3):
        trap = "宽度陷阱"
        # 反抽=退潮/退坡/高潮/发酵后宽度爆量反弹但纯首板(二连板=0)无接力(最危险陷阱)
        if (prev and mom is not None and mom >= 1.0 and el == 0
                and prev_stage in ("退潮", "退坡", "高潮", "发酵")):
            trap = "反抽"

    # 1 消亡: 前日在池(宽≥3或高≥2) 且 当日宽≤2 高≤1
    if prev and (pw >= 3 or ph >= 2) and w <= 2 and h <= 1:
        return "消亡", trap
    # 2 萌发: 宽≤3 高≤1
    if w <= 3 and h <= 1:
        return "萌发", trap
    # 3 启动: 首爆(环比≥+100% 且 高≤3) 或 (前日宽≤5 且 当日宽≥8 且 高≤3) 或 (断裂首日 宽≥8 高≤3)
    if mom is not None and mom >= 1.0 and h <= 3:
        return "启动", trap
    if prev and pw is not None and pw <= 5 and w >= 8 and h <= 3:
        return "启动", trap
    if prev is None and w >= 8 and h <= 3:
        return "启动", trap
    # 4 高潮: 双峰(宽≥15 且 高≥4)
    if w >= 15 and h >= 4:
        return "高潮", trap
    # 5 退坡 vs 退潮: 宽度环比≤-20% 时, 高度续命(h≥前日)=退坡(分歧), 高度也降(h<前日)=退潮(崩)
    if mom is not None and mom <= -0.2:
        if prev and ph is not None and h >= ph:
            return "退坡", trap   # 高度续命(滞后)
        return "退潮", trap        # 宽度塌+高度也降(龙头断板)
    # 6 退潮: 高度跌破前日 且 晋级率=0
    if prev and ph is not None and h < ph and (row["jj"] or 0) == 0:
        return "退潮", trap
    # 7 发酵: 高度≥3 且 宽度未塌(默认承接)
    if h >= 3:
        return "发酵", trap
    return "发酵", trap


def build_trans(series, days):
    """全历史(<=days末尾)转移矩阵 {(前日阶段, 当日阶段): 次数}。零后视镜, 断裂不跨段。"""
    trans = {}
    for line in series:
        dts = [dt for dt in sorted(series[line].keys()) if dt in days]
        for i in range(1, len(dts)):
            prev, prev_stage = _prev_of(series[line], dts, i)
            stage, _ = classify(series[line][dts[i]], prev, prev_stage)
            trans[(prev_stage, stage)] = trans.get((prev_stage, stage), 0) + 1
    return trans


def stage_out(trans, stage):
    return sum(c for (a, b), c in trans.items() if a == stage)


def _c(field, op, val):
    """结构化判定条件 {字段,op,值}。字段∈四维字段名。"""
    return {"字段": field, "op": op, "值": val}


def predict(stage, trap, row, trans=None):
    """次日预判列表。每项: {转移, 确认条件[], 证伪条件[], 仓位, 概率, 样本N}。条件全部AND。
    概率=历史转移频率(trans), 样本N<3时概率标null(零编造), 只给方向+条件。"""
    P = []

    def prob(target):
        if not trans:
            return None, 0
        n = stage_out(trans, stage)
        if n == 0:
            return None, 0
        c = trans.get((stage, target), 0)
        return (round(c / n, 2) if n >= 3 else None), n

    def add(target, confirms, falsifies):
        p, n = prob(target)
        P.append({"转移": target, "确认条件": confirms, "证伪条件": falsifies,
                  "仓位": POS_MEAN.get(target, ""), "概率": p, "样本N": n})

    if trap == "反抽":
        add("退坡", [_c("高度", "<=", 2)], [_c("高度", ">=", 3)])
        return P

    if stage == "萌发":
        add("启动", [_c("宽度环比", ">=", 1.0), _c("宽度", ">=", 8)], [_c("宽度", "<=", 5)])
    elif stage == "启动":
        if trap == "宽度陷阱":
            add("退坡", [_c("宽度环比", "<=", -0.3)], [_c("高度", ">=", 3)])
        else:
            add("发酵", [_c("高度", ">=", 3), _c("宽度环比", ">=", 0)], [_c("宽度环比", "<=", -0.3)])
            add("退坡", [_c("宽度环比", "<=", -0.3)], [_c("高度", ">=", 3)])
    elif stage == "发酵":
        add("高潮", [_c("宽度环比", ">=", 0), _c("高度", ">=", 4)], [_c("宽度环比", "<=", -0.2)])
        add("退坡", [_c("宽度环比", "<=", -0.2)], [_c("宽度环比", ">=", 0)])
    elif stage == "高潮":
        add("退坡", [_c("宽度环比", "<=", -0.2)], [_c("宽度环比", ">=", 0), _c("高度", ">", 4)])
    elif stage == "退坡":
        add("退潮", [_c("高度", "<", 4), _c("题材晋级率", "==", 0)], [_c("宽度环比", ">=", 0)])
        add("启动", [_c("宽度环比", ">=", 1.0)], [_c("高度", ">=", 4)])
    elif stage == "退潮":
        add("消亡", [_c("宽度", "<=", 2)], [_c("宽度环比", ">=", 1.0), _c("高度", ">=", 3)])
    elif stage == "消亡":
        add("萌发", [_c("宽度", ">=", 5)], [_c("宽度", "<=", 2)])
    return P


def eval_cond(cond, nxt):
    """机械化求值单条条件。nxt=次日四维row(key=w/h/sb/el/mom/jj)。字段中文名映射到英文key。"""
    f = {"宽度": "w", "高度": "h", "首板": "sb", "二连板": "el",
         "宽度环比": "mom", "题材晋级率": "jj"}.get(cond["字段"], cond["字段"])
    op = cond["op"]
    val = cond["值"]
    got = nxt.get(f)
    if got is None:
        return None  # 数据不足, 不可判定
    try:
        got = float(got)
    except Exception:
        return None
    if op == ">=":
        return got >= val
    if op == ">":
        return got > val
    if op == "<=":
        return got <= val
    if op == "<":
        return got < val
    if op == "==":
        return abs(got - val) < 1e-9
    if op == "!=":
        return abs(got - val) >= 1e-9
    return None


def _conds_verdict(conds, nxt):
    """条件列表AND求值: 全True=命中, 任一False=未命中, 有None且无False=待定。"""
    if not conds:
        return None
    seen_none = False
    for c in conds:
        r = eval_cond(c, nxt)
        if r is False:
            return False
        if r is None:
            seen_none = True
    return None if seen_none else True


def classify_day(series, days, d, trans):
    """对日期d(须在days内)逐线分类+预判。返回阶段表。断裂不跨段(prev=None)。"""
    out = []
    for line in sorted(series.keys()):
        row = series[line].get(d)
        if row is None:
            continue  # 该日此线出池, 不列当日阶段表
        dts = [dt for dt in sorted(series[line].keys()) if dt in days]
        i = dts.index(d) if d in dts else -1
        prev, prev_stage = _prev_of(series[line], dts, i) if i >= 0 else (None, None)
        stage, trap = classify(row, prev, prev_stage)
        preds = predict(stage, trap, row, trans)
        out.append({
            "线": line, "阶段": stage, "陷阱": trap,
            "当日": {k: row[k] for k in ("w", "h", "sb", "el", "mom", "jj")},
            "序列": [{"日期": dt, **series[line][dt]} for dt in dts if series[line].get(dt) is not None][-6:],
            "预判": preds,
        })
    order = {s: i for i, s in enumerate(STAGES)}
    out.sort(key=lambda x: (-order[x["阶段"]], -x["当日"]["w"]))
    return out


def main(d):
    series, days = load_series(d)
    if d not in days:
        print(f"[跳过] {d} 无题材四维数据")
        return
    trans = build_trans(series, days)
    table = classify_day(series, days, d, trans)
    active = [(r["线"], r["阶段"], r["陷阱"]) for r in table]
    doc = {
        "日期": d, "路": "theme", "版本": "1.0.0",
        "七段": STAGES,
        "口径": "七段=米开3.1八段去细分分歧/前补萌发/后补消亡;陷阱(宽度陷阱/反抽)=标记不占段;阈值=假设;"
                "数据=_题材四维.json(零后视镜,只用<=当日);强度(一字/封单/炸板)四维不含,由题材命门agent判断层补;"
                "概率=历史转移频率,样本N<3标null。",
        "转移矩阵": {f"{a}→{b}": c for (a, b), c in trans.items()},
        "阶段表": table,
        "摘要": {"总线数": len(table),
                 "高潮/发酵": [l for l, s, t in active if s in ("高潮", "发酵")],
                 "启动": [l for l, s, t in active if s == "启动"],
                 "退坡/退潮": [l for l, s, t in active if s in ("退坡", "退潮")],
                 "陷阱标记": [f"{l}({t})" for l, s, t in active if t]},
    }
    fp = os.path.join(L, f"题材生命周期_{d}.json")
    json.dump(doc, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"== {d} 题材生命周期(七段状态机) == 总线数{len(table)}")
    for r in table:
        trap = f" ⚠{r['陷阱']}" if r["陷阱"] else ""
        print(f"  {r['线']:<10} [{r['阶段']}{trap}] 宽{r['当日']['w']} 高{r['当日']['h']}")
        for p in r["预判"]:
            ps = f" ({p['概率']:.0%},N={p['样本N']})" if p["概率"] is not None else f" (N={p['样本N']}<3)"
            print(f"      →{p['转移']}{ps} 仓位[{p['仓位']}] 确认[{','.join(c['字段']+c['op']+str(c['值']) for c in p['确认条件'])}] 证伪[{','.join(c['字段']+c['op']+str(c['值']) for c in p['证伪条件'])}]")
    print(f"  产出 {fp}")


def settle(dprev):
    """结算 dprev 的预判: 用 dnext 实际四维验证每条预判的确认/证伪条件。"""
    fp = os.path.join(L, f"题材生命周期_{dprev}.json")
    if not os.path.isfile(fp):
        print(f"[跳过] 无 {fp}")
        return
    doc = json.load(open(fp, encoding="utf-8"))
    series, days = load_series("99999999")
    if dprev not in days:
        print(f"[跳过] {dprev} 不在四维序列")
        return
    i = days.index(dprev)
    if i + 1 >= len(days):
        print(f"[跳过] {dprev} 无下一交易日四维, 无法结算")
        return
    dnext = days[i + 1]
    rows = []
    n_hit = n_miss = n_pend = 0
    for r in doc["阶段表"]:
        line = r["线"]
        nxt = series.get(line, {}).get(dnext)
        if nxt is None:
            for p in r["预判"]:
                verdict = "兑现" if p["转移"] in ("消亡", "退潮") else "证伪"
                note = "线已出池(次日四维无此线)"
                rows.append({**p, "结算日": dnext, "判定": verdict, "注": note,
                             "线": line, "预判日阶段": r["阶段"]})
                if verdict == "兑现":
                    n_hit += 1
                else:
                    n_miss += 1
            continue
        for p in r["预判"]:
            conf = _conds_verdict(p["确认条件"], nxt)
            fals = _conds_verdict(p["证伪条件"], nxt)
            if conf is True and fals is not True:
                verdict, note = "兑现", "确认条件命中"
            elif fals is True and conf is not True:
                verdict, note = "证伪", "证伪条件命中"
            elif conf is None or fals is None:
                verdict, note = "待定", "数据不足(条件字段null)"
            else:
                verdict, note = "证伪", "确认/证伪均未命中(走了第三条路)"
            if verdict == "兑现":
                n_hit += 1
            elif verdict == "证伪":
                n_miss += 1
            else:
                n_pend += 1
            rows.append({**p, "结算日": dnext, "判定": verdict, "注": note,
                         "线": line, "预判日阶段": r["阶段"],
                         "次日四维": {k: nxt[k] for k in ("w", "h", "mom", "jj")}})
    out = {"预判日": dprev, "结算日": dnext,
           "汇总": {"兑现": n_hit, "证伪": n_miss, "待定": n_pend,
                   "总预判数": n_hit + n_miss + n_pend},
           "明细": rows}
    fp2 = os.path.join(L, f"题材生命周期结算_{dprev}.json")
    json.dump(out, open(fp2, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(L, "_题材生命周期结算.jsonl"), "a", encoding="utf-8").write(
        json.dumps({"预判日": dprev, "结算日": dnext, **out["汇总"]}, ensure_ascii=False) + "\n")
    refl = (f"{dprev}题材生命周期结算: 预判{out['汇总']['总预判数']}条, 兑现{n_hit}证伪{n_miss}待定{n_pend}。"
            f"兑现明细: " + "; ".join(
                f"{r['线']}[{r['预判日阶段']}→{r['转移']}]={r['判定']}({r['注']})" for r in rows if r["判定"] == "兑现") + "。")
    open(os.path.join(L, "_题材生命周期反思.jsonl"), "a", encoding="utf-8").write(
        json.dumps({"预判日": dprev, "结算日": dnext, "反思": refl}, ensure_ascii=False) + "\n")
    print(refl)
    print(f"  产出 {fp2}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--settle" in args:
        settle(args[0])
    else:
        main(args[0] if args else None)
