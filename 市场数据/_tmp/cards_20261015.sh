#!/bin/bash
# 卡生成链 —— 分批执行, 逐条打印 PASS/FAIL
cd "D:/股票数据/市场数据" || exit 1
PY="D:/股票数据/.venv312/Scripts/python.exe"
D=20261015
DP=20261014
run(){
  echo "=== $* ==="
  env -u PYTHONPATH "$PY" "$@" 2>&1 | tail -6
  echo "[exit=${PIPESTATUS[0]}]"
}
case "$1" in
  g1)
    run 市场温度.py $D
    run 涨停质量训练.py --fetch $D
    ;;
  g2)
    run 质量荐票结算.py $DP
    run 题材荐票结算.py $DP
    run 逻辑荐票结算.py $DP
    run 席位荐票结算.py $DP
    run 预判结算.py $DP
    run 预判结算.py --preread $DP
    ;;
  g3)
    run 涨停质量荐票.py $D
    run 市场温度.py --card $D
    run 竞价池结算.py $DP
    run 竞价评分.py $D
    ;;
  g4)
    run 席位动向库.py rank
    run 席位荐票.py $D
    run 资金温度.py
    run 中报预增雷达.py $D
    ;;
  g5)
    run 龙虎榜双源校验.py $D
    run 风险日历.py $D
    run 竞价撤单差分.py $D
    run 开盘验证维.py $D
    ;;
  g6)
    run 日内温度曲线.py $D
    run 日内轮动图谱.py $D
    run 横切面扫描.py $D
    ;;
  g7)
    run 自主拓展扫描.py scan $D
    run 自主拓展扫描.py tick $D
    run 五路战绩画像.py $D
    ;;
esac
