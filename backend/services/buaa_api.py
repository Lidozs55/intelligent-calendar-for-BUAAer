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
                        # 兼容旧的返回格式
                        'data': course_result['data'],
                        # 新的返回格式
                        'courses': course_result['data'],
                        'exams': []
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
                'jsxm': '未知',  # 新格式中没有教师信息
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