@echo off
chcp 65001 >nul
REM 注册 数据回填 计划任务(每天19:40,周末照跑历史回填) — 需右键以管理员身份运行
net session >nul 2>&1
if not %errorlevel%==0 ( echo [X] 请右键 - 以管理员身份运行 ^& pause ^& exit /b 1 )
schtasks /create /f /tn "情绪复盘数据回填" /tr "D:\股票数据\市场数据\数据回填每晚.bat" /sc daily /st 19:40
if %errorlevel%==0 ( echo [√] 已注册: 每天19:40自动回填 ) else ( echo [X] 注册失败 )
schtasks /query /tn "情绪复盘数据回填" | findstr 情绪
pause
