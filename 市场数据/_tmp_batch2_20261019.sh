#!/bin/bash
# 20261019 卡生成链 批2
cd "D:/股票数据/市场数据" || exit 1
PY="D:/股票数据/.venv312/Scripts/python.exe"
run(){ echo "===== $* ====="; env -u PYTHONPATH -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy "$PY" "$@" 2>&1 | tail -14; echo "[rc=$?]"; }
run 涨停质量荐票.py 20261019
run 市场温度.py --card 20261019
run 竞价池结算.py 20261016
run 竞价评分.py 20261019
run 席位动向库.py rank
run 席位荐票.py 20261019
run 资金温度.py 20261019
run 中报预增雷达.py 20261019
run 龙虎榜双源校验.py 20261019
run 风险日历.py 20261019
run 竞价撤单差分.py 20261019
run 开盘验证维.py 20261019
run 日内温度曲线.py 20261019
run 日内轮动图谱.py 20261019
run 横切面扫描.py 20261019
run 自主拓展扫描.py scan 20261019
run 自主拓展扫描.py tick 20261019
run 五路战绩画像.py 20261019
echo "===== BATCH2 DONE ====="
