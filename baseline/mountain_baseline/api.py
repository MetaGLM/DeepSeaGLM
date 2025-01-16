import pandas as pd

def calculate_uptime(start_time, end_time, shebeiname="折臂吊车"):
    """
    计算指定时间段内的开机时长，并返回三种格式的开机时长
    :param start_time: 查询的开始时间（字符串或 datetime 类型）
    :param end_time: 查询的结束时间（字符串或 datetime 类型）
    :param shebeiname: 设备名称，默认为 '折臂吊车'
    :return: 包含三种格式开机时长的字符串
    """
    print("-------calculate_uptime执行***计算开机时间-------")
    # 设备配置映射：设备名称 -> (文件路径, 开机状态, 关机状态)
    device_config = {
        "折臂吊车": (
            "database_in_use/device_13_11_meter_1311.csv",
            "折臂吊车开机",
            "折臂吊车关机",
        ),
        "A架": ("database_in_use/Ajia_plc_1.csv", "开机", "关机"),
        "DP": ("database_in_use/Port3_ksbg_9.csv", "ON_DP", "OFF_DP"),
    }

    # 检查设备名称是否有效
    if shebeiname not in device_config:
        raise ValueError(f"未知的设备名称: {shebeiname}")

    # 获取设备配置
    file_path, start_status, end_status = device_config[shebeiname]

    # 读取 CSV 文件
    df = pd.read_csv(file_path)

    # 将时间列转换为 datetime 类型
    df["csvTime"] = pd.to_datetime(df["csvTime"])

    # 将传入的开始时间和结束时间转换为 datetime 类型
    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)

    # 筛选出指定时间段内的数据
    df_filtered = df[(df["csvTime"] >= start_time) & (df["csvTime"] <= end_time)]

    # 初始化变量
    total_duration = pd.Timedelta(0)
    start_uptime = None

    # 遍历筛选后的数据
    for index, row in df_filtered.iterrows():
        if row["status"] == start_status:
            start_uptime = row["csvTime"]
        elif row["status"] == end_status and start_uptime is not None:
            end_uptime = row["csvTime"]
            total_duration += end_uptime - start_uptime
            start_uptime = None

    # 计算三种格式的开机时长
    seconds = total_duration.total_seconds()
    minutes = int(seconds / 60)
    hours = int(seconds // 3600)
    remaining_minutes = int((seconds % 3600) // 60)

    # 将小时和分钟格式化为两位数
    hours_str = f"{hours:02d}"  # 使用格式化字符串确保两位数
    minutes_str = f"{remaining_minutes:02d}"  # 使用格式化字符串确保两位数

    # 返回三种格式的开机时长
    result = {
        "function": "calculate_uptime",  # 说明这个返回结果来自哪个函数
        "result": (
            # f'开机时长：{seconds}秒',
            f"开机时长：{minutes}分钟",
            # f'开机时长：{hours_str}小时{minutes_str}分钟'
        ),
    }
    return result


def compute_operational_duration(start_time, end_time, device_name="A架"):
    # 设备配置映射：设备名称 -> (文件路径, 开机状态, 关机状态)
    print("-------compute_operational_duration执行-------")
    device_config = {
        "A架": ("database_in_use/Ajia_plc_1.csv", "有电流", "无电流"),
    }
    # 检查设备名称是否有效
    if device_name not in device_config:
        raise ValueError(f"未知的设备名称: {device_name}")

    # 获取设备配置
    file_path, start_status, end_status = device_config[device_name]

    # 读取 CSV 文件
    df = pd.read_csv(file_path)

    # 将时间列转换为 datetime 类型
    df["csvTime"] = pd.to_datetime(df["csvTime"])

    # 将传入的开始时间和结束时间转换为 datetime 类型
    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)

    # 筛选出指定时间段内的数据
    df_filtered = df[(df["csvTime"] >= start_time) & (df["csvTime"] <= end_time)]

    # 初始化变量
    total_duration = pd.Timedelta(0)
    start_uptime = None
    # 遍历筛选后的数据
    for index, row in df_filtered.iterrows():
        if row["check_current_presence"] == start_status:
            start_uptime = row["csvTime"]
        elif row["check_current_presence"] == end_status and start_uptime is not None:
            end_uptime = row["csvTime"]
            total_duration += end_uptime - start_uptime
            start_uptime = None

    # 计算三种格式的开机时长
    seconds = total_duration.total_seconds()
    minutes = int(seconds / 60)
    hours = int(seconds // 3600)
    remaining_minutes = int((seconds % 3600) // 60)

    # 将小时和分钟格式化为两位数
    hours_str = f"{hours:02d}"  # 使用格式化字符串确保两位数
    minutes_str = f"{remaining_minutes:02d}"  # 使用格式化字符串确保两位数

    result = {
        "function": "calculate_uptime",  # 说明这个返回结果来自哪个函数
        "result": (
            # f'运行时长：{seconds}秒',
            f"运行时长：{minutes}分钟",
            # f'运行时长：{hours_str}小时{minutes_str}分钟'
        ),
    }
    return result


def get_table_data(table_name, start_time, end_time, columns=None, status=None):
    """
    根据数据表名、开始时间、结束时间、列名和状态获取指定时间范围内的相关数据。

    参数:
    table_name (str): 数据表名
    start_time (str): 开始时间，格式为 'YYYY-MM-DD HH:MM:SS'
    end_time (str): 结束时间，格式为 'YYYY-MM-DD HH:MM:SS'
    columns (list): 需要查询的列名列表，如果为None，则返回所有列
    status (str): 需要筛选的状态（例如 "开机"、"关机"），如果为None，则不筛选状态

    返回:
    dict: 包含指定列名和对应值的字典，或错误信息
    """
    # 创建一个字典来存储元数据
    metadata = {
        "table_name": table_name,
        "start_time": start_time,
        "end_time": end_time,
        "columns": columns,
        "status": status,
    }

    try:
        df = pd.read_csv(f"database_in_use/{table_name}.csv")
    except FileNotFoundError:
        return {"error": f"数据表 {table_name} 不存在", "metadata": metadata}

    # 将csvTime列从时间戳转换为datetime类型
    df["csvTime"] = pd.to_datetime(df["csvTime"], unit="ns")  # 假设时间戳是纳秒级别

    # 将开始时间和结束时间转换为datetime类型
    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)
    # 如果开始时间和结束时间是同一分钟
    if (
            start_time.minute == end_time.minute
            and start_time.hour == end_time.hour
            and start_time.day == end_time.day
    ):
        # 将开始时间设置为这一分钟的00秒
        start_time = start_time.replace(second=0)
        # 将结束时间设置为这一分钟的59秒
        end_time = end_time.replace(second=59)
    # 筛选指定时间范围内的数据
    filtered_data = df[(df["csvTime"] >= start_time) & (df["csvTime"] <= end_time)]

    if filtered_data.empty:
        return {
            "error": f"在数据表 {table_name} 中未找到时间范围 {start_time} 到 {end_time} 的数据",
            "metadata": metadata,
        }

    # 如果传入了 status 参数，则进一步筛选状态
    if status is not None:
        filtered_data = filtered_data[filtered_data["status"] == status]
        if filtered_data.empty:
            return {
                "error": f"在数据表 {table_name} 中未找到状态为 {status} 的数据",
                "metadata": metadata,
            }

    # 如果未指定列名，则返回所有列
    if columns is None:
        columns = filtered_data.columns.tolist()

    # 检查列名是否存在
    missing_columns = [
        column for column in columns if column not in filtered_data.columns
    ]
    if missing_columns:
        return {
            "error": f"列名 {missing_columns} 在数据表 {table_name} 中不存在",
            "metadata": metadata,
        }

    # 获取指定列名和对应的值
    result = {}
    for column in columns:
        if column == "csvTime":
            # 将时间格式化为字符串
            result[column] = (
                filtered_data[column].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
            )
        else:
            result[column] = filtered_data[column].values.tolist()

    # 返回结果和元数据
    return {"result": result, "metadata": metadata}


# 能耗计算
def load_and_filter_data(file_path, start_time, end_time, power_column):
    """
    加载 CSV 文件并筛选指定时间范围内的数据
    :param file_path: CSV 文件路径
    :param start_time: 开始时间
    :param end_time: 结束时间
    :param power_column: 功率列名
    :return: 筛选后的 DataFrame
    """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"文件 {file_path} 未找到")

    # 确保时间列是 datetime 类型
    try:
        df["csvTime"] = pd.to_datetime(df["csvTime"])
    except Exception as e:
        raise ValueError(f"时间列转换失败: {e}")

    # 筛选特定时间范围内的数据
    filtered_data = df[
        (df["csvTime"] >= start_time) & (df["csvTime"] < end_time)
        ].copy()

    if filtered_data.empty:
        return None

    # 计算时间差（秒）
    filtered_data.loc[:, "diff_seconds"] = (
        filtered_data["csvTime"].diff().dt.total_seconds().shift(-1)
    )

    # 计算每个时间间隔的能耗（kWh）
    filtered_data.loc[:, "energy_kWh"] = (
            filtered_data["diff_seconds"] * filtered_data[power_column] / 3600
    )

    return filtered_data


def calculate_total_energy(start_time, end_time, device_name="折臂吊车"):
    """
    计算指定时间段内的总能耗
    :param start_time: 查询的开始时间（字符串或 datetime 类型）
    :param end_time: 查询的结束时间（字符串或 datetime 类型）
    :param device_name: 设备名称，默认为 '折臂吊车'
    :return: 总能耗（kWh，float 类型）
    """
    # 设备配置映射：设备名称 -> (表名, 功率列名)
    device_config = {
        "折臂吊车": ("device_13_11_meter_1311", "13-11-6_v"),
        "一号门架": ("device_1_5_meter_105", "1-5-6_v"),  # 一号门架的配置
        "二号门架": ("device_13_14_meter_1314", "13-14-6_v"),  # 二号门架的配置
        "绞车": ("device_1_15_meter_115", "1-15-6_v"),  # 添加绞车的配置
    }

    # 检查设备名称是否有效
    if device_name not in device_config:
        raise ValueError(f"未知的设备名称: {device_name}")

    # 获取设备配置
    table_name, power_column = device_config[device_name]

    # 读取 CSV 文件并计算能耗
    file_path = f"database_in_use/{table_name}.csv"
    try:
        filtered_data = load_and_filter_data(
            file_path, start_time, end_time, power_column
        )
        if filtered_data is None:
            return None
        total_energy_kWh = filtered_data["energy_kWh"].sum()
        return round(total_energy_kWh, 2)
    except Exception as e:
        raise ValueError(f"计算能耗时出错: {e}")


def calculate_total_deck_machinery_energy(start_time, end_time):
    """
    计算所有设备（折臂吊车、一号门架、二号门架、绞车）在指定时间范围内的总能耗
    :param start_time: 查询的开始时间（字符串或 datetime 类型）
    :param end_time: 查询的结束时间（字符串或 datetime 类型）
    :return: 所有设备的总能耗（kWh，float 类型）
    """
    # 定义设备列表
    devices = ["折臂吊车", "一号门架", "二号门架", "绞车"]

    total_energy = 0  # 初始化总能耗

    # 遍历每个设备，计算能耗并累加
    for device in devices:
        try:
            energy = calculate_total_energy(start_time, end_time, device_name=device)
            if energy is not None:
                total_energy += energy
        except Exception as e:
            print(f"计算设备 {device} 能耗时出错: {e}")
    return round(total_energy, 2)  # 返回总能耗，保留两位小数


def calculate_energy_consumption(start_time, end_time):
    """
    计算指定时间范围内的侧推的总能耗
    :param start_time: 开始时间（字符串或 datetime 类型）
    :param end_time: 结束时间（字符串或 datetime 类型）
    :return: 总能耗（kWh，float 类型），如果数据为空则返回 None
    """
    # 文件路径和功率列名直接定义在函数内部
    file_path = "database_in_use/Port3_ksbg_9.csv"
    power_column = "P3_18"  # 使用 "艏推功率反馈,单位:kW" 列

    try:
        # 加载 CSV 文件
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"文件 {file_path} 未找到")

    # 确保时间列是 datetime 类型
    try:
        df["csvTime"] = pd.to_datetime(df["csvTime"])
    except Exception as e:
        raise ValueError(f"时间列转换失败: {e}")

    # 筛选特定时间范围内的数据
    filtered_data = df[
        (df["csvTime"] >= start_time) & (df["csvTime"] < end_time)
        ].copy()

    if filtered_data.empty:
        return None

    # 计算时间差（秒）
    filtered_data.loc[:, "diff_seconds"] = (
        filtered_data["csvTime"].diff().dt.total_seconds().shift(-1)
    )

    # 计算每个时间间隔的能耗（kWh）
    filtered_data.loc[:, "energy_kWh"] = (
            filtered_data["diff_seconds"] * filtered_data[power_column] / 3600
    )

    # 计算总能耗
    total_energy_kWh = filtered_data["energy_kWh"].sum()

    return round(total_energy_kWh, 2)


