#!/usr/bin/env python3
"""
智能日历应用入口文件
"""

import sys
import os
import pathlib

# 获取当前文件目录
current_dir = pathlib.Path(__file__).parent

# 设置正确的工作目录
os.chdir(str(current_dir))

# 添加当前目录到sys.path
sys.path.append(str(current_dir))

# 确保backend模块可以被导入
sys.path.append(str(current_dir / 'backend'))

# 只导入必要的模块，避免重复导入导致的错误
# 现在导入app模块
from backend.app import create_app

if __name__ == '__main__':
    # 创建应用
    app = create_app()
    
    # 启动应用
    print("智能日历应用正在启动...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止应用")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"应用启动失败: {e}")
        sys.exit(1)
