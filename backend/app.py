from flask import Flask, send_from_directory, render_template_string
from flask_cors import CORS
import os
import pathlib
import subprocess
import platform

# 设置当前工作目录
current_dir = pathlib.Path(__file__).parent
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
        # 首先检查cpolar.exe的可能路径
        cpolar_path = None
        
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
        
        # 如果找到cpolar_path，直接使用它；否则尝试使用环境变量中的cpolar命令
        if cpolar_path:
            # 启动cpolar服务，不创建新窗口，直接在后台运行
            start_cmd = [cpolar_path, 'http', '5000']
            
            # 直接启动子进程，不使用shell=True（Windows）或nohup（Linux）
            # 设置stdout和stderr为DEVNULL，避免输出干扰主进程
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen(
                    start_cmd,
                    stdout=devnull,
                    stderr=devnull,
                    stdin=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0,
                    cwd=str(current_dir)
                )
            
            print(f"[CPolar] 已启动cpolar服务，使用路径：{cpolar_path}")
        else:
            # 尝试使用环境变量中的cpolar命令
            try:
                # 启动cpolar服务，不创建新窗口
                start_cmd = ['cpolar', 'http', '5000']
                
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen(
                        start_cmd,
                        stdout=devnull,
                        stderr=devnull,
                        stdin=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0,
                        cwd=str(current_dir)
                    )
                
                print("[CPolar] 已使用环境变量中的cpolar命令启动服务")
            except Exception:
                # 不打印详细错误，只显示简洁提示
                print("[CPolar] 未找到cpolar可执行文件，您可以手动启动：cpolar http 5000")
    except Exception as e:
        # 只打印关键错误信息
        print(f"[CPolar] 启动cpolar服务失败：{str(e)[:50]}...")


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
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(courses_bp, url_prefix='/api/courses')
    app.register_blueprint(entries_bp, url_prefix='/api/entries')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(llm_bp, url_prefix='/api/llm')
    app.register_blueprint(schedule_bp, url_prefix='/api/schedule')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(reminders_bp, url_prefix='/api/reminders')
    
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
