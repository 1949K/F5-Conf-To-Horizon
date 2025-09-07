"""
基础处理器 V2
为F5配置翻译工具提供优化的基础处理器
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from ..shared.logging_config import LoggerMixin, get_logger
from ..shared.exceptions import FileProcessError, ValidationError
from ..shared.validators import validate_file_exists, validate_file_extension
from ..shared.types import FileInfo, ProcessResult


class BaseProcessorV2(LoggerMixin):
    """基础处理器 V2，提供通用的处理方法"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化基础处理器
        
        Args:
            config: 配置字典
        """
        super().__init__()
        self.config = config or {}
        self._setup_processor()
    
    def _setup_processor(self) -> None:
        """设置处理器"""
        self.logger.info(f"初始化处理器: {self.__class__.__name__}")
    
    def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否存在且扩展名是否允许
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 文件是否有效
            
        Raises:
            FileProcessError: 文件验证失败
        """
        try:
            # 验证文件是否存在
            validate_file_exists(file_path)
            
            # 验证文件扩展名
            filename = os.path.basename(file_path)
            validate_file_extension(filename)
            
            self.logger.debug(f"文件验证通过: {file_path}")
            return True
            
        except ValidationError as e:
            self.logger.error(f"文件验证失败: {e.message}")
            raise FileProcessError(e.message, file_path=file_path, operation="文件验证")
    
    def ensure_output_dir(self, output_dir: str) -> Path:
        """
        确保输出目录存在
        
        Args:
            output_dir: 输出目录路径
            
        Returns:
            Path: 输出目录路径对象
        """
        path = Path(output_dir)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"创建输出目录: {output_dir}")
        return path
    
    def get_file_info(self, file_path: str) -> FileInfo:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            FileInfo: 文件信息
        """
        path = Path(file_path)
        stat = path.stat()
        
        return {
            'name': path.name,
            'size': stat.st_size,
            'upload_time': str(stat.st_mtime),
            'status': 'valid',
            'file_type': path.suffix.lower(),
            'path': str(path)
        }
    
    def process(self, *args, **kwargs) -> ProcessResult:
        """
        处理方法，需要被子类重写
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            ProcessResult: 处理结果
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现process方法")
    
    def cleanup(self) -> None:
        """清理资源"""
        self.logger.debug(f"清理处理器资源: {self.__class__.__name__}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.logger.debug(f"进入处理器上下文: {self.__class__.__name__}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()
        if exc_type is not None:
            self.logger.error(f"处理过程中发生错误: {exc_val}")
            return False  # 重新抛出异常
        return True
    
    def log_process_start(self, process_name: str, **kwargs) -> None:
        """
        记录处理开始
        
        Args:
            process_name: 处理名称
            **kwargs: 额外参数
        """
        self.logger.info(f"开始处理: {process_name}")
        if kwargs:
            self.logger.debug(f"处理参数: {kwargs}")
    
    def log_process_success(self, process_name: str, result: Optional[Dict[str, Any]] = None) -> None:
        """
        记录处理成功
        
        Args:
            process_name: 处理名称
            result: 处理结果
        """
        self.logger.info(f"处理成功: {process_name}")
        if result:
            self.logger.debug(f"处理结果: {result}")
    
    def log_process_error(self, process_name: str, error: Exception) -> None:
        """
        记录处理错误
        
        Args:
            process_name: 处理名称
            error: 错误对象
        """
        self.logger.error(f"处理失败: {process_name} - {str(error)}")
    
    def log_process_progress(self, process_name: str, progress: int, total: int, message: str = "") -> None:
        """
        记录处理进度
        
        Args:
            process_name: 处理名称
            progress: 当前进度
            total: 总数
            message: 进度消息
        """
        percentage = (progress / total) * 100 if total > 0 else 0
        log_message = f"处理进度: {process_name} - {progress}/{total} ({percentage:.1f}%)"
        if message:
            log_message += f" - {message}"
        self.logger.info(log_message) 