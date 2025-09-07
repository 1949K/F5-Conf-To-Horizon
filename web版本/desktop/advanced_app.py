#!/usr/bin/env python3
"""
F5配置翻译工具 - 高级桌面应用
实现与Web应用相同的功能，包括用户管理、文件处理、状态跟踪等
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
from typing import Optional, Dict, List, Any
from pathlib import Path
import threading
import json
import shutil
import zipfile
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import Config
from core.user_manager import user_manager
from core.processors.f5_ucs_processor import F5UCSProcessor
from core.processors.unified_processor import UnifiedProcessor

class DesktopApp:
    """F5配置翻译工具桌面应用主类"""
    
    def __init__(self):
        self.app = tk.Tk()
        self.app.title("F5配置翻译工具 - 桌面版")
        self.current_user = None
        self.user_data = {}
        
        # 初始化配置
        Config.init()
        
        # 设置窗口
        self._setup_window()
        
        # 创建UI组件
        self.notebook = None
        self.status_label = None
        self.log_text = None
        self.file_listbox = None
        self.status_tree = None
        
        # 重定向输出
        self.original_stdout = sys.stdout
        sys.stdout = self
        
        # 创建UI
        self.create_ui()
        
    def write(self, text: str) -> None:
        """重写write方法以捕获print输出"""
        if self.log_text:
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)
        self.original_stdout.write(text)
        
    def flush(self) -> None:
        """重写flush方法"""
        self.original_stdout.flush()
        
    def __del__(self) -> None:
        """恢复标准输出"""
        sys.stdout = self.original_stdout
        
    def _setup_window(self):
        """设置主窗口"""
        screen_width = self.app.winfo_screenwidth()
        screen_height = self.app.winfo_screenheight()
        
        window_width = 1200
        window_height = 800
        
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.app.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.app.minsize(800, 600)
        
        # 设置样式
        style = ttk.Style()
        style.theme_use("clam")
        
    def create_ui(self):
        """创建用户界面"""
        # 创建菜单栏
        self.create_menu()
        
        # 创建主框架
        main_frame = ttk.Frame(self.app)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # 创建各个页面
        self.create_login_page()
        self.create_main_page()
        self.create_ucs_page()
        self.create_show_page()
        self.create_files_page()
        self.create_logs_page()
        
        # 创建状态栏
        self.status_label = ttk.Label(self.app, text="状态: 未登录", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建日志区域
        self.create_log_area()
        
        # 默认显示登录页面
        self.notebook.select(0)
        
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.app)
        self.app.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="上传文件", command=self.upload_files)
        file_menu.add_command(label="下载文件", command=self.download_files)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.app.quit)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="处理UCS文件", command=self.process_ucs_files_unified)
        tools_menu.add_command(label="处理Show文件", command=self.process_show_files_unified)
        tools_menu.add_separator()
        tools_menu.add_command(label="查看状态矩阵", command=self.show_status_matrix)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        
    def create_login_page(self):
        """创建登录页面"""
        login_frame = ttk.Frame(self.notebook)
        self.notebook.add(login_frame, text="登录")
        
        # 登录表单
        form_frame = ttk.Frame(login_frame, padding=50)
        form_frame.pack(expand=True)
        
        ttk.Label(form_frame, text="F5配置翻译工具", font=("Arial", 20, "bold")).pack(pady=20)
        
        # 用户名
        ttk.Label(form_frame, text="用户名:").pack(pady=5)
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.pack(pady=5)
        
        # 密码
        ttk.Label(form_frame, text="密码:").pack(pady=5)
        self.password_entry = ttk.Entry(form_frame, show="*", width=30)
        self.password_entry.pack(pady=5)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="登录", command=self.login).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="注册", command=self.register).pack(side=tk.LEFT, padx=10)
        
    def create_main_page(self):
        """创建主页面"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="主页")
        
        # 欢迎信息
        welcome_frame = ttk.Frame(main_frame, padding=50)
        welcome_frame.pack(expand=True)
        
        self.welcome_label = ttk.Label(welcome_frame, text="欢迎使用F5配置翻译工具", font=("Arial", 16, "bold"))
        self.welcome_label.pack(pady=20)
        
        # 功能按钮
        buttons_frame = ttk.Frame(welcome_frame)
        buttons_frame.pack(pady=20)
        
        ttk.Button(buttons_frame, text="UCS配置处理", command=lambda: self.notebook.select(2)).pack(pady=10, fill=tk.X)
        ttk.Button(buttons_frame, text="Show配置处理", command=lambda: self.notebook.select(3)).pack(pady=10, fill=tk.X)
        ttk.Button(buttons_frame, text="文件管理", command=lambda: self.notebook.select(4)).pack(pady=10, fill=tk.X)
        ttk.Button(buttons_frame, text="系统日志", command=lambda: self.notebook.select(5)).pack(pady=10, fill=tk.X)
        
    def create_ucs_page(self):
        """创建UCS处理页面"""
        ucs_frame = ttk.Frame(self.notebook)
        self.notebook.add(ucs_frame, text="UCS处理")
        
        # 左侧：文件列表
        left_frame = ttk.Frame(ucs_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(left_frame, text="UCS文件列表", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 文件列表
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.ucs_file_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.ucs_file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ucs_file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ucs_file_listbox.config(yscrollcommand=scrollbar.set)
        
        # 按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="上传文件", command=lambda: self.upload_files('ucs')).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="删除文件", command=lambda: self.delete_files('ucs')).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="刷新列表", command=lambda: self.refresh_file_list('ucs')).pack(side=tk.LEFT, padx=2)
        
        # 右侧：处理操作
        right_frame = ttk.Frame(ucs_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(right_frame, text="处理操作", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 处理按钮 - 使用与web相同的处理流程
        process_frame = ttk.Frame(right_frame)
        process_frame.pack(fill=tk.X, pady=5)
        
        # 统一的处理按钮，模拟web的处理机制
        ttk.Button(process_frame, text="处理UCS文件", command=lambda: self.process_ucs_files_unified()).pack(fill=tk.X, pady=2)
        
        # 状态显示
        status_frame = ttk.LabelFrame(right_frame, text="处理状态", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.ucs_status_tree = ttk.Treeview(status_frame, columns=("status",), show="tree headings")
        self.ucs_status_tree.heading("#0", text="文件名")
        self.ucs_status_tree.heading("status", text="状态")
        self.ucs_status_tree.pack(fill=tk.BOTH, expand=True)
        
    def create_show_page(self):
        """创建Show处理页面"""
        show_frame = ttk.Frame(self.notebook)
        self.notebook.add(show_frame, text="Show处理")
        
        # 左侧：文件列表
        left_frame = ttk.Frame(show_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Show文件列表", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 文件列表
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.show_file_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.show_file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.show_file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.show_file_listbox.config(yscrollcommand=scrollbar.set)
        
        # 按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="上传文件", command=lambda: self.upload_files('show')).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="删除文件", command=lambda: self.delete_files('show')).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="刷新列表", command=lambda: self.refresh_file_list('show')).pack(side=tk.LEFT, padx=2)
        
        # 右侧：处理操作
        right_frame = ttk.Frame(show_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(right_frame, text="处理操作", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 处理按钮 - 使用与web相同的处理流程
        process_frame = ttk.Frame(right_frame)
        process_frame.pack(fill=tk.X, pady=5)
        
        # 统一的处理按钮，模拟web的处理机制
        ttk.Button(process_frame, text="处理Show文件", command=lambda: self.process_show_files_unified()).pack(fill=tk.X, pady=2)
        
        # 状态显示
        status_frame = ttk.LabelFrame(right_frame, text="处理状态", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.show_status_tree = ttk.Treeview(status_frame, columns=("status",), show="tree headings")
        self.show_status_tree.heading("#0", text="文件名")
        self.show_status_tree.heading("status", text="状态")
        self.show_status_tree.pack(fill=tk.BOTH, expand=True)
        
    def create_files_page(self):
        """创建文件管理页面"""
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="文件管理")
        
        # 文件类型选择
        type_frame = ttk.Frame(files_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(type_frame, text="文件类型:").pack(side=tk.LEFT)
        self.file_type_var = tk.StringVar(value="ucs")
        ttk.Radiobutton(type_frame, text="UCS", variable=self.file_type_var, value="ucs", 
                       command=self.refresh_file_list).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="Show", variable=self.file_type_var, value="show", 
                       command=self.refresh_file_list).pack(side=tk.LEFT, padx=10)
        
        # 文件列表
        list_frame = ttk.Frame(files_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # 操作按钮
        button_frame = ttk.Frame(files_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="下载文件", command=self.download_selected_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="删除文件", command=self.delete_selected_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="查看状态", command=self.show_file_status).pack(side=tk.LEFT, padx=2)
        
    def create_logs_page(self):
        """创建日志页面"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="系统日志")
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(logs_frame, text="应用日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 日志操作按钮
        button_frame = ttk.Frame(logs_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="刷新日志", command=self.refresh_logs).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="清空日志", command=self.clear_logs).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="保存日志", command=self.save_logs).pack(side=tk.LEFT, padx=2)
        
    def create_log_area(self):
        """创建日志区域"""
        log_frame = ttk.LabelFrame(self.app, text="实时日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def login(self):
        """用户登录"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return
            
        try:
            session_id = user_manager.authenticate_user(username, password)
            if session_id:
                self.current_user = username
                self.status_label.config(text=f"状态: 已登录 - {username}")
                self.welcome_label.config(text=f"欢迎, {username}!")
                
                # 切换到主页
                self.notebook.select(1)
                
                # 刷新文件列表
                self.refresh_file_list()
                
                messagebox.showinfo("成功", "登录成功！")
            else:
                messagebox.showerror("错误", "用户名或密码错误")
        except Exception as e:
            messagebox.showerror("错误", f"登录失败: {str(e)}")
            
    def register(self):
        """用户注册"""
        username = simpledialog.askstring("注册", "请输入用户名:")
        if not username:
            return
            
        password = simpledialog.askstring("注册", "请输入密码:", show="*")
        if not password:
            return
            
        confirm_password = simpledialog.askstring("注册", "请确认密码:", show="*")
        if not confirm_password:
            return
            
        if password != confirm_password:
            messagebox.showerror("错误", "两次输入的密码不一致")
            return
            
        if len(password) < 6:
            messagebox.showerror("错误", "密码长度至少6位")
            return
            
        try:
            if user_manager.register_user(username, password):
                messagebox.showinfo("成功", "注册成功！请登录")
            else:
                messagebox.showerror("错误", "用户名已存在")
        except Exception as e:
            messagebox.showerror("错误", f"注册失败: {str(e)}")
            
    def upload_files(self, file_type=None):
        """上传文件"""
        if not self.current_user:
            messagebox.showerror("错误", "请先登录")
            return
            
        if not file_type:
            file_type = self.file_type_var.get()
            
        # 选择文件
        filetypes = []
        if file_type == 'ucs':
            filetypes = [("UCS文件", "*.ucs"), ("TAR文件", "*.tar"), ("所有文件", "*.*")]
        elif file_type == 'show':
            filetypes = [("TXT文件", "*.txt"), ("CONF文件", "*.conf"), ("所有文件", "*.*")]
            
        files = filedialog.askopenfilenames(
            title=f"选择{file_type.upper()}文件",
            filetypes=filetypes
        )
        
        if not files:
            return
            
        # 上传文件
        try:
            upload_dir = user_manager.get_user_upload_dir(self.current_user, file_type)
            os.makedirs(upload_dir, exist_ok=True)
            
            uploaded_count = 0
            for file_path in files:
                filename = os.path.basename(file_path)
                dest_path = os.path.join(upload_dir, filename)
                shutil.copy2(file_path, dest_path)
                uploaded_count += 1
                
            messagebox.showinfo("成功", f"成功上传 {uploaded_count} 个文件")
            self.refresh_file_list(file_type)
            
        except Exception as e:
            messagebox.showerror("错误", f"上传失败: {str(e)}")
            
    def download_files(self):
        """下载文件（菜单功能）"""
        if not self.current_user:
            messagebox.showerror("错误", "请先登录")
            return
            
        # 选择保存目录
        save_dir = filedialog.askdirectory(title="选择保存目录")
        if not save_dir:
            return
            
        try:
            file_type = self.file_type_var.get()
            upload_dir = user_manager.get_user_upload_dir(self.current_user, file_type)
            
            if not os.path.exists(upload_dir):
                messagebox.showwarning("警告", "没有可下载的文件")
                return
                
            # 下载所有文件
            files = os.listdir(upload_dir)
            if not files:
                messagebox.showwarning("警告", "没有可下载的文件")
                return
                
            downloaded_count = 0
            for filename in files:
                src_path = os.path.join(upload_dir, filename)
                dst_path = os.path.join(save_dir, filename)
                
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                    downloaded_count += 1
                    
            messagebox.showinfo("成功", f"成功下载 {downloaded_count} 个文件")
            
        except Exception as e:
            messagebox.showerror("错误", f"下载失败: {str(e)}")
            
    def refresh_file_list(self, file_type=None):
        """刷新文件列表"""
        if not self.current_user:
            return
            
        if not file_type:
            file_type = self.file_type_var.get()
            
        try:
            files = user_manager.get_user_files(self.current_user, file_type)
            
            # 更新对应的列表框
            if file_type == 'ucs' and hasattr(self, 'ucs_file_listbox'):
                self.ucs_file_listbox.delete(0, tk.END)
                for file in files:
                    self.ucs_file_listbox.insert(tk.END, file)
            elif file_type == 'show' and hasattr(self, 'show_file_listbox'):
                self.show_file_listbox.delete(0, tk.END)
                for file in files:
                    self.show_file_listbox.insert(tk.END, file)
                    
            # 更新文件管理页面的列表
            if hasattr(self, 'file_listbox'):
                self.file_listbox.delete(0, tk.END)
                for file in files:
                    self.file_listbox.insert(tk.END, file)
                    
        except Exception as e:
            print(f"刷新文件列表失败: {e}")
            
    def process_files(self, file_type, action):
        """处理文件"""
        if not self.current_user:
            messagebox.showerror("错误", "请先登录")
            return
            
        try:
            # 获取处理器
            processor = F5UCSProcessor()
            processor.user_processed_dir = user_manager.get_user_processed_dir(self.current_user, file_type)
            
            # 获取文件列表
            files = user_manager.get_user_files(self.current_user, file_type)
            
            if not files:
                messagebox.showwarning("警告", "没有可处理的文件")
                return
                
            # 执行处理
            self.status_label.config(text=f"状态: 正在处理{file_type}文件...")
            
            # 在新线程中执行处理
            thread = threading.Thread(target=self._process_files_thread, args=(processor, files, action, file_type))
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")
            self.status_label.config(text="状态: 处理失败")
            
    def _process_files_thread(self, processor, files, action, file_type):
        """在后台线程中处理文件"""
        try:
            if action == 'ucs_to_zip':
                for file in files:
                    if file.lower().endswith('.ucs'):
                        file_path = os.path.join(user_manager.get_user_upload_dir(self.current_user, file_type), file)
                        processor.ucs_to_zip(file_path)
                        
            elif action == 'unzip_files':
                for file in files:
                    if file.lower().endswith('.tar'):
                        file_path = os.path.join(user_manager.get_user_upload_dir(self.current_user, file_type), file)
                        processor.untar_file(file_path)
                        
            elif action == 'extract_conf_base':
                processor.extract_conf_and_base(processor.user_processed_dir)
                
            elif action == 'conf_and_base_to_excel_txt':
                # 导入处理模块
                from core.function.ucs.lxl_package_4_BaseConfProcess.F5_base_to_excel_txt import process_folder as process_base_folder
                from core.function.ucs.lxl_package_3_ConfProcess.Conf_Add_File import process_folder as process_conf_folder
                
                ucs_dir = os.path.dirname(processor.user_processed_dir)
                conf_dir = os.path.join(ucs_dir, 'conf')
                base_dir = os.path.join(ucs_dir, 'base')
                
                if os.path.exists(conf_dir):
                    process_conf_folder(conf_dir)
                if os.path.exists(base_dir):
                    process_base_folder(base_dir)
                    
            # 更新状态
            self.app.after(0, lambda: self.status_label.config(text="状态: 处理完成"))
            self.app.after(0, lambda: messagebox.showinfo("成功", "文件处理完成"))
            self.app.after(0, self.refresh_file_list)
            
        except Exception as e:
            self.app.after(0, lambda: self.status_label.config(text="状态: 处理失败"))
            self.app.after(0, lambda: messagebox.showerror("错误", f"处理失败: {str(e)}"))
            
    def download_selected_files(self):
        """下载选中的文件"""
        if not self.current_user:
            messagebox.showerror("错误", "请先登录")
            return
            
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要下载的文件")
            return
            
        # 选择保存目录
        save_dir = filedialog.askdirectory(title="选择保存目录")
        if not save_dir:
            return
            
        try:
            file_type = self.file_type_var.get()
            upload_dir = user_manager.get_user_upload_dir(self.current_user, file_type)
            
            downloaded_count = 0
            for index in selection:
                filename = self.file_listbox.get(index)
                src_path = os.path.join(upload_dir, filename)
                dst_path = os.path.join(save_dir, filename)
                
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dst_path)
                    downloaded_count += 1
                    
            messagebox.showinfo("成功", f"成功下载 {downloaded_count} 个文件")
            
        except Exception as e:
            messagebox.showerror("错误", f"下载失败: {str(e)}")
            
    def delete_files(self, file_type):
        """删除文件"""
        if not self.current_user:
            messagebox.showerror("错误", "请先登录")
            return
            
        # 获取选中的文件
        if file_type == 'ucs' and hasattr(self, 'ucs_file_listbox'):
            selection = self.ucs_file_listbox.curselection()
            listbox = self.ucs_file_listbox
        elif file_type == 'show' and hasattr(self, 'show_file_listbox'):
            selection = self.show_file_listbox.curselection()
            listbox = self.show_file_listbox
        else:
            return
            
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的文件")
            return
            
        # 确认删除
        if not messagebox.askyesno("确认", "确定要删除选中的文件吗？"):
            return
            
        try:
            upload_dir = user_manager.get_user_upload_dir(self.current_user, file_type)
            
            deleted_count = 0
            for index in selection:
                filename = listbox.get(index)
                file_path = os.path.join(upload_dir, filename)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    
            messagebox.showinfo("成功", f"成功删除 {deleted_count} 个文件")
            self.refresh_file_list(file_type)
            
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")
            
    def delete_selected_files(self):
        """删除选中的文件（文件管理页面）"""
        file_type = self.file_type_var.get()
        self.delete_files(file_type)
        
    def show_file_status(self):
        """显示文件状态"""
        if not self.current_user:
            messagebox.showerror("错误", "请先登录")
            return
            
        file_type = self.file_type_var.get()
        
        try:
            # 获取状态矩阵
            if file_type == 'ucs':
                status_data = self.get_ucs_status_matrix()
            else:
                status_data = self.get_show_status_matrix()
                
            # 显示状态窗口
            self.show_status_window(status_data, file_type)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取状态失败: {str(e)}")
            
    def get_ucs_status_matrix(self):
        """获取UCS状态矩阵"""
        # 这里实现与Web应用相同的状态矩阵逻辑
        # 简化版本，实际应该与Web应用保持一致
        return {}
        
    def get_show_status_matrix(self):
        """获取Show状态矩阵"""
        # 这里实现与Web应用相同的状态矩阵逻辑
        return {}
        
    def show_status_window(self, status_data, file_type):
        """显示状态窗口"""
        status_window = tk.Toplevel(self.app)
        status_window.title(f"{file_type.upper()}文件状态")
        status_window.geometry("600x400")
        
        # 创建状态树形视图
        tree = ttk.Treeview(status_window, columns=("ucs", "tar", "extracted", "conf", "base"), show="tree headings")
        tree.heading("#0", text="文件名")
        tree.heading("ucs", text="UCS")
        tree.heading("tar", text="TAR")
        tree.heading("extracted", text="已解压")
        tree.heading("conf", text="CONF")
        tree.heading("base", text="BASE")
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def show_status_matrix(self):
        """显示状态矩阵"""
        self.show_file_status()
        

        
    def process_ucs_files_unified(self):
        """统一处理UCS文件（模拟Web应用的流程）"""
        if not self.current_user:
            messagebox.showerror("错误", "请先登录")
            return
            
        # 切换到UCS处理页面
        self.notebook.select(2)
        
        # 获取文件列表
        files = user_manager.get_user_files(self.current_user, 'ucs')
        if not files:
            messagebox.showwarning("警告", "没有可处理的UCS文件")
            return
            
        # 执行处理
        self.status_label.config(text="状态: 正在处理UCS文件...")
        
        # 在新线程中执行处理
        thread = threading.Thread(target=self._process_ucs_files_thread, args=(files,))
        thread.daemon = True
        thread.start()
        
    def _process_ucs_files_thread(self, files):
        """在后台线程中处理UCS文件"""
        try:
            # 获取统一处理器
            processor = UnifiedProcessor(user_manager.get_user_processed_dir(self.current_user, 'ucs'))
            
            # 获取上传目录
            upload_dir = user_manager.get_user_upload_dir(self.current_user, 'ucs')
            
            # 执行处理
            result = processor.process_ucs_files(files, upload_dir)
            
            if result['success']:
                # 更新状态
                self.app.after(0, lambda: self.status_label.config(text="状态: 处理完成"))
                self.app.after(0, lambda: messagebox.showinfo("成功", f"UCS文件处理完成\n共处理 {len(result['processed_files'])} 个文件"))
            else:
                # 处理失败
                self.app.after(0, lambda: self.status_label.config(text="状态: 处理失败"))
                self.app.after(0, lambda: messagebox.showerror("错误", f"处理失败: {result['error']}"))
            
            self.app.after(0, self.refresh_file_list)
            
        except Exception as e:
            self.app.after(0, lambda: self.status_label.config(text="状态: 处理失败"))
            self.app.after(0, lambda: messagebox.showerror("错误", f"处理失败: {str(e)}"))
            
    def process_show_files_unified(self):
        """统一处理Show文件（模拟Web应用的流程）"""
        if not self.current_user:
            messagebox.showerror("错误", "请先登录")
            return
            
        # 切换到Show处理页面
        self.notebook.select(3)
        
        # 获取文件列表
        files = user_manager.get_user_files(self.current_user, 'show')
        if not files:
            messagebox.showwarning("警告", "没有可处理的Show文件")
            return
            
        # 执行处理
        self.status_label.config(text="状态: 正在处理Show文件...")
        
        # 在新线程中执行处理
        thread = threading.Thread(target=self._process_show_files_thread, args=(files,))
        thread.daemon = True
        thread.start()
        
    def _process_show_files_thread(self, files):
        """在后台线程中处理Show文件"""
        try:
            # 获取统一处理器
            processor = UnifiedProcessor(user_manager.get_user_processed_dir(self.current_user, 'show'))
            
            # 获取上传目录
            upload_dir = user_manager.get_user_upload_dir(self.current_user, 'show')
            
            # 执行处理
            result = processor.process_show_files(files, upload_dir)
            
            if result['success']:
                # 更新状态
                self.app.after(0, lambda: self.status_label.config(text="状态: 处理完成"))
                self.app.after(0, lambda: messagebox.showinfo("成功", f"Show文件处理完成\n共处理 {len(result['processed_files'])} 个文件"))
            else:
                # 处理失败
                self.app.after(0, lambda: self.status_label.config(text="状态: 处理失败"))
                self.app.after(0, lambda: messagebox.showerror("错误", f"处理失败: {result['error']}"))
            
            self.app.after(0, self.refresh_file_list)
            
        except Exception as e:
            self.app.after(0, lambda: self.status_label.config(text="状态: 处理失败"))
            self.app.after(0, lambda: messagebox.showerror("错误", f"处理失败: {str(e)}"))
            
    def refresh_logs(self):
        """刷新日志"""
        try:
            log_file = os.path.join(Config.DATA_DIR, 'logs', 'app.log')
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.log_text.delete(1.0, tk.END)
                    self.log_text.insert(1.0, content)
            else:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(1.0, "日志文件不存在")
        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(1.0, f"读取日志失败: {str(e)}")
            
    def clear_logs(self):
        """清空日志"""
        if messagebox.askyesno("确认", "确定要清空日志吗？"):
            try:
                log_file = os.path.join(Config.DATA_DIR, 'logs', 'app.log')
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write('')
                self.refresh_logs()
                messagebox.showinfo("成功", "日志已清空")
            except Exception as e:
                messagebox.showerror("错误", f"清空日志失败: {str(e)}")
                
    def save_logs(self):
        """保存日志"""
        file_path = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".log",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                content = self.log_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", "日志已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志失败: {str(e)}")
                
    def show_about(self):
        """显示关于信息"""
        about_text = """
F5配置翻译工具 - 桌面版
版本: 1.0.0

功能特性:
- UCS配置文件处理
- Show配置文件处理
- 用户管理和文件隔离
- 实时状态跟踪
- 文件上传下载管理

技术支持: 请联系开发团队
        """
        messagebox.showinfo("关于", about_text)
        
    def run(self):
        """运行应用程序"""
        self.app.mainloop()

def main():
    """主程序入口"""
    app = DesktopApp()
    app.run()

if __name__ == "__main__":
    main() 