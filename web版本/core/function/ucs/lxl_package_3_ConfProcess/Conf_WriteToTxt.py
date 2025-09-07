import re
from ipaddress import ip_address, IPv6Address

import pandas as pd


# 检查ip地址是否连续

def is_consecutive(ip_list):
    """
    检查 IP 地址是否是连续的。
    """
    sorted_ips = sorted(ip_list, key=lambda ip: ip_address(ip))
    for i in range(1, len(sorted_ips)):
        if ip_address(sorted_ips[i]) != ip_address(sorted_ips[i - 1]) + 1:
            return False
    return True


# 检查ip地址是否连续
def get_ip_ranges(ip_list):
    """
    将连续的 IP 地址合并为范围。
    """
    sorted_ips = sorted(ip_list, key=lambda ip: ip_address(ip))
    ranges = []
    start = sorted_ips[0]
    prev = sorted_ips[0]

    for ip in sorted_ips[1:]:
        if ip_address(ip) == ip_address(prev) + 1:
            prev = ip
        else:
            ranges.append((start, prev))
            start = ip
            prev = ip
    ranges.append((start, prev))
    return ranges


def format_irule_as_tcl(content, indent_level=4):
    """
    将 iRule 内容格式化为符合 Tcl 规范的缩进格式，调整 `else` 和 `elseif` 的位置，
    并将所有的 `}{` 替换为 `} {`。

    :param content: 原始 iRule 内容（字符串）
    :param indent_level: 每一级的缩进空格数，默认4
    :return: 格式化后的 iRule 内容
    """
    formatted_lines = []
    current_indent = 0
    indent = " " * indent_level
    lines = content.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # 检查是否是结束的 "}" 并且下一行是 "else {" 或 "elseif {"
        if line == '}' and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith('else') or next_line.startswith('elseif'):
                # 减少缩进级别，因为 "}" 应该与对应的 "if" 对齐
                current_indent -= 1
                # 构建合并后的行，如 "} else {" 或 "} elseif {"
                merged_line = f"}} {next_line}"
                formatted_lines.append(f"{indent * current_indent}{merged_line}")
                # 如果合并后的行以 "{" 结尾，增加缩进级别
                if merged_line.endswith('{'):
                    current_indent += 1
                i += 2  # 跳过下一行
                continue

        # 如果是结束的 "}", 减少缩进级别
        if line.startswith('}'):
            current_indent -= 1

        # 添加当前行，并根据当前缩进级别调整缩进
        formatted_lines.append(f"{indent * current_indent}{line}")

        # 如果是开始的 "{", 增加缩进级别
        if line.endswith('{'):
            current_indent += 1

        i += 1

    # 合并格式化后的行
    formatted_content = "\n".join(formatted_lines)

    # 替换所有的 "}{" 为 "} {"
    formatted_content = formatted_content.replace('}{', '} {')

    return formatted_content


