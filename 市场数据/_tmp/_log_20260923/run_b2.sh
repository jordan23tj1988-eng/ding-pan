#!/usr/bin/env bash
# 20260923 卡生成链 B2 (j..n, 不含 tick)
cd "D:/股票数据/市场数据" || exit 1
LOG='_tmp/_log_20260923/chain_b2.txt'
: > "$LOG"
PY='D:/股票数据/.venv312/Scripts/python.exe'
run(){ echo "=== $* ===" >>"$LOG"; env -u PYTHONPATH "$PY" "$@" >>"$LOG" 2>&1; echo "[rc=$?] $*" >>"$LOG"; }
run 资金温度.py
run 中报预增雷达.py 20260923
run 龙虎榜双源校验.py 20260923
run 风险日历.py 20260923
run 竞价撤单差分.py 20260923
run 开盘验证维.py 20260923
run 日内温度曲线.py 20260923
run 日内轮动图谱.py 20260923
run 横切面扫描.py 20260923
run 自主拓展扫描.py scan 20260923
run 五路战绩画像.py 20260923
echo "[DONE B2]" >>"$LOG"
