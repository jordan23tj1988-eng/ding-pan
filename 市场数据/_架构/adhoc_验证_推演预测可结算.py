# -*- coding: utf-8 -*-
"""adhoc_验证_推演预测可结算.py {d} —— 推演/大师计划的可结算性与零后视镜独立验收器。

动机(2026-09-11 实测): 20260910 深度推演由子 agent 交付, 自报"6条次日可证伪预测
全部机械化", 但其 verify 脚本跑完即删、不可复现。用 review_learning._prediction_rows
**独立口径重扫**发现: 6 条数值预测里 5 条 op=None(措辞未命中既有解析器)——
即"看着有判定条件, 实际无法机械结算"。本脚本把该检查固化为可随时重跑的行为契约。

重跑命令(必须用项目 venv 并清 PYTHONPATH):
  cd "D:/股票数据/市场数据" && env -u PYTHONPATH "D:/股票数据/.venv312/Scripts/python.exe" \
      _架构/adhoc_验证_推演预测可结算.py 20260910

判定: 全部 PASS → rc=0; 任一 FAIL → rc=1(stderr 明细)。
声明: ad-hoc验证(非套件绿灯)。
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_OPS = {"ge", "gt", "le", "lt", "eq"}

results = []  # (ok: bool, name: str, detail: str)


def chk(ok, name, detail=""):
    results.append((bool(ok), name, str(detail)))


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1 or not re.fullmatch(r"\d{8}", argv[0]):
        print("用法: adhoc_验证_推演预测可结算.py YYYYMMDD")
        return 2
    d = argv[0]
    sys.path.insert(0, str(ROOT))
    try:
        from review_learning import _prediction_rows
    except Exception as exc:  # noqa: BLE001
        chk(False, "导入 review_learning", exc)
        _report()
        return 1

    # 1) 推演文件存在 + 日期绑定
    tui = ROOT / "_学习" / f"推演_{d}.json"
    chk(tui.is_file(), f"推演_{d}.json 存在", tui)
    if not tui.is_file():
        _report()
        return 1
    try:
        obj = _load(tui)
        chk(str(obj.get("日期")) == d, "推演 日期==目标日", f"日期={obj.get('日期')}")
        chk(int(obj.get("schema_version", 1)) == 1, "推演 schema_version==1",
            f"schema_version={obj.get('schema_version')}")
    except Exception as exc:  # noqa: BLE001
        chk(False, "推演 JSON 可解析", exc)
        _report()
        return 1

    # 2) 既有解析器能否消费(不抛异常), 且数值预测全部落到白名单 op
    try:
        rows = _prediction_rows(ROOT, d)
    except Exception as exc:  # noqa: BLE001
        chk(False, "review_learning 可消费 推演_{d}.json", exc)
        _report()
        return 1
    numeric = [r for r in rows if r.get("field") and r.get("event_type") in ("numeric", "stock")]
    unresolved = [r for r in numeric if r.get("op") not in VALID_OPS]
    chk(bool(numeric), "存在数值型预测", f"n={len(numeric)}")
    chk(not unresolved, "数值预测全部可机械结算(op 白名单)",
        "无法结算: " + ", ".join(f"{r.get('field')}(op={r.get('op')})" for r in unresolved))
    chk(all(r.get("threshold") is not None for r in numeric), "数值预测均带阈值",
        ", ".join(f"{r.get('field')}={r.get('threshold')}" for r in numeric))
    detail = "; ".join(f"{r.get('field')}{r.get('op')}{r.get('threshold')}" for r in numeric)
    chk(True, f"数值预测清单(n={len(numeric)})", detail)

    # 3) 零后视镜: **证据出处**不得指向晚于目标日的文件/日期
    #    (正文里提到次日作为"预测目标日"是合法的, 只查证据链)
    refs = []
    for item in (obj.get("证据") or []):
        if isinstance(item, str):
            refs.append(item)
    for row in (obj.get("次日可证伪预测") or obj.get("predictions") or []):
        if isinstance(row, dict):
            src = row.get("证据来源")
            refs.extend(src if isinstance(src, list) else [src] if isinstance(src, str) else [])
    future = set()
    for text_ in refs:
        for m in re.finditer(r"(?<![0-9])(\d{4})-?(\d{2})-?(\d{2})(?![0-9])", text_):
            key = "".join(m.groups())
            if key > d:
                future.add(key)
    chk(not future, "证据链零后视镜(无晚于目标日的证据出处)", "越界: " + ", ".join(sorted(future)))

    # 4) 大师计划: 结构 + 与状态一致性(空仓不得编造卖出)
    plan_p = ROOT / "_学习" / f"交易计划_master_{d}.json"
    chk(plan_p.is_file(), f"交易计划_master_{d}.json 存在", plan_p)
    if plan_p.is_file():
        try:
            plan = _load(plan_p)
            chk(str(plan.get("日期")) == d, "master 计划 日期==目标日", f"日期={plan.get('日期')}")
            chk(plan.get("路") == "master", "master 计划 路==master", f"路={plan.get('路')}")
            buys, sells = plan.get("buys"), plan.get("sells")
            chk(isinstance(buys, list) and isinstance(sells, list), "buys/sells 均为数组",
                f"buys={type(buys).__name__} sells={type(sells).__name__}")
            st_p = ROOT / "_学习" / "_模拟盘" / "master" / "状态.json"
            if st_p.is_file():
                st = _load(st_p)
                hold = st.get("持仓") or []
                chk(not (not hold and sells), "空仓 → sells 必须为空(禁编造卖出)",
                    f"持仓={len(hold)} sells={len(sells)}")
        except Exception as exc:  # noqa: BLE001
            chk(False, "master 计划可解析", exc)

    return _report()


def _report():
    ok_all = all(x[0] for x in results)
    for ok, name, detail in results:
        print(("PASS " if ok else "FAIL ") + name + ((" | " + detail) if detail else ""))
    passed = sum(1 for x in results if x[0])
    print(f"RESULT: {'ALL PASS' if ok_all else 'FAIL'} ({passed}/{len(results)})")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
