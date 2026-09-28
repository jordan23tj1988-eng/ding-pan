# -*- coding: utf-8 -*-
"""Compatibility entrypoint for the canonical prediction-contract verifier.

The old standalone verifier drifted from ``review_learning._prediction_rows``.
This wrapper deliberately delegates to the maintained, independently rerunnable
checker so there is only one prediction contract to verify.
"""
from pathlib import Path
import runpy

_TARGET = Path(__file__).resolve().parent / "_架构" / "adhoc_验证_推演预测可结算.py"

if __name__ == "__main__":
    runpy.run_path(str(_TARGET), run_name="__main__")
