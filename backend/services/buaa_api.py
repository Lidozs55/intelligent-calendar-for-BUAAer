import requests
import time
import re
from config import Config
from typing import Dict, Optional, Any, Tuple
from .session_manager import global_session_manager


class BUAAAPIError(Exception):
    """北航API错误基类"""
    pass


class NetworkError(BUAAAPIError):
    """网络错误"""
    pass


class AuthenticationError(BUAAAPIError):
    """认证错误"""
    pass


class DataError(BUAAAPIError):
    """数据错误"""
    pass


class SSOLoginHandler:
    """
    SSO登录处理器，负责处理北航SSO登录流程
    """
    
    def __init__(self):
        self.sso_login_url = 'https://sso.buaa.edu.cn/login'
        # 修改正则表达式，去掉对type属性的限制，只匹配name="execution"的input元素
        self.execution_pattern = r'<input\s+[^>]*?name=[\'"]execution[\'"]*?[^>]*?value=[\'"](.*?)[\'"]'
        self.target_api = 'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/api/home/teachingSchedule/detail.do?rq=2025-12-01&lxdm=student'
    
    def extract_execution(self, login_page_html: str) -> str:
        """
        从登录页面提取execution参数
        :param login_page_html: 登录页面HTML内容
        :return: execution参数值
        :raises AuthenticationError: 无法提取execution参数时抛出
        """
        execution_match = re.search(self.execution_pattern, login_page_html, re.IGNORECASE | re.DOTALL)
        if not execution_match:
            raise AuthenticationError("无法从登录页面获取execution参数")
        
        execution = execution_match.group(1)
        return execution
    
    def perform_sso_login(self, session: requests.Session, username: str, password: str) -> Dict[str, str]:
        """
        执行完整的SSO登录流程
        :param session: requests会话对象
        :param username: 北航学号
        :param password: 北航密码
        :return: 登录成功后的Cookie字典
        :raises AuthenticationError: 登录失败时抛出
        :raises NetworkError: 网络错误时抛出
        """
        try:
            # 第一步：触发重定向到SSO
            initial_response = session.get(self.target_api, allow_redirects=False, timeout=10)
            
            if initial_response.status_code == 302:
                sso_url = initial_response.headers['Location']
                
                # 第二步：获取SSO登录页面并提取参数
                sso_page_response = session.get(sso_url, timeout=10)
                sso_page_response.raise_for_status()
                
                execution = self.extract_execution(sso_page_response.text)
                
                # 第三步：提交登录表单，允许重定向跟随完整回调链
                login_data = {
                    'username': username,
                    'password': password,
                    'execution': execution,
                    '_eventId': 'submit',
                    'geolocation': ''
                }
                
                # 发送POST请求，不允许重定向，以便查看详细响应
                login_response = session.post(
                    sso_url,
                    data=login_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    allow_redirects=False,
                    timeout=15
                )
                
                # 检查响应状态码
                login_response.raise_for_status()
                
                # 如果是重定向，继续跟随
                if login_response.status_code == 302:
                    redirect_url = login_response.headers.get('Location')
                    
                    # 跟随重定向
                    follow_response = session.get(redirect_url, allow_redirects=True, timeout=15)
                    follow_response.raise_for_status()
                
                # 第四步：验证登录成功，检查核心认证Cookie
                try:
                    cookies = session.cookies.get_dict()
                except Exception as e:
                    # 处理多个同名cookie的情况，手动构建Cookie字典
                    cookies = {}
                    for c in session.cookies:
                        # 如果已经有这个Cookie，跳过（只保留第一个）
                        if c.name not in cookies:
                            cookies[c.name] = c.value
                
                # 验证是否获得核心认证Cookie
                if 'CASTGC' in cookies or '_WEU' in cookies:
                    return cookies
                else:
                    raise AuthenticationError("登录失败，未获得核心认证Cookie")
            else:
                raise AuthenticationError(f"初始请求未返回302重定向，状态码: {initial_response.status_code}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"网络请求失败: {str(e)}")
        except KeyError as e:
            raise AuthenticationError(f"登录流程异常，缺少关键参数: {str(e)}")


class BUAAAPIClient:
    """
    北航API客户端，用于调用北航系统的各种API
    """
    
    def __init__(self):
        self.api_base_url = Config.BUAA_API_BASE_URL
        self.sso_handler = SSOLoginHandler()
        self.test_url = f"{self.api_base_url}/homeapp/api/home/teachingSchedule/detail.do?rq=2025-11-28&lxdm=student"
    
    def _build_headers(self) -> Dict[str, str]:
        """
        构建请求头
        :return: 请求头字典
        """
        return {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'max-age=0',
            'fetch-api': 'true',
            'priority': 'u=1, i',
            'referrer': 'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/home/index.html',
            'sec-ch-ua': '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }
    
    def _handle_api_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理API响应
        :param response: API响应对象
        :return: 处理后的响应数据
        :raises DataError: 数据格式错误时抛出
        """
        if response.status_code == 200:
            try:
                data = response.json()
                
                # 处理北航API返回的格式：{"datas":[],"code":"0","msg":null}
                if isinstance(data, dict) and 'datas' in data and 'code' in data:
                    # 输出response的datas字段（暂时注释）
                    # print(f"API响应datas字段: {data.get('datas')}")
                    
                    if data.get('code') == '0':
                        return {
                            'status': 'success',
                            'data': data.get('datas', []),
                            'raw_data': data
                        }
                    else:
                        raise DataError(f'API返回错误: {data.get("msg", "未知错误")}')
                else:
                    raise DataError(f'无效的API返回格式')
            except ValueError:
                raise DataError(f'无法解析API响应')
        elif response.status_code == 302:
            # 需要登录
            login_url = response.headers.get('Location', '')
            return {
                'status': 'need_login',
                'login_url': login_url
            }
        else:
            raise NetworkError(f'HTTP错误: {response.status_code} {response.reason}')
    
    def check_login_status(self, user_key: str) -> Tuple[bool, Optional[str]]:
        """
        检查登录状态
        :param user_key: 用户唯一标识
        :return: (是否已登录, 登录URL)
        """
        session = global_session_manager.get_session(user_key)
        if not session:
            return False, None
        
        try:
            response = session.get(self.test_url, allow_redirects=False, timeout=10)
            
            if response.status_code == 200:
                # 尝试解析响应，确认是否为有效的API响应
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'code' in data and data.get('code') == '0':
                        return True, None
                except ValueError:
                    pass
            
            # 检查是否需要重定向登录
            if response.status_code == 302:
                login_url = response.headers.get('Location', '')
                return False, login_url
            
            return False, None
        except requests.exceptions.RequestException:
            return False, None
    
    def direct_api_call(self, session: requests.Session, api_url: str) -> Dict[str, Any]:
        """
        直接调用API
        :param session: requests会话对象
        :param api_url: API URL
        :return: API响应数据
        :raises NetworkError: 网络错误时抛出
        :raises DataError: 数据格式错误时抛出
        """
        try:
            # 第一次请求
            response = session.get(api_url, allow_redirects=False, timeout=10)
            
            # 检查是否是302重定向
            if response.status_code == 302:
                # 使用保存的cookie再次请求原API URL
                retry_response = session.get(api_url, allow_redirects=False, timeout=10)
                
                # 处理重试响应
                return self._handle_api_response(retry_response)
            
            # 第一次请求不是302，直接处理响应
            return self._handle_api_response(response)
        except requests.exceptions.RequestException as e:
            raise NetworkError(f'API调用失败: {str(e)}')
    
    def _calculate_term_code(self, date: str) -> str:
        """
        计算学期代码
        :param date: 查询日期，格式为YYYY-MM-DD
        :return: 学期代码，格式为{A}-{A+1}-1或{A}-{A+1}-2
        """
        from datetime import datetime
        
        # 解析日期
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month
        
        # 计算学期代码
        if 8 <= month <= 12:
            # A年8月至A+1年2月：{A}-{A+1}-1
            term_code = f"{year}-{year+1}-1"
        elif 1 <= month <= 2:
            # A年8月至A+1年2月：{A}-{A+1}-1
            term_code = f"{year-1}-{year}-1"
        else:
            # 其他月份：{A}-{A+1}-2
            term_code = f"{year}-{year+1}-2"
        
        return term_code
    
    def fetch_exam_schedule(self, user_key: str, date: str) -> Dict[str, Any]:
        """
        获取考试信息
        :param user_key: 用户唯一标识
        :param date: 查询日期，用于计算学期代码
        :return: 考试信息数据
        """
        session = global_session_manager.get_session(user_key)
        if not session:
            return {
                'need_login': True,
                'message': '会话已过期或不存在'
            }
        
        # 计算学期代码
        term_code = self._calculate_term_code(date)
        
        api_url = f"{self.api_base_url}/homeapp/api/home/student/exams.do?termCode={term_code}"
        
        try:
            # 设置必要的头信息
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
                'Referer': 'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/home/index.html',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            # 打印考试API请求URL
            print(f"请求考试信息API: {api_url}")
            
            result = self.direct_api_call(session, api_url)
            
            # 打印考试API响应结果
            print(f"考试API响应结果: {result}")
            
            if result['status'] == 'success':
                # 打印获取到的考试数据
                print(f"获取到的考试数据: {result['data']}")
                return {
                    'need_login': False,
                    'data': {
                        'exams': result['data']
                    }
                }
            elif result['status'] == 'need_login':
                return {
                    'need_login': True,
                    'login_url': result['login_url']
                }
        except NetworkError as e:
            return {
                'need_login': False,
                'error': f'网络错误: {str(e)}',
                'cookies': session.cookies.get_dict()
            }
        except DataError as e:
            return {
                'need_login': False,
                'error': f'数据错误: {str(e)}',
                'cookies': session.cookies.get_dict()
            }
        except Exception as e:
            return {
                'need_login': False,
                'error': f'未知错误: {str(e)}',
                'cookies': session.cookies.get_dict()
            }
        
        return {
            'need_login': False,
            'error': '未知错误',
            'cookies': session.cookies.get_dict()
        }
    
    def fetch_course_schedule(self, user_key: str, date: str) -> Dict[str, Any]:
        """
        获取课程表
        :param user_key: 用户唯一标识
        :param date: 查询日期
        :return: 课程表数据
        """
        session = global_session_manager.get_session(user_key)
        if not session:
            return {
                'need_login': True,
                'message': '会话已过期或不存在'
            }
        
        api_url = f"{self.api_base_url}/homeapp/api/home/teachingSchedule/detail.do?rq={date}&lxdm=student"
        
        try:
            # 设置必要的头信息
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
                'Referer': 'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/home/index.html',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            # 获取课程表数据
            course_result = self.direct_api_call(session, api_url)
            
            if course_result['status'] == 'success':
                # 构建返回结果，兼容旧的返回格式
                result = {
                    'need_login': False,
                    'data': {
                        # 只返回兼容旧格式的data字段，避免前端直接使用courses和exams字段
                        'data': course_result['data']
                    }
                }
                
                return result
            elif course_result['status'] == 'need_login':
                return {
                    'need_login': True,
                    'login_url': course_result['login_url']
                }
        except NetworkError as e:
            return {
                'need_login': False,
                'error': f'网络错误: {str(e)}',
                'cookies': session.cookies.get_dict()
            }
        except DataError as e:
            return {
                'need_login': False,
                'error': f'数据错误: {str(e)}',
                'cookies': session.cookies.get_dict()
            }
        except Exception as e:
            # print(f"获取课程表时发生未知错误: {str(e)}")
            # import traceback
            # traceback.print_exc()
            return {
                'need_login': False,
                'error': f'未知错误: {str(e)}',
                'cookies': session.cookies.get_dict()
            }
        
        return {
            'need_login': False,
            'error': '未知错误',
            'cookies': session.cookies.get_dict()
        }
    
    def test_cookie_validity(self, session: requests.Session) -> bool:
        """
        测试Cookie是否真的有效
        :param session: requests会话对象
        :return: Cookie是否有效的布尔值
        """
        test_urls = [
            "https://byxt.buaa.edu.cn/jwapp/sys/homeapp/api/home/teachingSchedule/detail.do?rq=2025-12-01&lxdm=student",
            "https://byxt.buaa.edu.cn/jwapp/sys/homeapp/home/index.html"
        ]
        
        is_valid = False
        for test_url in test_urls:
            try:
                test_response = session.get(test_url, timeout=10)
                
                if test_response.status_code == 200:
                    # 检查响应内容
                    if '我的首页' in test_response.text or '个人中心' in test_response.text:
                        is_valid = True
                    elif test_response.text.strip() and len(test_response.text) > 100:
                        is_valid = True
            except Exception:
                pass
        
        return is_valid
    
    def test_multiple_dates(self, session: requests.Session) -> Dict[str, Any]:
        """
        测试多个日期的课程数据
        :param session: requests会话对象
        :return: 不同日期的课程数据结果
        """
        test_dates = [
            '2025-11-29',  # 当前日期
            '2025-11-28',  # 昨天
            '2025-12-01',  # 未来日期
            '2025-11-27'   # 前天
        ]
        
        results = {}
        for test_date in test_dates:
            test_url = f"https://byxt.buaa.edu.cn/jwapp/sys/homeapp/api/home/teachingSchedule/detail.do?rq={test_date}&lxdm=student"
            try:
                test_response = session.get(test_url, timeout=10)
                
                if test_response.status_code == 200:
                    try:
                        data = test_response.json()
                        datas = data.get('datas', [])
                        results[test_date] = {
                            'status_code': test_response.status_code,
                            'data_count': len(datas),
                            'data': datas,
                            'code': data.get('code'),
                            'msg': data.get('msg')
                        }
                    except Exception as e:
                        results[test_date] = {
                            'status_code': test_response.status_code,
                            'error': f"JSON解析错误: {e}",
                            'raw_text': test_response.text[:200]
                        }
                else:
                    results[test_date] = {
                        'status_code': test_response.status_code,
                        'error': f"HTTP错误: {test_response.status_code}"
                    }
            except Exception as e:
                results[test_date] = {
                    'error': f"请求失败: {e}"
                }
        
        return results
    
    def process_login_callback(self, session: requests.Session, callback_url: str) -> Dict[str, str]:
        """
        处理登录回调
        :param session: requests会话对象
        :param callback_url: 回调URL
        :return: 更新后的Cookie字典
        :raises NetworkError: 网络错误时抛出
        """
        try:
            # 访问回调URL，让byxt系统设置会话Cookie
            callback_response = session.get(callback_url, allow_redirects=True, timeout=10)
            callback_response.raise_for_status()
            return session.cookies.get_dict()
        except requests.exceptions.RequestException as e:
            raise NetworkError(f'处理登录回调失败: {str(e)}')


class SPOCAPIClient:
    """
    北航SPOC API客户端，用于调用北航SPOC系统的各种API
    """
    
    def __init__(self):
        # 导入必要的加密模块
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad, unpad
        import base64
        import json
        
        # AES加密配置
        self.AES_KEY = b'inco12345678ocni'  # 16 bytes
        self.AES_IV = b'ocni12345678inco'   # 16 bytes
        self.AES_MODE = AES.MODE_CBC
        
        # SPOC相关URL
        self.spoc_base_url = 'https://spoc.buaa.edu.cn'
        self.spoc_init_url = f'{self.spoc_base_url}/spocnewht/jxkj/queryJxkjData'
        self.spoc_query_one_url = f'{self.spoc_base_url}/spocnewht/inco/ht/queryOne'
        self.spoc_query_list_url = f'{self.spoc_base_url}/spocnewht/inco/ht/queryListByPage'
        self.spoc_login_check_url = f'{self.spoc_base_url}/spocnew/common/zycskzy'
        
        # 保存导入的模块，方便后续方法使用
        self.AES = AES
        self.pad = pad
        self.unpad = unpad
        self.base64 = base64
        self.json = json
    
    def aes_encrypt(self, data_dict: Dict[str, Any]) -> str:
        """
        AES-CBC加密数据字典，返回Base64字符串
        :param data_dict: 要加密的数据字典
        :return: 加密后的Base64字符串
        """
        # 将字典转换为JSON字符串
        data_str = self.json.dumps(data_dict, separators=(',', ':'), ensure_ascii=False)
        
        # 创建AES加密器
        cipher = self.AES.new(self.AES_KEY, self.AES_MODE, self.AES_IV)
        
        # 加密并填充
        encrypted_data = cipher.encrypt(self.pad(data_str.encode('utf-8'), self.AES.block_size, style='pkcs7'))
        
        # 转换为Base64字符串
        return self.base64.b64encode(encrypted_data).decode('utf-8')
    
    def aes_decrypt(self, base64_str: str) -> Dict[str, Any]:
        """
        AES-CBC解密Base64字符串，返回数据字典
        :param base64_str: 加密后的Base64字符串
        :return: 解密后的数据字典
        """
        # 处理空字符串情况
        if not base64_str:
            print("[LOG] 尝试解密空字符串，返回空字典")
            return {}
        
        try:
            # 解码Base64字符串
            encrypted_data = self.base64.b64decode(base64_str)
            
            # 处理空的加密数据
            if not encrypted_data:
                print("[LOG] 尝试解密空的加密数据，返回空字典")
                return {}
            
            # 创建AES解密器
            cipher = self.AES.new(self.AES_KEY, self.AES_MODE, self.AES_IV)
            
            # 解密
            decrypted_bytes = cipher.decrypt(encrypted_data)
            
            # 去除填充
            try:
                decrypted_data = self.unpad(decrypted_bytes, self.AES.block_size, style='pkcs7')
            except ValueError as e:
                print(f"[LOG] 去除填充失败，尝试直接使用解密数据: {str(e)}")
                # 如果去除填充失败，尝试直接使用解密数据
                decrypted_data = decrypted_bytes
            
            # 转换为JSON字典
            return self.json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            print(f"[LOG] AES解密失败: {str(e)}")
            return {}
    
    def login_spoc(self, username: str, password: str) -> Dict[str, Any]:
        """
        SSO登录SPOC系统，完全按照新的流程实现
        :param username: 北航学号
        :param password: 北航密码
        :return: 登录结果，包含session和初始化参数
        """
        # 创建会话
        session = requests.Session()
        
        # 设置通用请求头
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'x-requested-with': 'XMLHttpRequest',
            'rolecode': '01',  # 默认角色代码
        })
        
        # 1. 检查是否已经登录
        try:
            print("[LOG] 检查SPOC登录状态")
            login_check_response = session.get(self.spoc_login_check_url, timeout=10, allow_redirects=False)
            
            # 如果返回302，说明需要登录
            if login_check_response.status_code == 302 or login_check_response.status_code == 404:
                print("[LOG] 需要执行SSO登录")
                
                # 2. 执行SSO登录
                # 构造SSO登录URL - 使用正确的service URL（jxkj2）
                sso_login_url = f"https://sso.buaa.edu.cn/login?service=https%3A%2F%2Fspoc.buaa.edu.cn%2Fspocnewht%2FcasLogin"
                print(f"[LOG] 访问SSO登录URL: {sso_login_url}")
                
                # 获取SSO登录页面
                sso_page_response = session.get(sso_login_url, timeout=10)
                sso_page_response.raise_for_status()
                
                # 提取execution参数
                execution_pattern = r'<input\s+[^>]*?name=[\'\"]execution[\'\"]*?[^>]*?value=[\'\"]?([^\'\">\s]+)[\'\"]?'
                execution_match = re.search(execution_pattern, sso_page_response.text, re.IGNORECASE | re.DOTALL)
                
                if not execution_match:
                    print("[LOG] 无法提取execution参数，登录失败")
                    raise AuthenticationError("无法提取SSO登录参数")
                
                execution = execution_match.group(1)
                print(f"[LOG] 提取到execution参数: {execution}")
                
                # 提交登录表单，不允许重定向，以便获取包含ticket的302响应
                login_data = {
                    'username': username,
                    'password': password,
                    'execution': execution,
                    '_eventId': 'submit',
                    'geolocation': ''
                }
                
                print(f"[LOG] 提交登录表单，用户: {username}")
                
                # 发送POST请求，允许自动重定向，简化流程
                print(f"[LOG] 发送登录请求，允许自动重定向")
                login_response = session.post(
                    sso_login_url,
                    data=login_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    allow_redirects=True,
                    timeout=30
                )
                
                print(f"[LOG] 登录请求完成，最终状态: {login_response.status_code}")
                print(f"[LOG] 登录请求最终URL: {login_response.url}")
                
                # 即使返回404，也继续处理，因为浏览器访问时会有后续重定向
                print("[LOG] 登录请求完成，开始后续处理")
                # 打印当前session的cookies和headers，确保获取完整
                print(f"[LOG] 当前session的cookies: {session.cookies.get_dict()}")
                print(f"[LOG] 当前session的headers: {dict(session.headers)}")
                
                # 尝试从响应中提取token（无论状态码如何）
                token_match = re.search(r'token\s*=\s*[\'"](Inco-[\w-]+)[\'"]', login_response.text)
                if token_match:
                    final_token = token_match.group(1)
                    session.headers.update({'token': final_token})
                    print(f"[LOG] 从响应中提取并设置Token: {final_token[:20]}...")
                
                # 从最终URL中提取SPOC token和refreshToken（关键步骤）
                import urllib.parse
                parsed_url = urllib.parse.urlsplit(login_response.url)
                query_params = dict(urllib.parse.parse_qsl(parsed_url.query))
                
                spoc_token = query_params.get('token')
                refresh_token = query_params.get('refreshToken')
                
                if spoc_token and refresh_token:
                    # 将提取到的token和refreshToken都设置到session headers中（关键修正）
                    session.headers.update({
                        'token': spoc_token,
                        'refreshToken': refresh_token
                    })
                    print(f"[LOG] ✅ 从URL中提取并设置SPOC Token: {spoc_token[:20]}...")
                    print(f"[LOG] ✅ 从URL中提取并设置refreshToken: {refresh_token[:20]}...")
                
                print("[LOG] 开始手动追踪重定向链，捕获所有Cookie")
                
                # 手动追踪重定向链，确保捕获所有Set-Cookie
                current_url = login_response.url
                max_redirects = 10
                redirect_count = 0
                
                while redirect_count < max_redirects:
                    print(f"[LOG] 手动追踪重定向 #{redirect_count+1}: {current_url}")
                    
                    # 禁止自动重定向，手动处理
                    redirect_response = session.get(
                        current_url,
                        allow_redirects=False,
                        timeout=15
                    )
                    
                    print(f"[LOG] 重定向响应状态码: {redirect_response.status_code}")
                    
                    # 检查是否有Set-Cookie头部
                    if 'Set-Cookie' in redirect_response.headers:
                        print(f"[LOG] ✅ 捕获到新的Cookie: {redirect_response.headers['Set-Cookie']}")
                    
                    # 检查状态码
                    if redirect_response.status_code == 200:
                        print(f"[LOG] ✅ 到达最终页面，重定向链追踪完成")
                        break
                    elif redirect_response.status_code in (301, 302, 307, 308):
                        # 获取下一个重定向URL
                        next_url = redirect_response.headers.get('Location')
                        if not next_url:
                            print(f"[LOG] ❌ 重定向链中断，无Location头部")
                            break
                        
                        print(f"[LOG] -> 重定向到: {next_url}")
                        current_url = next_url
                        redirect_count += 1
                    else:
                        print(f"[LOG] ❌ 重定向链中断，未知状态码: {redirect_response.status_code}")
                        break
                
                if redirect_count >= max_redirects:
                    print(f"[LOG] ⚠️  重定向次数超过上限({max_redirects})，可能陷入循环")
                
                print("[LOG] SSO登录流程完成，继续后续操作")
                print(f"[LOG] 当前session的headers: {dict(session.headers)}")
                print(f"[LOG] 当前session的完整cookies: {session.cookies.get_dict()}")
            else:
                print("[LOG] 已经登录SPOC系统")
        except Exception as e:
            print(f"[LOG] SSO登录流程异常: {str(e)}")
            raise AuthenticationError(f"SSO登录失败: {str(e)}")
        
        # 3. 获取初始化数据和initData_props
        try:
            print(f"[LOG] 获取初始化数据: {self.spoc_init_url}")
            
            # 先获取一下SPOC首页，确保session有效
            print(f"[LOG] 访问SPOC首页: {self.spoc_base_url}/spocnew/jxkj2")
            home_response = session.get(f"{self.spoc_base_url}/spocnew/jxkj2", timeout=10, allow_redirects=True)
            print(f"[LOG] SPOC首页响应状态: {home_response.status_code}")
            print(f"[LOG] SPOC首页最终URL: {home_response.url}")
            
            # 获取当前session的cookies
            print(f"[LOG] 当前session的cookies: {session.cookies.get_dict()}")
            
            # 获取当前session的headers
            print(f"[LOG] 当前session的headers: {dict(session.headers)}")
            
            # 尝试获取初始化数据
            print(f"[LOG] 发送初始化数据请求")
            init_response = session.get(
                self.spoc_init_url,
                headers={
                    'x-requested-with': 'XMLHttpRequest',
                    'Referer': home_response.url,
                },
                timeout=15
            )
            
            print(f"[LOG] 初始化数据请求状态码: {init_response.status_code}")
            print(f"[LOG] 初始化数据请求响应头: {dict(init_response.headers)}")
            print(f"[LOG] 初始化数据请求响应内容: {init_response.text}")
            
            init_response.raise_for_status()
            
            try:
                init_data = init_response.json()
                print(f"[LOG] 初始化数据响应: {init_data}")
            except ValueError as json_error:
                print(f"[LOG] 解析初始化数据JSON失败: {str(json_error)}")
                # 如果无法解析JSON，使用默认的initData_props
                import time
                init_data_props = f"{int(time.time()*1000)}d{time.time()}"
                referer = f'{self.spoc_base_url}/spocnew/zycskzy?initData_props={init_data_props}'
                return {
                    'session': session,
                    'init_data_props': init_data_props,
                    'referer': referer
                }
            
            # 检查响应是否包含token
            if 'token' in init_data.get('content', {}):
                token = init_data['content']['token']
                session.headers.update({'token': token})
                print(f"[LOG] 从响应中提取到token: {token}")
            
            # 提取initData_props
            tzlj = init_data.get('content', {}).get('zy', [{}])[0].get('tzlj', '')
            print(f"[LOG] tzlj字段: {tzlj}")
            
            if 'initData_props=' in tzlj:
                init_data_props = tzlj.split('initData_props=')[1]
                print(f"[LOG] 提取到initData_props: {init_data_props}")
            else:
                # 如果无法提取initData_props，尝试使用当前时间戳作为默认值
                import time
                init_data_props = f"{int(time.time()*1000)}d{time.time()}"
                print(f"[LOG] 无法从tzlj中提取initData_props，使用默认值: {init_data_props}")
                
            # 构造完整的Referer - 使用正确的/jxkj2路径
            referer = f'{self.spoc_base_url}/spocnew/jxkj2?initData_props={init_data_props}'
            print(f"[LOG] 构造Referer: {referer}")
            
            return {
                'session': session,
                'init_data_props': init_data_props,
                'referer': referer
            }
            
        except Exception as e:
            print(f"[LOG] 获取初始化数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 如果获取初始化数据失败，尝试使用默认的initData_props继续执行
            import time
            init_data_props = f"{int(time.time()*1000)}d{time.time()}"
            referer = f'{self.spoc_base_url}/spocnew/jxkj2?initData_props={init_data_props}'
            return {
                'session': session,
                'init_data_props': init_data_props,
                'referer': referer
            }
    
    def get_sqlid(self, session: requests.Session, init_data_props: str, referer: str) -> str:
        """
        获取最终的sqlid
        :param session: requests会话对象
        :param init_data_props: initData_props参数
        :param referer: Referer头部
        :return: 最终的sqlid
        """
        try:
            # 构造queryOne请求payload
            query_one_payload = {
                "sqlid": "402881b27e800d3d017e812d3345001c",
                "id": init_data_props
            }
            
            # 加密payload
            encrypted_param = self.aes_encrypt(query_one_payload)
            
            # 发送请求
            print(f"[LOG] 发送queryOne请求: {self.spoc_query_one_url}")
            # 合并session.headers和请求特定headers
            request_headers = dict(session.headers)
            request_headers.update({
                'Referer': referer,
                'Content-Type': 'application/json',
                'x-requested-with': 'XMLHttpRequest',
            })
            print(f"[LOG] queryOne请求headers: {request_headers}")
            print(f"[LOG] queryOne请求cookies: {session.cookies.get_dict()}")
            response = session.post(
                self.spoc_query_one_url,
                json={"param": encrypted_param},
                headers=request_headers,
                timeout=10
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            print(f"[LOG] queryOne响应: {response_data}")
            
            # 检查响应数据
            data_field = response_data.get('data', '')
            if not data_field:
                print(f"[LOG] queryOne响应的data字段为空: {data_field}")
                raise ValueError("queryOne响应的data字段为空")
            
            # 解密响应数据
            decrypted_data = self.aes_decrypt(data_field)
            print(f"[LOG] 解密后queryOne数据: {decrypted_data}")
            
            # 提取sqlid
            sqlid = decrypted_data.get('sqlId', '')
            print(f"[LOG] 提取到sqlid: {sqlid}")
            
            if not sqlid:
                # 如果无法从响应中提取sqlid，尝试使用默认值
                print(f"[LOG] 无法从queryOne响应中提取sqlid，使用默认值")
                # 默认的sqlid，可能需要根据实际情况调整
                return "402881b27e800d3d017e812d3345001d"
            
            return sqlid
            
        except ValueError as e:
            print(f"[LOG] 获取sqlid失败: {str(e)}")
            # 如果获取sqlid失败，尝试使用默认值
            return "402881b27e800d3d017e812d3345001d"
        except Exception as e:
            print(f"[LOG] 获取sqlid失败: {str(e)}")
            raise NetworkError(f"获取SPOC sqlid失败: {str(e)}")
    
    def get_homework_list(self, session: requests.Session, sqlid: str, referer: str) -> Dict[str, Any]:
        """
        获取作业列表
        :param session: requests会话对象
        :param sqlid: 动态获取的sqlid
        :param referer: Referer头部
        :return: 作业列表数据
        """
        try:
            # 构造queryListByPage请求payload
            query_list_payload = {
                "sqlid": sqlid,
                "pageNum": 1,
                "pageSize": 20,
                "xnxq": None,
                "kcid": None,
                "tjzt": "1",  # 1表示未完成
                "bt": None,
                "yzwz": None
            }
            
            # 加密payload
            encrypted_param = self.aes_encrypt(query_list_payload)
            
            # 发送请求
            print(f"[LOG] 发送queryListByPage请求: {self.spoc_query_list_url}")
            # 合并session.headers和请求特定headers
            request_headers = dict(session.headers)
            request_headers.update({
                'Referer': referer,
                'Content-Type': 'application/json',
                'x-requested-with': 'XMLHttpRequest',
            })
            print(f"[LOG] queryListByPage请求headers: {request_headers}")
            print(f"[LOG] queryListByPage请求cookies: {session.cookies.get_dict()}")
            response = session.post(
                self.spoc_query_list_url,
                json={"param": encrypted_param},
                headers=request_headers,
                timeout=10
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            print(f"[LOG] queryListByPage响应: {response_data}")
            
            # 解密响应数据
            decrypted_data = self.aes_decrypt(response_data.get('data', ''))
            print(f"[LOG] 解密后作业数据: {decrypted_data}")
            
            return decrypted_data
            
        except Exception as e:
            print(f"[LOG] 获取作业列表失败: {str(e)}")
            raise NetworkError(f"获取SPOC作业列表失败: {str(e)}")
    
    def fetch_all_homeworks(self, username: str, password: str) -> Dict[str, Any]:
        """
        完整的作业获取流程
        :param username: 北航学号
        :param password: 北航密码
        :return: 完整的作业列表
        """
        try:
            # 1. 登录并获取初始化参数
            login_result = self.login_spoc(username, password)
            session = login_result['session']
            init_data_props = login_result['init_data_props']
            referer = login_result['referer']
            
            # 2. 获取sqlid
            sqlid = self.get_sqlid(session, init_data_props, referer)
            
            # 3. 获取作业列表
            homework_data = self.get_homework_list(session, sqlid, referer)
            
            print(f"[LOG] 作业获取成功，共{homework_data.get('total', 0)}条作业")
            
            return homework_data
            
        except Exception as e:
            print(f"[LOG] 完整作业获取流程失败: {str(e)}")
            raise BUAAAPIError(f"获取SPOC作业失败: {str(e)}")


def parse_course_data(course_data, date=None):
    """
    解析课程数据，确保数据准确性
    :param course_data: 原始课程数据
    :param date: 查询日期，用于计算星期几
    :return: 解析后的课程数据列表
    """
    parsed_courses = []
    
    # 计算星期几（1-7，周一到周日）
    day_of_week = 1  # 默认周一
    if date:
        try:
            from datetime import datetime
            # 将日期字符串转换为datetime对象
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            # 获取星期几，Monday=0, Sunday=6，转换为1-7
            day_of_week = date_obj.weekday() + 1
        except ValueError:
            day_of_week = 1  # 日期格式错误，默认周一
    
    # 处理新的数据格式，直接从datas字段获取数据
    if isinstance(course_data, dict):
        # 检查是否是新的数据格式（直接包含datas字段）
        if 'datas' in course_data:
            raw_courses = course_data['datas']
        # 检查是否是旧的数据格式（包含data字段）
        elif 'data' in course_data:
            # 检查data字段是否包含courses字段（新的返回格式）
            if isinstance(course_data['data'], dict) and 'courses' in course_data['data']:
                raw_courses = course_data['data']['courses']
            else:
                raw_courses = course_data['data']
        # 检查是否直接包含courses字段（新的返回格式）
        elif 'courses' in course_data:
            raw_courses = course_data['courses']
        else:
            return parsed_courses
    elif isinstance(course_data, list):
        # 如果直接传入课程列表，直接使用
        raw_courses = course_data
    else:
        return parsed_courses
    
    for course_item in raw_courses:
        # 处理新的数据格式
        if isinstance(course_item, dict) and 'bizName' in course_item and 'time' in course_item and 'place' in course_item:
            # 新数据格式：bizName, time, place
            course_name = course_item['bizName'].strip() if course_item['bizName'] else ''
            course_time = course_item['time']
            classroom = course_item['place'].strip() if course_item['place'] else ''
            
            # 从bizName中提取教师信息（如果包含）
            teacher = '未知'
            if '(' in course_name and ')' in course_name:
                # 尝试从课程名称中提取教师信息，格式：课程名称(教师)
                teacher_match = re.search(r'\(([^)]+)\)', course_name)
                if teacher_match:
                    teacher = teacher_match.group(1).strip()
                    # 去除教师信息后的课程名称
                    course_name = course_name.replace(teacher_match.group(0), '').strip()
            
            # 解析时间格式 (HH:MM-HH:MM)
            try:
                start_time_str, end_time_str = course_time.split('-')
                start_hour, start_minute = map(int, start_time_str.split(':'))
                end_hour, end_minute = map(int, end_time_str.split(':'))
                
                if not (0 <= start_hour < 24 and 0 <= start_minute < 60 and 0 <= end_hour < 24 and 0 <= end_minute < 60):
                    continue
            except ValueError:
                continue
            
            # 构建解析后的课程数据（兼容旧格式）
            parsed_course = {
                'kcmc': course_name,
                'jsxm': teacher,  # 提取或默认教师信息
                'jxlh': classroom.split('楼')[0] + '楼' if '楼' in classroom else classroom,  # 提取教学楼
                'jash': classroom.split('楼')[-1] if '楼' in classroom else classroom,  # 提取教室号
                'kssj': start_time_str,
                'jssj': end_time_str,
                'xqj': day_of_week,  # 使用传入的日期计算星期几
                'zcd': '1-16',  # 新格式中没有周次信息，默认1-16周
                'original_date': date  # 保存原始日期，用于去重
            }
            
            parsed_courses.append(parsed_course)
        # 处理旧的数据格式
        elif isinstance(course_item, dict) and all(key in course_item for key in ['kcmc', 'jsxm', 'jxlh', 'jash', 'kssj', 'jssj', 'xqj', 'zcd']):
            # 解析星期几（1-7，周一到周日）
            day_of_week = int(course_item['xqj'])
            if day_of_week < 1 or day_of_week > 7:
                continue
            
            # 解析时间格式
            try:
                # 验证时间格式，确保是HH:MM格式
                start_hour, start_minute = map(int, course_item['kssj'].split(':'))
                end_hour, end_minute = map(int, course_item['jssj'].split(':'))
                
                if not (0 <= start_hour < 24 and 0 <= start_minute < 60 and 0 <= end_hour < 24 and 0 <= end_minute < 60):
                    continue
            except ValueError:
                continue
            
            # 验证周次范围
            week_range = course_item['zcd']
            if not week_range:
                continue
            
            # 构建解析后的课程数据
            parsed_course = {
                'kcmc': course_item['kcmc'].strip(),
                'jsxm': course_item['jsxm'].strip(),
                'jxlh': course_item['jxlh'].strip(),
                'jash': course_item['jash'].strip(),
                'kssj': course_item['kssj'],
                'jssj': course_item['jssj'],
                'xqj': day_of_week,
                'zcd': week_range.strip(),
                'original_date': date  # 保存原始日期，用于去重
            }
            
            parsed_courses.append(parsed_course)
    
    return parsed_courses

def parse_exam_data(exam_data):
    """
    解析考试数据
    :param exam_data: 原始考试数据
    :return: 解析后的考试数据列表
    """
    parsed_exams = []
    
    # 处理数据格式
    if isinstance(exam_data, dict):
        # 检查是否直接包含exams字段
        if 'exams' in exam_data:
            raw_exams = exam_data['exams']
        # 检查data字段是否包含exams字段
        elif 'data' in exam_data and isinstance(exam_data['data'], dict) and 'exams' in exam_data['data']:
            raw_exams = exam_data['data']['exams']
        # 检查是否直接是数据列表
        elif 'datas' in exam_data:
            raw_exams = exam_data['datas']
        else:
            return parsed_exams
    elif isinstance(exam_data, list):
        # 如果直接传入考试列表，直接使用
        raw_exams = exam_data
    else:
        return parsed_exams
    
    for exam_item in raw_exams:
        # 处理考试数据格式
        if isinstance(exam_item, dict):
            # 解析考试数据
            parsed_exam = {
                'kcmc': exam_item.get('kcmc', '').strip(),  # 课程名称
                'ksrq': exam_item.get('ksrq', '').strip(),  # 考试日期
                'kssj': exam_item.get('kssj', '').strip(),  # 开始时间
                'jssj': exam_item.get('jssj', '').strip(),  # 结束时间
                'ksdd': exam_item.get('ksdd', '').strip(),  # 考试地点
                'ksxz': exam_item.get('ksxz', '').strip(),  # 考试性质
                'kh': exam_item.get('kh', '').strip(),  # 课号
                'kch': exam_item.get('kch', '').strip(),  # 课程号
                'xf': exam_item.get('xf', '').strip(),  # 学分
                'cj': exam_item.get('cj', '').strip(),  # 成绩
                'khfsmc': exam_item.get('khfsmc', '').strip()  # 考核方式名称
            }
            
            parsed_exams.append(parsed_exam)
    
    return parsed_exams


# 创建全局BUAA API客户端实例
buaa_api_client = BUAAAPIClient()
sso_login_handler = SSOLoginHandler()
spoc_api_client = SPOCAPIClient()