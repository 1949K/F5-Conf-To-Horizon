import pandas as pd


def write_to_txt_attention(txt_file_attention_path, vs_data, pool_data, pool_member_data, node_data, monitor_data,
                           persistence_data, profile_data, snatpool_data, route_data, rule_data, auth_date):
    """
    将数据写入文本
    """
    if pool_data:
        pool_df = pd.DataFrame(pool_data)
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

    with open(txt_file_attention_path, 'w') as txt_file_attention:
        if node_data:
            txt_file_attention.write('################  Node Information:  ################\n')
            for idx, row in node_df.iterrows():
                txt_file_attention.write(f'slb node {row["node_ip"]} {row["node_ip"]}\n')
            txt_file_attention.write('\n\n')

        if rule_data:
            txt_file_attention.write('################  rule Information:  ################\n')
            for idx, row in rule_df.iterrows():
                txt_file_attention.write('#####################################################\n')
                txt_file_attention.write(f'{row["rule_info"]}\n')
            txt_file_attention.write('\n\n')
