import os
import logging
import tkinter as tk
from tkinter import filedialog

logger = logging.getLogger(__name__)

def process_file(file_path):
    """处理单个TXT文件，将其重命名为LOG文件"""
    try:
        if not file_path.endswith(".txt"):
            return {
                "message": "文件不是TXT格式",
                "success": False
            }
            
        new_filename = os.path.splitext(os.path.basename(file_path))[0] + ".log"
        new_filepath = os.path.join(os.path.dirname(file_path), new_filename)
        
        os.rename(file_path, new_filepath)
        logger.info(f"TXT文件已成功重命名为LOG: {os.path.basename(file_path)} -> {new_filename}")
        
        return {
            "message": "TXT文件已成功转换为LOG",
            "success": True
        }
    except Exception as e:
        logger.error(f"处理TXT文件时出错: {str(e)}")
        return {
            "message": f"处理TXT文件时出错: {str(e)}",
            "success": False
        }

def run_script():
    """运行脚本，选择文件夹并处理TXT文件"""
    # 创建一个Tkinter根窗口并隐藏它
    root = tk.Tk()
    root.withdraw()

    # 使用文件夹选择对话框来获取用户选择的文件夹
    folder_path = filedialog.askdirectory()
    
    if not folder_path:
        print("未选择文件夹")
        return
    
    print(f"选择的文件夹: {folder_path}")
    
    # 遍历文件夹中的所有文件
    processed_count = 0
    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root_dir, file)
                result = process_file(file_path)
                if result["success"]:
                    processed_count += 1
                    print(f"成功处理: {file}")
                else:
                    print(f"处理失败: {file} - {result['message']}")
    
    print(f"处理完成，共处理 {processed_count} 个TXT文件")
