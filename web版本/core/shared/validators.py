"""
验证器模块
为F5配置翻译工具提供统一的验证功能
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from .exceptions import ValidationError
from .constants import FILE_EXTENSIONS, MAX_FILE_SIZE, MAX_FILES_COUNT, ERROR_MESSAGES


def validate_file_extension(filename: str) -> bool:
    """
    验证文件扩展名
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 文件扩展名无效
    """
    if not filename or '.' not in filename:
        raise ValidationError(
            ERROR_MESSAGES['INVALID_FILE_TYPE'],
            field='filename',
            value=filename
        )
    
    extension = filename.rsplit('.', 1)[1].lower()
    if extension not in FILE_EXTENSIONS:
        raise ValidationError(
            f"不支持的文件类型: {extension}",
            field='extension',
            value=extension
        )
    
    return True


def validate_file_size(file_size: int) -> bool:
    """
    验证文件大小
    
    Args:
        file_size: 文件大小（字节）
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 文件大小超过限制
    """
    if file_size > MAX_FILE_SIZE:
        raise ValidationError(
            ERROR_MESSAGES['FILE_TOO_LARGE'],
            field='file_size',
            value=file_size
        )
    
    return True


def validate_upload_count(files_count: int) -> bool:
    """
    验证上传文件数量
    
    Args:
        files_count: 文件数量
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 文件数量超过限制
    """
    if files_count > MAX_FILES_COUNT:
        raise ValidationError(
            f"文件数量超过限制: {files_count} > {MAX_FILES_COUNT}",
            field='files_count',
            value=files_count
        )
    
    return True


def validate_file_exists(file_path: str) -> bool:
    """
    验证文件是否存在
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 文件是否存在
        
    Raises:
        ValidationError: 文件不存在
    """
    if not os.path.exists(file_path):
        raise ValidationError(
            ERROR_MESSAGES['FILE_NOT_FOUND'],
            field='file_path',
            value=file_path
        )
    
    return True


def validate_directory_exists(dir_path: str) -> bool:
    """
    验证目录是否存在
    
    Args:
        dir_path: 目录路径
        
    Returns:
        bool: 目录是否存在
        
    Raises:
        ValidationError: 目录不存在
    """
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        raise ValidationError(
            "目录不存在",
            field='dir_path',
            value=dir_path
        )
    
    return True


def validate_username(username: str) -> bool:
    """
    验证用户名
    
    Args:
        username: 用户名
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 用户名无效
    """
    if not username or len(username.strip()) == 0:
        raise ValidationError(
            "用户名不能为空",
            field='username',
            value=username
        )
    
    if len(username) < 3:
        raise ValidationError(
            "用户名长度至少3个字符",
            field='username',
            value=username
        )
    
    if len(username) > 20:
        raise ValidationError(
            "用户名长度不能超过20个字符",
            field='username',
            value=username
        )
    
    # 检查用户名是否包含特殊字符
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValidationError(
            "用户名只能包含字母、数字和下划线",
            field='username',
            value=username
        )
    
    return True


def validate_password(password: str) -> bool:
    """
    验证密码
    
    Args:
        password: 密码
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 密码无效
    """
    if not password or len(password.strip()) == 0:
        raise ValidationError(
            "密码不能为空",
            field='password',
            value=None
        )
    
    if len(password) < 6:
        raise ValidationError(
            "密码长度至少6个字符",
            field='password',
            value=len(password)
        )
    
    if len(password) > 50:
        raise ValidationError(
            "密码长度不能超过50个字符",
            field='password',
            value=len(password)
        )
    
    return True


def validate_email(email: str) -> bool:
    """
    验证邮箱地址
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 邮箱地址无效
    """
    if not email:
        return True  # 邮箱是可选的
    
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError(
            "邮箱地址格式无效",
            field='email',
            value=email
        )
    
    return True


def validate_session_id(session_id: str) -> bool:
    """
    验证会话ID
    
    Args:
        session_id: 会话ID
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 会话ID无效
    """
    if not session_id or len(session_id.strip()) == 0:
        raise ValidationError(
            "会话ID不能为空",
            field='session_id',
            value=session_id
        )
    
    if len(session_id) < 10:
        raise ValidationError(
            "会话ID长度不足",
            field='session_id',
            value=len(session_id)
        )
    
    return True


def validate_file_type(file_type: str) -> bool:
    """
    验证文件类型
    
    Args:
        file_type: 文件类型
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 文件类型无效
    """
    valid_types = {'ucs', 'show', 'horizon'}
    
    if file_type not in valid_types:
        raise ValidationError(
            f"不支持的文件类型: {file_type}",
            field='file_type',
            value=file_type
        )
    
    return True


def validate_process_action(action: str) -> bool:
    """
    验证处理动作
    
    Args:
        action: 处理动作
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 处理动作无效
    """
    valid_actions = {'process_ucs', 'process_show', 'process_horizon'}
    
    if action not in valid_actions:
        raise ValidationError(
            f"不支持的处理动作: {action}",
            field='action',
            value=action
        )
    
    return True


def validate_download_type(download_type: str) -> bool:
    """
    验证下载类型
    
    Args:
        download_type: 下载类型
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 下载类型无效
    """
    valid_types = {'excel', 'txt', 'log', 'zip', 'all'}
    
    if download_type not in valid_types:
        raise ValidationError(
            f"不支持的下载类型: {download_type}",
            field='download_type',
            value=download_type
        )
    
    return True


def validate_pagination_params(page: int, per_page: int) -> bool:
    """
    验证分页参数
    
    Args:
        page: 页码
        per_page: 每页数量
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 分页参数无效
    """
    if page < 1:
        raise ValidationError(
            "页码必须大于0",
            field='page',
            value=page
        )
    
    if per_page < 1 or per_page > 100:
        raise ValidationError(
            "每页数量必须在1-100之间",
            field='per_page',
            value=per_page
        )
    
    return True


def validate_search_query(query: str) -> bool:
    """
    验证搜索查询
    
    Args:
        query: 搜索查询
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 搜索查询无效
    """
    if not query or len(query.strip()) == 0:
        raise ValidationError(
            "搜索查询不能为空",
            field='query',
            value=query
        )
    
    if len(query) > 100:
        raise ValidationError(
            "搜索查询长度不能超过100个字符",
            field='query',
            value=len(query)
        )
    
    return True


def validate_file_list(files: List[str]) -> bool:
    """
    验证文件列表
    
    Args:
        files: 文件列表
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 文件列表无效
    """
    if not files:
        raise ValidationError(
            "文件列表不能为空",
            field='files',
            value=files
        )
    
    # 验证文件数量
    validate_upload_count(len(files))
    
    # 验证每个文件
    for file in files:
        validate_file_extension(file)
    
    return True


def validate_config_dict(config: Dict[str, Any]) -> bool:
    """
    验证配置字典
    
    Args:
        config: 配置字典
        
    Returns:
        bool: 是否有效
        
    Raises:
        ValidationError: 配置无效
    """
    required_keys = {'web', 'desktop', 'file'}
    
    for key in required_keys:
        if key not in config:
            raise ValidationError(
                f"缺少必需的配置项: {key}",
                field='config',
                value=key
            )
    
    return True 