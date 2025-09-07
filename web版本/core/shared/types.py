"""
类型定义
为F5配置翻译工具定义所有类型注解
"""

from typing import TypedDict, List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime


class ProcessResult(TypedDict):
    """处理结果类型"""
    success: bool
    message: str
    results: List[str]
    processed_files: List[str]
    error: Optional[str]
    details: Optional[Dict[str, Any]]


class FileInfo(TypedDict):
    """文件信息类型"""
    name: str
    size: int
    upload_time: str
    status: str
    file_type: str
    path: str


class UserInfo(TypedDict):
    """用户信息类型"""
    username: str
    email: Optional[str]
    role: str
    created_at: str
    last_login: Optional[str]


class SessionInfo(TypedDict):
    """会话信息类型"""
    session_id: str
    username: str
    created_at: str
    expires_at: str


class UploadResult(TypedDict):
    """上传结果类型"""
    success: bool
    message: str
    uploaded_files: List[str]
    failed_files: List[str]
    total_size: int


class DownloadResult(TypedDict):
    """下载结果类型"""
    success: bool
    message: str
    file_path: Optional[str]
    file_size: Optional[int]
    content_type: Optional[str]


class StatusInfo(TypedDict):
    """状态信息类型"""
    file_name: str
    status: str
    progress: int
    message: str
    timestamp: str


class ConfigInfo(TypedDict):
    """配置信息类型"""
    key: str
    value: Any
    description: str
    category: str


class LogEntry(TypedDict):
    """日志条目类型"""
    timestamp: str
    level: str
    message: str
    user: Optional[str]
    action: Optional[str]


class ProcessStep(TypedDict):
    """处理步骤类型"""
    step_name: str
    status: str
    start_time: str
    end_time: Optional[str]
    message: Optional[str]


class ValidationResult(TypedDict):
    """验证结果类型"""
    valid: bool
    errors: List[str]
    warnings: List[str]


class ApiResponse(TypedDict):
    """API响应类型"""
    success: bool
    message: str
    data: Optional[Any]
    error: Optional[str]
    timestamp: str


class PaginationInfo(TypedDict):
    """分页信息类型"""
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


class SearchResult(TypedDict):
    """搜索结果类型"""
    query: str
    results: List[Any]
    total: int
    pagination: PaginationInfo


class FileStats(TypedDict):
    """文件统计类型"""
    total_files: int
    total_size: int
    file_types: Dict[str, int]
    upload_times: Dict[str, int]


class UserStats(TypedDict):
    """用户统计类型"""
    total_users: int
    active_users: int
    total_sessions: int
    file_uploads: int


class SystemStats(TypedDict):
    """系统统计类型"""
    uptime: str
    memory_usage: float
    disk_usage: float
    active_processes: int


# 联合类型
FileType = Union[str, Path]
FileList = List[FileType]
ConfigDict = Dict[str, Any]
ErrorDict = Dict[str, Any]
ResultDict = Dict[str, Any]

# 可选类型
OptionalStr = Optional[str]
OptionalInt = Optional[int]
OptionalBool = Optional[bool]
OptionalDict = Optional[Dict[str, Any]]
OptionalList = Optional[List[Any]] 