def write_to_txt(txt_file_path, vs_data, pool_data, pool_member_data, node_data, monitor_data, persistence_data,
                 profile_data, snatpool_data, route_data, rule_data, auth_date):
    """
    将数据写入文本文件
    """
    # 省略其他写入文本文件的部分...
    # 将汇总信息写入 txt 文件

    if pool_data:
        pool_df = pd.DataFrame(pool_data)
    if pool_member_data:
        pool_member_df = pd.DataFrame(pool_member_data)
    if vs_data:
        vs_df = pd.DataFrame(vs_data)
    if node_data:
        node_df = pd.DataFrame(node_data)
    if monitor_data:
        monitor_df = pd.DataFrame(monitor_data)
    if persistence_data:
        persistence_df = pd.DataFrame(persistence_data)
    if profile_data:
        profile_df = pd.DataFrame(profile_data)
    if snatpool_data:
        snatpool_df = pd.DataFrame(snatpool_data)
    if route_data:
        route_df = pd.DataFrame(route_data)
    if rule_data:
        rule_df = pd.DataFrame(rule_data)
    if auth_date:
        auth_df = pd.DataFrame(auth_date)

    with open(txt_file_path, 'w') as txt_file:
        if auth_date:
            txt_file.write('################  Auth Information:  ################\n')
            for idx, row in auth_df.iterrows():
                if "radius" in row["tacacs_source_type"]:
                    txt_file.write('radius-server read-write\n')
                    txt_file.write(f'# 注意：更改 secret XXXXXXXX\n')
                    txt_file.write(f'radius-server host {row["radius_servers"]} secret XXXXXXXX\n')
                    txt_file.write('authentication type radius buffer-local\n')
                    txt_file.write('authentication console type radius buffer-local\n')
                elif "tacacs" in row.tacacs_source_type:
                    tacacs_servers = re.findall(r'[\d.]+', row.tacacs_servers)
                    txt_file.write(f'# 注意：更改 secret XXXXXXXX\n')
                    for tacacs_server in tacacs_servers:
                        txt_file.write(f'tacacs-server host {tacacs_server} secret XXXXXXXX port 49 timeout 12\n')
                    txt_file.write('authentication type tacacsplus buffer-local\n')
                    txt_file.write('authentication console type tacacsplus buffer-local\n')
                else:
                    txt_file.write(f'# 注意：tacacs_source_type：{row["tacacs_source_type"]}\n')

            txt_file.write('\n\n')

        if node_data:
            txt_file.write('################  Node Information:  ################\n')
            for idx, row in node_df.iterrows():
                txt_file.write(f'slb node {row["node_ip"]} {row["node_ip"]}\n')
            txt_file.write('\n\n')

        # if snatpool_data:
        #     txt_file.write('################  SNAT_Pool Information:  ################\n')
        #     for idx, row in snatpool_df.iterrows():
        #         txt_file.write(f'ip nat pool {row["snatpool_name"]}\n')
        #         txt_file.write('{\n')
        #         for member in row["snatpool_member"]:
        #             txt_file.write(f'   member {member} {member} netmask /24\n')
        #         txt_file.write('}\n\n')
        #     txt_file.write('\n')

        if snatpool_data:
            txt_file.write('################  SNAT_Pool Information:  ################\n')
            for idx, row in snatpool_df.iterrows():
                txt_file.write(f'ip nat pool {row["snatpool_name"]}\n')
                txt_file.write('{\n')
                # 获取 SNAT_Pool 的 IP 范围
                ranges = get_ip_ranges(row["snatpool_member"])
                for start, end in ranges:
                    # 根据 IP 地址类型输出 IPv4 或 IPv6 的格式
                    if isinstance(ip_address(start), IPv6Address):
                        if start == end:
                            txt_file.write(f'   ipv6 member {start} {end} netmask /64\n')
                        else:
                            txt_file.write(f'   ipv6 member {start} {end} netmask /64\n')
                    else:
                        if start == end:
                            txt_file.write(f'   member {start} {end} netmask /24\n')
                        else:
                            txt_file.write(f'   member {start} {end} netmask /24\n')
                txt_file.write('}\n\n')
            txt_file.write('\n')

        if monitor_data:
            txt_file.write('################  Monitor Information:  ################\n')
            for idx, row in monitor_df.iterrows():

                # 提取间隔和超时时间
                monitor_interval = int(row["monitor_interval"])
                monitor_timeout = int(row["monitor_timeout"])
                # 取整数
                # monitor_timeout_ok = int((monitor_timeout / monitor_interval) - 1)
                monitor_timeout_ok = int((monitor_timeout / monitor_interval))
                # 最大5次重试
                if monitor_timeout_ok > 5:
                    monitor_timeout_ok = 5
                txt_file.write(
                    f'health check {row["monitor_name"]} interval {monitor_interval} retry {monitor_timeout_ok} timeout {monitor_interval} up-check-cnt 1\n')

                txt_file.write('{\n')
                txt_file.write('    wait-all-retry\n')

                # 提取 别名端口和别名地址
                alias = row["monitor_destination"]
                # Improved regex to handle all cases
                alias_match = re.search(
                    r'^'
                    r'('
                    r'(\*)|'  # Wildcard *
                    r'(\d{1,3}\.){3}\d{1,3}|'  # IPv4
                    r'\[([0-9a-fA-F:]+)\]|'  # IPv6 with brackets
                    r'([0-9a-fA-F:]+)'  # IPv6 without brackets
                    r')'
                    r'[:.]'  # Separator : or .
                    r'(\*|\d+)$',  # Port (* or number)
                    alias.strip()
                )

                if alias_match:
                    # Determine IP and port
                    alias_ip = alias_match.group(1)
                    alias_port = alias_match.group(6)

                    # Clean IPv6 address (remove brackets if present) 删除ipv6外部的[]框
                    if alias_ip.startswith('[') and alias_ip.endswith(']'):
                        alias_ip = alias_ip[1:-1]

                    # Determine if IP is IPv4 or IPv6
                    is_ipv6 = ':' in alias_ip and '.' not in alias_ip  # Simple heuristic for IPv6

                    # http 和 tcp 的别名端口和别名地址 限定：类型为http和tcp类型，且不为"*:*"才进行处理
                    if row["monitor_defaults-from"] in ["http", "https", "tcp", "gateway_icmp"] and row[
                        "monitor_destination"] != "*:*":
                        if alias_ip == "*" and alias_port != "*":
                            txt_file.write(f'    alias-port {alias_port}\n')
                        elif alias_ip != "*" and alias_port == "*":
                            if is_ipv6:
                                txt_file.write(f'    alias-address-ipv6 {alias_ip}\n')
                            else:
                                txt_file.write(f'    alias-address {alias_ip}\n')
                        else:
                            if is_ipv6:
                                txt_file.write(f'    alias-address-ipv6 {alias_ip}\n')
                                txt_file.write(f'    alias-port {alias_port}\n')
                            else:
                                txt_file.write(f'    alias-address {alias_ip}\n')
                                txt_file.write(f'    alias-port {alias_port}\n')

                # 提取 发送/接收/禁用 字符串
                monitor_send = row["monitor_send"]
                monitor_recv = row["monitor_recv"]
                monitor_recv_disable = row["monitor_recv-disable"]

                monitor_tcp_send = ""
                monitor_http_send = ""

                # 将http和tcp分开提取send，因为http和https的send有双引号包裹，tcp的send可能没有
                if row["monitor_defaults-from"] == "http" or row["monitor_defaults-from"] == "https":
                    # monitor_http_send_match = re.search(r'GET\s+([\w?/.=_-]+) ', monitor_send)
                    monitor_http_send_match = re.search(r'GET\s+([^\s"]+)', monitor_send)
                    monitor_http_send = monitor_http_send_match.group(1) if monitor_http_send_match else ''
                elif row["monitor_defaults-from"] == "tcp":
                    monitor_tcp_send_match = re.search(r'([^\n]+)', monitor_send)
                    monitor_tcp_send = monitor_tcp_send_match.group(1) if monitor_tcp_send_match else ''

                # 有的F5的tcp健康检查使用xml查询，会很长，但是弘积的设备不支持大于256支付的tcp健康检查。
                if (len(monitor_tcp_send) >= 256):
                    txt_file.write(f'    #TCP发送字符串太长：<<< {monitor_tcp_send} >>>\n')

                if '?' in monitor_http_send:
                    monitor_http_send_to_unicode = monitor_http_send.replace('?', r'\077')
                    monitor_http_send = '"' + monitor_http_send_to_unicode + '"'
                if '?' in monitor_tcp_send:
                    monitor_tcp_send_to_unicode = monitor_tcp_send.replace('?', r'\077')
                    monitor_tcp_send = '"' + monitor_tcp_send_to_unicode + '"'
                if '?' in monitor_recv:
                    monitor_recv_to_unicode = monitor_recv.replace('?', r'\077')
                    monitor_recv = '"' + monitor_recv_to_unicode + '"'
                if '?' in monitor_recv_disable:
                    monitor_recv_disable_to_unicode = monitor_recv_disable.replace('?', r'\077')
                    monitor_recv_disable = '"' + monitor_recv_disable_to_unicode + '"'

                # 提取 http 类型的 发送 接收和禁用 进行处理
                if row["monitor_defaults-from"] == "tcp":
                    if monitor_recv and monitor_recv_disable and monitor_recv != "none" and monitor_recv != "none":
                        txt_file.write(
                            f'    method tcp port 80 send {monitor_tcp_send} recv {monitor_recv} recv-disable {monitor_recv}\n')
                    elif monitor_recv and monitor_recv != "none" and monitor_recv != "none":
                        txt_file.write(f'    method tcp port 80 send {monitor_tcp_send} recv {monitor_recv}\n')
                    else:
                        txt_file.write('    method tcp port 80\n')
                elif row["monitor_defaults-from"] == "http":
                    if ('200 OK' in monitor_recv or '200' in monitor_recv) and monitor_http_send == "/":
                        txt_file.write(f'    method http response response-code 200\n')
                    elif ('200 OK' in monitor_recv or '200' in monitor_recv) and monitor_http_send and monitor_http_send != "/":
                        txt_file.write(f'    method http url GET {monitor_http_send} response response-code 200\n')
                    elif monitor_recv and monitor_recv_disable and monitor_recv != "none" and monitor_recv_disable != "none":
                        txt_file.write(
                            f'    method http url GET {monitor_http_send} response {monitor_recv} recv-disable {monitor_recv_disable}\n')
                    elif monitor_recv and monitor_recv != "none" and monitor_recv_disable == "none":
                        txt_file.write(f'    method http url GET {monitor_http_send} response {monitor_recv}\n')
                    elif monitor_http_send and monitor_http_send != "none":
                        txt_file.write(f'    method http url GET {monitor_http_send}\n')
                    else:
                        txt_file.write('    method http\n')

                elif row["monitor_defaults-from"] == "https":
                    monitor_recv_cipher = "cipher TLS1_RSA_AES_128_SHA TLS1_RSA_AES_256_SHA TLS1_RSA_AES_128_SHA256 TLS1_RSA_AES_256_SHA256 TLS1_ECDHE_RSA_WITH_AES_128_CBC_SHA TLS1_ECDHE_RSA_WITH_AES_128_GCM_SHA256 TLS1_ECDHE_RSA_WITH_AES_256_GCM_SHA384 TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256 TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384 TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256 TLS_DHE_RSA_WITH_CHACHA20_POLY1305_SHA256 TLS_DHE_RSA_WITH_AES_128_GCM_SHA256 TLS_DHE_RSA_WITH_AES_256_GCM_SHA384 TLS_DHE_RSA_WITH_AES_128_CBC_SHA256 TLS1_RSA_WITH_AES_128_GCM_SHA256 TLS1_RSA_WITH_AES_256_GCM_SHA384 TLS1_ECDHE_ECDSA_WITH_AES_128_CBC_SHA TLS1_ECDHE_ECDSA_WITH_AES_256_CBC_SHA TLS1_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 TLS1_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384 TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256 TLS_AES_128_GCM_SHA256 TLS_AES_256_GCM_SHA384 TLS_CHACHA20_POLY1305_SHA256 TLS_SM4_GCM_SM3 TLS_SM4_CCM_SM3"
                    if ('200 OK' in monitor_recv or '200' in monitor_recv) and monitor_http_send == "/":
                        txt_file.write(f'    method https {monitor_recv_cipher} response response-code 200\n')
                    elif ('200 OK' in monitor_recv or '200' in monitor_recv) and monitor_http_send and monitor_http_send != "/":
                        txt_file.write(
                            f'    method https url GET {monitor_http_send} {monitor_recv_cipher} response response-code 200\n')
                    elif monitor_recv and monitor_recv_disable and monitor_recv != "none" and monitor_recv_disable != "none":
                        txt_file.write(
                            f'    method https url GET {monitor_http_send} {monitor_recv_cipher} response {monitor_recv} recv-disable {monitor_recv_disable}\n')
                    elif monitor_recv and monitor_recv != "none" and monitor_recv_disable == "none":
                        txt_file.write(
                            f'    method https url GET {monitor_http_send} {monitor_recv_cipher} response {monitor_recv}\n')
                    elif monitor_http_send and monitor_http_send != "none":
                        txt_file.write(f'    method https url GET {monitor_http_send} {monitor_recv_cipher}\n')
                    else:
                        txt_file.write(f'    method https {monitor_recv_cipher}\n')

                elif row["monitor_defaults-from"] == "tcp-half-open":
                    txt_file.write('    method tcp port 80 send-rst\n')

                elif row["monitor_defaults-from"] == "icmp" or row["monitor_defaults-from"] == "gateway_icmp":
                    txt_file.write('')

                elif row["monitor_defaults-from"] == "dns":
                    if row["monitor_dns_qname"] :
                        txt_file.write(f'    method dns domain {row["monitor_dns_qname"]} response response-code 0\n')
                    else:
                        txt_file.write('    method dns domain www.baidu.com response response-code 0\n')



                else:
                    txt_file.write('    method tcp port 80\n')
                    txt_file.write(f'#    注意：F5配置中的健康检查类型为“{row["monitor_defaults-from"]}”，这里改为tcp\n')

                txt_file.write('}\n\n')

            txt_file.write('\n')

        # if pool_member_data:
        #     txt_file.write('################  Pool_Member_Ratio Information:  ################\n')
        #     for idx, row in pool_member_df.iterrows():
        #         pool_name = row['pool_name']
        #         pool_monitor = row['pool_monitor']
        #
        #         pool_member_ip = row['pool_member_ip']
        #         pool_member_port = row['pool_member_port']
        #         pool_member_monitor = row['pool_member_monitor']
        #         pool_member_ratio = row['pool_member_ratio']
        #
        #         if pool_member_ratio:
        #             txt_file.write(f'slb pool {pool_name} tcp\n')
        #             txt_file.write(f'    member {pool_member_ip}:{pool_member_port} priority {pool_member_ratio}\n')
        #             txt_file.write('\n\n')

            txt_file.write('################  Pool_Member_Monitor Information:  ################\n')
            for idx, row in pool_member_df.iterrows():
                pool_name = row['pool_name']
                pool_monitor = row['pool_monitor']

                pool_member_ip = row['pool_member_ip']
                pool_member_port = row['pool_member_port']
                pool_member_monitor = row['pool_member_monitor']
                pool_member_ratio = row['pool_member_ratio']

                if pool_member_monitor:
                    txt_file.write(f'slb node {pool_member_ip} {pool_member_ip}\n')
                    txt_file.write(f'    port {pool_member_port} tcp\n')
                    txt_file.write(f'        health-check {pool_member_monitor}\n')
                    txt_file.write('\n\n')

        if persistence_data:
            txt_file.write('################  Persistence Information:  ################\n')
            for idx, row in persistence_df.iterrows():
                protocol = row["persistence_protocol"]
                name = row["persistence_name"]
                timeout = row["persistence_timeout"]

                if protocol == "source-addr":
                    txt_file.write(f'slb profile persist source-ip {name}\n')
                elif protocol == "cookie":
                    txt_file.write(f'slb profile persist cookie {name}\n')
                elif protocol == "dest-addr":
                    txt_file.write(f'slb profile persist dest-ip {name}\n')
                elif protocol == "universal":
                    txt_file.write(f'slb profile persist source-ip {name}\n')
                else:
                    txt_file.write(f'#slb profile persist source-ip {name}\n')
                # else:
                #     txt_file.write(f'#slb profile persist {protocol} {name}\n')
                txt_file.write('{\n')
                if timeout:
                    timeout_s = int(timeout)
                    timeout_m = int(timeout_s / 60)
                    if protocol in ["source-addr", "cookie", "dest-addr"]:
                        txt_file.write(f'    timeout {timeout_m}\n')
                    else:
                        txt_file.write(f'#    timeout {timeout_m}\n')
                txt_file.write('}\n\n')
            txt_file.write('\n')

        if profile_data:

            # 创建一个空集合来存储不重复的值
            unique_profiles = set()
            conf_creat_profiles = set()

            txt_file.write('################  profile Information:  ################\n')
            for idx, row in vs_df.iterrows():
                matches = []  # 在每次循环开始时初始化matches列表
                if "/Common/" in row["vs_profiles"]:
                    vs_profiles_match = list(re.finditer(r'/Common/+?([^\s{]+)', row["vs_profiles"]))
                    matches = [match.group(1) for match in vs_profiles_match]
                if "udp" in row["vs_protocol"]:
                    matches.append("udp")

                # 将匹配项添加到集合中
                unique_profiles.update(matches)

            for idx, row in profile_df.iterrows():
                profile_name = row["profile_name"]  # 直接获取profile_name
                conf_creat_profiles.add(profile_name)  # 使用.add()方法添加到集合中

            txt_file.write(f'# VS中调用的profile有如下几种：\n')
            for profile in unique_profiles:
                txt_file.write(f'# {profile}\n')
            txt_file.write('\n')

            txt_file.write(f'# 配置文件中创建的profile有如下几种：\n')
            for profile in conf_creat_profiles:
                txt_file.write(f'# {profile}\n')
            txt_file.write('\n')

            txt_file.write(f'# VS中调用的profile没有创建如下几种：\n')
            txt_file.write(f'# 注意：\n')
            txt_file.write(f'# 对于fastL4的profile，将直接翻译为tcp\n')
            txt_file.write(f'# 对于tcp类型的profile，将直接翻译为tcp和ks_tcp\n')
            for profile in unique_profiles:
                if profile not in profile_df['profile_name'].values and profile not in ["tcp", "fastL4", "udp"]:
                    txt_file.write(f'# {profile}\n')
            txt_file.write('\n')

            # 只进行一次运行
            tcp_fastL4_executed = False
            for profile in unique_profiles:
                if "tcp" in profile or "fastL4" in profile:
                    if not tcp_fastL4_executed:  # 只有在没有执行过时执行以下代码
                        txt_file.write(f'slb profile tcp tcp\n')
                        txt_file.write('{\n')
                        txt_file.write(f'    idle-timeout 300\n')
                        txt_file.write(f'    reset-node\n')
                        txt_file.write(f'    reset-client\n')
                        txt_file.write('}\n')
                        txt_file.write(f'slb profile tcp-agent ks_tcp\n')
                        txt_file.write('{\n')
                        txt_file.write(f'    idle-timeout 300\n')
                        txt_file.write(f'    reset-node\n')
                        txt_file.write(f'    reset-client\n')
                        txt_file.write('}\n\n')
                        tcp_fastL4_executed = True  # 设置为已执行

            udp_executed = False
            if not udp_executed:  # 只有在没有执行过时执行以下代码
                for profile in unique_profiles:
                    if "udp" in profile:
                        txt_file.write(f'slb profile udp udp\n')
                        txt_file.write('\n\n')
                        udp_executed = True  # 设置为已执行

            # 只进行一次运行
            ftp_executed = False
            for profile in unique_profiles:
                if "ftp" in profile:
                    if not ftp_executed:  # 只有在没有执行过时执行以下代码
                        txt_file.write(f'slb profile ftp ftp\n\n')
                        ftp_executed = True  # 设置为已执行

            for idx, row in profile_df.iterrows():
                # 下面是在conf文件中，非默认的profile，进行了单独的处理。
                if row["profile_defaults-from"] == "http":
                    txt_file.write(f'slb profile http {row["profile_name"]}\n')
                    txt_file.write('{\n')
                    if row["profile_xff"]:
                        txt_file.write(f'    client-ip-insert X-Forwarded-For\n')
                    txt_file.write('}\n\n')
                elif row["profile_defaults-from"] == "oneconnect":
                    txt_file.write(f'slb profile connection-multiplex {row["profile_name"]}\n\n')
                elif row["profile_defaults-from"] == "fastL4":
                    txt_file.write(f'slb profile tcp {row["profile_name"]}\n')
                    txt_file.write('{\n')
                    txt_file.write(f'    idle-timeout {row["profile_idle_timeout"]}\n')
                    txt_file.write(f'    reset-node\n')
                    txt_file.write(f'    reset-client\n')
                    txt_file.write('}\n\n')
                elif row["profile_defaults-from"] == "tcp":
                    txt_file.write(f'slb profile tcp {row["profile_name"]}\n')
                    txt_file.write('{\n')
                    txt_file.write(f'    idle-timeout {row["profile_idle_timeout"]}\n')
                    txt_file.write(f'    reset-node\n')
                    txt_file.write(f'    reset-client\n')
                    txt_file.write('}\n')
                    txt_file.write(f'slb profile tcp-agent ks_{row["profile_name"]}\n')
                    txt_file.write('{\n')
                    txt_file.write(f'    idle-timeout {row["profile_idle_timeout"]}\n')
                    txt_file.write(f'    reset-node\n')
                    txt_file.write(f'    reset-client\n')
                    txt_file.write('}\n\n')
                else:
                    txt_file.write(f'slb profile tcp {row["profile_name"]}\n')
                    txt_file.write('{\n')
                    txt_file.write(f'    reset-node\n')
                    txt_file.write(f'    reset-client\n')
                    txt_file.write('}\n')

            txt_file.write('\n')

        # if pool_data:
        #     txt_file.write('################  Pool Information:  ################\n')
        #     for idx, row in pool_df.iterrows():
        #         txt_file.write(f'slb pool {row["pool_name"]} tcp\n')
        #         txt_file.write('{\n')
        #         if row["pool_monitor"] == "gateway_icmp" or row["pool_monitor"] == "gateway-icmp":
        #         # if row["pool_monitor"] == "gateway_icmp" :
        #             txt_file.write(f'    health-check ping\n')
        #         elif row["pool_monitor"]:
        #             txt_file.write(f'    health-check {row["pool_monitor"]}\n')
        #
        #         if row["pool_lbm"] == "least-connections-member":
        #             txt_file.write(f'    method service-least-connection\n')
        #
        #         for member in row["pool_members"]:
        #             for idx, pool_members_row in pool_member_df.iterrows():
        #                 if pool_members_row["pool_member_session_user_disabled"] == "user-disabled":
        #                     txt_file.write(f'    {member}  disable\n')
        #                 else:
        #                     txt_file.write(f'    {member}\n')
        #         txt_file.write('}\n\n')
        #     txt_file.write('\n')
        if pool_data:
            txt_file.write('################  Pool Information:  ################\n')
            for _, pool_row in pool_df.iterrows():
                pool_name = pool_row["pool_name"]
                txt_file.write(f'slb pool {pool_name} tcp\n')
                txt_file.write('{\n')

                # 1. 处理 health-check（监控）
                if pool_row["pool_monitor"] in ("gateway_icmp", "gateway-icmp"):
                    txt_file.write('    health-check ping\n')
                elif pool_row["pool_monitor"]:
                    txt_file.write(f'    health-check {pool_row["pool_monitor"]}\n')

                # 2. 处理负载均衡方法
                if pool_row["pool_lbm"] == "least-connections-member":
                    txt_file.write('    method service-least-connection\n')

                # 3. 处理 members（优化：避免双重循环）
                # (1) 先筛选当前 pool 的所有 members
                current_pool_members = pool_member_df[pool_member_df["pool_name"] == pool_name]
                # print(current_pool_members)

                # (2) 遍历当前 pool 的 members
                for member in pool_row["pool_members"]:
                    # 提取 IP:Port（例如 "member 10.204.10.153:8087" → "10.204.10.153:8087"）
                    member_ip_port = member.replace("member ", "")

                    # (3) 检查是否有独立配置（用 IP:Port 匹配）
                    member_info = current_pool_members[
                        (current_pool_members["pool_member_ip"] + ":" +
                         current_pool_members["pool_member_port"].astype(str)) == member_ip_port
                        ]

                    if not member_info.empty:
                        # 如果有独立配置（如 disable/ratio）
                        session_status = member_info.iloc[0]["pool_member_session_user_disabled"]
                        ratio = member_info.iloc[0]["pool_member_ratio"]

                        # 写入 member 行（带 disable 或 weight）
                        if session_status == "user-disabled" and ratio != "":
                            txt_file.write(f'    {member} priority {ratio}\n')
                        elif session_status == "user-disabled":
                            txt_file.write(f'    {member} disable\n')
                        elif ratio != "":  # 如果 ratio 不是默认值 1，则写入 weight
                            txt_file.write(f'    {member} priority {ratio}\n')
                        else:
                            txt_file.write(f'    {member}\n')
                    else:
                        # 如果没有独立配置，直接写入 member
                        txt_file.write(f'    {member}\n')

                txt_file.write('}\n\n')
            txt_file.write('\n')
            
        if rule_data:
            txt_file.write('################  rule Information:  ################\n')
            # 遍历规则并分别写入文件
            for idx, row in rule_df.iterrows():
                # 获取第一行内容作为文件名并附加 `.arl` 后缀
                rule_content = row["rule_info"].strip()
                rule_lines = rule_content.splitlines()

                if len(rule_lines) >= 2:
                    file_name = rule_lines[0].split("{")[0].strip()

                    # 内容为去掉第一行和最后一行的大括号内内容
                    content = "\n".join(rule_lines[1:-1]).strip()

                    # 格式化代码
                    formatted_content = format_irule_as_tcl(content)

                    # 在 `txt_file_attention` 文件中记录规则信息
                    txt_file.write(f'erule add {file_name}\n')
                    txt_file.write(formatted_content)
                    txt_file.write('\n.\n\n')
            txt_file.write('\n')


        if vs_data:
            txt_file.write('################  Virtual Server Information:  ################\n')
            persist_default_conf_cookie = 0
            persist_default_conf_source_addr = 0
            vs_protocol_stats_in = 0

            for idx, row in vs_df.iterrows():
                vs_protocol_stats = ""
                vs_protocol_other = 0
                vs_protocol = "tcp"
                vs_protocol_name = ""
                # 下面的代码，会判定关联了什么profile，并且根据profile进行相应的协议选择
                if "/Common/" in row["vs_profiles"]:
                    vs_profiles_match = list(re.finditer(r'/Common/+?([^\s{]+)', row["vs_profiles"]))
                    matches = [match.group(1) for match in vs_profiles_match]
                    if len(vs_profiles_match) == 1:
                        if "udp" in row["vs_protocol"]:
                            vs_protocol = "udp"
                            vs_protocol_stats = "1_udp"
                        else:
                            if "fastL4" in matches or "tcp" in matches or "mptcp-mobile-optimized" in matches:
                                vs_protocol = "tcp"
                                vs_protocol_stats = "1_tcp"
                            elif "ftp" in matches:
                                vs_protocol = "tcp"
                                vs_protocol_stats = "1_ftp"
                            else:
                                vs_protocol_other = 1
                                vs_protocol_stats = "1"
                                vs_protocol_name = matches[0]

                    elif len(vs_profiles_match) == 2 or len(vs_profiles_match) == 3 or len(vs_profiles_match) == 4:
                        if any(keyword in matches for keyword in
                               ["http", "oneconnect", "cookie"]):
                            vs_protocol = "http"
                            vs_protocol_stats = "234_http"
                            if any(keyword in matches for keyword in ["oneconnect"]):
                                vs_protocol_stats_in = "oneconnect"
                        elif "ftp" in matches:
                            vs_protocol = "ftp"
                            vs_protocol_stats = "234_ftp"
                        else:
                            vs_protocol_other = 1
                            vs_protocol_stats = "234"
                    else:
                        vs_protocol_other = 1
                        vs_protocol_stats = "5+"

                if "/Common/" in row["vs_persist"]:
                    vs_persist_match = list(re.finditer(r'/Common/+?([^\s{]+)', row["vs_persist"]))
                    matches = [match.group(1) for match in vs_persist_match]
                    if "cookie" in matches:
                        vs_protocol = "http"
                        vs_protocol_other = 0

                if row["vs_ip_forward"] != "ip-forward":
                    txt_file.write(f'slb virtual-address {row["vs_ip_add"]}_va {row["vs_ip_add"]}\n')
                    txt_file.write('{\n')
                    if vs_protocol:
                        txt_file.write(f'    port {row["vs_ip_port"]} {vs_protocol}\n')

                    if vs_protocol_other:
                        txt_file.write(f'    #profile关联了: {" ".join(matches)}\n')
                    txt_file.write('    {\n')
                    txt_file.write(f'        name {row["vs_name"]}\n')

                    if "vs_pool_name" in row and row["vs_pool_name"]:
                        txt_file.write(f'        pool {row["vs_pool_name"]}\n')

                    if vs_protocol_stats == "1_tcp":
                        txt_file.write(f'        profile tcp tcp\n')
                    elif vs_protocol_stats == "1_udp":
                        txt_file.write(f'        profile udp udp\n')
                    elif vs_protocol_stats == "1_ftp":
                        txt_file.write(f'        profile ftp ftp\n')
                    elif vs_protocol_stats == "234_http":
                        txt_file.write(f'        profile tcp-agent ks_tcp\n')
                    elif vs_protocol_stats == "234_ftp":
                        txt_file.write(f'        profile ftp ftp\n')
                    elif vs_protocol_stats == "1":
                        txt_file.write(f'        profile tcp {vs_protocol_name}\n')
                    else:
                        txt_file.write(f'        profile tcp tcp\n')

                    # 下面几行代码，是翻译F5关联了默认的会话保持配置，但只考虑了默认的cookie和源地址；如果有其他的默认会话保持，需要改写代码。
                    if "/Common/cookie {" in row["vs_persist"]:
                        persist_default_conf_cookie = 1
                        txt_file.write(f'        profile persist cookie cookie\n')
                    elif "/Common/source_addr {" in row["vs_persist"]:
                        persist_default_conf_source_addr = 1
                        txt_file.write(f'        profile persist source-ip source_addr_180s\n')
                    elif "/Common/" in row["vs_persist"]:
                        # 使用正则表达式匹配vs_persist中的名称
                        vs_persist_name_match = re.search(r'/Common/+([^\s{]+)', row["vs_persist"])
                        if vs_persist_name_match:
                            vs_persist_name = vs_persist_name_match.group(1).strip()
                            # 在persistence_data中查找匹配的名称并提取persistence_protocol
                            if vs_persist_name in persistence_data['persistence_name']:
                                index = persistence_data['persistence_name'].index(vs_persist_name)
                                vs_persist_protocol = persistence_data['persistence_protocol'][index]
                                # 将信息写入文本文件
                                if vs_persist_protocol == "source-addr":
                                    txt_file.write(f'        profile persist source-ip {vs_persist_name}\n')
                                elif vs_persist_protocol == "cookie":
                                    txt_file.write(f'        profile persist cookie {vs_persist_name}\n')
                                elif vs_persist_protocol == "dest-addr":
                                    txt_file.write(f'        profile persist dest-ip {vs_persist_name}\n')

                                else:
                                    txt_file.write(
                                        f'#        profile persist {vs_persist_protocol} {vs_persist_name}\n')

                    # 下面代码，是翻译F5的automap和SNAT的代码
                    if "disabled" in row["vs_disabled"]:
                        txt_file.write(f'        disable\n')

                    # 下面代码，是翻译F5的automap和SNAT的代码
                    if "type automap" in row["vs_source_translation"]:
                        txt_file.write(f'        source-nat interface\n')
                    elif "pool /Common/" in row["vs_source_translation"]:
                        snatpool_name_match = re.search(r'pool /Common/+([^\s{]+)', row["vs_source_translation"])
                        snatpool_name = snatpool_name_match.group(1).strip()
                        txt_file.write(f'        source-nat pool {snatpool_name}\n')

                    if (vs_protocol_stats_in == "oneconnect") and ("pool /Common/" in row["vs_source_translation"]):
                        txt_file.write(f'        profile connection-multiplex oneconnect\n')

                    txt_file.write('        path-persist\n')
                    txt_file.write('        immediate-action-on-service-down reset\n')

                    # rule配置
                    if "/Common/" in row["vs_rule"]:
                        vs_rule_match = re.search(r'/Common/+?([^\s{]+)', row["vs_rule"])
                        vs_rule = vs_rule_match.group(1).strip()
                        txt_file.write(f'        erule {vs_rule}\n')

                    # connection_limit配置
                    if row["vs_connection_limit"] != '':
                        limit = row["vs_connection_limit"].strip()
                        txt_file.write(f'        connection-limit {limit} do-not-log\n')

                    txt_file.write('   }\n')
                    txt_file.write('}\n\n')
            txt_file.write('\n')

            # 判断vs是否关联了默认的profile
            if persist_default_conf_cookie:
                txt_file.write('################  Persistence_default_cookie Information:  ################\n')
                txt_file.write('slb profile persist cookie cookie\n')
                txt_file.write('\n\n')
            elif persist_default_conf_source_addr:
                txt_file.write('################  Persistence_default_source-ip Information:  ################\n')
                txt_file.write('slb profile persist source-ip source_addr_180s\n')
                txt_file.write('   timeout 3\n')
                txt_file.write('\n\n')

            if vs_protocol_stats_in == "oneconnect":
                txt_file.write('################  profile_default_oneconnect Information:  ################\n')
                txt_file.write('slb profile connection-multiplex oneconnect\n')
                txt_file.write('\n\n')

        if route_data:
            txt_file.write('################  route_data Information:  ################\n')
            if route_data['route_name']:
                txt_file.write(f'static-route service\n')
                txt_file.write('{\n')

            # 遍历 DataFrame 的每一行
            for _, row in route_df.iterrows():
                network = row["route_network"]
                is_default = network in ('default', 'default-inet6')

                # 判断协议类型（IPv4/IPv6）
                if network == 'default':
                    route_type = 'ipv4'
                    resolved_network = '0.0.0.0/0'
                elif network == 'default-inet6':
                    route_type = 'ipv6'
                    resolved_network = '::/0'
                else:
                    route_type = 'ipv6' if ':' in network else 'ipv4'
                    resolved_network = network  # 非默认路由，保持原样

                # 注释前缀（如果是默认路由则注释掉）
                prefix = "#    " if is_default else "    "

                # 生成 gateway 路由命令
                if row["route_gateway"]:
                    if route_type == 'ipv4':
                        cmd = f'ip route {resolved_network} {row["route_gateway"]} description {row["route_name"]}'
                    else:  # IPv6
                        # cmd = f'ipv6 route {resolved_network} {row["route_gateway"]} description {row["route_name"]}'
                        cmd = f'ipv6 route {resolved_network} {row["route_gateway"]}'
                    txt_file.write(f"{prefix}{cmd}\n")

                # 生成 gateway_pool 路由命令
                if row["route_gateway_pool"]:
                    if route_type == 'ipv4':
                        cmd = f'ip route {resolved_network} pool {row["route_gateway_pool"]} description {row["route_name"]}'
                    else:  # IPv6
                        # cmd = f'ipv6 route {resolved_network} pool {row["route_gateway_pool"]} description {row["route_name"]}'
                        cmd = f'ipv6 route {resolved_network} pool {row["route_gateway_pool"]}'
                    txt_file.write(f"{prefix}{cmd}\n")

            if route_data['route_name']:
                txt_file.write('}\n\n')
