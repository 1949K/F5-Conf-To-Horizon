import os
import shutil
import tarfile
import zipfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .base_processor import BaseProcessor
from core.config import Config

class HorizonProcessor(BaseProcessor):
    """弘积主备配置对比处理器"""
    
    def __init__(self, user_processed_dir=None):
        super().__init__()
        self.user_horizon_dir = None
        self.temp_dir = None
        self.user_processed_dir = user_processed_dir
        self._directories_cache = None  # 添加缓存
        
    def set_user_directories(self, user_horizon_dir: str, user_processed_dir: str = None):
        """设置用户目录"""
        self.user_horizon_dir = user_horizon_dir
        if user_processed_dir:
            self.user_processed_dir = user_processed_dir
        self._directories_cache = None  # 清除缓存
        
    def ensure_horizon_directories(self, username: str) -> Dict[str, str]:
        """确保弘积用户目录存在"""
        # 如果缓存存在且目录已存在，直接返回缓存
        if self._directories_cache:
            all_exist = True
            for dir_path in self._directories_cache.values():
                if not os.path.exists(dir_path):
                    all_exist = False
                    break
            if all_exist:
                return self._directories_cache
        
        directories = {
            'upload': os.path.join(self.user_horizon_dir, 'upload'),
            'unzip': os.path.join(self.user_horizon_dir, 'unzip'),
            'config': os.path.join(self.user_horizon_dir, 'config'),
            'compare': os.path.join(self.user_horizon_dir, 'compare')
        }
        
        # 创建所有目录
        for dir_path in directories.values():
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                self.logger.info(f"创建目录: {dir_path}")
        
        # 缓存结果
        self._directories_cache = directories
        return directories
    
    def normalize_filename(self, filename: str) -> str:
        """标准化文件名，处理弘积配置文件"""
        name, ext = os.path.splitext(filename)
        
        # 检查是否为弘积配置文件格式（IP地址-日期格式）
        if '-' in filename and '.' in filename.split('-')[0]:
            # 弘积配置文件，添加.tar后缀
            return f"{filename}.tar"
        elif not ext:
            # 没有后缀，添加.tar后缀
            return f"{name}.tar"
        elif ext.lower() not in ['.tar', '.zip', '.gz', '.bz2']:
            # 有其他后缀，改为.tar
            return f"{name}.tar"
        else:
            # 已经是支持的压缩格式
            return filename
    
    def is_archive_file(self, file_path: str) -> bool:
        """检查文件是否为压缩文件"""
        file_path = Path(file_path)
        if not file_path.exists():
            return False
        
        # 检查文件头来判断文件类型
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                
            # 检查常见的压缩文件头
            if header.startswith(b'\x1f\x8b'):  # gzip
                return True
            elif header.startswith(b'BZ'):  # bzip2
                return True
            elif header.startswith(b'PK'):  # ZIP
                return True
            elif header.startswith(b'ustar'):  # TAR
                return True
            else:
                # 检查文件扩展名，但弘积配置文件即使有.tar后缀也按普通文件处理
                ext = file_path.suffix.lower()
                if ext == '.tar':
                    # 对于.tar文件，进一步检查是否为真正的tar文件
                    try:
                        with tarfile.open(file_path, 'r') as tar:
                            # 如果能成功打开，说明是真正的tar文件
                            return True
                    except Exception:
                        # 如果无法打开，说明不是真正的tar文件，按普通文件处理
                        return False
                return ext in ['.zip', '.gz', '.bz2']
        except Exception:
            return False
    
    def process_file_without_extension(self, file_path: str, extract_dir: str) -> str:
        """处理没有扩展名的文件或弘积配置文件"""
        file_path = Path(file_path)
        
        # 首先尝试作为压缩文件处理
        if self.is_archive_file(str(file_path)):
            try:
                return self.extract_archive(str(file_path), extract_dir)
            except Exception as e:
                self.logger.warning(f"尝试解压文件失败，按普通文件处理: {e}")
                # 如果解压失败，按普通文件处理
        
        # 如果不是压缩文件或解压失败，按普通文件处理
        # 直接复制到解压目录
        extract_path = Path(extract_dir)
        extract_path.mkdir(parents=True, exist_ok=True)
        
        # 复制文件到解压目录
        target_path = extract_path / file_path.name
        shutil.copy2(file_path, target_path)
        
        self.logger.info(f"已将文件复制到: {target_path}")
        return str(extract_path)
    
    def extract_archive(self, archive_path: str, extract_dir: str) -> str:
        """解压压缩文件"""
        if not self.validate_file(archive_path):
            raise ValueError(f"无效的压缩文件: {archive_path}")
            
        archive_path = Path(archive_path)
        extract_path = Path(extract_dir)
        
        # 确保解压目录存在
        extract_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 首先检查文件头来确定文件类型
            with open(archive_path, 'rb') as f:
                header = f.read(8)
            
            if header.startswith(b'PK'):  # ZIP文件
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            elif header.startswith(b'\x1f\x8b'):  # gzip
                subprocess.run(['gunzip', '-c', str(archive_path)], 
                             stdout=open(extract_path / archive_path.stem, 'wb'))
            elif header.startswith(b'BZ'):  # bzip2
                subprocess.run(['bunzip2', '-c', str(archive_path)], 
                             stdout=open(extract_path / archive_path.stem, 'wb'))
            elif header.startswith(b'ustar'):  # TAR文件
                with tarfile.open(archive_path, 'r') as tar:
                    tar.extractall(extract_path)
            else:
                # 如果无法通过文件头识别，则根据扩展名处理
                if archive_path.suffix.lower() == '.tar':
                    with tarfile.open(archive_path, 'r') as tar:
                        tar.extractall(extract_path)
                elif archive_path.suffix.lower() == '.zip':
                    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                elif archive_path.suffix.lower() in ['.gz', '.bz2']:
                    if archive_path.suffix.lower() == '.gz':
                        subprocess.run(['gunzip', '-c', str(archive_path)], 
                                     stdout=open(extract_path / archive_path.stem, 'wb'))
                    else:  # .bz2
                        subprocess.run(['bunzip2', '-c', str(archive_path)], 
                                     stdout=open(extract_path / archive_path.stem, 'wb'))
                else:
                    raise ValueError(f"不支持的压缩格式: {archive_path.suffix}")
                
            self.logger.info(f"已解压文件到: {extract_path}")
            return str(extract_path)
            
        except Exception as e:
            self.logger.error(f"解压文件时发生错误: {e}")
            raise
    
    def find_startup_config(self, root_dir: str) -> Optional[str]:
        """在解压目录中查找startup-config文件"""
        root_path = Path(root_dir)
        
        # 查找路径：datafile/management/etc/startup-config
        possible_paths = [
            root_path / 'datafile' / 'management' / 'etc' / 'startup-config',
            root_path / 'management' / 'etc' / 'startup-config',
            root_path / 'etc' / 'startup-config',
            root_path / 'startup-config'
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                self.logger.info(f"找到startup-config文件: {path}")
                return str(path)
        
        # 递归搜索
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file == 'startup-config':
                    config_path = os.path.join(root, file)
                    self.logger.info(f"找到startup-config文件: {config_path}")
                    return config_path
        
        self.logger.warning(f"在目录 {root_dir} 中未找到startup-config文件")
        return None
    
    def extract_config_file(self, config_path: str, output_dir: str, filename: str) -> str:
        """提取配置文件到用户目录"""
        if not os.path.exists(config_path):
            raise ValueError(f"配置文件不存在: {config_path}")
            
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名（使用上传文件名）
        output_filename = f"{filename}.config"
        output_path = os.path.join(output_dir, output_filename)
        
        try:
            # 复制配置文件
            shutil.copy2(config_path, output_path)
            self.logger.info(f"已提取配置文件到: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"提取配置文件时发生错误: {e}")
            raise
    
    def extract_config_info(self, config_file: str) -> Dict:
        """提取配置文件中的关键信息"""
        try:
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            config_info = {
                'hostname': '',
                'vrrp_unit_id': '',
                'first_ip_address': '',
                'mgmt_ip_address': ''
            }
            
            in_mgmt_interface = False
            
            for line in lines:
                line = line.strip()
                
                # 提取hostname
                if line.startswith('hostname '):
                    config_info['hostname'] = line.replace('hostname ', '').strip()
                
                # 提取vrrp unit-id
                elif line.startswith('vrrp unit-id '):
                    config_info['vrrp_unit_id'] = line.replace('vrrp unit-id ', '').strip()
                
                # 检测管理接口
                elif line.startswith('interface mgmt'):
                    in_mgmt_interface = True
                elif line.startswith('interface ') and not line.startswith('interface mgmt'):
                    in_mgmt_interface = False
                
                # 提取管理接口IP地址
                elif in_mgmt_interface and line.startswith('ip address '):
                    ip_part = line.replace('ip address ', '').strip()
                    if ' ' in ip_part:
                        ip_address = ip_part.split(' ')[0]
                        config_info['mgmt_ip_address'] = ip_address
                    elif '/' in ip_part:
                        ip_address = ip_part.split('/')[0]
                        config_info['mgmt_ip_address'] = ip_address
                    else:
                        config_info['mgmt_ip_address'] = ip_part
                
                # 提取第一个ip address（通常是接口配置）
                elif line.startswith('ip address ') and not config_info['first_ip_address']:
                    # 提取IP地址部分
                    ip_part = line.replace('ip address ', '').strip()
                    # 分割IP和子网掩码
                    if ' ' in ip_part:
                        ip_address = ip_part.split(' ')[0]
                        config_info['first_ip_address'] = ip_address
                    elif '/' in ip_part:
                        # 处理CIDR格式：10.20.252.34/24
                        ip_address = ip_part.split('/')[0]
                        config_info['first_ip_address'] = ip_address
                    else:
                        # 如果没有分隔符，直接使用
                        config_info['first_ip_address'] = ip_part
            
            return config_info
            
        except Exception as e:
            self.logger.error(f"提取配置文件信息时发生错误: {e}")
            return {
                'hostname': '',
                'vrrp_unit_id': '',
                'first_ip_address': '',
                'mgmt_ip_address': ''
            }
    
    def extract_device_series_from_filename(self, filename: str) -> str:
        """从文件名提取设备系列信息"""
        # 移除.config后缀
        name = filename.replace('.config', '')
        
        # 处理IP地址格式的文件名
        if '-' in name and '.' in name.split('-')[0]:
            # IP地址格式：10.20.252.43-20250801
            ip_part = name.split('-')[0]
            ip_parts = ip_part.split('.')
            if len(ip_parts) == 4:
                # 使用前三个八位字节作为系列标识
                return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
        
        # 处理其他格式的文件名
        if name.startswith('test'):
            return 'test'
        elif 'sysdf-dfdjk' in name:
            return 'sysdf-dfdjk'
        elif name.startswith('ok'):
            return 'ok'
        else:
            # 提取设备系列前缀
            # 例如：ZJyw2HongJi8020-01 -> ZJyw2HongJi8020
            # SQpu1SLB8020-03 -> SQpu1SLB8020
            parts = name.split('-')
            if len(parts) >= 2:
                return parts[0]  # 返回设备系列名称
            else:
                return name
    
    def find_ip_pairs(self, config_details: List[Dict]) -> List[Dict]:
        """查找IP地址格式的配置文件对"""
        ip_configs = []
        other_configs = []
        
        # 分离IP地址格式和其他格式的配置
        for config in config_details:
            filename = config['filename']
            if '-' in filename and '.' in filename.split('-')[0]:
                ip_part = filename.split('-')[0]
                ip_parts = ip_part.split('.')
                if len(ip_parts) == 4:
                    ip_configs.append(config)
                else:
                    other_configs.append(config)
            else:
                other_configs.append(config)
        
        # 对IP地址配置进行配对
        ip_pairs = []
        used_indices = set()
        
        for i, config1 in enumerate(ip_configs):
            if i in used_indices:
                continue
                
            filename1 = config1['filename']
            ip1 = filename1.split('-')[0]
            ip_parts1 = ip1.split('.')
            
            # 寻找配对IP（通常是相邻的IP地址）
            best_match = None
            best_similarity = 0
            
            for j, config2 in enumerate(ip_configs):
                if j <= i or j in used_indices:
                    continue
                    
                filename2 = config2['filename']
                ip2 = filename2.split('-')[0]
                ip_parts2 = ip2.split('.')
                
                # 检查是否是同一网段的相邻IP
                if (ip_parts1[0] == ip_parts2[0] and 
                    ip_parts1[1] == ip_parts2[1] and 
                    ip_parts1[2] == ip_parts2[2]):
                    
                    # 计算IP地址的相似度（相邻IP应该有较高的相似度）
                    ip1_num = int(ip_parts1[3])
                    ip2_num = int(ip_parts2[3])
                    similarity = 1.0 - abs(ip1_num - ip2_num) / 255.0
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = (j, config2)
            
            if best_match and best_similarity > 0.5:  # 设置相似度阈值
                j, config2 = best_match
                ip_pairs.append({
                    'config1': config1,
                    'config2': config2
                })
                used_indices.add(i)
                used_indices.add(j)
        
        return ip_pairs
    
    def find_vrrp_pairs(self, vrrp_groups: Dict[str, List[Dict]]) -> List[Dict]:
        """寻找VRRP配对（unit-id 1 与 unit-id 2）"""
        pairs = []
        
        # 检查是否有unit-id 1和unit-id 2的配对
        if '1' in vrrp_groups and '2' in vrrp_groups:
            configs_1 = vrrp_groups['1']
            configs_2 = vrrp_groups['2']
            
            # 如果每个组只有一个设备，直接配对
            if len(configs_1) == 1 and len(configs_2) == 1:
                pairs.append({
                    'config1': configs_1[0],
                    'config2': configs_2[0]
                })
            else:
                # 如果有多个设备，选择最相似的一对
                best_pair = self.find_best_vrrp_pair(configs_1, configs_2)
                if best_pair:
                    pairs.append(best_pair)
        
        return pairs
    
    def find_best_vrrp_pair(self, configs_1: List[Dict], configs_2: List[Dict]) -> Optional[Dict]:
        """在多个VRRP设备中找到最佳配对"""
        best_pair = None
        best_similarity = 0
        
        for config1 in configs_1:
            for config2 in configs_2:
                # 计算hostname相似度
                similarity = self.calculate_hostname_similarity(config1['hostname'], config2['hostname'])
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_pair = {
                        'config1': config1,
                        'config2': config2
                    }
        
        return best_pair
    
    def calculate_hostname_similarity(self, hostname1: str, hostname2: str) -> float:
        """计算hostname相似度"""
        if not hostname1 or not hostname2:
            return 0.0
        
        # 提取设备系列部分（去掉最后的数字）
        series1 = self.extract_hostname_series(hostname1)
        series2 = self.extract_hostname_series(hostname2)
        
        if series1 == series2:
            return 1.0
        else:
            # 计算字符串相似度
            return self.calculate_string_similarity(series1, series2)
    
    def extract_hostname_series(self, hostname: str) -> str:
        """从hostname提取设备系列"""
        # 移除最后的数字部分（如-01, -02等）
        import re
        series = re.sub(r'-\d+$', '', hostname)
        return series
    
    def calculate_string_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        if not str1 or not str2:
            return 0.0
        
        # 使用简单的编辑距离计算相似度
        len1, len2 = len(str1), len(str2)
        max_len = max(len1, len2)
        
        if max_len == 0:
            return 1.0
        
        # 计算编辑距离
        distance = self.levenshtein_distance(str1, str2)
        similarity = 1.0 - (distance / max_len)
        
        return max(0.0, similarity)
    
    def levenshtein_distance(self, str1: str, str2: str) -> int:
        """计算编辑距离"""
        len1, len2 = len(str1), len(str2)
        
        # 创建矩阵
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # 初始化第一行和第一列
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        # 填充矩阵
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if str1[i-1] == str2[j-1]:
                    matrix[i][j] = matrix[i-1][j-1]
                else:
                    matrix[i][j] = min(
                        matrix[i-1][j] + 1,    # 删除
                        matrix[i][j-1] + 1,    # 插入
                        matrix[i-1][j-1] + 1   # 替换
                    )
        
        return matrix[len1][len2]
    
    def compare_config_pair(self, config1: Dict, config2: Dict) -> Optional[Dict]:
        """对比两个配置文件"""
        try:
            # 读取配置文件内容
            with open(config1['file'], 'r', encoding='utf-8', errors='ignore') as f:
                lines1 = f.readlines()
            with open(config2['file'], 'r', encoding='utf-8', errors='ignore') as f:
                lines2 = f.readlines()
            
            # 获取配置文件大小
            config1_size = os.path.getsize(config1['file']) / 1024  # 转换为KB
            config2_size = os.path.getsize(config2['file']) / 1024  # 转换为KB
            
            # 找出差异
            differences = []
            for line_num, (line1, line2) in enumerate(zip(lines1, lines2), 1):
                if line1 != line2:
                    differences.append({
                        "line": line_num,
                        "file1": line1.strip(),
                        "file2": line2.strip()
                    })
            
            # 处理长度不同的情况
            if len(lines1) != len(lines2):
                max_lines = max(len(lines1), len(lines2))
                for line_num in range(min(len(lines1), len(lines2)) + 1, max_lines + 1):
                    if line_num <= len(lines1):
                        differences.append({
                            "line": line_num,
                            "file1": lines1[line_num - 1].strip(),
                            "file2": ""
                        })
                    else:
                        differences.append({
                            "line": line_num,
                            "file1": "",
                            "file2": lines2[line_num - 1].strip()
                        })
            
            # 计算相似度
            similarity = round((max(len(lines1), len(lines2)) - len(differences)) / max(len(lines1), len(lines2)) * 100, 2) if max(len(lines1), len(lines2)) > 0 else 0
            
            return {
                "file1": {
                    "name": config1['filename'],
                    "hostname": config1['hostname'],
                    "vrrp_unit_id": config1['vrrp_unit_id'],
                    "device_series": config1['device_series'],
                    "mgmt_ip": config1.get('mgmt_ip_address', ''),
                    "first_ip": config1.get('first_ip_address', ''),
                    "config_size": round(config1_size, 1)
                },
                "file2": {
                    "name": config2['filename'],
                    "hostname": config2['hostname'],
                    "vrrp_unit_id": config2['vrrp_unit_id'],
                    "device_series": config2['device_series'],
                    "mgmt_ip": config2.get('mgmt_ip_address', ''),
                    "first_ip": config2.get('first_ip_address', ''),
                    "config_size": round(config2_size, 1)
                },
                "differences": differences,
                "stats": {
                    "total_lines": max(len(lines1), len(lines2)),
                    "different_lines": len(differences),
                    "similarity": similarity
                }
            }
            
        except Exception as e:
            self.logger.error(f"对比配置文件时发生错误: {e}")
            return None
    
    def find_best_match_in_group(self, group_files: List[Dict]) -> Optional[Dict]:
        """在VRRP组内找到最佳匹配的文件对"""
        if len(group_files) < 2:
            return None
        
        best_pair = None
        best_similarity = 0
        
        for i in range(len(group_files)):
            for j in range(i + 1, len(group_files)):
                file1_info = group_files[i]
                file2_info = group_files[j]
                
                # 获取配置文件路径
                config_dir = os.path.join(self.user_horizon_dir, 'config')
                file1_config = os.path.join(config_dir, f"{os.path.splitext(file1_info['name'])[0].replace('.tar', '')}.config")
                file2_config = os.path.join(config_dir, f"{os.path.splitext(file2_info['name'])[0].replace('.tar', '')}.config")
                
                if not (os.path.exists(file1_config) and os.path.exists(file2_config)):
                    continue
                
                # 读取配置文件内容
                with open(file1_config, 'r', encoding='utf-8', errors='ignore') as f:
                    lines1 = f.readlines()
                with open(file2_config, 'r', encoding='utf-8', errors='ignore') as f:
                    lines2 = f.readlines()
                
                # 找出差异
                differences = []
                for line_num, (line1, line2) in enumerate(zip(lines1, lines2), 1):
                    if line1 != line2:
                        differences.append({
                            "line": line_num,
                            "file1": line1.strip(),
                            "file2": line2.strip()
                        })
                
                # 处理长度不同的情况
                if len(lines1) != len(lines2):
                    max_lines = max(len(lines1), len(lines2))
                    for line_num in range(min(len(lines1), len(lines2)) + 1, max_lines + 1):
                        if line_num <= len(lines1):
                            differences.append({
                                "line": line_num,
                                "file1": lines1[line_num - 1].strip(),
                                "file2": ""
                            })
                        else:
                            differences.append({
                                "line": line_num,
                                "file1": "",
                                "file2": lines2[line_num - 1].strip()
                            })
                
                # 计算相似度
                similarity = round((max(len(lines1), len(lines2)) - len(differences)) / max(len(lines1), len(lines2)) * 100, 2) if max(len(lines1), len(lines2)) > 0 else 0
                
                # 选择相似度最高的一对
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_pair = {
                        "file1": {
                            "name": file1_info['name'],
                            "hostname": file1_info['config_info'].get('hostname', ''),
                            "ip_address": file1_info['config_info'].get('first_ip_address', ''),
                            "vrrp_unit_id": file1_info['config_info'].get('vrrp_unit_id', '')
                        },
                        "file2": {
                            "name": file2_info['name'],
                            "hostname": file2_info['config_info'].get('hostname', ''),
                            "ip_address": file2_info['config_info'].get('first_ip_address', ''),
                            "vrrp_unit_id": file2_info['config_info'].get('vrrp_unit_id', '')
                        },
                        "differences": differences,
                        "stats": {
                            "total_lines": max(len(lines1), len(lines2)),
                            "different_lines": len(differences),
                            "similarity": similarity
                        }
                    }
        
        return best_pair
    
    def find_best_match_between_groups(self, group_1: List[Dict], group_2: List[Dict], vrrp_id_1: str, vrrp_id_2: str) -> Optional[Dict]:
        """在两个VRRP组之间找到最佳匹配的文件对"""
        if not group_1 or not group_2:
            return None
        
        best_pair = None
        best_similarity = 0
        
        for file1_info in group_1:
            for file2_info in group_2:
                # 获取配置文件路径
                config_dir = os.path.join(self.user_horizon_dir, 'config')
                file1_config = os.path.join(config_dir, f"{os.path.splitext(file1_info['name'])[0].replace('.tar', '')}.config")
                file2_config = os.path.join(config_dir, f"{os.path.splitext(file2_info['name'])[0].replace('.tar', '')}.config")
                
                if not (os.path.exists(file1_config) and os.path.exists(file2_config)):
                    continue
                
                # 读取配置文件内容
                with open(file1_config, 'r', encoding='utf-8', errors='ignore') as f:
                    lines1 = f.readlines()
                with open(file2_config, 'r', encoding='utf-8', errors='ignore') as f:
                    lines2 = f.readlines()
                
                # 找出差异
                differences = []
                for line_num, (line1, line2) in enumerate(zip(lines1, lines2), 1):
                    if line1 != line2:
                        differences.append({
                            "line": line_num,
                            "file1": line1.strip(),
                            "file2": line2.strip()
                        })
                
                # 处理长度不同的情况
                if len(lines1) != len(lines2):
                    max_lines = max(len(lines1), len(lines2))
                    for line_num in range(min(len(lines1), len(lines2)) + 1, max_lines + 1):
                        if line_num <= len(lines1):
                            differences.append({
                                "line": line_num,
                                "file1": lines1[line_num - 1].strip(),
                                "file2": ""
                            })
                        else:
                            differences.append({
                                "line": line_num,
                                "file1": "",
                                "file2": lines2[line_num - 1].strip()
                            })
                
                # 计算相似度
                similarity = round((max(len(lines1), len(lines2)) - len(differences)) / max(len(lines1), len(lines2)) * 100, 2) if max(len(lines1), len(lines2)) > 0 else 0
                
                # 选择相似度最高的一对
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_pair = {
                        "file1": {
                            "name": file1_info['name'],
                            "hostname": file1_info['config_info'].get('hostname', ''),
                            "ip_address": file1_info['config_info'].get('first_ip_address', ''),
                            "vrrp_unit_id": file1_info['config_info'].get('vrrp_unit_id', '')
                        },
                        "file2": {
                            "name": file2_info['name'],
                            "hostname": file2_info['config_info'].get('hostname', ''),
                            "ip_address": file2_info['config_info'].get('first_ip_address', ''),
                            "vrrp_unit_id": file2_info['config_info'].get('vrrp_unit_id', '')
                        },
                        "differences": differences,
                        "stats": {
                            "total_lines": max(len(lines1), len(lines2)),
                            "different_lines": len(differences),
                            "similarity": similarity
                        }
                    }
        
        return best_pair
    
    def compare_configs(self, config_files: List[str]) -> Dict:
        """对比配置文件，基于设备系列、hostname和VRRP unit-id进行智能匹配"""
        if len(config_files) < 2:
            return {"error": "需要至少两个配置文件进行对比"}
        
        # 创建缓存键，基于文件列表的排序
        config_files_sorted = sorted(config_files)
        cache_key = "|".join(config_files_sorted)
        
        # 检查是否有缓存的结果
        if hasattr(self, '_comparison_cache') and cache_key in self._comparison_cache:
            self.logger.info("使用缓存的对比结果")
            return self._comparison_cache[cache_key]
            
        comparison_results = {
            "pairs": [],
            "summary": {
                "total_pairs": 0,
                "total_differences": 0
            }
        }
        
        try:
            # 提取所有配置文件的详细信息
            config_details = []
            for config_file in config_files:
                config_info = self.extract_config_info(config_file)
                filename = os.path.basename(config_file)
                
                # 解析文件名获取设备系列信息
                device_series = self.extract_device_series_from_filename(filename)
                
                config_details.append({
                    'file': config_file,
                    'filename': filename,
                    'hostname': config_info['hostname'],
                    'vrrp_unit_id': config_info['vrrp_unit_id'],
                    'first_ip_address': config_info['first_ip_address'],
                    'mgmt_ip_address': config_info['mgmt_ip_address'],
                    'device_series': device_series
                })
            
            # 首先处理IP地址格式的配置文件
            ip_pairs = self.find_ip_pairs(config_details)
            for pair in ip_pairs:
                comparison_result = self.compare_config_pair(pair['config1'], pair['config2'])
                if comparison_result:
                    comparison_results["pairs"].append(comparison_result)
                    comparison_results["summary"]["total_pairs"] += 1
                    comparison_results["summary"]["total_differences"] += comparison_result["stats"]["different_lines"]
            
            # 处理剩余的配置文件（非IP地址格式）
            remaining_configs = []
            paired_files = set()
            for pair in ip_pairs:
                paired_files.add(pair['config1']['file'])
                paired_files.add(pair['config2']['file'])
            
            for config in config_details:
                if config['file'] not in paired_files:
                    remaining_configs.append(config)
            
            # 按设备系列分组处理剩余文件
            series_groups = {}
            for config in remaining_configs:
                series = config['device_series']
                if series not in series_groups:
                    series_groups[series] = []
                series_groups[series].append(config)
            
            # 对每个设备系列内的设备进行配对
            for series_name, series_configs in series_groups.items():
                if len(series_configs) >= 2:
                    # 按VRRP unit-id分组
                    vrrp_groups = {}
                    for config in series_configs:
                        vrrp_id = config['vrrp_unit_id']
                        if vrrp_id not in vrrp_groups:
                            vrrp_groups[vrrp_id] = []
                        vrrp_groups[vrrp_id].append(config)
                    
                    # 寻找配对（unit-id 1 与 unit-id 2）
                    pairs = self.find_vrrp_pairs(vrrp_groups)
                    
                    # 对每对设备进行配置对比
                    for pair in pairs:
                        comparison_result = self.compare_config_pair(pair['config1'], pair['config2'])
                        if comparison_result:
                            comparison_results["pairs"].append(comparison_result)
                            comparison_results["summary"]["total_pairs"] += 1
                            comparison_results["summary"]["total_differences"] += comparison_result["stats"]["different_lines"]
            
            # 按配置文件名称排序
            comparison_results["pairs"].sort(key=lambda x: (x["file1"]["name"], x["file2"]["name"]))
            
            self.logger.info(f"配置对比完成，共 {comparison_results['summary']['total_pairs']} 对文件，总计 {comparison_results['summary']['total_differences']} 处差异")
            
            # 缓存结果
            if not hasattr(self, '_comparison_cache'):
                self._comparison_cache = {}
            self._comparison_cache[cache_key] = comparison_results
            
            return comparison_results
            
        except Exception as e:
            self.logger.error(f"配置对比时发生错误: {e}")
            return {"error": f"配置对比失败: {str(e)}"}
    
    def process(self, file_path: str, username: str) -> Dict:
        """处理弘积配置文件"""
        try:
            # 确保用户目录存在
            directories = self.ensure_horizon_directories(username)
            
            # 获取原始文件名
            original_filename = os.path.basename(file_path)
            
            # 创建解压目录（使用原始文件名作为目录名，但移除.tar后缀）
            base_name = original_filename.replace('.tar', '')
            unzip_dir = os.path.join(directories['unzip'], base_name)
            
            # 检查文件格式
            file_ext = os.path.splitext(original_filename)[1].lower()
            
            # 检查是否为弘积配置文件格式（IP地址-日期格式），但排除已经标准化的文件
            base_name = original_filename.replace('.tar', '')  # 移除.tar后缀
            if '-' in base_name and '.' in base_name.split('-')[0] and file_ext == '.tar':
                # 已经是标准化的弘积配置文件，按无扩展名文件处理
                self.logger.info(f"处理标准化的弘积配置文件: {file_path}")
                extracted_dir = self.process_file_without_extension(file_path, unzip_dir)
            elif file_ext == '.tar':
                # 检查是否为真正的tar文件
                if self.is_archive_file(file_path):
                    # 是真正的tar文件，正常解压
                    self.logger.info(f"开始解压TAR文件: {file_path}")
                    extracted_dir = self.extract_archive(file_path, unzip_dir)
                else:
                    # 不是真正的tar文件，按普通文件处理
                    self.logger.info(f"处理非TAR文件: {file_path}")
                    extracted_dir = self.process_file_without_extension(file_path, unzip_dir)
            elif not file_ext:
                # 没有扩展名的文件
                self.logger.info(f"处理无扩展名文件: {file_path}")
                extracted_dir = self.process_file_without_extension(file_path, unzip_dir)
            else:
                # 有扩展名的文件，正常解压
                self.logger.info(f"开始解压文件: {file_path}")
                extracted_dir = self.extract_archive(file_path, unzip_dir)
            
            # 查找startup-config文件
            self.logger.info(f"在解压目录中查找startup-config文件: {extracted_dir}")
            config_file = self.find_startup_config(extracted_dir)
            
            if not config_file:
                return {
                    "success": False,
                    "error": "未找到startup-config文件",
                    "extracted_dir": extracted_dir
                }
            
            # 提取配置文件到用户目录
            self.logger.info(f"提取配置文件: {config_file}")
            extracted_config = self.extract_config_file(
                config_file, 
                directories['config'], 
                base_name
            )
            
            # 查找其他配置文件进行对比
            config_files = []
            for file in os.listdir(directories['config']):
                if file.endswith('.config'):
                    config_files.append(os.path.join(directories['config'], file))
            
            # 进行配置对比
            comparison_results = None
            if len(config_files) >= 2:
                self.logger.info("开始配置对比")
                # 清理缓存以确保使用最新的文件
                self.clear_comparison_cache()
                comparison_results = self.compare_configs(config_files)
            
            return {
                "success": True,
                "original_file": file_path,
                "extracted_dir": extracted_dir,
                "config_file": extracted_config,
                "all_config_files": config_files,
                "comparison_results": comparison_results
            }
            
        except Exception as e:
            self.logger.error(f"处理文件时发生错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def clear_comparison_cache(self):
        """清理对比结果缓存"""
        if hasattr(self, '_comparison_cache'):
            self._comparison_cache.clear()
            self.logger.info("已清理对比结果缓存")
    
    def cleanup(self):
        """清理资源"""
        self.clear_comparison_cache()
        super().cleanup()
    
    def get_processing_status(self, filename: str) -> Dict:
        """获取文件处理状态"""
        if not self.user_horizon_dir:
            return {"status": "error", "message": "用户目录未设置"}
        
        directories = self.ensure_horizon_directories("")
        base_name = os.path.splitext(filename)[0]
        
        status = {
            "upload": os.path.exists(os.path.join(directories['upload'], filename)),
            "unzip": os.path.exists(os.path.join(directories['unzip'], base_name)),
            "config": os.path.exists(os.path.join(directories['config'], f"{base_name}.config")),
            "compare": len([f for f in os.listdir(directories['config']) if f.endswith('.config')]) >= 2
        }
        
        return status 