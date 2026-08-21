@echo off
chcp 65001 >nul
schtasks /Create /TN "ding-pan每日同步" /TR "\"D:\股票数据\同步GitHub\同步到GitHub.bat\" auto" /SC DAILY /ST 21:00 /F
if errorlevel 1 (
    echo [X] 创建失败, 请右键"以管理员身份运行"再试
) else (
    echo [√] 已创建计划任务: 每天 21:00 自动同步到 GitHub
    echo     想改时间: 开始菜单搜"任务计划程序" - 找到"ding-pan每日同步"
)
pause
