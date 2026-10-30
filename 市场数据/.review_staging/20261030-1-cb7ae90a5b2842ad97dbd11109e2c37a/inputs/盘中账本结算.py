# -*- coding: utf-8 -*-
"""P2 全量学习/盘中账本审计兼容入口。

真实实现位于 review_learning.audit_learning；它会独立写出清单覆盖、到期推演、
认知与 Master 结算，不修改输入 root。用法:
python -B 盘中账本结算.py YYYYMMDD --root INPUT_ROOT --out NEW_RUN_ROOT
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from review_learning import audit_learning


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("d")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    result = audit_learning(a.root, a.d, a.out)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
