"""
配置管理模块
为F5配置翻译工具提供统一的配置管理
"""

import os
from dataclasses import dataclass, field
from typing import Set, Dict, Any, Optional
from pathlib import Path

from .shared.exceptions import ConfigError
from .shared.constants import DEFAULT_CONFIG, FILE_EXTENSIONS, MAX_FILE_SIZE, MAX_FILES_COUNT


@dataclass
class WebConfig:
    """Web应用配置"""
    host: str = '0.0.0.0'
    port: int = 5001
    debug: bool = True
    secret_key: str = 'your-secret-key-here'
    session_lifetime: int = 3600  # 1小时
    cookie_secure: bool = False  # 开发环境设为False
    cookie_httponly: bool = True
    cookie_samesite: str = 'Lax'
    max_content_length: int = 100 * 1024 * 1024  # 100 MB


@dataclass
class DesktopConfig:
    """桌面应用配置"""
    window_width: int = 1200
    window_height: int = 800
    theme: str = 'clam'
    min_width: int = 800
    min_height: int = 600
    title: str = 'F5配置翻译工具 - 桌面版'


@dataclass
class FileConfig:
    """文件处理配置"""
    allowed_extensions: Set[str] = field(default_factory=lambda: FILE_EXTENSIONS)
    max_file_size: int = MAX_FILE_SIZE
    max_files_count: int = MAX_FILES_COUNT
    upload_dir: str = 'uploads'
    processed_dir: str = 'processed'
    temp_dir: str = 'temp'


@dataclass
class LogConfig:
    """日志配置"""
    log_dir: str = 'logs'
    log_file: str = 'app.log'
    log_level: str = 'INFO'
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    max_log_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5


@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_type: str = 'sqlite'  # sqlite, mysql, postgresql
    db_path: str = 'data/app.db'
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None


@dataclass
class SecurityConfig:
    """安全配置"""
    password_min_length: int = 6
    password_max_length: int = 50
    username_min_length: int = 3
    username_max_length: int = 20
    session_timeout: int = 3600  # 1小时
    max_login_attempts: int = 5
    lockout_duration: int = 300  # 5分钟


