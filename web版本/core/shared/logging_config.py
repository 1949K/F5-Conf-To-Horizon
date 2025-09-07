"""
日志配置管理模块
为F5配置翻译工具提供统一的日志管理
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .exceptions import ConfigError
from .constants import LOG_LEVELS, LOG_FORMAT


class LogManager:
    """日志管理器"""
    
    _loggers: Dict[str, logging.Logger] = {}
    _handlers: Dict[str, logging.Handler] = {}
    _initialized = False
    
    @classmethod
    def initialize(cls, log_dir: str, log_file: str = 'app.log', 
                   log_level: str = 'INFO', max_size: int = 10 * 1024 * 1024, 
                   backup_count: int = 5) -> None:
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志目录
            log_file: 日志文件名
            log_level: 日志级别
            max_size: 最大文件大小
            backup_count: 备份文件数量
        """
        if cls._initialized:
            return
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建格式化器
        formatter = logging.Formatter(LOG_FORMAT)
        
        # 创建文件处理器（带轮转）
        log_file_path = os.path.join(log_dir, log_file)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        
        # 添加处理器到根日志记录器
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # 存储处理器引用
        cls._handlers['file'] = file_handler
        cls._handlers['console'] = console_handler
        
        cls._initialized = True
        
        # 记录初始化信息
        logger = logging.getLogger(__name__)
        logger.info(f"日志管理器初始化完成，日志文件: {log_file_path}")
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器
        """
        if not cls._initialized:
            raise ConfigError("日志管理器未初始化，请先调用 initialize() 方法")
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def set_level(cls, level: str) -> None:
        """
        设置日志级别
        
        Args:
            level: 日志级别
        """
        if not cls._initialized:
            raise ConfigError("日志管理器未初始化")
        
        log_level = getattr(logging, level.upper())
        
        # 设置根日志记录器级别
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # 设置所有处理器级别
        for handler in cls._handlers.values():
            handler.setLevel(log_level)
        
        # 记录级别变更
        logger = logging.getLogger(__name__)
        logger.info(f"日志级别已设置为: {level}")
    
    @classmethod
    def add_handler(cls, handler: logging.Handler) -> None:
        """
        添加日志处理器
        
        Args:
            handler: 日志处理器
        """
        if not cls._initialized:
            raise ConfigError("日志管理器未初始化")
        
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
    
    @classmethod
    def remove_handler(cls, handler: logging.Handler) -> None:
        """
        移除日志处理器
        
        Args:
            handler: 日志处理器
        """
        if not cls._initialized:
            raise ConfigError("日志管理器未初始化")
        
        root_logger = logging.getLogger()
        root_logger.removeHandler(handler)
    
    @classmethod
    def cleanup(cls) -> None:
        """清理日志管理器"""
        # 关闭所有处理器
        for handler in cls._handlers.values():
            handler.close()
        
        # 清除记录器缓存
        cls._loggers.clear()
        cls._handlers.clear()
        cls._initialized = False


class LoggerMixin:
    """日志记录器混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = None
    
    @property
    def logger(self) -> logging.Logger:
        """获取日志记录器"""
        if self._logger is None:
            self._logger = LogManager.get_logger(self.__class__.__name__)
        return self._logger


def setup_logging(config: Dict[str, Any]) -> None:
    """
    设置日志配置
    
    Args:
        config: 日志配置字典
    """
    log_dir = config.get('log_dir', 'logs')
    log_file = config.get('log_file', 'app.log')
    log_level = config.get('log_level', 'INFO')
    max_size = config.get('max_log_size', 10 * 1024 * 1024)
    backup_count = config.get('backup_count', 5)
    
    LogManager.initialize(
        log_dir=log_dir,
        log_file=log_file,
        log_level=log_level,
        max_size=max_size,
        backup_count=backup_count
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    return LogManager.get_logger(name)


# 便捷函数
def info(message: str, logger_name: Optional[str] = None) -> None:
    """记录信息日志"""
    logger = get_logger(logger_name or __name__)
    logger.info(message)


def warning(message: str, logger_name: Optional[str] = None) -> None:
    """记录警告日志"""
    logger = get_logger(logger_name or __name__)
    logger.warning(message)


def error(message: str, logger_name: Optional[str] = None) -> None:
    """记录错误日志"""
    logger = get_logger(logger_name or __name__)
    logger.error(message)


def debug(message: str, logger_name: Optional[str] = None) -> None:
    """记录调试日志"""
    logger = get_logger(logger_name or __name__)
    logger.debug(message)


def critical(message: str, logger_name: Optional[str] = None) -> None:
    """记录严重错误日志"""
    logger = get_logger(logger_name or __name__)
    logger.critical(message) 