def query_device_parameter(parameter_name_cn):
    """
    通过参数中文名查询设备参数信息
    :param parameter_name_cn: 参数中文名
    :param device_parameter_file: 设备参数详情表的文件路径，默认为'设备参数详情表.csv'
    :return: 返回包含参数信息的字典
    """
    print("-------query_device_parameter执行-------")
    # 读取设备参数详情表
    df = pd.read_csv("database_in_use/设备参数详情表.csv")

    # 检查参数中文名是否包含在 Channel_Text_CN 列中
    if not df["Channel_Text_CN"].str.contains(parameter_name_cn).any():
        raise ValueError(f"未找到包含 '{parameter_name_cn}' 的参数中文名")

    # 获取包含参数中文名的所有行
    parameter_info = df[df["Channel_Text_CN"].str.contains(parameter_name_cn)].iloc[0]

    # 将参数信息转换为字典
    parameter_dict = {
        "参数名": parameter_info["Channel_Text"],
        "参数中文名": parameter_info["Channel_Text_CN"],
        "参数下限": parameter_info["Alarm_Information_Range_Low"],
        "参数上限": parameter_info["Alarm_Information_Range_High"],
        "报警值的单位": parameter_info["Alarm_Information_Unit"],
        "报警值": parameter_info["Parameter_Information_Alarm"],
        "屏蔽值": parameter_info["Parameter_Information_Inhibit"],
        "延迟值": parameter_info["Parameter_Information_Delayed"],
        "安全保护设定值": parameter_info["Safety_Protection_Set_Value"],
        "附注": parameter_info["Remarks"],
    }
    return parameter_dict


