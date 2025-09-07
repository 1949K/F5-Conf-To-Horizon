"""
自定义异常类
为F5配置翻译工具提供统一的异常处理
"""

from typing import Optional, Any, Dict


class F5ConfigError(Exception):
    """F5配置处理基础异常"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """将异常转换为字典格式"""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class FileProcessError(F5ConfigError):
    """文件处理异常"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if file_path:
            details['file_path'] = file_path
        if operation:
            details['operation'] = operation
        super().__init__(message, error_code='FILE_PROCESS_ERROR', details=details)


class ValidationError(F5ConfigError):
    """验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = value
        super().__init__(message, error_code='VALIDATION_ERROR', details=details)


class AuthError(F5ConfigError):
    """认证异常"""
    
    def __init__(self, message: str, username: Optional[str] = None, action: Optional[str] = None):
        details = {}
        if username:
            details['username'] = username
        if action:
            details['action'] = action
        super().__init__(message, error_code='AUTH_ERROR', details=details)


class ConfigError(F5ConfigError):
    """配置异常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        if config_value is not None:
            details['config_value'] = config_value
        super().__init__(message, error_code='CONFIG_ERROR', details=details)


class ProcessError(F5ConfigError):
    """处理异常"""
    
    def __init__(self, message: str, process_type: Optional[str] = None, step: Optional[str] = None):
        details = {}
        if process_type:
            details['process_type'] = process_type
        if step:
            details['step'] = step
        super().__init__(message, error_code='PROCESS_ERROR', details=details)


class DownloadError(F5ConfigError):
    """下载异常"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, download_type: Optional[str] = None):
        details = {}
        if file_path:
            details['file_path'] = file_path
        if download_type:
            details['download_type'] = download_type
        super().__init__(message, error_code='DOWNLOAD_ERROR', details=details)


class UploadError(F5ConfigError):
    """上传异常"""
    
    def __init__(self, message: str, filename: Optional[str] = None, file_size: Optional[int] = None):
        details = {}
        if filename:
            details['filename'] = filename
        if file_size is not None:
            details['file_size'] = file_size
        super().__init__(message, error_code='UPLOAD_ERROR', details=details) 