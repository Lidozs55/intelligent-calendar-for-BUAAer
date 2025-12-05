import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """Flask应用配置"""
    # 密钥，用于会话管理和加密
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # 数据库配置 - 使用更可靠的路径
    if hasattr(sys, '_MEIPASS'):
        # 打包后的运行环境
        basedir = os.path.dirname(sys.executable)
    else:
        # 开发环境
        basedir = os.path.abspath(os.path.dirname(__file__))
    
    # 确保instance目录存在
    instance_dir = os.path.join(basedir, "instance")
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    # 数据库URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(instance_dir, "app.db")}'
    
    # 北航API配置
    BUAA_API_BASE_URL = 'https://byxt.buaa.edu.cn/jwapp/sys'
    
    # 大语言模型API配置
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_API_URL = os.environ.get('LLM_API_URL') or 'https://api.qwen.com/v1/chat/completions'
    
    # 提醒配置
    REMINDER_INTERVAL = 60  # 检查提醒的间隔时间（秒）
