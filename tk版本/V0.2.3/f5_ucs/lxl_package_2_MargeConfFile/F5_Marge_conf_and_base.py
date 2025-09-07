import os
import shutil
import tkinter as tk
from tkinter import filedialog


def run_script():
    # 创建一个Tkinter根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口

    # 弹出文件选择对话框，让用户选择目录
    base_directory = filedialog.askdirectory()

    if base_directory:
        # 新建名为 'bigip_conf' 和 'bigip_base' 的目录
        bigip_dir = os.path.join(base_directory, 'bigip_conf')
        os.makedirs(bigip_dir, exist_ok=True)
        bigip_base_dir = os.path.join(base_directory, 'bigip_base')
        os.makedirs(bigip_base_dir, exist_ok=True)

        # 遍历目录，查找包含 'conf' 目录的文件夹
        for root_dir, subdirs, files in os.walk(base_directory):
            for subdir in subdirs:
                conf_dir = os.path.join(root_dir, subdir, 'config')

                # 查找 bigip.conf 文件并复制到 'bigip_conf' 目录
                bigip_conf_file = os.path.join(conf_dir, 'bigip.conf')
                if os.path.isfile(bigip_conf_file):
                    new_bigip_file = os.path.join(bigip_dir, f"{subdir}_bigip.conf")
                    shutil.copy(bigip_conf_file, new_bigip_file)

                # 查找 bigip_base.conf 文件并复制到 'bigip_base' 目录
                bigip_base_conf_file = os.path.join(conf_dir, 'bigip_base.conf')
                if os.path.isfile(bigip_base_conf_file):
                    new_bigip_base_file = os.path.join(bigip_base_dir, f"{subdir}_bigip_base.conf")
                    shutil.copy(bigip_base_conf_file, new_bigip_base_file)

        print("bigip.conf 和 bigip_base.conf 文件已复制到 '/bigip_conf/' 和 '/bigip_base/' 目录")
    else:
        print("未选择目录")

    # 关闭Tkinter根窗口
    root.destroy()
