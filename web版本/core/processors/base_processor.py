import logging
from pathlib import Path
from ..config import Config

class BaseProcessor:
    """基础处理器类，提供通用的处理方法"""
    
    def __init__(self):
        self.config = Config
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        # 检查是否已经有处理器，避免重复添加
        if logger.handlers:
            return logger
        
        # 文件处理器
        fh = logging.FileHandler(self.config.LOG_FILE)
        fh.setLevel(logging.INFO)
        
        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(self.config.LOG_FORMAT)
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def validate_file(self, file_path: str) -> bool:
        """验证文件是否存在且扩展名是否允许"""
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"文件不存在: {file_path}")
            return False
        if not self.config.allowed_file(path.name):
            self.logger.error(f"不支持的文件类型: {path.suffix}")
            return False
        return True
    
    def ensure_output_dir(self, output_dir: str) -> Path:
        """确保输出目录存在"""
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def process(self, *args, **kwargs):
        """处理方法，需要被子类重写"""
        raise NotImplementedError("子类必须实现process方法")
    
    def cleanup(self):
        """清理资源"""
        pass
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()
        if exc_type is not None:
            self.logger.error(f"处理过程中发生错误: {exc_val}")
            return False  # 重新抛出异常
        return True 