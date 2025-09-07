import os
import re
import tkinter as tk
from tkinter import filedialog

import pandas as pd


def split_blocks(content):
    blocks = []
    current_block = []

    for line in content.split('\n'):
        if re.match(r'^(cm|net|security|sys)', line) or line.startswith("#"):
            # if re.match(r'^[a-zA-Z]', line) or line.startswith("#"):
            if current_block:
                blocks.append('\n'.join(current_block))
            current_block = [line]
        elif line:
            current_block.append(line)

    if current_block:
        blocks.append('\n'.join(current_block))

    return blocks


def extract_pools_vs_nodes(blocks):
    trunk_id = 0
    mgmt_route_data = {'mgmt_route_name': [], 'mgmt_route_gateway': [], 'mgmt_route_network': [],
                       'mgmt_route_description': []}
    mgmt_ip_data = {'mgmt_ip_name': [], 'mgmt_ip_description': []}
    vlan_data = {'vlan_name': [], 'vlan_interfaces': [], 'vlan_tag': []}
    trunk_data = {'trunk_name': [], 'trunk_interfaces': [], 'trunk_lacp': [], 'trunk_id': []}
    hostname_data = {'hostname': []}
    self_data = {'self_name': [], 'self_address': [], 'self_vlan_name': [], 'self_traffic_group': [],
                 'self_allow_service': []}
    device_group_data = {'device_group_name': [], 'device_group_devices': [], 'device_group_auto_sync': [],
                         'device_group_hidden': [], 'device_group_network_failover_match': []}
    sshd_data = {'sshd_allow_name': []}
    httpd_data = {'httpd_allow_name': []}
    snmp_data = {'snmp_allow': [], 'snmp_sys_contact': [], 'snmp_sys_location': []}
    syslog_data = {'syslog_destination_name': [], 'syslog_destination_block': [], 'syslog_log': [],
                   'syslog_remote_servers': []}
    ntp_data = {'ntp_servers_match': [], 'ntp_timezone': []}

    for block in blocks:
        if block:
            if block.startswith('sys management-route '):
                mgmt_route_name_match = re.search(r'sys management-route /Common/+([^\s{]+)', block)
                mgmt_route_name = mgmt_route_name_match.group(1) if mgmt_route_name_match else ''

                mgmt_route_description_match = re.search(r'description (\S+)', block)
                mgmt_route_description = mgmt_route_description_match.group(1) if mgmt_route_description_match else ''

                mgmt_route_gateway_match = re.search(r'gateway ([\w.:]+)', block)
                mgmt_route_gateway = mgmt_route_gateway_match.group(1) if mgmt_route_gateway_match else ''

                mgmt_route_network_match = re.search(r'network ([\w.:/]+)', block)
                mgmt_route_network = mgmt_route_network_match.group(1) if mgmt_route_network_match else ''

                mgmt_route_data['mgmt_route_name'].append(mgmt_route_name)
                mgmt_route_data['mgmt_route_gateway'].append(mgmt_route_gateway)
                mgmt_route_data['mgmt_route_network'].append(mgmt_route_network)
                mgmt_route_data['mgmt_route_description'].append(mgmt_route_description)

            if block.startswith('sys management-ip '):
                mgmt_ip_name_match = re.search(r'sys management-ip ([\w.:/]+)', block)
                mgmt_ip_name = mgmt_ip_name_match.group(1) if mgmt_ip_name_match else ''

                mgmt_ip_description_match = re.search(r'description (\S+)', block)
                mgmt_ip_description = mgmt_ip_description_match.group(1) if mgmt_ip_description_match else ''

                mgmt_ip_data['mgmt_ip_name'].append(mgmt_ip_name)
                mgmt_ip_data['mgmt_ip_description'].append(mgmt_ip_description)

            elif block.startswith('net vlan '):
                vlan_name_match = re.search(r'net vlan /Common/+([^\s{]+)', block)
                vlan_name = vlan_name_match.group(1) if vlan_name_match else ''

                vlan_interfaces_match = re.search(r'interfaces\s+\{([\s\S]*?)\n    \}\n', block)
                vlan_interfaces = vlan_interfaces_match.group(1).strip() if vlan_interfaces_match else ''

                vlan_tag_match = re.search(r'tag (\d+)', block)
                vlan_tag = vlan_tag_match.group(1) if vlan_tag_match else ''

                vlan_data['vlan_name'].append(vlan_name)
                vlan_data['vlan_interfaces'].append(vlan_interfaces)
                vlan_data['vlan_tag'].append(vlan_tag)

            elif block.startswith('net trunk '):
                trunk_name_match = re.search(r'net trunk +([^\s{]+)', block)
                trunk_name = trunk_name_match.group(1) if trunk_name_match else ''

                trunk_interfaces_match = re.search(r'interfaces\s+\{([\s\S]*?)\n    \}\n', block)
                trunk_interfaces = trunk_interfaces_match.group(1).strip() if trunk_interfaces_match else ''

                trunk_lacp_match = re.search(r'lacp (\w+)', block)
                trunk_lacp = trunk_lacp_match.group(1) if trunk_lacp_match else ''

                trunk_id += 1

                trunk_data['trunk_name'].append(trunk_name)
                trunk_data['trunk_interfaces'].append(trunk_interfaces)
                trunk_data['trunk_lacp'].append(trunk_lacp)
                trunk_data['trunk_id'].append(trunk_id)

            elif block.startswith('sys global-settings '):
                hostname_match = re.search(r'hostname (\S+)', block)
                hostname = hostname_match.group(1) if hostname_match else ''

                hostname_data['hostname'].append(hostname)

            elif block.startswith('net self '):
                self_name_match = re.search(r'net self /Common/+(\S+) {', block)
                self_name = self_name_match.group(1) if self_name_match else ''

                self_address_match = re.search(r'address ([\w.:/]+)', block)
                self_address = self_address_match.group(1) if self_address_match else ''

                self_vlan_name_match = re.search(r'vlan /Common/+(\S+)', block)
                self_vlan_name = self_vlan_name_match.group(1) if self_vlan_name_match else ''

                self_traffic_group_match = re.search(r'traffic-group /Common/+(\S+)', block)
                self_traffic_group = self_traffic_group_match.group(1) if self_traffic_group_match else ''

                self_allow_service_match = re.search(r'allow-service\s+\{([\s\S]*?)\n    \}\n', block)
                self_allow_service = self_allow_service_match.group(0) if self_allow_service_match else ''

                self_data['self_name'].append(self_name)
                self_data['self_address'].append(self_address)
                self_data['self_vlan_name'].append(self_vlan_name)
                self_data['self_traffic_group'].append(self_traffic_group)
                self_data['self_allow_service'].append(self_allow_service)

            elif block.startswith('cm device-group '):
                device_group_name_match = re.search(r'cm device-group /Common/+(\S+) {', block)
                device_group_name = device_group_name_match.group(1) if device_group_name_match else ''

                device_group_devices_match = re.search(r'devices\s+\{([\s\S]*?)\n    \}\n', block)
                device_group_devices = device_group_devices_match.group(1) if device_group_devices_match else ''

                device_group_auto_sync_match = re.search(r'auto-sync (\S+)', block)
                device_group_auto_sync = device_group_auto_sync_match.group(1) if device_group_auto_sync_match else ''

                device_group_hidden_match = re.search(r'hidden (\S+)', block)
                device_group_hidden = device_group_hidden_match.group(1) if device_group_hidden_match else ''

                device_group_network_failover_match = re.search(r'network-failover (\S+)', block)
                device_group_network_failover_match = device_group_network_failover_match.group(
                    1) if device_group_network_failover_match else ''

                device_group_data['device_group_name'].append(device_group_name)
                device_group_data['device_group_devices'].append(device_group_devices)
                device_group_data['device_group_auto_sync'].append(device_group_auto_sync)
                device_group_data['device_group_hidden'].append(device_group_hidden)
                device_group_data['device_group_network_failover_match'].append(device_group_network_failover_match)

            elif block.startswith('sys sshd '):

                sshd_allow_name_match = re.search(r'allow { ([\w\s.:/]+) }', block)
                sshd_allow_name = sshd_allow_name_match.group(1) if sshd_allow_name_match else ''

                sshd_data['sshd_allow_name'].append(sshd_allow_name)

            elif block.startswith('sys httpd '):

                httpd_allow_name_match = re.search(r'allow { ([\w\s.:/]+) }', block)
                httpd_allow_name = httpd_allow_name_match.group(1) if httpd_allow_name_match else ''

                httpd_data['httpd_allow_name'].append(httpd_allow_name)

            elif block.startswith('sys snmp '):

                snmp_allow_match = re.search(r'allowed-addresses { ([\w\s.:/]+) }', block)
                snmp_allow = snmp_allow_match.group(1) if snmp_allow_match else ''

                snmp_sys_contact_match = re.search(r'sys-contact ([\w\W\s.:/]+\n)', block)
                snmp_sys_contact = snmp_sys_contact_match.group(1) if snmp_sys_contact_match else ''

                snmp_sys_location_match = re.search(r'sys-location ([\w\W\s.:/]+\n)', block)
                snmp_sys_location = snmp_sys_location_match.group(1) if snmp_sys_location_match else ''

                snmp_data['snmp_allow'].append(snmp_allow)
                snmp_data['snmp_sys_contact'].append(snmp_sys_contact)
                snmp_data['snmp_sys_location'].append(snmp_sys_location)

            elif block.startswith('sys syslog '):

                syslog_destination_match = re.search(r'destination\s+(\S+)\s+\{([\s\S]*?)\n    [};]+\n', block)
                syslog_destination_name = syslog_destination_match.group(1) if syslog_destination_match else ''
                syslog_destination_block = syslog_destination_match.group(2) if syslog_destination_match else ''
                syslog_destination_block = re.sub(r'^\s+', '', syslog_destination_block, flags=re.MULTILINE)

                syslog_log_match = re.search(r'\s\s\s\slog\s+\{([\s\S]*?)\n    [};]+\n', block)
                syslog_log = syslog_log_match.group(1) if syslog_log_match else ''
                syslog_log = re.sub(r'^\s+', '', syslog_log, flags=re.MULTILINE)

                syslog_remote_servers_match = re.search(r'remote-servers\s+\{([\s\S]*?)\n    [};]+\n', block)
                syslog_remote_servers = syslog_remote_servers_match.group(1) if syslog_remote_servers_match else ''
                syslog_remote_servers = re.sub(r'^\s+', '', syslog_remote_servers, flags=re.MULTILINE)

                syslog_data['syslog_destination_name'].append(syslog_destination_name)
                syslog_data['syslog_destination_block'].append(syslog_destination_block)
                syslog_data['syslog_log'].append(syslog_log)
                syslog_data['syslog_remote_servers'].append(syslog_remote_servers)

            elif block.startswith('sys ntp '):

                ntp_servers_match = re.search(r'servers { ([\w\s.:/]+) }', block)
                ntp_servers_match = ntp_servers_match.group(1) if ntp_servers_match else ''

                ntp_timezone_match = re.search(r'timezone ([\w/]+)', block)
                ntp_timezone = ntp_timezone_match.group(1) if ntp_timezone_match else ''

                ntp_data['ntp_servers_match'].append(ntp_servers_match)
                ntp_data['ntp_timezone'].append(ntp_timezone)

    return (
        mgmt_route_data, vlan_data, trunk_data, hostname_data, self_data, mgmt_ip_data, device_group_data, sshd_data,
        httpd_data, snmp_data, syslog_data, ntp_data)


