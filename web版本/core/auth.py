from functools import wraps
from flask import session, redirect, url_for, flash, request
from core.user_manager import user_manager

def login_required(f):
    """登录要求装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not user_manager.get_current_user():
            flash('请先登录', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """获取当前用户"""
    return user_manager.get_current_user()

def get_user_upload_dir(file_type='ucs'):
    """获取当前用户的上传目录"""
    username = get_current_user()
    if username:
        return user_manager.get_user_upload_dir(username, file_type)
    return ''

def get_user_processed_dir(file_type='ucs'):
    """获取当前用户的处理结果目录"""
    username = get_current_user()
    if username:
        return user_manager.get_user_processed_dir(username, file_type)
    return '' 