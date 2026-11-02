#!/bin/bash
# 20261102 傍晚卡生成链(step4) 顺序执行 + 日志
cd "/d/股票数据/市场数据" || exit 1
PY='D:\股票数据\.venv312\Scripts\python.exe'
D=20261102
PREV=20261030
LOG=_tmp_chain4_${D}.log
: > "$LOG"
run() {
  echo "=== $(date +%H:%M:%S) RUN $*" >> "$LOG"
  env -u PYTHONPATH -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy "$PY" "$@" >> "$LOG" 2>&1
  echo "=== rc=$? $*" >> "$LOG"
}
run 涨停质量训练.py --fetch $D
run 质量荐票结算.py $PREV
run 题材荐票结算.py $PREV
run 逻辑荐票结算.py $PREV
run 席位荐票结算.py $PREV
run 预判结算.py $PREV
run 预判结算.py --preread $PREV
run 涨停质量荐票.py $D
run 市场温度.py --card $D
run 竞价池结算.py $PREV
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
echo "=== $(date +%H:%M:%S) CHAIN4 DONE" >> "$LOG"
