import os
import json
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from flask import session, request
from core.config import Config

class UserManager:
    """用户管理类"""
    
    def __init__(self):
        self.users_file = os.path.join(Config.DATA_DIR, 'users.json')
        self.users = self._load_users()
        self.sessions = {}  # 存储活跃会话
    
    def _load_users(self) -> Dict:
        """加载用户数据"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_users(self):
        """保存用户数据"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return secrets.token_urlsafe(32)
    
    def register_user(self, username: str, password: str, email: str = "") -> bool:
        """注册新用户"""
        if username in self.users:
            return False
        
        # 创建用户目录
        user_dirs = self._create_user_directories(username)
        
        # 保存用户信息
        self.users[username] = {
            'password_hash': self._hash_password(password),
            'email': email,
            'created_at': datetime.now().isoformat(),
            'directories': user_dirs
        }
        
        self._save_users()
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """用户认证"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        if user['password_hash'] == self._hash_password(password):
            # 生成会话ID
            session_id = self._generate_session_id()
            self.sessions[session_id] = {
                'username': username,
                'created_at': datetime.now(),
                'last_activity': datetime.now()
            }
            return session_id
        
        return None
    
    def get_current_user(self) -> Optional[str]:
        """获取当前用户"""
        session_id = session.get('session_id')
        if session_id and session_id in self.sessions:
            session_data = self.sessions[session_id]
            # 检查会话是否过期（24小时）
            if datetime.now() - session_data['last_activity'] < timedelta(hours=24):
                session_data['last_activity'] = datetime.now()
                return session_data['username']
            else:
                # 删除过期会话
                del self.sessions[session_id]
                session.pop('session_id', None)
        return None
    
    def logout_user(self):
        """用户登出"""
        session_id = session.get('session_id')
        if session_id:
            self.sessions.pop(session_id, None)
            session.pop('session_id', None)
    
    def _create_user_directories(self, username: str) -> Dict[str, str]:
        """创建用户目录结构"""
        user_base = os.path.join(Config.DATA_DIR, 'users', username)
        
        # 定义所有需要的目录
        directories = {
            'ucs_uploads': os.path.join(user_base, 'ucs', 'uploads'),
            'ucs_processed': os.path.join(user_base, 'ucs', 'processed'),
            'show_uploads': os.path.join(user_base, 'show', 'uploads'),
            'show_processed': os.path.join(user_base, 'show', 'processed'),
            'conf_uploads': os.path.join(user_base, 'ucs', 'conf'),
            'processed_uploads': os.path.join(user_base, 'ucs', 'processed'),
            'horizon_uploads': os.path.join(user_base, 'horizon', 'upload'),
            'horizon_unzip': os.path.join(user_base, 'horizon', 'unzip'),
            'horizon_config': os.path.join(user_base, 'horizon', 'config'),
            'horizon_compare': os.path.join(user_base, 'horizon', 'compare')
        }
        
        # 创建所有目录
        for dir_path in directories.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # 创建UCS相关的子目录
        ucs_dir = os.path.join(user_base, 'ucs')
        conf_dir = os.path.join(ucs_dir, 'conf')
        base_dir = os.path.join(ucs_dir, 'base')
        os.makedirs(conf_dir, exist_ok=True)
        os.makedirs(base_dir, exist_ok=True)
        
        # 创建弘积相关的子目录
        horizon_dir = os.path.join(user_base, 'horizon')
        os.makedirs(horizon_dir, exist_ok=True)
        
        return directories
    
    def get_user_directories(self, username: str) -> Dict[str, str]:
        """获取用户目录"""
        if username in self.users:
            return self.users[username].get('directories', {})
        return {}
    
    def get_user_upload_dir(self, username: str, file_type: str = 'ucs') -> str:
        """获取用户上传目录"""
        dirs = self.get_user_directories(username)
        if file_type == 'ucs':
            return dirs.get('ucs_uploads', '')
        elif file_type == 'show':
            return dirs.get('show_uploads', '')
        elif file_type == 'conf':
            # 对于conf文件，返回ucs目录，因为conf和base子目录在ucs目录下
            user_base = os.path.join(Config.DATA_DIR, 'users', username)
            return os.path.join(user_base, 'ucs')
        elif file_type == 'processed':
            return dirs.get('processed_uploads', '')
        elif file_type == 'horizon':
            # 对于horizon，直接构建路径，确保目录存在
            user_base = os.path.join(Config.DATA_DIR, 'users', username)
            horizon_upload_dir = os.path.join(user_base, 'horizon', 'upload')
            # 确保目录存在
            os.makedirs(horizon_upload_dir, exist_ok=True)
            return horizon_upload_dir
        return ''
    
    def ensure_user_directories_exist(self, username: str):
        """确保用户的所有目录都存在"""
        if username not in self.users:
            return False
        
        # 使用现有的目录创建逻辑
        self._create_user_directories(username)
        return True
    
    def get_user_processed_dir(self, username: str, file_type: str = 'ucs') -> str:
        """获取用户处理结果目录"""
        dirs = self.get_user_directories(username)
        if file_type == 'ucs':
            return dirs.get('ucs_processed', '')
        elif file_type == 'show':
            return dirs.get('show_processed', '')
        elif file_type == 'horizon':
            # 对于弘积，返回horizon目录，确保目录存在
            user_base = os.path.join(Config.DATA_DIR, 'users', username)
            horizon_dir = os.path.join(user_base, 'horizon')
            # 确保horizon目录及其子目录存在
            os.makedirs(horizon_dir, exist_ok=True)
            os.makedirs(os.path.join(horizon_dir, 'upload'), exist_ok=True)
            os.makedirs(os.path.join(horizon_dir, 'unzip'), exist_ok=True)
            os.makedirs(os.path.join(horizon_dir, 'config'), exist_ok=True)
            os.makedirs(os.path.join(horizon_dir, 'compare'), exist_ok=True)
            return horizon_dir
        return ''
    
    def get_user_files(self, username: str, file_type: str = 'ucs') -> List[str]:
        """获取用户文件列表"""
        upload_dir = self.get_user_upload_dir(username, file_type)
        if not upload_dir or not os.path.exists(upload_dir):
            return []
        
        files = []
        for file in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, file)
            if os.path.isfile(file_path):
                files.append(file)
        return files
    
    def get_user_processed_files(self, username: str, file_type: str = 'ucs') -> List[str]:
        """获取用户处理结果文件列表"""
        processed_dir = self.get_user_processed_dir(username, file_type)
        if not processed_dir or not os.path.exists(processed_dir):
            return []
        
        files = []
        for file in os.listdir(processed_dir):
            file_path = os.path.join(processed_dir, file)
            if os.path.isfile(file_path):
                files.append(file)
        return files
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            if current_time - session_data['last_activity'] > timedelta(hours=24):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]

# 全局用户管理器实例
user_manager = UserManager() 