def process_file(file_path):
    encodings_to_try = ['utf-8', 'utf-8-sig', 'ISO-8859-1', 'latin-1']

    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            # 如果成功读取文件，跳出循环
            break
        except UnicodeDecodeError:
            pass
    else:
        print(f"Error: Unable to read file {file_path} with any of the tried encodings.")
        return

    # 继续处理文件内容
    blocks = split_blocks(content)
    mgmt_route_data, vlan_data, trunk_data, hostname_data, self_data, mgmt_ip_data, device_group_data, sshd_data, httpd_data, snmp_data, syslog_data, ntp_data = extract_pools_vs_nodes(
        blocks)

    # 生成文件名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    excel_file_name = f"{base_name}.xlsx"
    txt_file_name = f"{base_name}.txt"

    # 获取源文件的目录
    source_directory = os.path.dirname(file_path)

    # 构建完整的文件路径
    excel_file_path = os.path.join(source_directory, excel_file_name)
    txt_file_path = os.path.join(source_directory, txt_file_name)

    # 创建数据框并将数据存储到Excel文件中
    with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
        if hostname_data:
            hostname_df = pd.DataFrame(hostname_data)
            hostname_df.to_excel(writer, sheet_name='Hostname', index=False)
        if vlan_data:
            vlan_df = pd.DataFrame(vlan_data)
            vlan_df.to_excel(writer, sheet_name='Vlan', index=False)
        if trunk_data:
            trunk_df = pd.DataFrame(trunk_data)
            trunk_df.to_excel(writer, sheet_name='Trunk', index=False)
        if self_data:
            self_df = pd.DataFrame(self_data)
            self_df.to_excel(writer, sheet_name='Self_IP', index=False)
        if mgmt_route_data:
            mgmt_route_df = pd.DataFrame(mgmt_route_data)
            mgmt_route_df.to_excel(writer, sheet_name='Mgmt_Route', index=False)
        if mgmt_ip_data:
            mgmt_ip_df = pd.DataFrame(mgmt_ip_data)
            mgmt_ip_df.to_excel(writer, sheet_name='Mgmt_IP', index=False)
        if device_group_data:
            device_group_data_df = pd.DataFrame(device_group_data)
            device_group_data_df.to_excel(writer, sheet_name='Device_group', index=False)
        if sshd_data:
            sshd_data_df = pd.DataFrame(sshd_data)
            sshd_data_df.to_excel(writer, sheet_name='sshd', index=False)
        if httpd_data:
            httpd_data_df = pd.DataFrame(httpd_data)
            httpd_data_df.to_excel(writer, sheet_name='httpd', index=False)
        if snmp_data:
            snmp_data_df = pd.DataFrame(snmp_data)
            snmp_data_df.to_excel(writer, sheet_name='snmp', index=False)
        if syslog_data:
            syslog_data_df = pd.DataFrame(syslog_data)
            syslog_data_df.to_excel(writer, sheet_name='Syslog', index=False)
        if ntp_data:
            ntp_data_df = pd.DataFrame(ntp_data)
            ntp_data_df.to_excel(writer, sheet_name='NTP', index=False)

    # 将汇总信息写入txt文件
    with open(txt_file_path, 'w') as txt_file:
        if hostname_data:
            txt_file.write('################  Hostname Information:  ################\n')
            for idx, row in hostname_df.iterrows():
                txt_file.write(f'hostname {row["hostname"]}\n\n')

        if trunk_data:
            txt_file.write('################  Trunk Information:  ################\n')
            for idx, row in trunk_df.iterrows():
                if row["trunk_interfaces"] and row["trunk_lacp"] == "enabled":
                    # 按空格分割存储
                    trunk_interfaces_id = row["trunk_interfaces"].split()
                    # 遍历分割后的结果
                    for interface_id in trunk_interfaces_id:
                        # 按分割的块，分别写入内容
                        txt_file.write(f'interface Ethernet{interface_id}\n')
                        txt_file.write('{\n')
                        txt_file.write(f'    description \"{row["trunk_name"]}\"\n')
                        txt_file.write(f'    lacp trunk{row["trunk_id"]} mode active\n')
                        txt_file.write('    lacp timeout long\n')
                        txt_file.write('}\n\n')
                elif row["trunk_interfaces"]:
                    txt_file.write(f'trunk{row["trunk_id"]}\n')
                    txt_file.write('{\n')
                    trunk_interfaces_id = row["trunk_interfaces"].split()
                    interface_id_Ethernet = ""
                    for interface_id in trunk_interfaces_id:
                        interface_id_Ethernet += "Ethernet" + interface_id + " "
                    txt_file.write(f'    interface {interface_id_Ethernet}\n')
                    txt_file.write('}\n\n')

        if vlan_data:
            txt_file.write('################  VLAN Information:  ################\n')

            # 用于存储已经写入的 VLAN 配置（通过 VLAN Tag 和名称的组合唯一标识）
            written_vlans = set()

            for idx_vlan, row_vlan in vlan_df.iterrows():
                vlan_interfaces_name_match = re.search(r'([^\s]+) \{\n', row_vlan["vlan_interfaces"])
                vlan_interfaces_name = vlan_interfaces_name_match.group(1) if vlan_interfaces_name_match else ''

                # Flag to track if this VLAN was already written with a trunk
                written_with_trunk = False

                for idx_trunk, row_trunk in trunk_df.iterrows():
                    # if "tagged" in row_vlan["vlan_interfaces"]:
                    # 优先处理 trunk 的情况
                    if vlan_interfaces_name in row_trunk["trunk_name"]:
                        unique_key = (row_vlan["vlan_tag"], row_vlan["vlan_name"], "trunk" + str(row_trunk["trunk_id"]))
                        if unique_key not in written_vlans:
                            # 写入 trunk 配置
                            txt_file.write(f'vlan {row_vlan["vlan_tag"]}\n')
                            txt_file.write('{\n')
                            txt_file.write(f'    tagged trunk{row_trunk["trunk_id"]}\n')
                            txt_file.write('    route-intf enable-ve\n')
                            txt_file.write(f'    name \"{row_vlan["vlan_name"]}\"\n')
                            txt_file.write('}\n\n')
                            written_vlans.add(unique_key)
                            written_with_trunk = True
                            break  # 优先 trunk，跳出 trunk 循环

                # 如果没有写入 trunk 配置，则处理 interfaces
                if not written_with_trunk and row_vlan["vlan_interfaces"]:
                    unique_key = (row_vlan["vlan_tag"], row_vlan["vlan_name"], "interfaces " + vlan_interfaces_name)
                    if unique_key not in written_vlans:
                        txt_file.write(f'vlan {row_vlan["vlan_tag"]}\n')
                        txt_file.write('{\n')
                        txt_file.write(f'    tagged interfaces {vlan_interfaces_name}\n')
                        txt_file.write('    route-intf enable-ve\n')
                        txt_file.write(f'    name \"{row_vlan["vlan_name"]}\"\n')
                        txt_file.write('}\n\n')
                        written_vlans.add(unique_key)

        # if vlan_data:
        #     txt_file.write('################  VLAN Information:  ################\n')
        #     for idx_vlan, row_vlan in vlan_df.iterrows():
        #         # for (idx_vlan, row_vlan), (idx_trunk, row_trunk) in zip(vlan_df.iterrows(), trunk_df.iterrows()):
        #         vlan_interfaces_name_match = re.search(r'([^\s]+) \{\n', row_vlan["vlan_interfaces"])
        #         vlan_interfaces_name = vlan_interfaces_name_match.group(1) if vlan_interfaces_name_match else ''
        #
        #         for idx_trunk, row_trunk in trunk_df.iterrows():
        #             if "tagged" in row_vlan["vlan_interfaces"]:
        #                 if vlan_interfaces_name in row_trunk["trunk_name"]:
        #                     txt_file.write(f'vlan {row_vlan["vlan_tag"]}\n')
        #                     txt_file.write('{\n')
        #                     txt_file.write(f'    tagged trunk{row_trunk["trunk_id"]}\n')
        #                     txt_file.write('    route-intf enable-ve\n')
        #                     txt_file.write(f'    name \"{row_vlan["vlan_name"]}\"\n')
        #                     txt_file.write('}\n\n')
        #                 elif row_vlan["vlan_interfaces"]:
        #                     txt_file.write(f'vlan {row_vlan["vlan_tag"]}\n')
        #                     txt_file.write('{\n')
        #                     txt_file.write(f'    tagged interfaces {vlan_interfaces_name}\n')
        #                     txt_file.write('    route-intf enable-ve\n')
        #                     txt_file.write(f'    name \"{row_vlan["vlan_name"]}\"\n')
        #                     txt_file.write('}\n\n')

        if self_data:
            txt_file.write('################  Self_IP Information:  ################\n')
            # 两个for循环，读取self和vlan的信息，因为配置selfIp需要用到vlan的tag号
            for idx, row_self in self_df.iterrows():
                for idx_vlan, row_vlan in vlan_df.iterrows():
                    # 处理接口IP（非浮动）
                    if row_self["self_traffic_group"] == "traffic-group-local-only":
                        # 处理打了tag的vlan
                        if "tagged" in row_vlan["vlan_interfaces"]:
                            if row_self["self_vlan_name"] == row_vlan["vlan_name"]:
                                txt_file.write(f'interface ve{row_vlan["vlan_tag"]}\n')
                                txt_file.write('{\n')

                                if ':' in row_self["self_address"]:
                                    txt_file.write(f'    ipv6 address {row_self["self_address"]}\n')
                                else:
                                    txt_file.write(f'    ip address {row_self["self_address"]}\n')

                                txt_file.write(f'    description \"{row_self["self_name"]}\"\n')
                                txt_file.write('}\n\n')

            txt_file.write('################  Floating_IP Information:  ################\n')
            txt_file.write(f'vrrp vrid 0\n')
            txt_file.write('{\n')
            for idx, row_self in self_df.iterrows():
                # 处理接口IP（浮动）
                if row_self["self_traffic_group"] == "traffic-group-1":
                    selfip_match = re.search(r'([\w.:]+)/\d+', row_self["self_address"])
                    selfip = selfip_match.group(1) if selfip_match else ''
                    # floating_ip =  re.search(r'([\d.]+)', row_self["self_address"])
                    txt_file.write(f'    virtual-ip {selfip}\n')

            txt_file.write('}\n\n')

        if mgmt_route_data:
            txt_file.write('################  mgmt_route_data Information:  ################\n')
            txt_file.write(f'static-route mgmt\n')
            txt_file.write('{\n')
            for idx, row in mgmt_route_df.iterrows():
                if '/' in row["mgmt_route_name"]:
                    txt_file.write(f'    ip route {row["mgmt_route_network"]} {row["mgmt_route_gateway"]}\n')
                elif row["mgmt_route_network"] == 'default':
                    txt_file.write(
                        f'#    ip route 0.0.0.0/0 {row["mgmt_route_gateway"]} description {row["mgmt_route_name"]}\n')
                else:
                    txt_file.write(
                        f'    ip route {row["mgmt_route_network"]} {row["mgmt_route_gateway"]} description {row["mgmt_route_name"]}\n')
            txt_file.write('}\n\n')


def process_folder(folder_path):
    # 遍历文件夹下的所有文件并处理它们
    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.conf'):
                file_path = os.path.join(root_dir, file)
                process_file(file_path)


def run_script():
    # 创建一个Tkinter根窗口并隐藏它
    root = tk.Tk()
    root.withdraw()

    # 使用文件夹选择对话框来获取用户选择的文件夹
    folder_path = filedialog.askdirectory()
    process_folder(folder_path)
