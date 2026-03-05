# Gunicorn 配置
# Flask-SocketIO 需要 eventlet/gevent 支持 WebSocket，sync worker 仅支持 HTTP
# 启动: gunicorn -c gunicorn_config.py app:app

bind = "0.0.0.0:5001"
workers = 1  # WebSocket 需单 worker
worker_class = "eventlet"  # 需安装: pip install eventlet
