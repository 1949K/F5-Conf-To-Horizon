import os

from .Conf_Extract import extract_pools_vs_nodes
from .Conf_Split import split_blocks
from .Conf_WriteToExcel import write_to_excel
from .Conf_WriteToTxt import write_to_txt
from .Conf_WriteToTxt_attention import write_to_txt_attention


def process_folder(folder_path):
    """
    遍历文件夹中的所有文件并调用write_to_txt来处理它们。
    :param folder_path: 文件夹路径
    """
    if folder_path:  # 用户取消选择时返回空字符串，需要检查是否为空
        # 遍历文件夹下的所有文件并处理它们
        for root_dir, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.conf'):
                    file_path = os.path.join(root_dir, file)
                    process_file(file_path)


def process_file(file_path):
    """
    处理单个文件，提取信息并输出到Excel和文本文件。
    :param file_path: 文件路径
    """
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
    (vs_data, pool_data, pool_member_data, node_data, monitor_data, persistence_data, profile_data, snatpool_data,
     route_data,
     rule_data, auth_date) = extract_pools_vs_nodes(blocks)

    # 生成文件名等
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    excel_file_name = f"{base_name}.xlsx"
    txt_file_name = f"{base_name}.txt"
    txt_file_attention_name = f"{base_name}_attention.txt"

    # 获取源文件的目录
    source_directory = os.path.dirname(file_path)
    
    # 创建output目录
    output_dir = os.path.join(source_directory, 'output')
    os.makedirs(output_dir, exist_ok=True)

    # 构建完整的文件路径
    excel_file_path = os.path.join(output_dir, excel_file_name)
    txt_file_path = os.path.join(output_dir, txt_file_name)
    txt_file_attention_path = os.path.join(output_dir, txt_file_attention_name)

    # 调用输出到 Excel 和文本文件的函数
    write_to_excel(excel_file_path, vs_data, pool_data, pool_member_data, node_data, monitor_data, persistence_data,
                   profile_data, snatpool_data, route_data, rule_data, auth_date)
    write_to_txt(txt_file_path, vs_data, pool_data, pool_member_data, node_data, monitor_data, persistence_data,
                 profile_data, snatpool_data, route_data, rule_data, auth_date)
    write_to_txt_attention(txt_file_attention_path, vs_data, pool_data, pool_member_data, node_data, monitor_data,
                           persistence_data, profile_data, snatpool_data, route_data, rule_data, auth_date)
