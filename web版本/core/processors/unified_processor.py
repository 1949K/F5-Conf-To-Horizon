#!/usr/bin/env python3
"""
统一处理管理器
为桌面应用和web应用提供相同的处理逻辑
"""

import os
import logging
from typing import List, Dict, Any
from .f5_ucs_processor import F5UCSProcessor

logger = logging.getLogger(__name__)

class UnifiedProcessor:
    """统一处理管理器"""
    
    def __init__(self, user_processed_dir: str = None):
        self.user_processed_dir = user_processed_dir
        self.ucs_processor = F5UCSProcessor(user_processed_dir=user_processed_dir)
        
    def process_ucs_files(self, files: List[str], upload_dir: str) -> Dict[str, Any]:
        """处理UCS文件 - 完整的处理流程"""
        try:
            results = []
            processed_files = []
            
            # 第一步：处理所有UCS文件 - UCS转TAR
            ucs_results = []
            for file in files:
                if file.lower().endswith('.ucs'):
                    file_path = os.path.join(upload_dir, file)
                    try:
                        tar_path = self.ucs_processor.ucs_to_zip(file_path)
                        ucs_results.append({
                            'original': file,
                            'converted': os.path.basename(tar_path)
                        })
                        results.append(f'UCS转TAR完成: {file}')
                    except Exception as e:
                        results.append(f'UCS转TAR失败: {file} - {str(e)}')
            
            # 第二步：解压所有TAR文件
            tar_files = [f for f in files if f.lower().endswith('.tar')]
            for file in tar_files:
                file_path = os.path.join(upload_dir, file)
                try:
                    extracted_path = self.ucs_processor.untar_file(file_path)
                    results.append(f'TAR解压完成: {file}')
                except Exception as e:
                    results.append(f'TAR解压失败: {file} - {str(e)}')
            
            # 第三步：从解压目录中提取配置文件
            if os.path.exists(self.user_processed_dir):
                try:
                    result = self.ucs_processor.extract_conf_and_base(self.user_processed_dir)
                    if result['status'] == 'success':
                        results.append('配置文件提取完成')
                    else:
                        results.append(f'配置文件提取失败: {result.get("error", "未知错误")}')
                except Exception as e:
                    results.append(f'配置文件提取失败: {str(e)}')
            
            # 第四步：分别处理conf和base文件
            ucs_dir = os.path.dirname(self.user_processed_dir)
            conf_dir = os.path.join(ucs_dir, 'conf')
            base_dir = os.path.join(ucs_dir, 'base')
            
            # 导入UCS处理模块
            from core.function.ucs.lxl_package_4_BaseConfProcess.F5_base_to_excel_txt import process_folder as process_base_folder
            from core.function.ucs.lxl_package_3_ConfProcess.Conf_Add_File import process_folder as process_conf_folder
            
            # 处理conf目录
            if os.path.exists(conf_dir):
                try:
                    process_conf_folder(conf_dir)
                    results.append('conf目录处理完成')
                    conf_files = [f for f in os.listdir(conf_dir) if f.endswith('.conf')]
                    processed_files.extend([f"conf/{f}" for f in conf_files])
                except Exception as e:
                    results.append(f'conf目录处理失败: {str(e)}')
            
            # 处理base目录
            if os.path.exists(base_dir):
                try:
                    process_base_folder(base_dir)
                    results.append('base目录处理完成')
                    base_files = [f for f in os.listdir(base_dir) if f.endswith('.conf')]
                    processed_files.extend([f"base/{f}" for f in base_files])
                except Exception as e:
                    results.append(f'base目录处理失败: {str(e)}')
            
            return {
                'success': True,
                'message': 'UCS文件处理完成',
                'results': results,
                'processed_files': processed_files,
                'ucs_results': ucs_results
            }
            
        except Exception as e:
            logger.error(f"处理UCS文件时发生错误: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_show_files(self, files: List[str], upload_dir: str) -> Dict[str, Any]:
        """处理Show文件 - 完整的处理流程"""
        try:
            results = []
            processed_files = []
            
            # 导入show处理模块
            from core.function.show.lxl_package_1_Txt_to_Log.F5_txt_to_log import process_file as txt_to_log_process
            from core.function.show.lxl_package_3_ConfProcess.Conf_Add_File import process_folder as process_conf_folder
            
            # 执行处理
            for file in files:
                file_path = os.path.join(upload_dir, file)
                
                if file.lower().endswith('.txt'):
                    # 处理TXT文件 - 转换为LOG
                    result = txt_to_log_process(file_path)
                    if result["success"]:
                        results.append(f'TXT文件处理完成: {file}')
                        processed_files.append(file)
                    else:
                        results.append(f'TXT文件处理失败: {file} - {result["message"]}')
                        
                elif file.lower().endswith('.conf'):
                    # 处理CONF文件 - 使用conf处理模块
                    try:
                        conf_dir = os.path.dirname(file_path)
                        process_conf_folder(conf_dir)
                        results.append(f'CONF文件处理完成: {file}')
                        processed_files.append(file)
                    except Exception as e:
                        results.append(f'CONF文件处理失败: {file} - {str(e)}')
            
            return {
                'success': True,
                'message': 'Show文件处理完成',
                'results': results,
                'processed_files': processed_files
            }
            
        except Exception as e:
            logger.error(f"处理Show文件时发生错误: {e}")
            return {
                'success': False,
                'error': str(e)
            } 