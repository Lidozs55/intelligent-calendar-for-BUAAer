import os
import sys
from dotenv import load_dotenv

# 数据库配置 - 使用更可靠的路径
if hasattr(sys, '_MEIPASS'):
    # 打包后的运行环境
    basedir = os.path.dirname(sys.executable)
    # 在打包环境中，.env文件位于与exe相同的目录
    env_path = os.path.join(basedir, '.env')
else:
    # 开发环境
    basedir = os.path.abspath(os.path.dirname(__file__))
    # 在开发环境中，.env文件位于backend目录下
    env_path = os.path.join(basedir, '.env')

# 加载环境变量，指定.env文件路径
load_dotenv(env_path, override=True)

class Config:
    """Flask应用配置"""
    # 密钥，用于会话管理和加密
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # 确保instance目录存在
    instance_dir = os.path.join(basedir, "instance")
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    # 数据库URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(instance_dir, "app.db")}'
    
    # 大语言模型API配置 - 直接从环境变量获取，支持从文件加载和系统环境变量
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_API_URL = os.environ.get('LLM_API_URL') or 'https://api.qwen.com/v1/chat/completions'
    
    # 提醒配置
    REMINDER_INTERVAL = 60  # 检查提醒的间隔时间（秒）
    
    # 北航API配置
    BUAA_API_BASE_URL = 'https://byxt.buaa.edu.cn/jwapp/sys'
    
    # 大语言模型API配置
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_API_URL = os.environ.get('LLM_API_URL') or 'https://api.qwen.com/v1/chat/completions'
    
    # 提醒配置
    REMINDER_INTERVAL = 60  # 检查提醒的间隔时间（秒）
