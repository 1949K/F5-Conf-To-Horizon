import os
import re
import pandas as pd


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


def write_to_txt_attention(txt_file_attention_path, vs_data, pool_data, pool_member_data, node_data, monitor_data,
                           persistence_data, profile_data, snatpool_data, route_data, rule_data, auth_date):
    # """
    # 将数据写入文本
    # """

    base_name = os.path.splitext(os.path.basename(txt_file_attention_path))[0].replace("_attention", "")

    # 如果需要保留 txt_file_attention 逻辑，写入同一个文件
    with open(txt_file_attention_path, 'w') as txt_file_attention:
        # 处理提示信息
        txt_file_attention.write('################  提示信息:  ################\n\n')
        txt_file_attention.write('## 1、需要手动更改 udp/dns 的 pool 的类型为udp##\n\n\n\n\n')

        if monitor_data:
            monitor_df = pd.DataFrame(monitor_data)

            # 记录已经处理过的IP地址
            processed_ips = set()

            found_conflict = False  # 标记是否找到冲突

            for idx, row in monitor_df.iterrows():
                # 提取 别名端口和别名地址
                monitor_name = row["monitor_name"]
                alias = row["monitor_destination"]
                # Improved regex to handle all cases
                alias_match = re.search(
                    r'^'
                    r'('
                    r'(\*)|'  # Wildcard *
                    r'(\d{1,3}\.){3}\d{1,3}|'  # IPv4
                    r'([0-9a-fA-F:]+)'  # IPv6 without brackets
                    r')'
                    r'[:.]'  # Separator : or .
                    r'(\*|\d+)$',  # Port (* or number)
                    alias.strip()
                )
                if alias_match:
                    # Determine IP and port
                    alias_ip = alias_match.group(1)
                    alias_port = alias_match.group(5)

                    # # http 和 tcp 的别名端口和别名地址 限定：类型为http和tcp类型，且不为"*:*"才进行处理
                    # if  row["monitor_destination"] != "*:*":
                    #     if alias_ip != "*" :
                    #         if vs_data:
                    #             vs_df = pd.DataFrame(vs_data)
                    #             for idx_vs, row_vs in vs_df.iterrows():
                    #                 if row_vs["vs_ip_add"] == alias_ip:
                    #                     txt_file_attention.write(f"健康检查{row['monitor_name']}配置别名{row['monitor_destination']}，与VS IP地址: {row_vs['vs_ip_add']}可能冲突（在120版本中，对自身设备的vs地址进行健康检查可能与预期不符）\n")


                    if row["monitor_destination"] != "*:*" and alias_ip != "*":
                        if vs_data and monitor_name not in processed_ips:  # 检查是否已处理过
                            vs_df = pd.DataFrame(vs_data)
                            for idx_vs, row_vs in vs_df.iterrows():
                                if row_vs["vs_ip_add"] == alias_ip:
                                    if not found_conflict:  # 如果是第一次找到冲突
                                        txt_file_attention.write('################  健康检查信息:  ################\n\n')
                                        found_conflict = True
                                    txt_file_attention.write(
                                        f"健康检查{row['monitor_name']}配置别名{row['monitor_destination']}，"
                                        f"与VS IP地址: {row_vs['vs_ip_add']}可能冲突"
                                        f"（在120版本中，对自身设备的vs地址进行健康检查可能与预期不符）\n"
                                    )
                                    processed_ips.add(alias_ip)  # 记录已处理的IP
                                    break  # 找到一个匹配后就可以跳出循环

        # 处理iRule规则,创建irule文件夹，以txt文件方式，写入文件夹
        if rule_data:
            rule_df = pd.DataFrame(rule_data)

            # 准备irule文件夹路径（只在有rule_data时才创建）
            irule_folder = os.path.join(os.path.dirname(txt_file_attention_path), f"{base_name}_irule")

            # 标记是否需要创建文件夹
            need_create_folder = False

            # 第一次遍历检查是否有有效内容
            for idx, row in rule_df.iterrows():
                rule_content = row["rule_info"].strip()
                rule_lines = rule_content.splitlines()

                if len(rule_lines) >= 2:
                    content = "\n".join(rule_lines[1:-1]).strip()
                    if content:
                        need_create_folder = True
                        break

            # 只有确实有内容需要写入时才创建文件夹
            if need_create_folder:
                os.makedirs(irule_folder, exist_ok=True)

                # 第二次遍历实际写入文件
                for idx, row in rule_df.iterrows():
                    rule_content = row["rule_info"].strip()
                    rule_lines = rule_content.splitlines()

                    if len(rule_lines) >= 2:
                        # 获取文件名并做基本清理
                        file_name = rule_lines[0].split("{")[0].strip()
                        file_name = "".join(c for c in file_name if c.isalnum() or c in ('_', '-', '.'))

                        # 获取内容
                        content = "\n".join(rule_lines[1:-1]).strip()

                        if content:  # 再次检查内容是否为空
                            # 构建安全文件路径
                            try:
                                rule_file_path = os.path.join(irule_folder, file_name)

                                # 格式化代码
                                formatted_content = format_irule_as_tcl(content)

                                # 写入文件
                                with open(rule_file_path, 'w') as rule_file:
                                    rule_file.write(formatted_content)
                            except (OSError, IOError) as e:
                                print(f"无法写入rule文件 {file_name}: {str(e)}")
                                continue


