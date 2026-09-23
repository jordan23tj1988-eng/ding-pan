# -*- coding: utf-8 -*-
"""P2 推演结算兼容入口。

真实实现位于 review_learning.settle_predictions；本入口只负责严格参数转发，
不覆盖输入 root 内的历史发布物。用法:
python -B 预判结算.py YYYYMMDD --root INPUT_ROOT --out NEW_RUN_ROOT --target-d YYYYMMDD
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from review_learning import settle_predictions


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("d")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--target-d", required=True)
    a = p.parse_args(argv)
    result = settle_predictions(a.root, a.d, a.target_d, a.out)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
