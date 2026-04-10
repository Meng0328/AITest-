"""
Flask 扩展初始化 - 解决循环导入问题
所有扩展在此文件中统一创建，供 app 和 models 共同使用
"""

from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# 延迟初始化，避免循环依赖
db = SQLAlchemy()
socketio = SocketIO()


def init_extensions(app):
    """初始化所有扩展"""
    db.init_app(app)
    socketio.init_app(
        app, 
        cors_allowed_origins="*", 
        async_mode='eventlet',
        path='/socket.io'
    )
    
    return db, socketio