import tkinter as tk
from tkinter import filedialog

from .Conf_Add_File import process_folder


def run_script():
    # 创建一个Tkinter根窗口并隐藏它
    root = tk.Tk()
    root.withdraw()

    # 使用文件夹选择对话框来获取用户选择的文件夹
    folder_path = filedialog.askdirectory()
    process_folder(folder_path)
