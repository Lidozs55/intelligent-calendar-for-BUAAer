from flask import Flask, send_from_directory, render_template_string
from flask_cors import CORS
import os
import pathlib

# 设置当前工作目录
current_dir = pathlib.Path(__file__).parent
os.chdir(str(current_dir))

# 确保config模块可以被导入
import sys
sys.path.append(str(current_dir))

# 现在导入本地模块
from config import Config
from extensions import db


def create_app(config_class=Config):
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 确保instance目录存在
    os.makedirs(app.instance_path, exist_ok=True)
    
    # 初始化扩展
    db.init_app(app)
    CORS(app, supports_credentials=True)  # 允许跨域请求并支持credentials
    
    # 注册蓝图
    from routes.auth import auth_bp
    from routes.courses import courses_bp
    from routes.tasks import tasks_bp
    from routes.llm import llm_bp
    from routes.schedule import schedule_bp
    from routes.entries import entries_bp
    from routes.settings import settings_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(courses_bp, url_prefix='/api/courses')
    app.register_blueprint(entries_bp, url_prefix='/api/entries')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(llm_bp, url_prefix='/api/llm')
    app.register_blueprint(schedule_bp, url_prefix='/api/schedule')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    
    # 确保instance目录存在
    instance_dir = os.path.join(app.root_path, 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 配置静态文件服务
    frontend_dist = current_dir.parent / 'frontend' / 'dist'
    
    # 静态文件路由
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(str(frontend_dist / 'assets'), filename)
    
    # 声音文件路由
    @app.route('/sound/<path:filename>')
    def serve_sounds(filename):
        return send_from_directory(str(current_dir.parent / 'frontend' / 'public' / 'sound'), filename)
    
    # 主页面路由
    @app.route('/')
    @app.route('/<path:path>')
    def serve_frontend(path=''):
        # 如果请求的是API，返回404
        if path.startswith('api/'):
            return {'error': 'Not Found'}, 404
        
        # 读取并返回index.html
        index_path = frontend_dist / 'index.html'
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                return f.read()
        return 'Frontend not built', 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=5000)
