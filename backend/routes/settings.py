from flask import Blueprint, request, jsonify
import os
import dotenv

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/api_key', methods=['POST'])
def save_api_key():
    """保存API_KEY到.env文件"""
    data = request.get_json()
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({'error': 'API_KEY is required'}), 400
    
    try:
        # 获取.env文件路径 - 兼容PyInstaller打包环境
        import sys
        if hasattr(sys, '_MEIPASS'):
            # 打包后的运行环境，.env文件位于exe所在目录
            basedir = os.path.dirname(sys.executable)
        else:
            # 开发环境，.env文件位于backend目录上一级
            basedir = os.path.abspath(os.path.dirname(__file__))
            basedir = os.path.dirname(basedir)
        env_path = os.path.join(basedir, '.env')
        
        # 读取现有.env文件内容
        env_content = ''
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.read()
        
        # 更新或添加LLM_API_KEY配置
        lines = env_content.split('\n')
        updated_lines = []
        api_key_found = False
        
        for line in lines:
            if line.strip().startswith('LLM_API_KEY'):
                # 更新现有配置
                updated_lines.append(f'LLM_API_KEY={api_key}')
                api_key_found = True
            else:
                updated_lines.append(line)
        
        if not api_key_found:
            # 添加新配置
            updated_lines.append(f'LLM_API_KEY={api_key}')
        
        # 写入更新后的内容
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        # 重新加载环境变量，确保配置立即生效
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)
        
        return jsonify({'message': 'API_KEY saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
