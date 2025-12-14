@echo off
REM cpolar 内网穿透启动脚本
REM 将本地 5000 端口暴露到公网

set CPOLAR_PATH=./cpolar/cpolar.exe
set LOCAL_PORT=5000

REM 检查 cpolar 是否存在
if not exist %CPOLAR_PATH% (
    echo 错误：未找到 cpolar.exe
    echo 请确保已下载并解压 cpolar 到 ./cpolar/ 目录
    pause
    exit /b 1
)

echo ====================================
echo cpolar 内网穿透启动脚本
echo ====================================
echo 本地端口：%LOCAL_PORT%
echo 访问地址：
echo  - 生产环境：http://localhost:%LOCAL_PORT%
echo  - 移动端页面：http://localhost:%LOCAL_PORT%/mobile
echo ====================================
echo 正在启动 cpolar 隧道...
echo ====================================
echo 请访问 https://dashboard.cpolar.com/auth 注册获取认证令牌
echo 然后在新窗口运行：cpolar.exe authtoken YOUR_TOKEN
echo ====================================

REM 启动 cpolar 隧道
%CPOLAR_PATH% http %LOCAL_PORT%

pause