class Config:
    """统一配置管理类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径
        """
        self.base_dir = Path(__file__).resolve().parent.parent
        self.data_dir = self.base_dir / 'data'
        
        # 初始化各配置模块
        self.web = WebConfig()
        self.desktop = DesktopConfig()
        self.file = FileConfig()
        self.log = LogConfig()
        self.database = DatabaseConfig()
        self.security = SecurityConfig()
        
        # 加载配置文件
        if config_file:
            self.load_config(config_file)
        
        # 初始化目录
        self.init_directories()
    
    def init_directories(self) -> None:
        """初始化必要的目录"""
        directories = [
            self.data_dir,
            self.data_dir / self.log.log_dir,
            self.data_dir / self.file.upload_dir,
            self.data_dir / self.file.processed_dir,
            self.data_dir / self.file.temp_dir,
            self.data_dir / 'delete'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def load_config(self, config_file: str) -> None:
        """
        从配置文件加载配置
        
        Args:
            config_file: 配置文件路径
        """
        try:
            import yaml
            
            if not os.path.exists(config_file):
                raise ConfigError(f"配置文件不存在: {config_file}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            self._update_config(config_data)
            
        except Exception as e:
            raise ConfigError(f"加载配置文件失败: {str(e)}")
    
    def _update_config(self, config_data: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            config_data: 配置数据
        """
        if 'web' in config_data:
            web_config = config_data['web']
            for key, value in web_config.items():
                if hasattr(self.web, key):
                    setattr(self.web, key, value)
        
        if 'desktop' in config_data:
            desktop_config = config_data['desktop']
            for key, value in desktop_config.items():
                if hasattr(self.desktop, key):
                    setattr(self.desktop, key, value)
        
        if 'file' in config_data:
            file_config = config_data['file']
            for key, value in file_config.items():
                if hasattr(self.file, key):
                    setattr(self.file, key, value)
        
        if 'log' in config_data:
            log_config = config_data['log']
            for key, value in log_config.items():
                if hasattr(self.log, key):
                    setattr(self.log, key, value)
        
        if 'database' in config_data:
            db_config = config_data['database']
            for key, value in db_config.items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
        
        if 'security' in config_data:
            security_config = config_data['security']
            for key, value in security_config.items():
                if hasattr(self.security, key):
                    setattr(self.security, key, value)
    
    def save_config(self, config_file: str) -> None:
        """
        保存配置到文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            import yaml
            
            config_data = {
                'web': self.web.__dict__,
                'desktop': self.desktop.__dict__,
                'file': self.file.__dict__,
                'log': self.log.__dict__,
                'database': self.database.__dict__,
                'security': self.security.__dict__
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            raise ConfigError(f"保存配置文件失败: {str(e)}")
    
    def get_web_config(self) -> Dict[str, Any]:
        """获取Web应用配置"""
        return {
            'host': self.web.host,
            'port': self.web.port,
            'debug': self.web.debug,
            'secret_key': self.web.secret_key,
            'max_content_length': self.web.max_content_length
        }
    
    def get_desktop_config(self) -> Dict[str, Any]:
        """获取桌面应用配置"""
        return {
            'window_width': self.desktop.window_width,
            'window_height': self.desktop.window_height,
            'theme': self.desktop.theme,
            'min_width': self.desktop.min_width,
            'min_height': self.desktop.min_height,
            'title': self.desktop.title
        }
    
    def get_file_config(self) -> Dict[str, Any]:
        """获取文件处理配置"""
        return {
            'allowed_extensions': list(self.file.allowed_extensions),
            'max_file_size': self.file.max_file_size,
            'max_files_count': self.file.max_files_count,
            'upload_dir': str(self.data_dir / self.file.upload_dir),
            'processed_dir': str(self.data_dir / self.file.processed_dir),
            'temp_dir': str(self.data_dir / self.file.temp_dir)
        }
    
    def get_log_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            'log_dir': str(self.data_dir / self.log.log_dir),
            'log_file': str(self.data_dir / self.log.log_dir / self.log.log_file),
            'log_level': self.log.log_level,
            'log_format': self.log.log_format,
            'max_log_size': self.log.max_log_size,
            'backup_count': self.log.backup_count
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return {
            'db_type': self.database.db_type,
            'db_path': str(self.data_dir / self.database.db_path),
            'db_host': self.database.db_host,
            'db_port': self.database.db_port,
            'db_name': self.database.db_name,
            'db_user': self.database.db_user,
            'db_password': self.database.db_password
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return {
            'password_min_length': self.security.password_min_length,
            'password_max_length': self.security.password_max_length,
            'username_min_length': self.security.username_min_length,
            'username_max_length': self.security.username_max_length,
            'session_timeout': self.security.session_timeout,
            'max_login_attempts': self.security.max_login_attempts,
            'lockout_duration': self.security.lockout_duration
        }
    
    def validate(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 验证端口范围
            if not (1 <= self.web.port <= 65535):
                raise ConfigError(f"Web端口无效: {self.web.port}")
            
            # 验证文件大小限制
            if self.file.max_file_size <= 0:
                raise ConfigError(f"文件大小限制无效: {self.file.max_file_size}")
            
            # 验证文件数量限制
            if self.file.max_files_count <= 0:
                raise ConfigError(f"文件数量限制无效: {self.file.max_files_count}")
            
            # 验证窗口大小
            if self.desktop.window_width <= 0 or self.desktop.window_height <= 0:
                raise ConfigError("窗口大小无效")
            
            return True
            
        except Exception as e:
            raise ConfigError(f"配置验证失败: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'base_dir': str(self.base_dir),
            'data_dir': str(self.data_dir),
            'web': self.get_web_config(),
            'desktop': self.get_desktop_config(),
            'file': self.get_file_config(),
            'log': self.get_log_config(),
            'database': self.get_database_config(),
            'security': self.get_security_config()
        }


# 全局配置实例
config = Config() 