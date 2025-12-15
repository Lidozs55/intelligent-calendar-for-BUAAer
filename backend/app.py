from flask import Flask, send_from_directory, render_template_string
from flask_cors import CORS
import os
import pathlib
import subprocess
import platform

# 设置当前工作目录
current_dir = pathlib.Path(__file__).parent
main_dir = current_dir.parent  # 获取主文件夹路径
os.chdir(str(current_dir))

# 确保config模块可以被导入
import sys
sys.path.append(str(current_dir))

# 现在导入本地模块
from config import Config
from extensions import db


def start_cpolar_service():
    """
    启动cpolar隧道服务
    """
    try:
        # 首先检查并杀死已存在的cpolar进程，防止并发会话数超过限制
        if platform.system() == 'Windows':
            # Windows系统，使用taskkill命令杀死cpolar进程
            subprocess.run(['taskkill', '/f', '/im', 'cpolar.exe'], capture_output=True, text=True)
            print("[CPolar] 已检查并杀死所有已存在的cpolar进程")
        else:
            # Linux/Mac系统，使用pkill命令杀死cpolar进程
            subprocess.run(['pkill', '-f', 'cpolar'], capture_output=True, text=True)
            print("[CPolar] 已检查并杀死所有已存在的cpolar进程")
        
        # 明确指定使用主文件夹下面的/cpolar/cpolar.exe路径
        if platform.system() == 'Windows':
            # Windows系统，使用主文件夹下的cpolar/cpolar.exe
            cpolar_path = os.path.join(main_dir, 'cpolar', 'cpolar.exe')
        else:
            # Linux/Mac系统，使用主文件夹下的cpolar/cpolar
            cpolar_path = os.path.join(main_dir, 'cpolar', 'cpolar')
        
        # 检查cpolar是否存在
        if os.path.exists(cpolar_path):
            # 检查是否有执行权限
            if platform.system() == 'Windows' or os.access(cpolar_path, os.X_OK):
                # 启动cpolar服务，使用正确的命令：cpolar http 5000
                # 在独立窗口中运行
                subprocess.Popen(
                    [cpolar_path, 'http', '5000'],
                    stdout=None,
                    stderr=None,
                    stdin=None,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == 'Windows' else 0,
                    cwd=str(current_dir)
                )
                print(f"[CPolar] 已在独立窗口中启动cpolar服务")
                print(f"[CPolar] 使用路径：{cpolar_path}")
                print(f"[CPolar] 启动命令：cpolar http 5000")
            else:
                print(f"[CPolar] 没有cpolar的执行权限：{cpolar_path}")
        else:
            print(f"[CPolar] 未找到cpolar可执行文件：{cpolar_path}")
            print(f"[CPolar] 您可以手动启动：cpolar http 5000")
    except Exception as e:
        print(f"[CPolar] 启动cpolar服务失败：{str(e)}")


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
    from routes.reminders import reminders_bp
    from routes.spoc import spoc_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(courses_bp, url_prefix='/api/courses')
    app.register_blueprint(entries_bp, url_prefix='/api/entries')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(llm_bp, url_prefix='/api/llm')
    app.register_blueprint(schedule_bp, url_prefix='/api/schedule')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(reminders_bp, url_prefix='/api/reminders')
    app.register_blueprint(spoc_bp, url_prefix='/api/spoc')
    
    # 确保instance目录存在
    instance_dir = os.path.join(app.root_path, 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 启动cpolar服务（异步，不阻塞其他初始化）
    import threading
    cpolar_thread = threading.Thread(target=start_cpolar_service)
    cpolar_thread.daemon = True
    cpolar_thread.start()
    
    # 立即启动cpolar域名自动刷新线程（它会自己处理延迟）
    from utils.qr_code import QRCodeGenerator
    QRCodeGenerator.start_cpolar_refresh()
    
    # 配置静态文件服务
    # 检查是否运行在PyInstaller打包的exe环境中
    import sys
    if hasattr(sys, '_MEIPASS'):
        # 打包为exe时，使用sys._MEIPASS作为基础路径
        meipass_path = sys._MEIPASS
        frontend_dist = pathlib.Path(meipass_path) / 'frontend' / 'dist'
        public_path = pathlib.Path(meipass_path) / 'frontend' / 'public'
    else:
        # 开发环境下，使用实际文件系统路径
        frontend_dist = current_dir.parent / 'frontend' / 'dist'
        public_path = current_dir.parent / 'frontend' / 'public'
    
    # 静态文件路由
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(str(frontend_dist / 'assets'), filename)
    
    # 声音文件路由
    @app.route('/sound/<path:filename>')
    def serve_sounds(filename):
        return send_from_directory(str(public_path / 'sound'), filename)
    
    # SVG文件路由
    @app.route('/svg/<path:filename>')
    def serve_svgs(filename):
        return send_from_directory(str(public_path / 'svg'), filename)
    
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
    
    # 手机端路由
    @app.route('/mobile')
    @app.route('/mobile/<path:path>')
    def serve_mobile(path=''):
        # 读取并返回移动端index.html
        index_path = frontend_dist / 'index.html'
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                return f.read()
        return 'Frontend not built', 500
    
    # 服务发现API - 返回手机访问信息
    @app.route('/api/mobile/info')
    def mobile_info():
        from utils.qr_code import QRCodeGenerator
        
        # 获取手机访问信息
        access_info = QRCodeGenerator.get_mobile_access_info(port=5000)
        
        return {
            'success': True,
            'data': access_info
        }, 200
    
    # 设置CPolar authtoken的API端点
    @app.route('/api/mobile/set_cpolar_authtoken', methods=['POST'])
    def set_cpolar_authtoken():
        from flask import request
        import json
        
        try:
            # 获取请求数据
            data = request.get_json()
            authtoken = data.get('authtoken')
            
            if not authtoken:
                return {
                    'success': False,
                    'message': '请提供CPolar Authtoken'
                }, 400
            
            # 保存authtoken到配置文件或环境变量
            import platform
            if platform.system() == 'Windows':
                # Windows系统，保存到cpolar配置目录
                import pathlib
                cpolar_config_dir = pathlib.Path.home() / '.cpolar'
                cpolar_config_dir.mkdir(exist_ok=True)
                
                # 创建或更新authtoken文件
                authtoken_file = cpolar_config_dir / 'authtoken'
                authtoken_file.write_text(authtoken, encoding='utf-8')
            else:
                # Linux/Mac系统，保存到~/.cpolar/authtoken
                import os
                cpolar_config_dir = os.path.expanduser('~/.cpolar')
                os.makedirs(cpolar_config_dir, exist_ok=True)
                
                authtoken_file = os.path.join(cpolar_config_dir, 'authtoken')
                with open(authtoken_file, 'w', encoding='utf-8') as f:
                    f.write(authtoken)
            
            # 重启cpolar服务
            from utils.qr_code import QRCodeGenerator
            QRCodeGenerator.restart_cpolar_service()
            
            return {
                'success': True,
                'message': 'CPolar Authtoken保存成功'
            }, 200
        except Exception as e:
            return {
                'success': False,
                'message': f'保存CPolar Authtoken失败: {str(e)}'
            }, 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=5000)
