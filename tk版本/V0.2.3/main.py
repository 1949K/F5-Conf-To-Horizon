import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Callable


class ConfigTranslatorApp:
    """配置翻译工具主应用类"""

    def __init__(self):
        self.app = tk.Tk()
        self.app.title("配置翻译工具")
        self._setup_main_window()
        self.notebook = None
        self.status_label = None
        self.log_text = None

        # 重定向标准输出
        self.original_stdout = sys.stdout
        sys.stdout = self  # 将标准输出重定向到当前对象

    def write(self, text):
        """重写write方法以捕获print输出"""
        if self.log_text:
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)
        self.original_stdout.write(text)  # 仍然保留控制台输出

    def flush(self):
        """重写flush方法"""
        self.original_stdout.flush()

    def __del__(self):
        """恢复标准输出"""
        sys.stdout = self.original_stdout

    def _setup_main_window(self) -> None:
        """设置主窗口大小和位置"""
        screen_width = self.app.winfo_screenwidth()
        screen_height = self.app.winfo_screenheight()

        window_width = 500  # 增加宽度以容纳日志区域
        window_height = 400  # 增加高度

        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        self.app.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.app.update_idletasks()

        self.app.attributes('-topmost', True)
        self.app.after(100, lambda: self.app.attributes('-topmost', False))

        style = ttk.Style()
        style.theme_use("clam")
        self.app.configure(bg="#f5f5f5")

    def safe_run(self, script_func: Callable[[], None], status_label: ttk.Label) -> None:
        """安全执行脚本的通用方法"""
        try:
            status_label.config(text="状态: 正在执行脚本...")
            self.app.update()

            # 清空日志区域
            if self.log_text:
                self.log_text.delete(1.0, tk.END)

            script_func()

            status_label.config(text="状态: 软件模块执行成功！")
            # messagebox.showinfo("成功", "软件模块执行成功！")
        except Exception as e:
            status_label.config(text="状态: 软件模块执行失败")
            messagebox.showerror("错误", f"软件模块执行时出错：{str(e)}")
            with open("error_log.txt", "a") as f:
                f.write(f"Error occurred: {str(e)}\n")

    def create_f5_module(self, tab_frame: ttk.Frame) -> None:
        """创建F5 UCS配置翻译模块"""
        block = ttk.LabelFrame(tab_frame, text="F5 UCS 配置翻译", padding=(10, 10))
        block.pack(fill="both", expand=True, padx=10, pady=10)

        # 动态导入模块以避免启动时加载所有模块
        from f5_ucs.lxl_package_1_UCStoZIP.F5_UCS_to_ZIP import run_script as run_UCS_to_ZIP
        from f5_ucs.lxl_package_2_MargeConfFile.F5_Marge_conf_and_base import run_script as run_Marge_conf_and_base
        from f5_ucs.lxl_package_3_ConfProcess.F5_Conf_To_Excel_Txt import run_script as run_F5_conf_to_excel_txt
        from f5_ucs.lxl_package_4_BaseConfProcess.F5_base_to_excel_txt import run_script as run_F5_base_to_excel_txt

        buttons = [
            ("1-UCS后缀改为ZIP", run_UCS_to_ZIP),
            ("2-提取conf和base", run_Marge_conf_and_base),
            ("3-conf翻译为txt和excel", run_F5_conf_to_excel_txt),
            ("4-base翻译为txt和excel", run_F5_base_to_excel_txt)
        ]

        for text, command in buttons:
            btn = ttk.Button(
                block,
                text=text,
                command=lambda cmd=command: self.safe_run(cmd, self.status_label)
            )
            btn.pack(padx=10, pady=5, fill="x")

    def create_f5_show_module(self, tab_frame: ttk.Frame) -> None:
        """创建F5 Show配置翻译模块"""
        block = ttk.LabelFrame(tab_frame, text="F5 Show 配置翻译", padding=(10, 10))
        block.pack(fill="both", expand=True, padx=10, pady=10)

        # 动态导入模块
        from f5_show.lxl_package_1_Txt_to_Log.F5_txt_to_log import run_script as run_txt_to_log
        from f5_show.lxl_package_3_ConfProcess.F5_Conf_To_Excel_Txt import run_script as run_F5_show_conf_to_excel_txt
        from f5_show.lxl_package_4_BaseConfProcess.F5_base_to_excel_txt import \
            run_script as run_F5_show_base_to_excel_txt

        buttons = [
            ("1-txt后缀改为log", run_txt_to_log),
            ("2-show conf翻译为txt和excel", run_F5_show_conf_to_excel_txt),
            ("3-show base翻译为txt和excel", run_F5_show_base_to_excel_txt)
        ]

        for text, command in buttons:
            btn = ttk.Button(
                block,
                text=text,
                command=lambda cmd=command: self.safe_run(cmd, self.status_label)
            )
            btn.pack(padx=10, pady=5, fill="x")

    def create_main_screen(self, tab_frame: ttk.Frame) -> None:
        """创建主界面"""
        welcome_frame = ttk.Frame(tab_frame, padding=(20, 20))
        welcome_frame.pack(fill="both", expand=True)

        ttk.Label(
            welcome_frame,
            text="配置翻译工具",
            font=("Arial", 16, "bold"),
            anchor="center"
        ).pack(pady=(20, 10))

        ttk.Label(
            welcome_frame,
            text="欢迎使用配置翻译工具，请选择一个功能模块开始。",
            anchor="center"
        ).pack(pady=(0, 20))

        button_style = {"padx": 50, "pady": 10, "fill": "x"}

        ttk.Button(
            welcome_frame,
            text="进入 F5 UCS 配置翻译模块",
            command=lambda: self.notebook.select(1)
        ).pack(**button_style)

        ttk.Button(
            welcome_frame,
            text="进入 F5 show 配置翻译模块",
            command=lambda: self.notebook.select(2)
        ).pack(**button_style)

    def create_log_area(self, parent: tk.Widget) -> None:
        """创建日志显示区域"""
        log_frame = ttk.LabelFrame(parent, text="执行日志", padding=(10, 10))
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=10,
            font=('Consolas', 10)
        )
        self.log_text.pack(fill="both", expand=True)

    def setup_ui(self) -> None:
        """设置主界面UI"""
        main_frame = ttk.Frame(self.app)
        main_frame.pack(fill="both", expand=True)

        # 上部区域 - 选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # 创建选项卡
        tabs = [
            ttk.Frame(self.notebook),  # 主界面
            ttk.Frame(self.notebook),  # F5 UCS
            ttk.Frame(self.notebook)  # F5 Show
        ]

        self.notebook.add(tabs[0], text="主界面")
        self.notebook.add(tabs[1], text="F5 UCS 配置翻译")
        self.notebook.add(tabs[2], text="F5 show 配置翻译")

        # 创建各模块界面
        self.create_main_screen(tabs[0])
        self.create_f5_module(tabs[1])
        self.create_f5_show_module(tabs[2])

        # 状态栏
        self.status_label = ttk.Label(
            self.app,
            text="状态: 待命",
            anchor="w",
            relief="sunken",
            padding=(5, 5)
        )
        self.status_label.pack(side="bottom", fill="x")

        # 日志区域
        self.create_log_area(main_frame)

    def run(self) -> None:
        """运行应用程序"""
        self.setup_ui()
        self.app.mainloop()


if __name__ == "__main__":
    app = ConfigTranslatorApp()
    app.run()