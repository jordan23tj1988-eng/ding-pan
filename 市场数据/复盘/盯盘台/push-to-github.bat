@echo off
chcp 65001 >nul
echo [盯盘台] 正在同步到 GitHub Pages...
echo.

REM 设置代理（根据你的系统代理自动配置）
set HTTP_PROXY=http://127.0.0.1:15236
set HTTPS_PROXY=http://127.0.0.1:15236

REM 进入盯盘台目录
cd /d "D:\股票数据\市场数据\复盘\盯盘台"

REM 添加所有变更
git add .

REM 提交（用当前日期时间作为提交信息）
for /f "tokens=1-5 delims=/ " %%a in ('echo %date% %time%') do (
    git commit -m "Update: %%a-%%b-%%c %%d:%%e"
)

REM 推送到 GitHub
git push origin master

if %errorlevel% == 0 (
    echo.
    echo [✓] 同步成功！
    echo [✓] 公网链接：https://jordan23tj1988-eng.github.io/ding-pan/
    echo [✓] 大约等待1-2分钟后刷新即可看到最新内容
) else (
    echo.
    echo [✗] 同步失败，请检查网络或代理状态
)

echo.
pause
