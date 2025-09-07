import os
from pathlib import Path

class Config:
    """Application configuration class"""
    
    # Base directory
    BASE_DIR = Path(__file__).resolve().parent.parent

    # Data directory
    DATA_DIR = BASE_DIR / 'data'

    # Web server configuration
    WEB_HOST = '0.0.0.0'
    WEB_PORT = 5001
    DEBUG_MODE = True

    # Logging configuration
    LOG_DIR = os.path.join(DATA_DIR, 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')

    # 文件处理配置
    ALLOWED_EXTENSIONS = {'ucs', 'tar', 'txt', 'conf', 'log'}
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload size
    MAX_FILES_COUNT = 12  # 最大文件数量限制
    
    # Web应用配置
    SECRET_KEY = 'your-secret-key-here'  # 在生产环境中应该使用环境变量
    
    # 桌面应用配置
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    
    # 日志配置
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def init(cls):
        """初始化配置，创建必要的目录"""
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        # 确保删除目录存在
        delete_dir = os.path.join(cls.DATA_DIR, 'delete')
        os.makedirs(delete_dir, exist_ok=True)
        
    @classmethod
    def allowed_file(cls, filename):
        """检查文件扩展名是否允许"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS 