import requests
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any


class SessionManager:
    """
    会话管理器，用于统一管理用户与北航系统的会话状态
    """
    
    def __init__(self):
        # 会话存储，key为用户标识，value为会话对象
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # 会话超时时间，默认30分钟
        self.session_timeout = timedelta(minutes=30)
        # 默认请求头
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def generate_user_key(self, user_id: str, buaa_id: str) -> str:
        """
        生成用户唯一标识
        :param user_id: 用户ID
        :param buaa_id: 北航学号
        :return: 用户唯一标识
        """
        return hashlib.md5(f"{user_id}_{buaa_id}".encode()).hexdigest()
    
    def create_session(self, user_id: str, buaa_id: str) -> str:
        """
        创建新会话
        :param user_id: 用户ID
        :param buaa_id: 北航学号
        :return: 会话ID
        """
        user_key = self.generate_user_key(user_id, buaa_id)
        
        # 创建新的requests会话
        session = requests.Session()
        session.headers.update(self.default_headers)
        
        # 存储会话信息
        self.sessions[user_key] = {
            'session': session,
            'created_at': datetime.now(),
            'last_used': datetime.now(),
            'status': 'active',  # active, expired, invalid
            'user_id': user_id,
            'buaa_id': buaa_id
        }
        
        return user_key
    
    def get_session(self, user_key: str) -> Optional[requests.Session]:
        """
        获取会话对象
        :param user_key: 用户唯一标识
        :return: 会话对象，如果会话不存在或已过期则返回None
        """
        if user_key not in self.sessions:
            return None
        
        session_info = self.sessions[user_key]
        
        # 检查会话是否过期
        if datetime.now() - session_info['last_used'] > self.session_timeout:
            # 会话已过期，销毁会话
            self.destroy_session(user_key)
            return None
        
        # 更新最后使用时间
        session_info['last_used'] = datetime.now()
        
        return session_info['session']
    
    def update_session_cookies(self, user_key: str, cookies: Dict[str, str]) -> bool:
        """
        更新会话Cookie
        :param user_key: 用户唯一标识
        :param cookies: Cookie字典
        :return: 更新是否成功
        """
        session = self.get_session(user_key)
        if session:
            session.cookies.update(cookies)
            return True
        return False
    
    def get_session_cookies(self, user_key: str) -> Optional[Dict[str, str]]:
        """
        获取会话Cookie
        :param user_key: 用户唯一标识
        :return: Cookie字典，如果会话不存在或已过期则返回None
        """
        session = self.get_session(user_key)
        if session:
            return session.cookies.get_dict()
        return None
    
    def destroy_session(self, user_key: str) -> bool:
        """
        销毁会话
        :param user_key: 用户唯一标识
        :return: 销毁是否成功
        """
        if user_key in self.sessions:
            del self.sessions[user_key]
            return True
        return False
    
    def check_session_health(self, user_key: str, test_url: str) -> bool:
        """
        检查会话健康状态
        :param user_key: 用户唯一标识
        :param test_url: 用于测试会话的URL
        :return: 会话是否健康
        """
        session = self.get_session(user_key)
        if not session:
            return False
        
        try:
            # 尝试访问测试URL，不允许重定向
            response = session.get(test_url, allow_redirects=False, timeout=10)
            
            # 如果返回200，则会话健康
            if response.status_code == 200:
                return True
            # 如果返回302重定向到登录页面，则会话需要重新认证
            elif response.status_code == 302:
                location = response.headers.get('Location', '')
                if 'sso.buaa.edu.cn' in location:
                    return False
            
            return True
        except requests.exceptions.RequestException:
            return False
    
    def clear_expired_sessions(self) -> int:
        """
        清理过期会话
        :return: 清理的会话数量
        """
        expired_keys = []
        for user_key, session_info in self.sessions.items():
            if datetime.now() - session_info['last_used'] > self.session_timeout:
                expired_keys.append(user_key)
        
        for user_key in expired_keys:
            self.destroy_session(user_key)
        
        return len(expired_keys)
    
    def get_session_status(self, user_key: str) -> Dict[str, Any]:
        """
        获取会话状态
        :param user_key: 用户唯一标识
        :return: 会话状态信息
        """
        if user_key not in self.sessions:
            return {
                'exists': False,
                'status': 'not_found',
                'created_at': None,
                'last_used': None
            }
        
        session_info = self.sessions[user_key]
        is_expired = datetime.now() - session_info['last_used'] > self.session_timeout
        
        return {
            'exists': True,
            'status': 'expired' if is_expired else session_info['status'],
            'created_at': session_info['created_at'].isoformat(),
            'last_used': session_info['last_used'].isoformat()
        }


# 创建全局会话管理器实例
global_session_manager = SessionManager()