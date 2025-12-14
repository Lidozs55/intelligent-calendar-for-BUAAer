from pyngrok import ngrok
import time
import sys

# 设置隧道配置
try:
    # 创建HTTP隧道，转发到本地5000端口
    tunnel = ngrok.connect(5000, "http")
    
    print("\n=== 内网穿透已启动 ===")
    print(f"公网访问地址: {tunnel.public_url}")
    print(f"本地访问地址: http://localhost:5000")
    print("\n手机端访问:")
    print(f"  - 主页面: {tunnel.public_url}")
    print(f"  - 移动端页面: {tunnel.public_url}/mobile")
    print("\n按 Ctrl+C 停止隧道")
    print("====================")
    
    # 保持脚本运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在关闭隧道...")
        ngrok.kill()
        print("隧道已关闭")
        sys.exit(0)
        
except Exception as e:
    print(f"启动隧道失败: {e}")
    print("可能需要设置ngrok认证令牌。请访问 https://ngrok.com 注册获取令牌，然后运行：")
    print("ngrok config add-authtoken YOUR_AUTHTOKEN")
    sys.exit(1)