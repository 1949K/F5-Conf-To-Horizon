"""
常量定义
为F5配置翻译工具定义所有常量
"""

from typing import Set, Dict, Any

# 文件扩展名
FILE_EXTENSIONS: Set[str] = {'ucs', 'tar', 'txt', 'conf', 'log'}

# 文件大小限制 (字节)
MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB
MAX_FILES_COUNT: int = 12

# 文件类型映射
FILE_TYPE_MAPPING: Dict[str, Set[str]] = {
    'ucs': {'ucs'},
    'show': {'txt', 'conf'},
    'horizon': {'txt', 'conf', 'log'}
}

# 处理状态
PROCESS_STATUS = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'CANCELLED': 'cancelled'
}

# 用户角色
USER_ROLES = {
    'ADMIN': 'admin',
    'USER': 'user',
    'GUEST': 'guest'
}

# 会话配置
SESSION_CONFIG = {
    'PERMANENT_SESSION_LIFETIME': 3600,  # 1小时
    'SESSION_COOKIE_SECURE': False,  # 开发环境
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax'
}

# 日志级别
LOG_LEVELS = {
    'DEBUG': 'DEBUG',
    'INFO': 'INFO',
    'WARNING': 'WARNING',
    'ERROR': 'ERROR',
    'CRITICAL': 'CRITICAL'
}

# 日志格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 响应状态码
HTTP_STATUS = {
    'OK': 200,
    'CREATED': 201,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

# 错误消息
ERROR_MESSAGES = {
    'FILE_NOT_FOUND': '文件不存在',
    'FILE_TOO_LARGE': '文件大小超过限制',
    'INVALID_FILE_TYPE': '不支持的文件类型',
    'UPLOAD_FAILED': '文件上传失败',
    'PROCESS_FAILED': '文件处理失败',
    'DOWNLOAD_FAILED': '文件下载失败',
    'AUTH_REQUIRED': '需要登录',
    'INVALID_CREDENTIALS': '用户名或密码错误',
    'USER_EXISTS': '用户已存在',
    'VALIDATION_FAILED': '数据验证失败'
}

# 成功消息
SUCCESS_MESSAGES = {
    'UPLOAD_SUCCESS': '文件上传成功',
    'PROCESS_SUCCESS': '文件处理成功',
    'DOWNLOAD_SUCCESS': '文件下载成功',
    'LOGIN_SUCCESS': '登录成功',
    'REGISTER_SUCCESS': '注册成功',
    'LOGOUT_SUCCESS': '登出成功',
    'DELETE_SUCCESS': '删除成功'
}

# 处理步骤
PROCESS_STEPS = {
    'UCS': [
        'UCS转TAR',
        '解压TAR文件',
        '提取配置文件',
        '处理conf文件',
        '处理base文件'
    ],
    'SHOW': [
        'TXT转LOG',
        '处理配置文件'
    ],
    'HORIZON': [
        '文件验证',
        '配置提取',
        '对比分析',
        '结果生成'
    ]
}

# 下载类型
DOWNLOAD_TYPES = {
    'EXCEL': 'excel',
    'TXT': 'txt',
    'LOG': 'log',
    'ZIP': 'zip',
    'ALL': 'all'
}

# 界面主题
UI_THEMES = {
    'LIGHT': 'light',
    'DARK': 'dark',
    'SYSTEM': 'system'
}

# 默认配置
DEFAULT_CONFIG = {
    'web': {
        'host': '0.0.0.0',
        'port': 5001,
        'debug': True,
        'secret_key': 'your-secret-key-here'
    },
    'desktop': {
        'window_width': 1200,
        'window_height': 800,
        'theme': 'clam'
    },
    'file': {
        'allowed_extensions': FILE_EXTENSIONS,
        'max_content_length': MAX_FILE_SIZE,
        'max_files_count': MAX_FILES_COUNT
    }
} 