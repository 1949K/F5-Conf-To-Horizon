import re

import pandas as pd


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
    if rule_data:
        auth_df = pd.DataFrame(auth_date)

    with open(txt_file_path, 'w') as txt_file:
        if rule_data:
            txt_file.write('################  Auth Information:  ################\n')
            for idx, row in auth_df.iterrows():
                if "radius" in row["tacacs_source_type"]:
                    txt_file.write('radius-server read-write\n')
                    txt_file.write(f'# 注意：更改 secret XXXXXXXX\n')
                    txt_file.write(f'radius-server host {row["radius_servers"]} secret XXXXXXXX\n')
                    txt_file.write('authentication type radius buffer-local\n')
                    txt_file.write('authentication console type radius buffer-local\n')
                # elif "tacacs" in row["tacacs_source_type"]:
                #     if " " in row["tacacs_servers"]:
                #         tacacs_match = re.search(r'([\d.]+) ([\d.]+)', row["tacacs_servers"])
                #         tacacs_1 = tacacs_match.group(1) if tacacs_match else ''
                #         tacacs_2 = tacacs_match.group(2) if tacacs_match else ''
                #         txt_file.write(f'# 注意：更改 secret XXXXXXXX\n')
                #         txt_file.write(f'tacacs-server host {tacacs_1} secret XXXXXXXX port 49 timeout 12\n')
                #         txt_file.write(f'tacacs-server host {tacacs_2} secret XXXXXXXX port 49 timeout 12\n')
                #         txt_file.write('authentication type tacacsplus buffer-local\n')
                #         txt_file.write('authentication console type tacacsplus buffer-local\n')
                #     elif row["tacacs_servers"]:
                #         tacacs_match = re.search(r'([\d.]+)', row["tacacs_servers"])
                #         tacacs_1 = tacacs_match.group(1) if tacacs_match else ''
                #         txt_file.write(f'# 注意：更改 secret XXXXXXXX\n')
                #         txt_file.write(f'tacacs-server host {tacacs_1} secret XXXXXXXX port 49 timeout 12\n')
                #         txt_file.write('authentication type tacacsplus buffer-local\n')
                #         txt_file.write('authentication console type tacacsplus buffer-local\n')
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

        if snatpool_data:
            txt_file.write('################  SNAT_Pool Information:  ################\n')
            for idx, row in snatpool_df.iterrows():
                txt_file.write(f'ip nat pool {row["snatpool_name"]}\n')
                txt_file.write('{\n')
                for member in row["snatpool_member"]:
                    txt_file.write(f'   member {member} {member} netmask /24\n')
                txt_file.write('}\n\n')
            txt_file.write('\n')
        if monitor_data:
            txt_file.write('################  Monitor Information:  ################\n')
            for idx, row in monitor_df.iterrows():

                # 提取间隔和超时时间
                monitor_interval = int(row["monitor_interval"])
                monitor_timeout = int(row["monitor_timeout"])
                # 取整数
                monitor_timeout_ok = int((monitor_timeout / monitor_interval) - 1)
                txt_file.write(
                    f'health check {row["monitor_name"]} interval {monitor_interval} retry {monitor_timeout_ok} timeout {monitor_interval} up-check-cnt 1\n')

                txt_file.write('{\n')
                txt_file.write('    wait-all-retry\n')

                # 提取 别名端口和别名地址
                alias = row["monitor_destination"]
                alias_match = re.search(r'([\d*.]+):([\d*]+)', alias)
                alias_ip = alias_match.group(1) if alias_match else ''
                alias_port = alias_match.group(2) if alias_match else ''

                # http 和 tcp 的别名端口和别名地址 限定：类型为http和tcp类型，且不为"*:*"才进行处理
                if row["monitor_defaults-from"] in ["http", "tcp"] and row["monitor_destination"] != "*:*":
                    if alias_ip == "*" and alias_port != "*":
                        txt_file.write(f'    alias-port {alias_port}\n')
                    elif alias_ip != "*" and alias_port == "*":
                        txt_file.write(f'    alias-address {alias_ip}\n')
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
                if row["monitor_protocol"] == "http" or row["monitor_protocol"] == "https":
                    monitor_http_send_match = re.search(r'GET ([\w?/.=_-]+) ', monitor_send)
                    monitor_http_send = monitor_http_send_match.group(1) if monitor_http_send_match else ''
                elif row["monitor_protocol"] == "tcp":
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
                if row["monitor_protocol"] == "http":
                    if monitor_recv == '"200 OK"' and monitor_http_send == "/":
                        txt_file.write(f'    method http response response-code 200\n')
                    elif monitor_recv == '"200 OK"' and monitor_http_send and monitor_http_send != "/":
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

                elif row["monitor_protocol"] == "https":
                    if monitor_recv == '"200 OK"' and monitor_http_send == "/":
                        txt_file.write(f'    method https response response-code 200\n')
                    elif monitor_recv == '"200 OK"' and monitor_http_send and monitor_http_send != "/":
                        txt_file.write(f'    method https url GET {monitor_http_send} response response-code 200\n')
                    elif monitor_recv and monitor_recv_disable and monitor_recv != "none" and monitor_recv_disable != "none":
                        txt_file.write(
                            f'    method https url GET {monitor_http_send} response {monitor_recv} recv-disable {monitor_recv_disable}\n')
                    elif monitor_recv and monitor_recv != "none" and monitor_recv_disable == "none":
                        txt_file.write(f'    method https url GET {monitor_http_send} response {monitor_recv}\n')
                    elif monitor_http_send and monitor_http_send != "none":
                        txt_file.write(f'    method https url GET {monitor_http_send}\n')
                    else:
                        txt_file.write('    method https\n')

                # elif row["monitor_protocol"] == "dns":
                #     if monitor_recv == '"200 OK"' and monitor_http_send == "/":
                #         txt_file.write(f'    method dns response response-code 200\n')
                #     elif monitor_recv == '"200 OK"' and monitor_http_send and monitor_http_send != "/":
                #         txt_file.write(f'    method dns url GET {monitor_http_send} response response-code 200\n')
                #     elif monitor_recv and monitor_recv_disable and monitor_recv != "none" and monitor_recv_disable != "none":
                #         txt_file.write(
                #             f'    method dns url GET {monitor_http_send} response {monitor_recv} recv-disable {monitor_recv_disable}\n')
                #     elif monitor_recv and monitor_recv != "none" and monitor_recv_disable == "none":
                #         txt_file.write(f'    method dns url GET {monitor_http_send} response {monitor_recv}\n')
                #     elif monitor_http_send and monitor_http_send != "none":
                #         txt_file.write(f'    method dns url GET {monitor_http_send}\n')
                #     else:
                #         txt_file.write('    method dns\n')

                elif row["monitor_protocol"] == "tcp-half-open":
                    txt_file.write('    method tcp port 80 send-rst\n')

                elif row["monitor_protocol"] == "tcp":
                    if monitor_recv and monitor_recv_disable and monitor_recv != "none" and monitor_recv != "none":
                        txt_file.write(
                            f'    method tcp port 80 send {monitor_tcp_send} recv {monitor_recv} recv-disable {monitor_recv}\n')
                    elif monitor_recv and monitor_recv != "none" and monitor_recv != "none":
                        txt_file.write(f'    method tcp port 80 send {monitor_tcp_send} recv {monitor_recv}\n')
                    else:
                        txt_file.write('    method tcp port 80\n')

                else:
                    txt_file.write('    method tcp port 80\n')
                    txt_file.write(f'#    注意：F5配置中的健康检查类型为“{row["monitor_protocol"]}”，这里改为tcp\n')

                txt_file.write('}\n\n')

            txt_file.write('\n')

        if pool_member_data:
            txt_file.write('################  Pool_Member_Ratio Information:  ################\n')
            for idx, row in pool_member_df.iterrows():
                pool_name = row['pool_name']
                pool_monitor = row['pool_monitor']

                pool_member_ip = row['pool_member_ip']
                pool_member_port = row['pool_member_port']
                pool_member_monitor = row['pool_member_monitor']
                pool_member_ratio = row['pool_member_ratio']

                if pool_member_ratio:
                    txt_file.write(f'slb pool {pool_name} tcp\n')
                    txt_file.write(f'    member {pool_member_ip}:{pool_member_port} priority {pool_member_ratio}\n')
                    txt_file.write('\n\n')

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
                else:
                    txt_file.write(f'#slb profile persist {protocol} {name}\n')
                txt_file.write('{\n')
                if timeout:
                    timeout_s = int(timeout)
                    timeout_m = int(timeout_s / 60)
                    if protocol in ["source-addr", "cookie"]:
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
                        txt_file.write('}\n')
                        txt_file.write(f'slb profile tcp-agent ks_tcp\n')
                        txt_file.write('{\n')
                        txt_file.write(f'    idle-timeout 300\n')
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
                if row["profile_protocol"] == "http":
                    txt_file.write(f'slb profile http {row["profile_name"]}\n')
                    txt_file.write('{\n')
                    if row["profile_xff"]:
                        txt_file.write(f'    client-ip-insert X-Forwarded-For\n')
                    txt_file.write('}\n\n')
                elif row["profile_protocol"] == "one-connect":
                    txt_file.write(f'slb profile connection-multiplex {row["profile_name"]}\n\n')
                elif row["profile_protocol"] == "fastl4":
                    txt_file.write(f'slb profile tcp {row["profile_name"]}\n')
                    txt_file.write('{\n')
                    txt_file.write(f'    idle-timeout {row["profile_idle_timeout"]}\n')
                    txt_file.write('}\n\n')
                elif row["profile_protocol"] == "tcp":
                    txt_file.write(f'slb profile tcp {row["profile_name"]}\n')
                    txt_file.write('{\n')
                    txt_file.write(f'    idle-timeout {row["profile_idle_timeout"]}\n')
                    txt_file.write('}\n')
                    txt_file.write(f'slb profile tcp-agent ks_{row["profile_name"]}\n')
                    txt_file.write('{\n')
                    txt_file.write(f'    idle-timeout {row["profile_idle_timeout"]}\n')
                    txt_file.write('}\n\n')
                else:
                    txt_file.write(f'slb profile tcp {row["profile_name"]}\n')
                    txt_file.write('{\n')
                    txt_file.write('}\n')

            txt_file.write('\n')

        if pool_data:
            txt_file.write('################  Pool Information:  ################\n')
            for idx, row in pool_df.iterrows():
                txt_file.write(f'slb pool {row["pool_name"]} tcp\n')
                txt_file.write('{\n')
                if row["pool_monitor"] == "gateway_icmp":
                    txt_file.write(f'    health-check ping\n')
                elif row["pool_monitor"]:
                    txt_file.write(f'    health-check {row["pool_monitor"]}\n')
                if row["pool_lbm"] == "least-connections-member":
                    txt_file.write(f'    method service-least-connection\n')
                for member in row["pool_members"]:
                    txt_file.write(f'    {member}\n')
                txt_file.write('}\n\n')
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
                # 下面的代码，会判定关联了什么profile，并且根据profile进行相应的协议选择
                if "/Common/" in row["vs_profiles"]:
                    vs_profiles_match = list(re.finditer(r'/Common/+?([^\s{]+)', row["vs_profiles"]))
                    matches = [match.group(1) for match in vs_profiles_match]
                    if len(vs_profiles_match) == 1:
                        if "fastL4" in matches or "tcp" in matches or "mptcp-mobile-optimized" in matches:
                            vs_protocol = "tcp"
                            vs_protocol_stats = "1_tcp"
                        elif "ftp" in matches:
                            vs_protocol = "tcp"
                            vs_protocol_stats = "1_ftp"
                        else:
                            vs_protocol_other = 1
                            vs_protocol_stats = "1"
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
                    txt_file.write(f'        pool {row["vs_pool_name"]}\n')
                    if vs_protocol_stats == "1_tcp":
                        txt_file.write(f'        profile tcp tcp\n')
                    elif vs_protocol_stats == "1_ftp":
                        txt_file.write(f'        profile ftp ftp\n')
                    elif vs_protocol_stats == "234_http":
                        txt_file.write(f'        profile tcp-agent ks_tcp\n')
                    elif vs_protocol_stats == "234_ftp":
                        txt_file.write(f'        profile ftp ftp\n')
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
                                else:
                                    txt_file.write(
                                        f'#        profile persist {vs_persist_protocol} {vs_persist_name}\n')

                    # 下面代码，是翻译F5的automap和SNAT的代码
                    if "type automap" in row["vs_source_translation"]:
                        txt_file.write(f'        source-nat interface\n')
                    elif "pool /Common/" in row["vs_source_translation"]:
                        snatpool_name_match = re.search(r'pool /Common/+([^\s{]+)', row["vs_source_translation"])
                        snatpool_name = snatpool_name_match.group(1).strip()
                        txt_file.write(f'        source-nat pool {snatpool_name}\n')

                    if vs_protocol_stats_in == "oneconnect" and "pool /Common/" in row["vs_source_translation"]:
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
            for idx, row in route_df.iterrows():
                if '/' in row["route_name"]:
                    txt_file.write(f'    ip route {row["route_network"]} {row["route_gateway"]}\n')
                elif row["route_network"] == 'default':
                    txt_file.write(f'#    ip route 0.0.0.0 {row["route_gateway"]} description {row["route_name"]}\n')
                else:
                    txt_file.write(
                        f'    ip route {row["route_network"]} {row["route_gateway"]} description {row["route_name"]}\n')
            if route_data['route_name']:
                txt_file.write('}\n\n')
