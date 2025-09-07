import pandas as pd


def write_to_excel(excel_file_path, vs_data, pool_data, pool_member_data, node_data, monitor_data, persistence_data,
                   profile_data, snatpool_data, route_data, rule_data, auth_date):
    """
    将数据写入 Excel 文件
    """
    # 创建数据框并将数据存储到Excel文件中
    with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
        if pool_data:
            pool_df = pd.DataFrame(pool_data)
            pool_df.to_excel(writer, sheet_name='Pools', index=False)
        if pool_member_data:
            pool_member_df = pd.DataFrame(pool_member_data)
            pool_member_df.to_excel(writer, sheet_name='Pool_members', index=False)
        if vs_data:
            vs_df = pd.DataFrame(vs_data)
            vs_df.to_excel(writer, sheet_name='VirtualServers', index=False)
        if node_data:
            node_df = pd.DataFrame(node_data)
            node_df.to_excel(writer, sheet_name='Nodes', index=False)
        if monitor_data:
            monitor_df = pd.DataFrame(monitor_data)
            monitor_df.to_excel(writer, sheet_name='Monitor', index=False)
        if persistence_data:
            persistence_df = pd.DataFrame(persistence_data)
            persistence_df.to_excel(writer, sheet_name='Persistence', index=False)
        if profile_data:
            profile_df = pd.DataFrame(profile_data)
            profile_df.to_excel(writer, sheet_name='Profile', index=False)
        if snatpool_data:
            snatpool_df = pd.DataFrame(snatpool_data)
            snatpool_df.to_excel(writer, sheet_name='SNATPool', index=False)
        if route_data:
            route_df = pd.DataFrame(route_data)
            route_df.to_excel(writer, sheet_name='Route', index=False)
        if rule_data:
            rule_df = pd.DataFrame(rule_data)
            rule_df.to_excel(writer, sheet_name='Rule', index=False)
        if auth_date:
            auth_df = pd.DataFrame(auth_date)
            auth_df.to_excel(writer, sheet_name='Auth', index=False)
