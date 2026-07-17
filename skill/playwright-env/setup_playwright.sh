#!/bin/bash
# 沙箱免root安装playwright无头浏览器（2026-07-15验证通过）
# 沙箱重置后需重跑本脚本（约1-2分钟，下载262MB内核）
set -e
HOME_DIR=$(eval echo ~)
pip install playwright --break-system-packages -q
export PATH=$PATH:$HOME_DIR/.local/bin
# 用headless-shell（262MB）而非完整chromium（更大），40秒内可下完
playwright install chromium-headless-shell
# 免root补齐缺失系统库（jammy沙箱实测只缺libXdamage）
mkdir -p $HOME_DIR/pwlibs && cd $HOME_DIR/pwlibs
MISSING=$(ldd $HOME_DIR/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell 2>/dev/null | grep "not found" | awk '{print $1}' | sort -u)
if echo "$MISSING" | grep -q libXdamage; then
  (apt-get download libxdamage1 2>/dev/null || wget -q http://archive.ubuntu.com/ubuntu/pool/main/libx/libxdamage/libxdamage1_1.1.5-2build2_amd64.deb)
  dpkg -x libxdamage1*.deb extracted
fi
echo "剩余缺失库(应为空): $(export LD_LIBRARY_PATH=$HOME_DIR/pwlibs/extracted/usr/lib/x86_64-linux-gnu; ldd $HOME_DIR/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell 2>/dev/null | grep 'not found' || echo 无)"
echo "安装完成。使用时: export LD_LIBRARY_PATH=$HOME_DIR/pwlibs/extracted/usr/lib/x86_64-linux-gnu"
