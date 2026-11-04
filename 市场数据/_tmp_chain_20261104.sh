#!/bin/bash
# 傍晚卡生成链 d~n（20261104）
cd "D:/股票数据/市场数据" || exit 1
PY="D:/股票数据/.venv312/Scripts/python.exe"
D=20261104
P=20261103
run() {
  echo "########## $* $(date +%H:%M:%S)"
  PYTHONPATH= "$PY" "$@" 2>&1 | tail -12
  echo "---- rc=$? $(date +%H:%M:%S)"
}
run 涨停质量荐票.py $D
run 市场温度.py --card $D
run 竞价池结算.py $P
run 竞价评分.py $D
run 席位动向库.py rank
run 席位荐票.py $D
run 资金温度.py
run 中报预增雷达.py $D
run 龙虎榜双源校验.py $D
run 风险日历.py $D
run 竞价撤单差分.py $D
run 开盘验证维.py $D
run 日内温度曲线.py $D
run 日内轮动图谱.py $D
run 横切面扫描.py $D
run 自主拓展扫描.py scan $D
run 自主拓展扫描.py tick $D
run 五路战绩画像.py $D
echo "########## ALL DONE $(date +%H:%M:%S)"
