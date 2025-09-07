import os
import tkinter as tk
from tkinter import filedialog


def run_script():
    # 创建一个Tkinter根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口

    # 弹出文件选择对话框，让用户选择目录
    directory_path = filedialog.askdirectory()

    if directory_path:
        # 获取目录内所有文件的列表
        file_list = os.listdir(directory_path)

        # 遍历文件列表，将后缀从.ucs改为.zip
        for filename in file_list:
            if filename.endswith(".txt"):
                new_filename = os.path.splitext(filename)[0] + ".log"
                old_filepath = os.path.join(directory_path, filename)
                new_filepath = os.path.join(directory_path, new_filename)
                os.rename(old_filepath, new_filepath)

        print("后缀已成功更改为.log")
    else:
        print("未选择目录")

    # 关闭Tkinter根窗口
    root.destroy()
