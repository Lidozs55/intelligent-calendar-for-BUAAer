from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db
import os


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
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
