from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',
    path='/socket.io',
    logger=False,
    engineio_logger=False
)
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py', silent=True)  # 从 config.py 加载配置

    CORS(app)  # 启用 CORS
    socketio.init_app(app)  # 初始化 SocketIO
    

    # 这里没有找到从config.py中获得的SQLALCHEMY_DATABASE_URI
    # 但是在routes.py中使用了SQLALCHEMY_DATABASE_URI
    # 所以这里需要在app.config中设置SQLALCHEMY_DATABASE_URI
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')

    # 初始化数据库
    db.init_app(app)
    migrate.init_app(app, db)

    from . import routes, sockets  # 导入蓝图和 Socket 事件处理
    app.register_blueprint(routes.bp)

    return app
