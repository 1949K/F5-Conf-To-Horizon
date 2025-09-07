import re


def extract_pools_vs_nodes(blocks):
    """
    从配置块中提取Virtual Server、Pool和Node信息。
    :param blocks: 配置块列表
    :return: 包含信息的字典
    """
    # 创建一个空的字典
    vs_data = {'vs_name': [], 'vs_connection_limit': [], 'vs_ip_add': [], 'vs_ip_port': [],
               'vs_protocol': [], 'vs_pool_name': [], 'vs_mask': [],
               'vs_source': [], 'translate_address': [], 'translate_port': [],
               'vs_source_translation': [], 'vs_profiles': [], 'vs_rule': [], 'vs_persist': [], 'vs_ip_forward': []}
    pool_data = {'pool_name': [], 'pool_members': [], 'pool_monitor': [], 'pool_lbm': []}
    pool_member_data = {'pool_name': [], 'pool_monitor': [], 'pool_member_ip': [], 'pool_member_port': [],
                        'pool_member_monitor': [], 'pool_member_ratio': []}
    node_data = {'node_ip': []}
    monitor_data = {'monitor_name': [], 'monitor_protocol': [], 'monitor_defaults-from': [],
                    'monitor_destination': [], 'monitor_interval': [], 'monitor_ip-dscp': [],
                    'monitor_recv': [], 'monitor_recv-disable': [], 'monitor_send': [],
                    'monitor_time-until-up': [], 'monitor_timeout': []}
    persistence_data = {'persistence_name': [], 'persistence_protocol': [], 'persistence_defaults-from': [],
                        'persistence_timeout': []}
    profile_data = {'profile_name': [], 'profile_protocol': [], 'profile_xff': [], 'profile_defaults-from': [],
                    'profile_idle_timeout': []}
    snatpool_data = {'snatpool_name': [], 'snatpool_member': []}
    route_data = {'route_name': [], 'route_gateway': [], 'route_network': []}
    rule_data = {'rule_name': [], 'rule_info': []}
    auth_date = {'tacacs_source_type': [], 'tacacs_servers': [], 'radius_servers': []}

    combined_auth_block = ""

    for block in blocks:
        if block:
            if block.startswith('auth '):

                if block.startswith('auth source ') or block.startswith('auth tacacs ') or block.startswith(
                        'auth radius-server '):
                    combined_auth_block += block + "\n"

            elif block.startswith('ltm virtual '):
                # 使用正则表达式提取vs_name
                vs_name_match = re.search(r'ltm virtual( )+([^\s{]+)', block)
                if vs_name_match:
                    vs_partition_name = vs_name_match.group(1).strip()
                    vs_name = vs_name_match.group(2).strip()

                    # 使用正则表达式提取vs_ip_add和vs_ip_port
                    vs_connection_limit_match = re.search(r'connection-limit (\d*)', block)
                    vs_connection_limit = vs_connection_limit_match.group(1) if vs_connection_limit_match else ''

                    # 使用正则表达式提取vs_ip_add和vs_ip_port
                    vs_ip_match = re.search(r'destination( )([\w:.]+)[:.](\d+)', block)
                    vs_ip_add = vs_ip_match.group(1) if vs_ip_match else ''
                    vs_ip_port = vs_ip_match.group(2) if vs_ip_match else ''

                    # 使用正则表达式提取vs_protocol
                    vs_protocol_match = re.search(r'ip-protocol (\S+)', block)
                    vs_protocol = vs_protocol_match.group(1) if vs_protocol_match else ''

                    # 使用正则表达式提取vs_protocol
                    vs_ip_forward_match = re.search(r'\n    (ip-forward)\n', block)
                    vs_ip_forward = vs_ip_forward_match.group(1) if vs_ip_forward_match else ''

                    # 使用正则表达式提取vs_mask
                    vs_mask_match = re.search(r'mask\s+([\d.]+)', block)
                    vs_mask = vs_mask_match.group(1) if vs_mask_match else ''

                    # 使用正则表达式提取vs_pool_name
                    vs_pool_name_match = re.search(r'pool( )+([^\s}]+)', block)
                    vs_pool_name = vs_pool_name_match.group(1).strip() if vs_pool_name_match else ''

                    # 使用正则表达式提取vs_source
                    vs_source_match = re.search(r'source\s+([\d./]+)', block)
                    vs_source = vs_source_match.group(1) if vs_source_match else ''

                    # 使用正则表达式提取translate-address
                    translate_address_match = re.search(r'translate-address\s+(\w+)', block)
                    translate_address = translate_address_match.group(1) if translate_address_match else ''

                    # 使用正则表达式提取translate-port
                    translate_port_match = re.search(r'translate-port\s+(\w+)', block)
                    translate_port = translate_port_match.group(1) if translate_port_match else ''

                    # 使用正则表达式提取vs_source-address-translation
                    vs_source_translation_match = re.findall(r'source-address-translation\s+\{([\s\S]*?)\n    \}\n',
                                                             block, re.DOTALL)
                    vs_source_translation_matches = [re.sub(r'\n\s+', '\n', line) for line in
                                                     vs_source_translation_match]
                    vs_source_translation = '\n'.join(vs_source_translation_matches)

                    # 使用正则表达式提取profiles块
                    vs_profiles_match = re.findall(r'profiles\s+\{([\s\S]*?)\n    \}\n', block, re.DOTALL)
                    vs_profiles_matches = [re.sub(r'\n\s+', '\n', line) for line in vs_profiles_match]
                    vs_profiles = '\n'.join(vs_profiles_matches)

                    # 使用正则表达式提取rules块
                    vs_rule_match = re.findall(r'rules\s+\{([\s\S]*?)\n    \}\n', block, re.DOTALL)
                    vs_rule_matches = [re.sub(r'\n\s+', '\n', line) for line in vs_rule_match]
                    vs_rule = '\n'.join(vs_rule_matches)

                    # 使用正则表达式提取vs_persist
                    vs_persist_match = re.findall(r'persist\s+\{([\s\S]*?)\n    \}\n', block, re.DOTALL)
                    vs_persist_matches = [re.sub(r'\n\s+', '\n', line) for line in vs_persist_match]
                    vs_persist = '\n'.join(vs_persist_matches)

                    # vs_data['vs_partition_name'].append(vs_partition_name)
                    vs_data['vs_name'].append(vs_name)
                    vs_data['vs_connection_limit'].append(vs_connection_limit)
                    vs_data['vs_ip_add'].append(vs_ip_add)
                    vs_data['vs_ip_port'].append(vs_ip_port)
                    vs_data['vs_protocol'].append(vs_protocol)
                    vs_data['vs_pool_name'].append(vs_pool_name)
                    vs_data['vs_mask'].append(vs_mask)
                    vs_data['vs_persist'].append(vs_persist)
                    vs_data['vs_profiles'].append(vs_profiles)
                    vs_data['vs_rule'].append(vs_rule)
                    vs_data['vs_source'].append(vs_source)
                    vs_data['vs_source_translation'].append(vs_source_translation)
                    vs_data['translate_address'].append(translate_address)
                    vs_data['translate_port'].append(translate_port)
                    vs_data['vs_ip_forward'].append(vs_ip_forward)

            elif block.startswith('ltm pool '):
                # 使用正则表达式提取pool_name
                pool_name_match = re.search(r'ltm pool( )+([^\s{]+)', block)
                if pool_name_match:
                    pool_name = pool_name_match.group(2).strip()

                    # 使用正则表达式提取load-balancing-mode信息
                    lbm_match = re.search(r'load-balancing-mode\s+(\S+)', block)
                    pool_lbm = lbm_match.group(1) if lbm_match else ''

                    # 匹配ipv4和ipv6
                    pool_member_matches = re.findall(r'/([^\s]+)/([\w:.]+)[:.](\d+)\s*{\s*address ([\w:.]+)', block,
                                                     re.DOTALL)
                    pool_members = [f'member {member[3]}:{member[2]}' for member in pool_member_matches]

                    # 使用正则表达式提取monitor信息
                    monitor_match = re.search(r'\n\s{4}monitor( )+([^\s}]+)', block)
                    pool_monitor = monitor_match.group(2) if monitor_match else ''

                    pool_data['pool_name'].append(pool_name)
                    pool_data['pool_lbm'].append(pool_lbm)
                    pool_data['pool_members'].append(pool_members)
                    pool_data['pool_monitor'].append(pool_monitor)

                    def split_pool_blocks(content):

                        blocks = []
                        current_block = []

                        for line in content.split('\n'):
                            start_patterns = ('    members {', '    }', '        }', '       ( )')
                            if line.startswith(start_patterns):
                                if current_block:
                                    blocks.append('\n'.join(current_block))
                                current_block = [line]
                            elif line:
                                current_block.append(line)

                        if current_block:
                            blocks.append('\n'.join(current_block))

                        return blocks

                    if "            monitor /" in block or "            ratio" in block:
                        pool_member_blocks = split_pool_blocks(block)

                        for pool_member_block in pool_member_blocks:
                            if "            monitor /" in pool_member_block or "            ratio" in pool_member_block:
                                pool_member_ip_port_block = re.search(
                                    r'/([^\s]+)/([\w:.]+)[:.](\d+)\s*{\s*address ([\w:.]+)',
                                    pool_member_block)
                                pool_member_ip = pool_member_ip_port_block.group(4) if pool_member_ip_port_block else ''
                                pool_member_port = pool_member_ip_port_block.group(
                                    3) if pool_member_ip_port_block else ''

                                pool_member_monitor_matches = re.search(r'monitor( )+([^\s}]+)',
                                                                        pool_member_block)
                                pool_member_monitor = pool_member_monitor_matches.group(
                                    2) if pool_member_monitor_matches else ''

                                pool_member_ratio_matches = re.search(r'ratio (\d)', pool_member_block)
                                pool_member_ratio = pool_member_ratio_matches.group(
                                    1) if pool_member_ratio_matches else ''

                                # 这里复用了pool提取的名称，
                                pool_member_data['pool_name'].append(pool_name)
                                # pool_member_data['pool_lbm'].append(pool_lbm)
                                # pool_member_data['pool_members'].append(pool_members)
                                pool_member_data['pool_monitor'].append(pool_monitor)

                                pool_member_data['pool_member_ip'].append(pool_member_ip)
                                pool_member_data['pool_member_port'].append(pool_member_port)
                                pool_member_data['pool_member_monitor'].append(pool_member_monitor)
                                pool_member_data['pool_member_ratio'].append(pool_member_ratio)



            elif block.startswith('ltm node '):
                # 使用正则表达式提取node_ip
                node_ip_match = re.search(r'address\s+([\S.:]+)', block)
                node_ip = node_ip_match.group(1) if node_ip_match else ''
                node_data['node_ip'].append(node_ip)

            elif block.startswith('ltm monitor '):

                # 使用正则表达式提取 monitor_protocol 和 monitor_name
                monitor_info_match = re.search(r'ltm monitor ([\w-]+)( )([^\s{]+)', block)
                monitor_protocol = monitor_info_match.group(1) if monitor_info_match else ''
                monitor_name = monitor_info_match.group(3) if monitor_info_match else ''

                # 使用正则表达式提取 monitor_defaults-from
                monitor_defaults_from_match = re.search(r'defaults-from( )(\w+)', block)
                monitor_defaults_from = monitor_defaults_from_match.group(2) if monitor_defaults_from_match else ''

                # 使用正则表达式提取 monitor_destination
                monitor_destination_match = re.search(r'destination ([^\n]+)', block)
                monitor_destination = monitor_destination_match.group(1) if monitor_destination_match else ''

                # 使用正则表达式提取 monitor_interval
                monitor_interval_match = re.search(r'interval (\d+)', block)
                monitor_interval = monitor_interval_match.group(1) if monitor_interval_match else ''

                # 使用正则表达式提取 monitor_ip-dscp
                monitor_ip_dscp_match = re.search(r'ip-dscp (\d+)', block)
                monitor_ip_dscp = monitor_ip_dscp_match.group(1) if monitor_ip_dscp_match else ''

                # 使用正则表达式提取 monitor_recv
                monitor_recv_match = re.search(r'recv ([\w" ]+)', block)
                monitor_recv = monitor_recv_match.group(1) if monitor_recv_match else ''

                # 使用正则表达式提取 monitor_recv-disable
                monitor_recv_disable_match = re.search(r'recv-disable ([\w" ]+)', block)
                monitor_recv_disable = monitor_recv_disable_match.group(1) if monitor_recv_disable_match else ''

                # 使用正则表达式提取 monitor_send：提取send到换行之间的内容
                monitor_send_match = re.search(r'send ([^\n]+)', block)
                monitor_send = monitor_send_match.group(1) if monitor_send_match else ''

                # 使用正则表达式提取 monitor_time-until-up
                monitor_time_until_up_match = re.search(r'time-until-up (\d+)', block)
                monitor_time_until_up = monitor_time_until_up_match.group(1) if monitor_time_until_up_match else ''

                # 使用正则表达式提取 monitor_timeout
                monitor_timeout_match = re.search(r'timeout (\d+)', block)
                monitor_timeout = monitor_timeout_match.group(1) if monitor_timeout_match else ''

                monitor_data['monitor_protocol'].append(monitor_protocol)
                monitor_data['monitor_name'].append(monitor_name)
                monitor_data['monitor_defaults-from'].append(monitor_defaults_from)
                monitor_data['monitor_destination'].append(monitor_destination)
                monitor_data['monitor_interval'].append(monitor_interval)
                monitor_data['monitor_ip-dscp'].append(monitor_ip_dscp)
                monitor_data['monitor_recv'].append(monitor_recv)
                monitor_data['monitor_recv-disable'].append(monitor_recv_disable)
                monitor_data['monitor_send'].append(monitor_send)
                monitor_data['monitor_time-until-up'].append(monitor_time_until_up)
                monitor_data['monitor_timeout'].append(monitor_timeout)

            elif block.startswith('ltm persistence '):
                # 使用正则表达式提取 persistence_protocol 和 persistence_name
                persistence_info_match = re.search(r'ltm persistence +([^\s{]+)( )+([^\s{]+)', block)
                persistence_protocol = persistence_info_match.group(1) if persistence_info_match else ''
                persistence_name = persistence_info_match.group(3) if persistence_info_match else ''

                persistence_defaults_from_match = re.search(r'defaults-from( )(\w+)', block)
                persistence_defaults_from = persistence_defaults_from_match.group(
                    2) if persistence_defaults_from_match else ''

                persistence_timeout_match = re.search(r'timeout (\d+)', block)
                persistence_timeout = persistence_timeout_match.group(1) if persistence_timeout_match else ''

                # 将提取的信息添加到 persistence_data 中
                persistence_data['persistence_protocol'].append(persistence_protocol)
                persistence_data['persistence_name'].append(persistence_name)
                persistence_data['persistence_defaults-from'].append(persistence_defaults_from)
                persistence_data['persistence_timeout'].append(persistence_timeout)

                # 根据你的需要存储或在 Excel 中显示这些信息

            elif block.startswith('ltm profile '):
                # 使用正则表达式提取 profile_protocol 和 profile_name
                profile_info_match = re.search(r'ltm profile +([^\s{]+)( )+([^\s{]+)', block)

                profile_protocol = profile_info_match.group(1) if profile_info_match else ''
                profile_name = profile_info_match.group(3) if profile_info_match else ''

                profile_defaults_from_match = re.search(r'defaults-from( )(\w+)', block)
                profile_defaults_from = profile_defaults_from_match.group(
                    2) if profile_defaults_from_match else ''

                profile_idle_timeout_match = re.search(r'idle-timeout (\d+)', block)
                profile_idle_timeout = profile_idle_timeout_match.group(1) if profile_idle_timeout_match else ''

                profile_xff_match = re.search(r'insert-xforwarded-for (\w+)', block)
                profile_xff = profile_xff_match.group(1) if profile_xff_match else ''

                # 将提取的信息添加到 profile_data 中
                profile_data['profile_protocol'].append(profile_protocol)
                profile_data['profile_name'].append(profile_name)
                profile_data['profile_defaults-from'].append(profile_defaults_from)
                profile_data['profile_idle_timeout'].append(profile_idle_timeout)
                profile_data['profile_xff'].append(profile_xff)

                # 存储或在 Excel 中显示这些信息，根据你的需要

            elif block.startswith('ltm snatpool '):
                # 使用正则表达式提取 snatpool_protocol 和 snatpool_name
                snatpool_info_match = re.search(r'ltm snatpool( )+([^\s{]+)', block)
                snatpool_name = snatpool_info_match.group(2) if snatpool_info_match else ''

                snatpool_matches = re.findall(r'   ( )([\w.:]+)', block, re.DOTALL)
                snatpool_member = [f'{member}' for member in snatpool_matches]

                # 将提取的信息添加到 snatpool_data 中
                snatpool_data['snatpool_name'].append(snatpool_name)
                snatpool_data['snatpool_member'].append(snatpool_member)

            elif block.startswith('net route '):
                route_name_match = re.search(r'net route( )+([^\s{]+)', block)
                route_name = route_name_match.group(2) if route_name_match else ''

                route_gateway_match = re.search(r'gw ([\w.:]+)', block)
                route_gateway = route_gateway_match.group(1) if route_gateway_match else ''

                route_network_match = re.search(r'network ([\w.:/]+)', block)
                route_network = route_network_match.group(1) if route_network_match else ''

                route_data['route_name'].append(route_name)
                route_data['route_gateway'].append(route_gateway)
                route_data['route_network'].append(route_network)

            elif block.startswith('ltm rule '):
                rule_name_match = re.search(r'ltm rule( )+([^\s{]+)', block)
                rule_name = rule_name_match.group(2) if rule_name_match else ''

                rule_info_match = re.search(r'ltm rule( )(.*)', block, re.DOTALL)
                rule_info = rule_info_match.group(2) if rule_info_match else ''

                rule_data['rule_name'].append(rule_name)
                rule_data['rule_info'].append(rule_info)

    if combined_auth_block:
        tacacs_source_type_match = re.search(r'type ([\w-]+)', combined_auth_block)
        tacacs_source_type = tacacs_source_type_match.group(1) if tacacs_source_type_match else ''

        tacacs_servers_match = re.search(r'servers \{ ([\d.\s]+) \}', combined_auth_block)
        tacacs_servers = tacacs_servers_match.group(1) if tacacs_servers_match else ''

        radius_servers_match = re.search(r'server ([\d.]+)', combined_auth_block)
        radius_servers = radius_servers_match.group(1) if radius_servers_match else ''

        auth_date['tacacs_source_type'].append(tacacs_source_type)
        auth_date['tacacs_servers'].append(tacacs_servers)
        auth_date['radius_servers'].append(radius_servers)

    return vs_data, pool_data, pool_member_data, node_data, monitor_data, persistence_data, profile_data, snatpool_data, route_data, rule_data, auth_date
