'''
Conf_Split.py
'''

import re


def split_blocks(content):
    """
    将输入的配置文件内容分割成块，并保留原始缩进。
    :param content: 配置文件内容
    :return: 块列表
    """
    blocks = []
    current_block = []

    for line in content.split('\n'):
        if re.match(r'^(auth|cm|cli|apm|ltm|net|sys|wom)', line) or line.startswith("#"):
            if current_block:
                blocks.append('\n'.join(current_block))
            current_block = [line]
        elif line:
            current_block.append(line)

    if current_block:
        blocks.append('\n'.join(current_block))

    return blocks
