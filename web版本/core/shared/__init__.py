"""
共享模块
包含Web和桌面应用共享的核心功能
"""

from .exceptions import *
from .validators import *
from .constants import *
from .types import *
from .logging_config import *

__all__ = [
    'F5ConfigError',
    'FileProcessError', 
    'ValidationError',
    'AuthError',
    'validate_file_extension',
    'validate_file_size',
    'validate_upload_count',
    'FILE_EXTENSIONS',
    'MAX_FILE_SIZE',
    'MAX_FILES_COUNT',
    'ProcessResult',
    'FileInfo',
    'UserInfo',
    'LogManager',
    'LoggerMixin',
    'setup_logging',
    'get_logger',
    'info',
    'warning',
    'error',
    'debug',
    'critical'
] 