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
            # 线程启动后，先等待8秒（5秒基础+3秒额外），给cpolar服务足够的启动时间
            wait_time = 8  # 8秒等待，确保cpolar服务有足够时间启动
            print(f"[QRCode] 线程已启动，等待{wait_time}秒后开始首次cpolar域名刷新...")
            time.sleep(wait_time)
            
            while True:
                try:
                    # 尝试获取最新的cpolar隧道信息
                    response = requests.get(cls.CPOLAR_API, timeout=5)
                    
                    if response.status_code == 200:
                        # 先尝试直接解析JSON
                        try:
                            tunnels_data = response.json()
                            
                            # 处理不同的响应格式
                            tunnel_list = []
                            if isinstance(tunnels_data, dict):
                                if 'tunnels' in tunnels_data:
                                    # 格式1: {"tunnels": [...], ...}
                                    tunnel_list = tunnels_data['tunnels']
                                elif 'url' in tunnels_data and 'proto' in tunnels_data:
                                    # 格式2: 直接返回单个隧道信息
                                    tunnel_list = [tunnels_data]
                            elif isinstance(tunnels_data, list):
                                # 格式3: 直接返回隧道列表
                                tunnel_list = tunnels_data
                            
                            # 找到HTTP隧道
                            for tunnel in tunnel_list:
                                if isinstance(tunnel, dict):
                                    proto = tunnel.get('proto', '')
                                    url = tunnel.get('url', '')
                                    if proto == 'http' and url:
                                        # 提取完整URL（包括http://）
                                        cls.current_cpolar_url = url
                                        print(f"[QRCode] 已更新cpolar域名: {cls.current_cpolar_url}")
                                        break
                        except json.JSONDecodeError as e:
                            # 尝试使用正则表达式直接从响应中提取URL
                            import re
                            url_pattern = r'http://[a-zA-Z0-9.-]+\.cpolar\.io'
                            match = re.search(url_pattern, response.text)
                            if match:
                                url = match.group(0)
                                cls.current_cpolar_url = url
                                print(f"[QRCode] 使用正则表达式提取到cpolar域名: {url}")
                except requests.exceptions.ConnectionError:
                    print(f"[QRCode] 无法连接到cpolar API，可能服务未启动")
                except Exception as e:
                    print(f"[QRCode] 刷新cpolar域名失败: {str(e)[:50]}...")
                
                # 等待指定间隔后再次刷新（5分钟）
                time.sleep(cls.REFRESH_INTERVAL)
        
        # 直接启动定时刷新线程，不执行第一次刷新（第一次刷新在线程内部进行）
        # 这样不会阻塞其他初始化工作
        thread = threading.Thread(target=refresh_cpolar_url, daemon=True)
        thread.start()
        print(f"[QRCode] cpolar域名刷新线程已启动，将每5分钟自动刷新一次")
    
    @staticmethod
    def get_local_ip():
        """
        获取本机在局域网中的IP地址
        
        Returns:
            str: 局域网IP地址
        """
        try:
            # 创建一个UDP socket，不实际连接
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接到一个公共的IP地址，这会让系统分配一个本地IP地址
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
        
        Args:
            url: 二维码指向的URL
            output_path: 图片保存路径
            
        Returns:
            str: 生成的二维码图片的Base64编码
        """
        try:
            # 创建二维码实例
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # 添加数据
            qr.add_data(url)
            qr.make(fit=True)
            
            # 创建图片
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 转换为Base64编码
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
        
        Args:
            port: 服务器端口
            
        Returns:
            dict: 包含访问信息的字典
        """
        local_ip = cls.get_local_ip()
        
        # 生成二维码和访问信息
        mobile_url = None
        local_mobile_url = f"http://{local_ip}:{port}/mobile"
        cpolar_status = "available" if cls.current_cpolar_url else "unavailable"
        
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
            "hotspot_guide": "电脑开启热点 → 手机连接 → 电脑获取热点IP → 手机访问该IP:5000/mobile"
        }
        
        # 使用动态刷新的cpolar公网地址（如果可用）
        cpolar_url = cls.current_cpolar_url
        if cpolar_url:
            # 确保cpolar_url格式正确
            if not cpolar_url.startswith(('http://', 'https://')):
                cpolar_url = f"http://{cpolar_url}"
            mobile_url = f"{cpolar_url}/mobile"
        else:
            # 如果没有cpolar地址，使用本地地址
            mobile_url = local_mobile_url
        
        # 生成二维码
        qr_code = cls.generate_qr_code(mobile_url)
        
        return {
            'local_ip': local_ip,
            'port': port,
            'mobile_url': mobile_url,  # 使用cpolar公网地址（如果可用）
            'local_mobile_url': local_mobile_url,  # 本地访问地址（备用）
            'cpolar_url': cpolar_url,  # cpolar公网地址
            'cpolar_status': cpolar_status,  # cpolar服务状态
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
            
            # 首先检查cpolar.exe的可能路径
            cpolar_path = None
            
            current_dir = pathlib.Path(__file__).parent.parent
            
            # 明确指定优先使用./cpolar/cpolar.exe路径
            if platform.system() == 'Windows':
                # Windows系统，优先使用./cpolar/cpolar.exe
                preferred_path = os.path.join(current_dir, 'cpolar', 'cpolar.exe')
                backup_path = os.path.join(current_dir, 'cpolar.exe')
            else:
                # Linux/Mac系统，优先使用./cpolar/cpolar
                preferred_path = os.path.join(current_dir, 'cpolar', 'cpolar')
                backup_path = os.path.join(current_dir, 'cpolar')
            
            # 先检查优先路径
            if os.path.exists(preferred_path):
                # 检查是否有执行权限
                if platform.system() == 'Windows' or os.access(preferred_path, os.X_OK):
                    cpolar_path = preferred_path
            # 如果优先路径不存在，检查备份路径
            elif os.path.exists(backup_path):
                if platform.system() == 'Windows' or os.access(backup_path, os.X_OK):
                    cpolar_path = backup_path
            
            # 如果找到cpolar_path，使用它；否则尝试使用环境变量中的cpolar命令
            if cpolar_path:
                cmd = [cpolar_path, 'restart']
            else:
                cmd = ['cpolar', 'restart']
            
            # 执行重启命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            print(f"[QRCode] 重启cpolar服务结果: {result.stdout.strip()}")
            if result.stderr:
                print(f"[QRCode] 重启cpolar服务错误: {result.stderr.strip()}")
            
            # 清除当前cpolar_url，触发重新获取
            cls.current_cpolar_url = None
            
            # 立即刷新一次cpolar域名
            cls.refresh_cpolar_url_once()
            
        except subprocess.TimeoutExpired:
            print("[QRCode] 重启cpolar服务超时")
        except Exception as e:
            print(f"[QRCode] 重启cpolar服务失败: {str(e)}")
    
    @classmethod
    def refresh_cpolar_url_once(cls):
        """
        立即刷新一次cpolar域名
        """
        try:
            # 尝试获取最新的cpolar隧道信息
            response = requests.get(cls.CPOLAR_API, timeout=5)
            
            if response.status_code == 200:
                # 先尝试直接解析JSON
                try:
                    tunnels_data = response.json()
                    
                    # 处理不同的响应格式
                    tunnel_list = []
                    if isinstance(tunnels_data, dict):
                        if 'tunnels' in tunnels_data:
                            # 格式1: {"tunnels": [...], ...}
                            tunnel_list = tunnels_data['tunnels']
                        elif 'url' in tunnels_data and 'proto' in tunnels_data:
                            # 格式2: 直接返回单个隧道信息
                            tunnel_list = [tunnels_data]
                    elif isinstance(tunnels_data, list):
                        # 格式3: 直接返回隧道列表
                        tunnel_list = tunnels_data
                    
                    # 找到HTTP隧道
                    for tunnel in tunnel_list:
                        if isinstance(tunnel, dict):
                            proto = tunnel.get('proto', '')
                            url = tunnel.get('url', '')
                            if proto == 'http' and url:
                                # 提取完整URL（包括http://）
                                cls.current_cpolar_url = url
                                print(f"[QRCode] 已更新cpolar域名: {cls.current_cpolar_url}")
                                break
                except json.JSONDecodeError as e:
                    # 尝试使用正则表达式直接从响应中提取URL
                    import re
                    url_pattern = r'http://[a-zA-Z0-9.-]+\.cpolar\.io'
                    match = re.search(url_pattern, response.text)
                    if match:
                        url = match.group(0)
                        cls.current_cpolar_url = url
                        print(f"[QRCode] 使用正则表达式提取到cpolar域名: {url}")
        except requests.exceptions.ConnectionError:
            print(f"[QRCode] 无法连接到cpolar API，可能服务未启动")
        except Exception as e:
            print(f"[QRCode] 刷新cpolar域名失败: {str(e)[:50]}...")
