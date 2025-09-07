import os
import shutil
import tkinter as tk
from tkinter import filedialog


def extract_conf_and_base(base_directory, output_directory=None):
    """提取conf和base文件到指定目录"""
    if not base_directory or not os.path.exists(base_directory):
        return {
            'status': 'error',
            'error': f"目录不存在: {base_directory}"
        }
    
    # 如果没有指定输出目录，则在base_directory同级创建conf和base目录
    if output_directory is None:
        output_directory = os.path.dirname(base_directory)
    
    # 创建conf和base目录
    conf_dir = os.path.join(output_directory, 'conf')
    base_dir = os.path.join(output_directory, 'base')
    os.makedirs(conf_dir, exist_ok=True)
    os.makedirs(base_dir, exist_ok=True)
    
    extracted_files = {
        'conf': [],
        'base': []
    }
    
    # 遍历processed目录中的所有文件夹
    for item in os.listdir(base_directory):
        item_path = os.path.join(base_directory, item)
        if os.path.isdir(item_path):
            # 在每个文件夹中查找config目录
            config_dir = os.path.join(item_path, 'config')
            if os.path.exists(config_dir) and os.path.isdir(config_dir):
                
                # 查找 bigip.conf 文件并复制到 'conf' 目录
                bigip_conf_file = os.path.join(config_dir, 'bigip.conf')
                if os.path.isfile(bigip_conf_file):
                    new_conf_file = os.path.join(conf_dir, f"{item}_bigip.conf")
                    shutil.copy2(bigip_conf_file, new_conf_file)
                    extracted_files['conf'].append(new_conf_file)
                
                # 查找 bigip_base.conf 文件并复制到 'base' 目录
                bigip_base_conf_file = os.path.join(config_dir, 'bigip_base.conf')
                if os.path.isfile(bigip_base_conf_file):
                    new_base_file = os.path.join(base_dir, f"{item}_bigip_base.conf")
                    shutil.copy2(bigip_base_conf_file, new_base_file)
                    extracted_files['base'].append(new_base_file)
    
    return {
        'status': 'success',
        'conf_dir': conf_dir,
        'base_dir': base_dir,
        'extracted_files': extracted_files
    }


def run_script():
    """原始的GUI脚本，保持向后兼容"""
    # 创建一个Tkinter根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口

    # 弹出文件选择对话框，让用户选择目录
    base_directory = filedialog.askdirectory()

    if base_directory:
        result = extract_conf_and_base(base_directory)
        if result['status'] == 'success':
            pass # 移除 print 语句
        else:
            print(f"提取失败: {result['error']}")
    else:
        print("未选择目录")

    # 关闭Tkinter根窗口
    root.destroy()
