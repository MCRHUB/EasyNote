# -*- coding: utf-8 -*-
"""
项目配置文件
"""
import os
import sys


def get_base_dir():
    """
    获取项目根目录
    - 开发环境：返回当前文件所在目录
    - PyInstaller 打包后：返回 exe 所在目录（而不是 sys._MEIPASS 临时目录）
      因为数据库和上传图片需要持久化保存，必须放在 exe 同级目录
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，sys.executable 是 exe 的完整路径
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


# 项目根目录
BASE_DIR = get_base_dir()

# SQLite 数据库文件路径（单文件，存放在 exe 同级目录，方便用户备份）
DB_PATH = os.path.join(BASE_DIR, 'notebook.db')

# 图片存储方案
# 'base64'   -> 图片以 base64 形式存入数据库
# 'filesystem' -> 图片保存到本地文件夹，数据库存相对路径
IMAGE_STORAGE_MODE = 'filesystem'

# 图片存储目录（方案2使用）
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Flask 服务监听地址（仅本机）
FLASK_HOST = '127.0.0.1'
FLASK_PORT = 5000

# Flask Secret Key（用于 session）
SECRET_KEY = 'notebook-offline-secret-key-change-me'

# 允许上传的图片扩展名
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# 最大上传图片大小（8MB）
MAX_CONTENT_LENGTH = 8 * 1024 * 1024