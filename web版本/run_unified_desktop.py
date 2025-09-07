#!/usr/bin/env python3
"""
F5配置翻译工具 - 统一桌面应用启动脚本
使用与Web应用相同的处理机制
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 检查Python环境
python_path = sys.executable
print(f"使用Python环境: {python_path}")

# 检查是否在正确的虚拟环境中
if "Python11" not in python_path:
    print("警告: 建议使用Python11环境")
    print("请使用以下命令启动:")
    print("/opt/anaconda3/envs/Python11/bin/python run_unified_desktop.py")

try:
    from desktop.advanced_app import main
    
    if __name__ == "__main__":
        print("启动F5配置翻译工具 - 统一桌面应用")
        print("使用与Web应用相同的处理机制")
        print("-" * 50)
        main()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖包已安装")
    print("可以运行: pip install -r requirements/desktop.txt")
except Exception as e:
    print(f"启动失败: {e}")
    import traceback
    traceback.print_exc() 