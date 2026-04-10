#!/usr/bin/env python3
"""
AI Test Hub - 一键启动脚本
专为 PyCharm 优化，自动加载 .env 配置并初始化数据库

使用方法:
    - PyCharm: 右键运行此文件
    - 命令行：python run.py
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置 Flask 环境
os.environ['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')
os.environ['FLASK_APP'] = 'app.py'

def main():
    """主函数：初始化数据库并启动 Flask 应用"""
    print("=" * 60)
    print("🚀 AI Test Hub v3.0 - 智能测试工作台")
    print("=" * 60)
    print(f"📁 工作目录：{os.getcwd()}")
    print(f"🌍 运行环境：{os.getenv('FLASK_ENV')}")
    print(f"🔑 Secret Key: {'已配置' if os.getenv('SECRET_KEY') else '使用默认值'}")
    print("-" * 60)
    
    # 导入并初始化应用
    from app import create_app, socketio
    from extensions import db
    
    # 创建应用实例
    app = create_app()
    
    # 初始化数据库（在应用上下文中）
    print("📊 正在初始化数据库...")
    with app.app_context():
        db.create_all()
    print("✅ 数据库初始化完成")
    print("-" * 60)
    
    # 获取配置
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🌐 服务地址：http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print(f"🔧 Debug 模式：{'开启' if debug else '关闭'}")
    print("=" * 60)
    print("✨ 按 Ctrl+C 停止服务")
    print("=" * 60)
    
    # 启动 SocketIO 服务器（支持 WebSocket）
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
        use_reloader=debug
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 启动失败：{e}")
        sys.exit(1)