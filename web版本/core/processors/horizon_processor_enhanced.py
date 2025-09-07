"""
增强的Horizon处理器
支持多设备配对和智能匹配
"""

import os
import shutil
import tarfile
import zipfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

from .base_processor_v2 import BaseProcessorV2


class HorizonProcessorEnhanced(BaseProcessorV2):
    """增强的弘积主备配置对比处理器"""
    
    def __init__(self, user_processed_dir=None):
        super().__init__()
        self.user_horizon_dir = None
        self.temp_dir = None
        self.user_processed_dir = user_processed_dir
        self._directories_cache = None
        
    def set_user_directories(self, user_horizon_dir: str, user_processed_dir: str = None):
        """设置用户目录"""
        self.user_horizon_dir = user_horizon_dir
        if user_processed_dir:
            self.user_processed_dir = user_processed_dir
        self._directories_cache = None
        
    def ensure_horizon_directories(self, username: str) -> Dict[str, str]:
        """确保弘积用户目录存在"""
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
        
        for dir_path in directories.values():
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                self.logger.info(f"创建目录: {dir_path}")
        
        self._directories_cache = directories
        return directories
    
    def extract_config_info(self, config_file: str) -> Dict:
        """提取配置文件信息"""
        config_info = {
            'hostname': 'Unknown',
            'vrrp_unit_id': 'Unknown',
            'first_ip_address': 'Unknown',
            'mgmt_ip_address': 'Unknown',
            'vrrp_groups': {},
            'interfaces': []
        }
        
        try:
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 提取hostname
            hostname_match = re.search(r'hostname\s+(\S+)', content)
            if hostname_match:
                config_info['hostname'] = hostname_match.group(1)
            
            # 提取管理IP
            mgmt_match = re.search(r'interface\s+Management0/0\s*\n.*?ip\s+address\s+(\S+)', content, re.DOTALL)
            if mgmt_match:
                config_info['mgmt_ip_address'] = mgmt_match.group(1).split()[0]
            
            # 提取VRRP信息
            vrrp_matches = re.finditer(r'interface\s+(\S+)\s*\n.*?vrrp\s+(\d+)\s+ip\s+(\S+)', content, re.DOTALL)
            for match in vrrp_matches:
                interface = match.group(1)
                vrrp_id = match.group(2)
                vrrp_ip = match.group(3)
                
                if vrrp_id not in config_info['vrrp_groups']:
                    config_info['vrrp_groups'][vrrp_id] = []
                
                config_info['vrrp_groups'][vrrp_id].append({
                    'interface': interface,
                    'ip': vrrp_ip
                })
            
            # 提取第一个IP地址
            ip_matches = re.findall(r'ip\s+address\s+(\S+)', content)
            if ip_matches:
                config_info['first_ip_address'] = ip_matches[0].split()[0]
            
            # 确定VRRP unit-id（取第一个VRRP组）
            if config_info['vrrp_groups']:
                config_info['vrrp_unit_id'] = list(config_info['vrrp_groups'].keys())[0]
            
        except Exception as e:
            self.logger.error(f"提取配置文件信息时出错: {e}")
        
        return config_info
    
    def find_enhanced_vrrp_pairs(self, vrrp_groups: Dict[str, List[Dict]]) -> List[Dict]:
        """增强的VRRP配对算法，支持多设备配对"""
        pairs = []
        
        # 检查是否有unit-id 1和unit-id 2的配对
        if '1' in vrrp_groups and '2' in vrrp_groups:
            configs_1 = vrrp_groups['1']
            configs_2 = vrrp_groups['2']
            
            # 如果每个组只有一个设备，直接配对
            if len(configs_1) == 1 and len(configs_2) == 1:
                pairs.append({
                    'config1': configs_1[0],
                    'config2': configs_2[0],
                    'pair_type': 'simple'
                })
            else:
                # 多设备配对 - 使用智能匹配算法
                enhanced_pairs = self.find_multi_device_pairs(configs_1, configs_2)
                pairs.extend(enhanced_pairs)
        
        return pairs
    
    def find_multi_device_pairs(self, configs_1: List[Dict], configs_2: List[Dict]) -> List[Dict]:
        """多设备智能配对算法"""
        pairs = []
        
        # 计算所有可能的配对组合
        all_combinations = []
        for config1 in configs_1:
            for config2 in configs_2:
                similarity = self.calculate_device_similarity(config1, config2)
                all_combinations.append({
                    'config1': config1,
                    'config2': config2,
                    'similarity': similarity
                })
        
        # 按相似度排序
        all_combinations.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 贪心算法选择最佳配对
        used_configs_1 = set()
        used_configs_2 = set()
        
        for combination in all_combinations:
            config1 = combination['config1']
            config2 = combination['config2']
            
            # 检查是否已被使用
            if (config1['filename'] not in used_configs_1 and 
                config2['filename'] not in used_configs_2):
                
                pairs.append({
                    'config1': config1,
                    'config2': config2,
                    'pair_type': 'enhanced',
                    'similarity': combination['similarity']
                })
                
                used_configs_1.add(config1['filename'])
                used_configs_2.add(config2['filename'])
        
        return pairs
    
    def calculate_device_similarity(self, config1: Dict, config2: Dict) -> float:
        """计算设备相似度"""
        similarity = 0.0
        
        # 1. Hostname相似度 (权重: 0.4)
        hostname_sim = self.calculate_hostname_similarity(config1['hostname'], config2['hostname'])
        similarity += hostname_sim * 0.4
        
        # 2. IP地址相似度 (权重: 0.3)
        ip_sim = self.calculate_ip_similarity(config1['mgmt_ip_address'], config2['mgmt_ip_address'])
        similarity += ip_sim * 0.3
        
        # 3. 文件名相似度 (权重: 0.3)
        filename_sim = self.calculate_filename_similarity(config1['filename'], config2['filename'])
        similarity += filename_sim * 0.3
        
        return similarity
    
    def calculate_hostname_similarity(self, hostname1: str, hostname2: str) -> float:
        """计算hostname相似度"""
        if not hostname1 or not hostname2:
            return 0.0
        
        # 提取设备系列部分
        series1 = self.extract_hostname_series(hostname1)
        series2 = self.extract_hostname_series(hostname2)
        
        if series1 == series2:
            return 1.0
        else:
            return self.calculate_string_similarity(series1, series2)
    
    def calculate_ip_similarity(self, ip1: str, ip2: str) -> float:
        """计算IP地址相似度"""
        if not ip1 or not ip2 or ip1 == 'Unknown' or ip2 == 'Unknown':
            return 0.0
        
        try:
            # 解析IP地址
            parts1 = ip1.split('.')
            parts2 = ip2.split('.')
            
            if len(parts1) != 4 or len(parts2) != 4:
                return 0.0
            
            # 计算前三个八位字节的相似度
            matches = 0
            for i in range(3):
                if parts1[i] == parts2[i]:
                    matches += 1
            
            return matches / 3.0
            
        except:
            return 0.0
    
    def calculate_filename_similarity(self, filename1: str, filename2: str) -> float:
        """计算文件名相似度"""
        if not filename1 or not filename2:
            return 0.0
        
        # 移除扩展名
        name1 = filename1.replace('.config', '')
        name2 = filename2.replace('.config', '')
        
        return self.calculate_string_similarity(name1, name2)
    
    def extract_hostname_series(self, hostname: str) -> str:
        """从hostname提取设备系列"""
        import re
        series = re.sub(r'-\d+$', '', hostname)
        return series
    
    def calculate_string_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        if not str1 or not str2:
            return 0.0
        
        len1, len2 = len(str1), len(str2)
        max_len = max(len1, len2)
        
        if max_len == 0:
            return 1.0
        
        distance = self.levenshtein_distance(str1, str2)
        similarity = 1.0 - (distance / max_len)
        
        return max(0.0, similarity)
    
    def levenshtein_distance(self, str1: str, str2: str) -> int:
        """计算编辑距离"""
        len1, len2 = len(str1), len(str2)
        
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if str1[i-1] == str2[j-1]:
                    matrix[i][j] = matrix[i-1][j-1]
                else:
                    matrix[i][j] = min(
                        matrix[i-1][j] + 1,
                        matrix[i][j-1] + 1,
                        matrix[i-1][j-1] + 1
                    )
        
        return matrix[len1][len2]
    
    def compare_configs_enhanced(self, config_files: List[str]) -> Dict:
        """增强的配置对比，支持多设备配对"""
        if len(config_files) < 2:
            return {"error": "需要至少两个配置文件进行对比"}
            
        comparison_results = {
            "pairs": [],
            "summary": {
                "total_pairs": 0,
                "total_differences": 0,
                "enhanced_pairs": 0,
                "simple_pairs": 0
            }
        }
        
        try:
            self.log_process_start("增强配置对比", total_files=len(config_files))
            
            # 提取所有配置文件的详细信息
            config_details = []
            for config_file in config_files:
                config_info = self.extract_config_info(config_file)
                filename = os.path.basename(config_file)
                device_series = self.extract_device_series_from_filename(filename)
                
                config_details.append({
                    'file': config_file,
                    'filename': filename,
                    'hostname': config_info['hostname'],
                    'vrrp_unit_id': config_info['vrrp_unit_id'],
                    'first_ip_address': config_info['first_ip_address'],
                    'mgmt_ip_address': config_info['mgmt_ip_address'],
                    'device_series': device_series,
                    'config_info': config_info
                })
            
            # 按设备系列分组
            series_groups = {}
            for config in config_details:
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
                    
                    # 使用增强的配对算法
                    pairs = self.find_enhanced_vrrp_pairs(vrrp_groups)
                    
                    # 对每对设备进行配置对比
                    for pair in pairs:
                        comparison_result = self.compare_config_pair_enhanced(pair['config1'], pair['config2'])
                        if comparison_result:
                            comparison_result['pair_type'] = pair.get('pair_type', 'unknown')
                            comparison_result['similarity'] = pair.get('similarity', 0.0)
                            comparison_results["pairs"].append(comparison_result)
                            comparison_results["summary"]["total_pairs"] += 1
                            comparison_results["summary"]["total_differences"] += comparison_result["stats"]["different_lines"]
                            
                            if pair.get('pair_type') == 'enhanced':
                                comparison_results["summary"]["enhanced_pairs"] += 1
                            else:
                                comparison_results["summary"]["simple_pairs"] += 1
            
            # 按配置文件名称排序
            comparison_results["pairs"].sort(key=lambda x: (x["file1"]["name"], x["file2"]["name"]))
            
            self.log_process_success("增强配置对比", {
                'total_pairs': comparison_results['summary']['total_pairs'],
                'enhanced_pairs': comparison_results['summary']['enhanced_pairs'],
                'simple_pairs': comparison_results['summary']['simple_pairs'],
                'total_differences': comparison_results['summary']['total_differences']
            })
            
            return comparison_results
            
        except Exception as e:
            self.log_process_error("增强配置对比", e)
            return {"error": f"配置对比失败: {str(e)}"}
    
    def compare_config_pair_enhanced(self, config1: Dict, config2: Dict) -> Optional[Dict]:
        """增强的配置对比"""
        try:
            # 这里可以调用原有的对比逻辑
            # 暂时返回一个简单的对比结果
            return {
                "file1": {
                    "name": config1['filename'],
                    "hostname": config1['hostname'],
                    "mgmt_ip": config1['mgmt_ip_address']
                },
                "file2": {
                    "name": config2['filename'],
                    "hostname": config2['hostname'],
                    "mgmt_ip": config2['mgmt_ip_address']
                },
                "stats": {
                    "different_lines": 0,  # 这里需要实际的对比逻辑
                    "total_lines": 0
                },
                "differences": []
            }
        except Exception as e:
            self.logger.error(f"配置对比失败: {e}")
            return None
    
    def extract_device_series_from_filename(self, filename: str) -> str:
        """从文件名提取设备系列信息"""
        name = filename.replace('.config', '')
        
        if '-' in name and '.' in name.split('-')[0]:
            ip_part = name.split('-')[0]
            ip_parts = ip_part.split('.')
            if len(ip_parts) == 4:
                return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
        
        if name.startswith('test'):
            return 'test'
        elif 'sysdf-dfdjk' in name:
            return 'sysdf-dfdjk'
        elif name.startswith('ok'):
            return 'ok'
        else:
            parts = name.split('-')
            if len(parts) >= 2:
                return parts[0]
            else:
                return name 