def calculate_total_energy_consumption(start_time, end_time, query_type="all"):
    """
    计算指定时间范围内两个推进变频器或推进系统的总能耗
    :param start_time: 开始时间（字符串或 datetime 类型）
    :param end_time: 结束时间（字符串或 datetime 类型）
    :param query_type: 查询类型，可选值为 '1'（一号推进）、'2'（二号推进）、'all'（整个推进系统）
    :return: 总能耗（kWh，float 类型），如果数据为空则返回 None
    """
    # 文件路径和功率列名
    file_path_1 = "database_in_use/Port3_ksbg_8.csv"
    power_column_1 = "P3_15"  # 一号推进变频器功率反馈,单位:kW

    file_path_2 = "database_in_use/Port4_ksbg_7.csv"
    power_column_2 = "P4_15"  # 二号推进变频器功率反馈,单位:kW
    try:
        # 加载 CSV 文件
        df1 = pd.read_csv(file_path_1)
        df2 = pd.read_csv(file_path_2)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"文件未找到: {e}")

    # 确保时间列是 datetime 类型
    try:
        df1["csvTime"] = pd.to_datetime(df1["csvTime"])
        df2["csvTime"] = pd.to_datetime(df2["csvTime"])
    except Exception as e:
        raise ValueError(f"时间列转换失败: {e}")

    # 筛选特定时间范围内的数据
    filtered_data_1 = df1[
        (df1["csvTime"] >= start_time) & (df1["csvTime"] < end_time)
        ].copy()
    filtered_data_2 = df2[
        (df2["csvTime"] >= start_time) & (df2["csvTime"] < end_time)
        ].copy()

    if filtered_data_1.empty or filtered_data_2.empty:
        return None

    # 计算时间差（秒）
    filtered_data_1.loc[:, "diff_seconds"] = (
        filtered_data_1["csvTime"].diff().dt.total_seconds().shift(-1)
    )
    filtered_data_2.loc[:, "diff_seconds"] = (
        filtered_data_2["csvTime"].diff().dt.total_seconds().shift(-1)
    )

    # 计算每个时间间隔的能耗（kWh）
    filtered_data_1.loc[:, "energy_kWh"] = (
            filtered_data_1["diff_seconds"] * filtered_data_1[power_column_1] / 3600
    )
    filtered_data_2.loc[:, "energy_kWh"] = (
            filtered_data_2["diff_seconds"] * filtered_data_2[power_column_2] / 3600
    )

    # 计算总能耗
    total_energy_kWh_1 = filtered_data_1["energy_kWh"].sum()
    total_energy_kWh_2 = filtered_data_2["energy_kWh"].sum()

    # 根据查询类型返回相应的能耗
    if query_type == "1":
        return round(total_energy_kWh_1, 2)
    elif query_type == "2":
        return round(total_energy_kWh_2, 2)
    elif query_type == "all":
        return round(total_energy_kWh_1 + total_energy_kWh_2, 2)
    else:
        raise ValueError("query_type 参数无效，请输入 '1'、'2' 或 'all'")


