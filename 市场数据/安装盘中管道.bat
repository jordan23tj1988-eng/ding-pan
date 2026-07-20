@echo off
chcp 65001 >nul
REM 注册 盘中实时管道 计划任务(工作日09:14) — 需右键以管理员身份运行
net session >nul 2>&1
if not %errorlevel%==0 ( echo [X] 请右键 - 以管理员身份运行 & pause & exit /b 1 )
schtasks /create /f /tn "情绪复盘盘中管道" /tr "D:\股票数据\市场数据\盘中实时管道.bat" /sc weekly /d MON,TUE,WED,THU,FRI /st 09:14
if %errorlevel%==0 ( echo [√] 已注册: 工作日09:14自动启动盘中管道 ) else ( echo [X] 注册失败 )
schtasks /query /tn "情绪复盘盘中管道" | findstr 情绪
pause
