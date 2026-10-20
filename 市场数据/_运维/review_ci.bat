@echo off
cd /d D:\股票数据\市场数据
echo [%date% %time%] CI start >> _学习\_运维\ci.log
"D:\股票数据\.venv312\Scripts\python.exe" _ops\ci.py --quick >> _学习\_运维\ci.log 2>&1
echo [%date% %time%] CI rc=%ERRORLEVEL% >> _学习\_运维\ci.log