def get_device_status_by_time_range(start_time, end_time):
    """
    根据数据表名、开始时间和结束时间，查询设备在该时间段内的状态变化，并排除 status 为 'False' 的记录。
    参数:
    start_time (str): 开始时间，格式为 'YYYY-MM-DD HH:MM:SS'
    end_time (str): 结束时间，格式为 'YYYY-MM-DD HH:MM:SS'

    返回:
    dict: 包含设备状态变化的时间点和对应状态的字典，或错误信息
    """

    def get_status_changes(table_name, device_name):
        """
        辅助函数：获取指定设备在指定时间范围内的状态变化。

        参数:
        table_name (str): 数据表名
        device_name (str): 设备名称

        返回:
        dict: 包含设备状态变化的时间点和对应状态的字典，或错误信息
        """
        metadata = {
            "table_name": table_name,
            "start_time": start_time,
            "end_time": end_time,
        }

        try:
            df = pd.read_csv(f"database_in_use/{table_name}.csv")
        except FileNotFoundError:
            return {"error": f"数据表 {table_name} 不存在", "metadata": metadata}

        # 将csvTime列从时间戳转换为datetime类型
        df["csvTime"] = pd.to_datetime(df["csvTime"], unit="ns")  # 假设时间戳是纳秒级别

        # 将开始时间和结束时间转换为datetime类型
        start_time_dt = pd.to_datetime(start_time)
        end_time_dt = pd.to_datetime(end_time)

        # 筛选指定时间范围内的数据，并排除 status 为 'False' 的记录
        filtered_data = df[
            (df["csvTime"] >= start_time_dt)
            & (df["csvTime"] <= end_time_dt)
            & (df["status"] != "False")
            ]

        if filtered_data.empty:
            return {
                "error": f"在数据表 {table_name} 中未找到时间范围 {start_time} 到 {end_time} 且 status 不为 'False' 的数据",
                "metadata": metadata,
            }

        # 检查是否存在status列
        if "status" not in filtered_data.columns:
            return {
                "error": f"数据表 {table_name} 中不存在 'status' 列",
                "metadata": metadata,
            }

        # 获取设备状态变化的时间点和对应状态
        status_changes = filtered_data[
            ["csvTime", "status"]
        ].copy()  # 显式创建副本以避免警告

        # 使用 .loc 避免 SettingWithCopyWarning
        status_changes.loc[:, "csvTime"] = status_changes["csvTime"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # 将结果转换为字典
        return {
            "设备名称": device_name,
            "正在进行的关键动作": status_changes.to_dict(orient="records"),
        }

    # 获取三个设备的状态变化
    result1 = get_status_changes("Ajia_plc_1", "A架")
    result2 = get_status_changes("device_13_11_meter_1311", "折臂吊车")
    result3 = get_status_changes("Port3_ksbg_9", "定位设备")

    # 过滤掉包含错误的结果
    results = [
        result for result in [result1, result2, result3] if "error" not in result
    ]

    # 返回结果和元数据
    return {
        "result": results,
        "metadata": {"start_time": start_time, "end_time": end_time},
    }


if __name__ == "__main__":
    # 调用函数，查询指定时间段内的开机时长
    """
    start_time = '2024/8/23 0:00'
    end_time = '2024/8/23 12:00'
    uptime = calculate_uptime(start_time, end_time, shebeiname='折臂吊车')
    # 输出结果
    print(f"指定时间段内的开机时长: {uptime} 秒")
    uptime = compute_operational_duration(start_time, end_time, device_name='A架')
    # 输出结果
    print(f"指定时间段内的运行时长: {uptime} 秒")
    """
    # 示例调用
    # 示例调用
    table_name = "Ajia_plc_1"
    start_time = "2024-08-19 00:00:00"  # 开始时间
    end_time = "2024-08-19 23:59:59"  # 结束时间
    columns = ["csvTime", "status"]  # 需要查询的列名
    status = "开机"  # 筛选状态为 "开机"

    # 获取数据
    data = get_table_data(table_name, start_time, end_time, columns, status)
    # print(data)
    start_time = "2024-08-23 00:00:00"  # 开始时间
    end_time = "2024-08-23 11:59:59"
    device_name = "折臂吊车"

    # Correctly constructing the tuple

    # data = compute_operational_duration(start_time, end_time, device_name)

    print(data)
    data = calculate_uptime(start_time, end_time, device_name)

    print(data)

    start_time = "2024-08-24 00:00:00"  # 开始时间
    end_time = "2024-08-24 11:59:59"
    device_name = "折臂吊车"

    print(calculate_total_energy(start_time, end_time, device_name=device_name))
    print(calculate_total_deck_machinery_energy(start_time, end_time))

    # 获取数据
    data = get_table_data(table_name, start_time, end_time, columns, status)
    # print(data)
    start_time = "2024-08-23 00:00:00"  # 开始时间
    end_time = "2024-08-23 11:59:59"
    device_name = "A架"

    # Correctly constructing the tuple

    data = compute_operational_duration(start_time, end_time, device_name)

    print(data)

    start_time = "2024-08-23 12:00:00"  # 开始时间
    end_time = "2024-08-23 23:59:59"
    device_name = "A架"

    data = calculate_uptime(start_time, end_time, device_name)

    print(data)
