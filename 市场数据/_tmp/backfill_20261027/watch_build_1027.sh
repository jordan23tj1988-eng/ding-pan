#!/bin/bash
# 等 1028 主链跑完 → 重建并发布 1027 → 若前台回退则再重建 1028 拉回
cd "D:/股票数据/市场数据" || exit 1
PY=D:/股票数据/.venv312/Scripts/python.exe
DB=C:/Users/66353/AppData/Local/hermes/profiles/a/cron/executions.db
LOG=_tmp/backfill_20261027/watch_and_build.log
: > "$LOG"

echo "[$(date +%H:%M:%S)] 开始监视 1028 主链" >> "$LOG"
for i in $(seq 1 150); do
  st=$(env -u PYTHONPATH "$PY" -c "
import sqlite3
c=sqlite3.connect(r'$DB')
r=c.execute(\"select status from executions where job_id='c4d23047161f' and started_at like '2026-10-28%' order by started_at desc limit 1\").fetchone()
print(r[0] if r else 'none')" 2>/dev/null)
  echo "[$(date +%H:%M:%S)] 1028 status=$st" >> "$LOG"
  if [ "$st" != "running" ]; then break; fi
  sleep 45
done

echo "[$(date +%H:%M:%S)] 1028 已结束，开始重建 1027" >> "$LOG"
env -u PYTHONPATH "$PY" 生成盯盘台.py 20261027 >> "$LOG" 2>&1
echo "EXIT_1027=$?" >> "$LOG"
D1=$(env -u PYTHONPATH "$PY" -c "import json;print(json.load(open('CURRENT.json',encoding='utf-8')).get('d'))" 2>/dev/null)
echo "[$(date +%H:%M:%S)] CURRENT=$D1" >> "$LOG"

if [ "$D1" = "20261027" ] && [ -d "复盘/盯盘台/20261028" ]; then
  echo "[$(date +%H:%M:%S)] 前台已回退到 1027，重建 1028 拉回" >> "$LOG"
  env -u PYTHONPATH "$PY" 生成盯盘台.py 20261028 >> "$LOG" 2>&1
  echo "EXIT_1028=$?" >> "$LOG"
  env -u PYTHONPATH "$PY" -c "import json;print('FINAL_CURRENT=',json.load(open('CURRENT.json',encoding='utf-8')).get('d'))" >> "$LOG" 2>&1
fi

echo "=== 关键行 ===" >> "$LOG"
echo "--- 完成 ---"
