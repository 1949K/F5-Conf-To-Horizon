"""
统一处理管理器 V2
为桌面应用和web应用提供相同的处理逻辑，使用新的异常处理和类型注解
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ..shared.exceptions import ProcessError, FileProcessError, ValidationError
from ..shared.types import ProcessResult, FileInfo, ProcessStep
from ..shared.validators import validate_file_list, validate_file_type
from ..shared.constants import PROCESS_STEPS, PROCESS_STATUS, SUCCESS_MESSAGES, ERROR_MESSAGES

logger = logging.getLogger(__name__)


class UnifiedProcessorV2:
    """统一处理管理器 V2"""
    
    def __init__(self, user_processed_dir: Optional[str] = None):
        """
        初始化统一处理器
        
        Args:
            user_processed_dir: 用户处理目录
        """
        self.user_processed_dir = user_processed_dir
        self.process_steps: List[ProcessStep] = []
        self.current_step: Optional[str] = None
        
        # 导入处理器
        from .f5_ucs_processor import F5UCSProcessor
        self.ucs_processor = F5UCSProcessor(user_processed_dir=user_processed_dir)
    
    def process_ucs_files(self, files: List[str], upload_dir: str) -> ProcessResult:
        """
        处理UCS文件 - 完整的处理流程
        
        Args:
            files: 文件列表
            upload_dir: 上传目录
            
        Returns:
            ProcessResult: 处理结果
        """
        try:
            # 验证输入
            validate_file_list(files)
            
            results = []
            processed_files = []
            ucs_results = []
            
            # 记录处理开始
            self._add_process_step("UCS文件处理开始", PROCESS_STATUS['PROCESSING'])
            
            # 第一步：处理所有UCS文件 - UCS转TAR
            self._add_process_step("UCS转TAR", PROCESS_STATUS['PROCESSING'])
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
                        error_msg = f'UCS转TAR失败: {file} - {str(e)}'
                        results.append(error_msg)
                        logger.error(error_msg)
                        raise FileProcessError(error_msg, file_path=file_path, operation="UCS转TAR")
            
            self._update_process_step("UCS转TAR", PROCESS_STATUS['COMPLETED'])
            
            # 第二步：解压所有TAR文件
            self._add_process_step("TAR解压", PROCESS_STATUS['PROCESSING'])
            tar_files = [f for f in files if f.lower().endswith('.tar')]
            for file in tar_files:
                file_path = os.path.join(upload_dir, file)
                try:
                    extracted_path = self.ucs_processor.untar_file(file_path)
                    results.append(f'TAR解压完成: {file}')
                except Exception as e:
                    error_msg = f'TAR解压失败: {file} - {str(e)}'
                    results.append(error_msg)
                    logger.error(error_msg)
                    raise FileProcessError(error_msg, file_path=file_path, operation="TAR解压")
            
            self._update_process_step("TAR解压", PROCESS_STATUS['COMPLETED'])
            
            # 第三步：从解压目录中提取配置文件
            if os.path.exists(self.user_processed_dir):
                self._add_process_step("配置文件提取", PROCESS_STATUS['PROCESSING'])
                try:
                    result = self.ucs_processor.extract_conf_and_base(self.user_processed_dir)
                    if result['status'] == 'success':
                        results.append('配置文件提取完成')
                    else:
                        error_msg = f'配置文件提取失败: {result.get("error", "未知错误")}'
                        results.append(error_msg)
                        raise FileProcessError(error_msg, operation="配置文件提取")
                except Exception as e:
                    error_msg = f'配置文件提取失败: {str(e)}'
                    results.append(error_msg)
                    logger.error(error_msg)
                    raise FileProcessError(error_msg, operation="配置文件提取")
                
                self._update_process_step("配置文件提取", PROCESS_STATUS['COMPLETED'])
            
            # 第四步：分别处理conf和base文件
            ucs_dir = os.path.dirname(self.user_processed_dir)
            conf_dir = os.path.join(ucs_dir, 'conf')
            base_dir = os.path.join(ucs_dir, 'base')
            
            # 导入UCS处理模块
            from ..function.ucs.lxl_package_4_BaseConfProcess.F5_base_to_excel_txt import process_folder as process_base_folder
            from ..function.ucs.lxl_package_3_ConfProcess.Conf_Add_File import process_folder as process_conf_folder
            
            # 处理conf目录
            if os.path.exists(conf_dir):
                self._add_process_step("conf文件处理", PROCESS_STATUS['PROCESSING'])
                try:
                    process_conf_folder(conf_dir)
                    results.append('conf目录处理完成')
                    conf_files = [f for f in os.listdir(conf_dir) if f.endswith('.conf')]
                    processed_files.extend([f"conf/{f}" for f in conf_files])
                except Exception as e:
                    error_msg = f'conf目录处理失败: {str(e)}'
                    results.append(error_msg)
                    logger.error(error_msg)
                    raise FileProcessError(error_msg, operation="conf文件处理")
                
                self._update_process_step("conf文件处理", PROCESS_STATUS['COMPLETED'])
            
            # 处理base目录
            if os.path.exists(base_dir):
                self._add_process_step("base文件处理", PROCESS_STATUS['PROCESSING'])
                try:
                    process_base_folder(base_dir)
                    results.append('base目录处理完成')
                    base_files = [f for f in os.listdir(base_dir) if f.endswith('.conf')]
                    processed_files.extend([f"base/{f}" for f in base_files])
                except Exception as e:
                    error_msg = f'base目录处理失败: {str(e)}'
                    results.append(error_msg)
                    logger.error(error_msg)
                    raise FileProcessError(error_msg, operation="base文件处理")
                
                self._update_process_step("base文件处理", PROCESS_STATUS['COMPLETED'])
            
            # 记录处理完成
            self._update_process_step("UCS文件处理开始", PROCESS_STATUS['COMPLETED'])
            
            return {
                'success': True,
                'message': SUCCESS_MESSAGES['PROCESS_SUCCESS'],
                'results': results,
                'processed_files': processed_files,
                'ucs_results': ucs_results,
                'process_steps': self.process_steps
            }
            
        except Exception as e:
            logger.error(f"处理UCS文件时发生错误: {e}")
            self._update_process_step(self.current_step, PROCESS_STATUS['FAILED'], str(e))
            return {
                'success': False,
                'error': str(e),
                'process_steps': self.process_steps
            }
    
    def process_show_files(self, files: List[str], upload_dir: str) -> ProcessResult:
        """
        处理Show文件 - 完整的处理流程
        
        Args:
            files: 文件列表
            upload_dir: 上传目录
            
        Returns:
            ProcessResult: 处理结果
        """
        try:
            # 验证输入
            validate_file_list(files)
            
            results = []
            processed_files = []
            
            # 记录处理开始
            self._add_process_step("Show文件处理开始", PROCESS_STATUS['PROCESSING'])
            
            # 导入show处理模块
            from ..function.show.lxl_package_1_Txt_to_Log.F5_txt_to_log import process_file as txt_to_log_process
            from ..function.show.lxl_package_3_ConfProcess.Conf_Add_File import process_folder as process_conf_folder
            
            # 执行处理
            for file in files:
                file_path = os.path.join(upload_dir, file)
                
                if file.lower().endswith('.txt'):
                    # 处理TXT文件 - 转换为LOG
                    self._add_process_step(f"TXT转LOG: {file}", PROCESS_STATUS['PROCESSING'])
                    result = txt_to_log_process(file_path)
                    if result["success"]:
                        results.append(f'TXT文件处理完成: {file}')
                        processed_files.append(file)
                        self._update_process_step(f"TXT转LOG: {file}", PROCESS_STATUS['COMPLETED'])
                    else:
                        error_msg = f'TXT文件处理失败: {file} - {result["message"]}'
                        results.append(error_msg)
                        self._update_process_step(f"TXT转LOG: {file}", PROCESS_STATUS['FAILED'], result["message"])
                        raise FileProcessError(error_msg, file_path=file_path, operation="TXT转LOG")
                        
                elif file.lower().endswith('.conf'):
                    # 处理CONF文件 - 使用conf处理模块
                    self._add_process_step(f"CONF处理: {file}", PROCESS_STATUS['PROCESSING'])
                    try:
                        conf_dir = os.path.dirname(file_path)
                        process_conf_folder(conf_dir)
                        results.append(f'CONF文件处理完成: {file}')
                        processed_files.append(file)
                        self._update_process_step(f"CONF处理: {file}", PROCESS_STATUS['COMPLETED'])
                    except Exception as e:
                        error_msg = f'CONF文件处理失败: {file} - {str(e)}'
                        results.append(error_msg)
                        self._update_process_step(f"CONF处理: {file}", PROCESS_STATUS['FAILED'], str(e))
                        raise FileProcessError(error_msg, file_path=file_path, operation="CONF处理")
            
            # 记录处理完成
            self._update_process_step("Show文件处理开始", PROCESS_STATUS['COMPLETED'])
            
            return {
                'success': True,
                'message': SUCCESS_MESSAGES['PROCESS_SUCCESS'],
                'results': results,
                'processed_files': processed_files,
                'process_steps': self.process_steps
            }
            
        except Exception as e:
            logger.error(f"处理Show文件时发生错误: {e}")
            self._update_process_step(self.current_step, PROCESS_STATUS['FAILED'], str(e))
            return {
                'success': False,
                'error': str(e),
                'process_steps': self.process_steps
            }
    
    def process_horizon_files(self, files: List[str], upload_dir: str) -> ProcessResult:
        """
        处理Horizon文件 - 完整的处理流程
        
        Args:
            files: 文件列表
            upload_dir: 上传目录
            
        Returns:
            ProcessResult: 处理结果
        """
        try:
            # 验证输入
            validate_file_list(files)
            
            results = []
            processed_files = []
            
            # 记录处理开始
            self._add_process_step("Horizon文件处理开始", PROCESS_STATUS['PROCESSING'])
            
            # 导入horizon处理模块
            from .horizon_processor import HorizonProcessor
            horizon_processor = HorizonProcessor()
            
            # 执行处理
            for file in files:
                file_path = os.path.join(upload_dir, file)
                self._add_process_step(f"Horizon处理: {file}", PROCESS_STATUS['PROCESSING'])
                
                try:
                    result = horizon_processor.process_file(file_path)
                    if result['success']:
                        results.append(f'Horizon文件处理完成: {file}')
                        processed_files.append(file)
                        self._update_process_step(f"Horizon处理: {file}", PROCESS_STATUS['COMPLETED'])
                    else:
                        error_msg = f'Horizon文件处理失败: {file} - {result.get("error", "未知错误")}'
                        results.append(error_msg)
                        self._update_process_step(f"Horizon处理: {file}", PROCESS_STATUS['FAILED'], result.get("error"))
                        raise FileProcessError(error_msg, file_path=file_path, operation="Horizon处理")
                except Exception as e:
                    error_msg = f'Horizon文件处理失败: {file} - {str(e)}'
                    results.append(error_msg)
                    self._update_process_step(f"Horizon处理: {file}", PROCESS_STATUS['FAILED'], str(e))
                    raise FileProcessError(error_msg, file_path=file_path, operation="Horizon处理")
            
            # 记录处理完成
            self._update_process_step("Horizon文件处理开始", PROCESS_STATUS['COMPLETED'])
            
            return {
                'success': True,
                'message': SUCCESS_MESSAGES['PROCESS_SUCCESS'],
                'results': results,
                'processed_files': processed_files,
                'process_steps': self.process_steps
            }
            
        except Exception as e:
            logger.error(f"处理Horizon文件时发生错误: {e}")
            self._update_process_step(self.current_step, PROCESS_STATUS['FAILED'], str(e))
            return {
                'success': False,
                'error': str(e),
                'process_steps': self.process_steps
            }
    
    def _add_process_step(self, step_name: str, status: str, message: Optional[str] = None) -> None:
        """
        添加处理步骤
        
        Args:
            step_name: 步骤名称
            status: 状态
            message: 消息
        """
        step: ProcessStep = {
            'step_name': step_name,
            'status': status,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'message': message
        }
        self.process_steps.append(step)
        self.current_step = step_name
    
    def _update_process_step(self, step_name: str, status: str, message: Optional[str] = None) -> None:
        """
        更新处理步骤
        
        Args:
            step_name: 步骤名称
            status: 状态
            message: 消息
        """
        for step in self.process_steps:
            if step['step_name'] == step_name:
                step['status'] = status
                step['end_time'] = datetime.now().isoformat()
                if message:
                    step['message'] = message
                break
    
    def get_process_status(self) -> Dict[str, Any]:
        """
        获取处理状态
        
        Returns:
            Dict[str, Any]: 处理状态信息
        """
        return {
            'current_step': self.current_step,
            'total_steps': len(self.process_steps),
            'completed_steps': len([s for s in self.process_steps if s['status'] == PROCESS_STATUS['COMPLETED']]),
            'failed_steps': len([s for s in self.process_steps if s['status'] == PROCESS_STATUS['FAILED']]),
            'process_steps': self.process_steps
        }
    
    def reset_process_steps(self) -> None:
        """重置处理步骤"""
        self.process_steps = []
        self.current_step = None 