@echo off
cd /d D:\股票数据\市场数据
"D:\股票数据\.venv312\Scripts\python.exe" _ops\ledger.py ingest --since 20260101 >> _学习\_运维\ledger.log 2>&1
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set TODAY=%%i
"D:\股票数据\.venv312\Scripts\python.exe" _ops\ledger.py weekly --week-end %TODAY% >> _学习\_运维\ledger.log 2>&1
