import os
import shutil
import subprocess
from pathlib import Path
from .base_processor import BaseProcessor
from core.function.ucs.lxl_package_2_MargeConfFile.F5_Marge_conf_and_base import extract_conf_and_base
import tarfile

class F5UCSProcessor(BaseProcessor):
    """F5 UCS配置处理器"""
    
    def __init__(self, user_processed_dir=None):
        super().__init__()
        self.temp_dir = None
        self.user_processed_dir = user_processed_dir
    
    def ucs_to_tar(self, file_path: str) -> str:
        """将UCS文件转换为TAR文件"""
        if not self.validate_file(file_path):
            raise ValueError(f"无效的文件: {file_path}")
        source_path = Path(file_path)
        if source_path.suffix.lower() != '.ucs':
            raise ValueError("文件必须是UCS格式")
        # 创建目标TAR文件路径
        target_path = source_path.with_suffix('.tar')
        try:
            shutil.copy2(source_path, target_path)
            self.logger.info(f"已将UCS文件转换为TAR: {target_path}")
            return str(target_path)
        except Exception as e:
            self.logger.error(f"转换UCS文件时发生错误: {e}")
            raise

    def ucs_to_zip(self, file_path: str) -> str:
        """将UCS文件转换为TAR文件（实际转换为TAR）"""
        return self.ucs_to_tar(file_path)

    def untar_file(self, tar_path: str) -> str:
        """解压TAR文件"""
        if not self.validate_file(tar_path):
            raise ValueError(f"无效的文件: {tar_path}")
        source_path = Path(tar_path)
        if source_path.suffix.lower() != '.tar':
            raise ValueError("文件必须是TAR格式")
        if not self.user_processed_dir:
            raise ValueError("用户处理目录未设置")
        base_dir = Path(self.user_processed_dir)
        output_dir = str(base_dir / source_path.stem)
        temp_dir_path = self.ensure_output_dir(output_dir)
        self.temp_dir = str(temp_dir_path)
        try:
            # 使用Python的tarfile模块解压
            with tarfile.open(tar_path, 'r') as tar_ref:
                tar_ref.extractall(self.temp_dir)
            self.logger.info(f"已解压文件到: {self.temp_dir}")
            return str(self.temp_dir)
        except PermissionError as e:
            self.logger.warning(f"解压时遇到权限问题，尝试跳过有问题的文件: {e}")
            # 如果遇到权限问题，尝试逐个解压文件，跳过有问题的
            try:
                with tarfile.open(tar_path, 'r') as tar_ref:
                    for member in tar_ref.getmembers():
                        try:
                            tar_ref.extract(member, self.temp_dir)
                        except (PermissionError, OSError) as e2:
                            self.logger.warning(f"跳过文件 {member.name}: {e2}")
                            continue
                self.logger.info(f"已解压文件到: {self.temp_dir}（跳过有问题的文件）")
                return str(self.temp_dir)
            except Exception as e3:
                self.logger.error(f"解压文件时发生错误: {e3}")
                raise
        except Exception as e:
            self.logger.error(f"解压文件时发生错误: {e}")
            raise
    
    def process_conf(self, conf_path: str) -> dict:
        """处理配置文件"""
        if not self.validate_file(conf_path):
            raise ValueError(f"无效的配置文件: {conf_path}")
            
        # TODO: 实现配置文件处理逻辑
        results = {
            'excel_path': None,
            'txt_path': None
        }
        
        return results
    
    def extract_conf_and_base(self, processed_directory: str) -> dict:
        """提取conf和base文件夹，使用F5_Marge_conf_and_base模块"""
        try:
            if not os.path.exists(processed_directory):
                raise ValueError(f"目录不存在: {processed_directory}")
            
            # 获取ucs目录作为输出目录（processed目录的父目录）
            ucs_dir = os.path.dirname(processed_directory)
            
            # 调用F5_Marge_conf_and_base模块的提取函数
            result = extract_conf_and_base(processed_directory, ucs_dir)
            
            if result['status'] == 'success':
                extracted_files = result['extracted_files'] if isinstance(result['extracted_files'], dict) else {}
                conf_names = [os.path.basename(f) for f in extracted_files.get('conf', [])]
                base_names = [os.path.basename(f) for f in extracted_files.get('base', [])]
                self.logger.info(
                    f"已提取 {len(conf_names)} 个 bigip.conf 文件和 {len(base_names)} 个 bigip_base.conf 文件，conf: {conf_names}，base: {base_names}"
                )
                # 转换返回格式以匹配Web应用期望的格式
                config_dir = result.get('conf_dir')
                base_dir = result.get('base_dir')
                if not isinstance(config_dir, str):
                    config_dir = ''
                if not isinstance(base_dir, str):
                    base_dir = ''
                return {
                    'status': 'success',
                    'config_dir': config_dir,
                    'base_dir': base_dir,
                    'extracted_files': {
                        'config': extracted_files.get('conf', []),
                        'base': extracted_files.get('base', [])
                    }
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"提取conf和base文件时发生错误: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def process(self, file_path: str, output_dir: str = None) -> dict:
        """处理UCS文件的主方法"""
        try:
            # 检查用户处理目录是否设置
            if not self.user_processed_dir:
                raise ValueError("用户处理目录未设置，无法处理文件")
            
            # 1. 转换UCS为TAR
            tar_path = self.ucs_to_tar(file_path)
            
            # 2. 解压TAR文件
            extracted_path = self.untar_file(tar_path)
            
            # 3. 查找并处理配置文件
            conf_files = list(Path(extracted_path).glob("**/*.conf"))
            results = []
            
            for conf_file in conf_files:
                result = self.process_conf(str(conf_file))
                results.append({
                    'conf_file': str(conf_file),
                    **result
                })
            
            return {
                'status': 'success',
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"处理过程中发生错误: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def cleanup(self):
        """清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"已清理临时目录: {self.temp_dir}")
            except Exception as e:
                self.logger.error(f"清理临时目录时发生错误: {e}") 