import os

# 获取当前项目的根目录
basedir = os.path.abspath(os.path.dirname(__file__))

# 数据库配置
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
