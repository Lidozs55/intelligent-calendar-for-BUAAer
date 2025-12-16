import qrcode
import os
from PIL import Image
from io import BytesIO
import base64
import socket
import time
import threading
import requests
import json

class QRCodeGenerator:
    """
    二维码生成器，用于生成手机访问地址的二维码
    """
    # 类变量存储当前的cpolar域名
    current_cpolar_url = None
    # 刷新间隔（秒）
    REFRESH_INTERVAL = 300  # 5分钟刷新一次
    # cpolar本地API地址
    CPOLAR_API = "http://localhost:4040/api/tunnels"
    
    @classmethod
    def start_cpolar_refresh(cls):
        """
        启动cpolar域名自动刷新线程
        """
        def refresh_cpolar_url():
            # 线程启动后，先等待15秒，给cpolar服务足够的启动时间
            wait_time = 15
            print(f"[QRCode] cpolar域名刷新线程已启动，等待{wait_time}秒后开始首次刷新...")
            time.sleep(wait_time)
            
            while True:
                try:
                    # 尝试获取cpolar隧道信息
                    print(f"[QRCode] 正在刷新cpolar域名...")
                    response = requests.get(cls.CPOLAR_API, timeout=5)
                    
                    if response.status_code == 200:
                        try:
                            # 尝试解析JSON响应
                            tunnels_data = response.json()
                            
                            # 处理不同的响应格式
                            tunnels = []
                            if isinstance(tunnels_data, dict):
                                # 格式1: {"tunnels": [...], ...}
                                if 'tunnels' in tunnels_data:
                                    tunnels = tunnels_data['tunnels']
                            elif isinstance(tunnels_data, list):
                                # 格式2: 直接返回隧道列表
                                tunnels = tunnels_data
                            
                            # 查找HTTP隧道
                            for tunnel in tunnels:
                                if isinstance(tunnel, dict):
                                    proto = tunnel.get('proto', '').lower()
                                    url = tunnel.get('url', '')
                                    if proto == 'http' and url:
                                        # 找到HTTP隧道，更新cpolar域名
                                        cls.current_cpolar_url = url
                                        print(f"[QRCode] 已更新cpolar域名: {cls.current_cpolar_url}")
                                        break
                        except json.JSONDecodeError:
                            # JSON解析失败，尝试从HTML中提取URL
                            import re
                            url_pattern = r'http://[a-zA-Z0-9.-]+\.cpolar\.io'
                            match = re.search(url_pattern, response.text)
                            if match:
                                url = match.group(0)
                                cls.current_cpolar_url = url
                                print(f"[QRCode] 已从HTML中提取cpolar域名: {cls.current_cpolar_url}")
                except requests.exceptions.ConnectionError:
                    print(f"[QRCode] 无法连接到cpolar API，可能服务未启动")
                except Exception as e:
                    print(f"[QRCode] 刷新cpolar域名失败: {str(e)}")
                
                # 等待指定间隔后再次刷新
                time.sleep(cls.REFRESH_INTERVAL)
        
        # 启动刷新线程
        thread = threading.Thread(target=refresh_cpolar_url, daemon=True)
        thread.start()
    
    @staticmethod
    def get_local_ip():
        """
        获取本机在局域网中的IP地址
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"获取本地IP地址失败: {e}")
            return '127.0.0.1'
    
    @staticmethod
    def generate_qr_code(url):
        """
        生成二维码图片
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            print(f"生成二维码失败: {e}")
            return None
    
    @classmethod
    def get_mobile_access_info(cls, port=5000):
        """
        获取手机访问信息，包括IP地址和二维码
        """
        local_ip = cls.get_local_ip()
        
        # 生成访问地址
        local_mobile_url = f"http://{local_ip}:{port}/mobile"
        mobile_url = local_mobile_url
        cpolar_url = None
        cpolar_status = "unavailable"
        
        # 如果有cpolar域名，优先使用
        if cls.current_cpolar_url:
            cpolar_url = cls.current_cpolar_url
            mobile_url = f"{cpolar_url}/mobile"
            cpolar_status = "available"
        
        # 生成故障排查信息
        troubleshooting = {
            "common_issues": [
                "1. 确保手机和电脑连接到同一网络",
                "2. 检查电脑防火墙是否允许5000端口",
                "3. 校园网可能限制设备间通信，尝试手机热点",
                "4. 尝试直接输入IP地址访问",
                "5. 检查网络是否分配在同一网段"
            ],
            "alternative_solutions": [
                "1. 电脑开启移动热点，手机连接热点",
                "2. 使用内网穿透工具（如ngrok、cpolar）",
                "3. 修改后端端口为常用端口（如8080）"
            ],
            "hotspot_guide": "电脑开启热点 → 手机连接热点 → 电脑获取热点IP → 手机访问该IP:5000/mobile"
        }
        
        # 生成二维码
        qr_code = cls.generate_qr_code(mobile_url)
        
        return {
            'local_ip': local_ip,
            'port': port,
            'mobile_url': mobile_url,
            'local_mobile_url': local_mobile_url,
            'cpolar_url': cpolar_url,
            'cpolar_status': cpolar_status,
            'qr_code': qr_code,
            'troubleshooting': troubleshooting
        }
    
    @classmethod
    def restart_cpolar_service(cls):
        """
        重启cpolar服务
        """
        try:
            import platform
            import subprocess
            import os
            import pathlib
            
            # 获取主文件夹路径
            main_dir = pathlib.Path(__file__).parent.parent.parent
            
            # 构建cpolar路径
            if platform.system() == 'Windows':
                cpolar_path = os.path.join(main_dir, 'cpolar', 'cpolar.exe')
            else:
                cpolar_path = os.path.join(main_dir, 'cpolar', 'cpolar')
            
            # 检查cpolar是否存在
            if os.path.exists(cpolar_path):
                # 杀死所有已存在的cpolar进程
                if platform.system() == 'Windows':
                    subprocess.run(['taskkill', '/f', '/im', 'cpolar.exe'], capture_output=True, text=True)
                else:
                    subprocess.run(['pkill', '-f', 'cpolar'], capture_output=True, text=True)
                
                # 重新启动cpolar服务
                subprocess.Popen(
                    [cpolar_path, 'http', '5000'],
                    stdout=None,
                    stderr=None,
                    stdin=None,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == 'Windows' else 0,
                    cwd=str(main_dir)
                )
                
                print(f"[QRCode] 已重启cpolar服务")
                
                # 清除当前cpolar域名，触发重新获取
                cls.current_cpolar_url = None
            else:
                print(f"[QRCode] 未找到cpolar可执行文件: {cpolar_path}")
        except Exception as e:
            print(f"[QRCode] 重启cpolar服务失败: {str(e)}")
    
    @classmethod
    def refresh_cpolar_url_once(cls):
        """
        立即刷新一次cpolar域名
        """
        try:
            # 尝试获取cpolar隧道信息
            response = requests.get(cls.CPOLAR_API, timeout=5)
            
            if response.status_code == 200:
                try:
                    # 尝试解析JSON响应
                    tunnels_data = response.json()
                    
                    # 处理不同的响应格式
                    tunnels = []
                    if isinstance(tunnels_data, dict):
                        # 格式1: {"tunnels": [...], ...}
                        if 'tunnels' in tunnels_data:
                            tunnels = tunnels_data['tunnels']
                    elif isinstance(tunnels_data, list):
                        # 格式2: 直接返回隧道列表
                        tunnels = tunnels_data
                    
                    # 查找HTTP隧道
                    for tunnel in tunnels:
                        if isinstance(tunnel, dict):
                            proto = tunnel.get('proto', '').lower()
                            url = tunnel.get('url', '')
                            if proto == 'http' and url:
                                # 找到HTTP隧道，更新cpolar域名
                                cls.current_cpolar_url = url
                                print(f"[QRCode] 已更新cpolar域名: {cls.current_cpolar_url}")
                                break
                except json.JSONDecodeError:
                    # JSON解析失败，尝试从HTML中提取URL
                    import re
                    url_pattern = r'http://[a-zA-Z0-9.-]+\.cpolar\.io'
                    match = re.search(url_pattern, response.text)
                    if match:
                        url = match.group(0)
                        cls.current_cpolar_url = url
                        print(f"[QRCode] 已从HTML中提取cpolar域名: {cls.current_cpolar_url}")
        except requests.exceptions.ConnectionError:
            print(f"[QRCode] 无法连接到cpolar API，可能服务未启动")
        except Exception as e:
            print(f"[QRCode] 刷新cpolar域名失败: {str(e)}")