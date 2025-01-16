import os
import pandas as pd
from collections import defaultdict
import json
from datetime import datetime
from predict_seq import get_result

data_path = '../../assets/初赛数据/'


def merge_csv_files(folder_path, out_path):
    # Store files by their prefix
    file_groups = defaultdict(list)
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv') and '字段释义' not in file_name:
            prefix = file_name.rsplit('_', 1)[0]
            file_groups[prefix].append(os.path.join(folder_path, file_name))

    # Merge files with the same prefix
    for prefix, file_list in file_groups.items():
        merged_df = pd.concat((pd.read_csv(file) for file in file_list), ignore_index=True)
        output_file = os.path.join(out_path, f'{prefix}.csv')

        print('-----------')
        print(output_file)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        merged_df.to_csv(output_file, index=False)
        print('---完成---')
        print(f'Merged files with prefix "{prefix}" into {output_file}')

    # Convert Excel to CSV
    os.makedirs('database_in_use', exist_ok=True)
    df_device = pd.read_excel(f'{data_path}设备参数详情.xlsx')
    df_device.to_csv('data/设备参数详情表.csv', index=False)
    df_device.to_csv('database_in_use/设备参数详情表.csv', index=False)


merge_csv_files(data_path, 'data')
merge_csv_files(data_path, 'database_in_use')


# In[3]:
# %%
# Pre2: Status and Events Detection
# 定义一个函数，将值转换为数值类型，无法转换的返回 -1
def convert_to_numeric(value):
    try:
        return float(value)
    except ValueError:
        return -1


# 读取CSV文件
df = pd.read_csv('data/Ajia_plc_1.csv')
# 将 Ajia-3_v 和 Ajia-5_v 列转换为数值类型，无法转换的设为 -1
df['Ajia-3_v'] = df['Ajia-3_v'].apply(convert_to_numeric)
df['Ajia-5_v'] = df['Ajia-5_v'].apply(convert_to_numeric)
# 初始化 status 列，默认值为 'False'
df['status'] = 'False'
df['check_current_presence'] = 'False'
# 遍历每一行，判断设备状态
for i in range(1, df.shape[0]):

    # 关机条件
    if df.loc[i, 'Ajia-5_v'] == -1 and (df.loc[i - 1, 'Ajia-5_v'] > 0 or df.loc[i - 1, 'Ajia-5_v'] == '0'):
        df.loc[i, 'status'] = '停电'
        # 开机条件
    if df.loc[i - 1, 'Ajia-3_v'] == -1 and (df.loc[i, 'Ajia-3_v'] == 0 or df.loc[i, 'Ajia-3_v'] == '0'):
        df.loc[i, 'status'] = '开机'
    if df.loc[i - 1, 'Ajia-3_v'] == -1 and df.loc[i, 'Ajia-3_v'] > 0:
        df.loc[i, 'status'] = '开机'
    if df.loc[i - 1, 'Ajia-5_v'] == -1 and (df.loc[i, 'Ajia-5_v'] == 0 or df.loc[i, 'Ajia-5_v'] == '0'):
        df.loc[i, 'status'] = '开机'
    # 关机条件
    if df.loc[i, 'Ajia-3_v'] == -1 and (df.loc[i - 1, 'Ajia-3_v'] == 0 or df.loc[i - 1, 'Ajia-3_v'] == '0'):
        df.loc[i, 'status'] = '关机'
    if df.loc[i, 'Ajia-5_v'] == -1 and (df.loc[i - 1, 'Ajia-5_v'] == 0 or df.loc[i - 1, 'Ajia-5_v'] == '0'):
        df.loc[i, 'status'] = '关机'
    if df.loc[i, 'Ajia-5_v'] > 0 and df.loc[i - 1, 'Ajia-5_v'] == -1:
        df.loc[i, 'check_current_presence'] = '有电流'
    if df.loc[i, 'Ajia-5_v'] > 0 and (df.loc[i - 1, 'Ajia-5_v'] == 0 or df.loc[i - 1, 'Ajia-5_v'] == '0'):
        df.loc[i, 'check_current_presence'] = '有电流'
    if df.loc[i, 'Ajia-5_v'] == 0 and (df.loc[i - 1, 'Ajia-5_v'] > 0 or df.loc[i - 1, 'Ajia-5_v'] == '0'):
        df.loc[i, 'check_current_presence'] = '无电流'


def is_mostly_fifty(L_):
    # 去掉列表中0或者超过200的值
    filtered_list = [x for x in L_ if x != 0 and x <= 200]
    # 将50到60之间的值视为50
    normalized_list = [50 if 50 <= x <= 60 else x for x in filtered_list]
    # 统计50的数量
    count_50 = normalized_list.count(50)

    # 如果50的数量超过列表长度的一半，返回1，否则返回0
    if count_50 > len(normalized_list) / 2:
        return 1  # 代表是待机
    else:
        return 0

    # 初始化变量


start_time = None
segments = []

# 遍历DataFrame
for index, row in df.iterrows():
    if row['status'] == '开机':
        start_time = row['csvTime']
    elif row['status'] == '关机' and start_time is not None:
        end_time = row['csvTime']
        segments.append((start_time, end_time))
        start_time = None


def extract_daily_power_on_times(df):
    """
    从CSV文件中提取一天内有两次开机的第一次和第二次开机时间。

    参数:
    file_path (str): CSV文件的路径，包含 'csvTime' 和 'status' 列。

    返回:
    first_start_times (list): 一天内有两次开机的第一次开机时间列表。
    second_start_times (list): 一天内有两次开机的第二次开机时间列表。
    """
    # 读取CSV文件
    df = df

    # 将 csvTime 转换为 datetime 类型
    df['csvTime'] = pd.to_datetime(df['csvTime'])

    # 按天分组
    df['date'] = df['csvTime'].dt.date

    # 初始化一个字典来存储每天的开机关机时间段
    daily_segments = {}

    # 遍历每一天的数据
    for date, group in df.groupby('date'):
        segments = []
        start_time = None

        # 遍历每一天的记录
        for index, row in group.iterrows():
            if row['status'] == '开机':
                start_time = row['csvTime']
            elif row['status'] == '关机' and start_time is not None:
                end_time = row['csvTime']
                segments.append((start_time, end_time))
                start_time = None

        # 将每天的开机关机时间段存入字典
        daily_segments[date] = segments

    # 统计每天的开机关机次数
    daily_counts = {date: len(segments) for date, segments in daily_segments.items()}

    # 筛选出一天内有两次开机关机的情况
    two_times_days = [date for date, count in daily_counts.items() if count == 2]

    # 初始化两个列表来存储第一次和第二次的开机时间
    first_start_times = []
    second_start_times = []

    # 遍历这些日期，提取第一次和第二次的开机时间
    for date in two_times_days:
        segments = daily_segments[date]
        first_start_times.append(segments[0][0])  # 第一次开机时间
        second_start_times.append(segments[1][0])  # 第二次开机时间

    return first_start_times, second_start_times


def find_peaks(data1):
    # 数据预处理
    data = [50 if 50 <= num <= 68 else num for num in data1]

    # 找到峰值
    peaks = []
    for i in range(1, len(data) - 1):  # 从第二个元素遍历到倒数第二个元素
        if data[i] > data[i - 1] and data[i] > data[i + 1]:  # 判断是否为峰值
            peaks.append(data[i])  # 只记录峰值值
    peaks = [peak for peak in peaks if peak > 80]
    # 返回峰值格式和具体的峰值
    return len(peaks), peaks


def find_first_increasing_value(data):
    """
    找到列表中第一个从稳定值（68以下）开始增加的值。

    参数:
    data (list): 输入的数值列表。

    返回:
    tuple: 第一个大于68的值及其索引。如果未找到，返回 (None, None)。
    """
    # 将介于50到68之间的值替换为50
    processed_data = [50 if 50 <= num <= 68 else num for num in data]

    # 找到第一个大于68的值及其索引
    for index, value in enumerate(processed_data):
        if value > 68 and value < 300:
            return value
    # 如果未找到，返回 (None, None)
    return 50


def find_stable_value(data, peak1, peak2):
    """
    找到两个峰值之间的数据中，回落到稳定值的第一个值。
    假设稳定值在 50 到 60 之间。

    参数:
    data (list): 数据列表
    peak1 (float): 第一个峰值
    peak2 (float): 第二个峰值

    返回:
    float or None: 稳定值，如果未找到则返回 None
    """
    # 找到峰值之间的数据
    try:
        start_index = data.index(peak1)
        end_index = data.index(peak2)
    except ValueError:
        # 如果峰值不在列表中，返回 None
        return None

    between_peaks = data[start_index:end_index + 1]

    # 找到回落到稳定值的第一个值（假设稳定值在 50 到 60 之间）
    for value in between_peaks:
        if 50 <= value <= 60:
            return value

    # 如果未找到稳定值，返回 None
    return None


def find_first_stable_after_peak(data, peak, stable_min=50, stable_max=60):
    """
    从峰值到列表末尾的数据中，找到第一个回落到稳定值的值。

    参数:
    data (list): 数据列表
    peak (float): 峰值
    stable_min (float): 稳定值的最小值
    stable_max (float): 稳定值的最大值

    返回:
    float or None: 稳定值，如果未找到则返回 None
    """
    try:
        # 找到峰值的索引
        start_index = data.index(peak)
    except ValueError:
        # 如果峰值不在列表中，返回 None
        return None

    # 切片获取从峰值到列表末尾的数据
    after_peak = data[start_index:]

    # 找到回落到稳定值的第一个值
    for value in after_peak:
        if stable_min <= value <= stable_max:
            return value

    # 如果未找到稳定值，返回 None
    return None


LLLL = []
import pandas as pd


def extract_events(df, segment):
    start, end = segment
    # start = pd.to_datetime(start)
    # end = pd.to_datetime(end)
    print(f"开机时间: {start}, 关机时间: {end}")
    events = df[
        (df['csvTime'] >= start) & (df['csvTime'] <= end) & (df['check_current_presence'].isin(['有电流', '无电流']))]
    print(f"事件数量: {events.shape[0]}")
    L3 = []
    # 检查事件数量是否为偶数
    if events.shape[0] >= 2 and events.shape[0] % 2 == 0:
        # 遍历所有偶数索引的事件对
        for i in range(0, events.shape[0], 2):
            event_start = events.iloc[i]
            event_end = events.iloc[i + 1]
            # 确保第一个事件是“有电流”，第二个事件是“无电流”
            if event_start['check_current_presence'] == '有电流' and event_end['check_current_presence'] == '无电流':
                start_event_time = event_start['csvTime']
                end_event_time = event_end['csvTime']

                # 提取两个事件之间的数据
                between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                data1 = list(between_events['Ajia-5_v'])
                print(f"事件对 ({i}, {i + 1}) 之间的数据: {data1}")

                # 调用 find_peaks 函数（假设已定义）
                len_peaks, peak_L = find_peaks(data1)
                print(f'峰值为{peak_L}')
                L3.append(len_peaks)
    return L3


L5 = []
# 提取每个区段内的“通电流”和“关电流”事件
for segment in segments:
    L4 = extract_events(df, segment=segment)
    L5.append(L4)
    start, end = segment
    events_2 = df[(df['csvTime'] >= start) & (df['csvTime'] <= end)]
    print('-----------------事件--------------------')
    print(list(events_2['Ajia-5_v']))
    print('-----------------事件--------------------')
    events_1 = df[
        (df['csvTime'] >= start) & (df['csvTime'] <= end) & (df['check_current_presence'].isin(['有电流', '无电流']))]
    LLLL.append(events_1.shape[0])
    # if start=='2024-08-24 07:55:08':

    if L4 == [0, 2]:
        events = df[(df['csvTime'] >= start) & (df['csvTime'] <= end) & (
            df['check_current_presence'].isin(['有电流', '无电流']))]
        if events.shape[0] % 2 == 0:
            if events.iloc[0]['check_current_presence'] == '有电流' and events.iloc[1][
                'check_current_presence'] == '无电流':
                start_event_time = events.iloc[0]['csvTime']
                end_event_time = events.iloc[1]['csvTime']
                between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                data1 = list(between_events['Ajia-5_v'])

                len_peaks, peak_L = find_peaks(data1)

                if len_peaks == 0:
                    if events.iloc[2]['check_current_presence'] == '有电流' and events.iloc[3][
                        'check_current_presence'] == '无电流':
                        start_event_time = events.iloc[2]['csvTime']
                        end_event_time = events.iloc[3]['csvTime']
                        between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                        data1 = list(between_events['Ajia-5_v'])
                        print(data1)
                        len_peaks, peak_L = find_peaks(data1)
                        if len_peaks == 2:
                            value_11 = find_first_increasing_value(data1)
                            indices = between_events.index[between_events['Ajia-5_v'] == value_11].tolist()
                            df.loc[indices, 'status'] = '征服者起吊'

                            value_11 = find_stable_value(data1, peak_L[0], peak_L[1])
                            indices = between_events.index[between_events['Ajia-5_v'] == value_11].tolist()
                            df.loc[indices, 'status'] = '缆绳解除'
                            previous_indices = [idx - 1 for idx in indices if idx > 0]
                            df.loc[previous_indices, 'status'] = '征服者入水'

                            # 找到 between_events 中 Ajia-5_v 等于 target_value 的索引
                            indices = between_events.index[between_events['Ajia-5_v'] == peak_L[1]].tolist()
                            df.loc[indices, 'status'] = 'A架摆回'
    if L4 == [2]:
        events = df[(df['csvTime'] >= start) & (df['csvTime'] <= end) & (
            df['check_current_presence'].isin(['有电流', '无电流']))]
        if events.shape[0] % 2 == 0:
            if events.iloc[0]['check_current_presence'] == '有电流' and events.iloc[1][
                'check_current_presence'] == '无电流':
                start_event_time = events.iloc[0]['csvTime']
                end_event_time = events.iloc[1]['csvTime']
                between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                data1 = list(between_events['Ajia-5_v'])

                len_peaks, peak_L = find_peaks(data1)

                if len_peaks == 2:
                    if events.iloc[0]['check_current_presence'] == '有电流' and events.iloc[1][
                        'check_current_presence'] == '无电流':
                        start_event_time = events.iloc[0]['csvTime']
                        end_event_time = events.iloc[1]['csvTime']
                        between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                        data1 = list(between_events['Ajia-5_v'])
                        len_peaks, peak_L = find_peaks(data1)
                        if len_peaks == 2:
                            value_11 = find_first_increasing_value(data1)
                            indices = between_events.index[between_events['Ajia-5_v'] == value_11].tolist()
                            df.loc[indices, 'status'] = '征服者起吊'

                            value_11 = find_stable_value(data1, peak_L[0], peak_L[1])
                            indices = between_events.index[between_events['Ajia-5_v'] == value_11].tolist()
                            df.loc[indices, 'status'] = '缆绳解除'
                            previous_indices = [idx - 1 for idx in indices if idx > 0]
                            df.loc[previous_indices, 'status'] = '征服者入水'

                            # 找到 between_events 中 Ajia-5_v 等于 target_value 的索引
                            indices = between_events.index[between_events['Ajia-5_v'] == peak_L[1]].tolist()
                            df.loc[indices, 'status'] = 'A架摆回'

    elif L4 == [0, 3]:
        events = df[(df['csvTime'] >= start) & (df['csvTime'] <= end) & (
            df['check_current_presence'].isin(['有电流', '无电流']))]
        if events.shape[0] % 2 == 0:
            if events.iloc[0]['check_current_presence'] == '有电流' and events.iloc[1][
                'check_current_presence'] == '无电流':
                start_event_time = events.iloc[0]['csvTime']
                end_event_time = events.iloc[1]['csvTime']
                between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                data1 = list(between_events['Ajia-5_v'])

                len_peaks, peak_L = find_peaks(data1)

                if len_peaks == 0:
                    if events.iloc[2]['check_current_presence'] == '有电流' and events.iloc[3][
                        'check_current_presence'] == '无电流':
                        start_event_time = events.iloc[2]['csvTime']
                        end_event_time = events.iloc[3]['csvTime']
                        between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                        data1 = list(between_events['Ajia-5_v'])
                        print(data1)
                        len_peaks, peak_L = find_peaks(data1)
                        if len_peaks == 3:
                            value_11 = find_first_increasing_value(data1)
                            indices = between_events.index[between_events['Ajia-5_v'] == value_11].tolist()
                            df.loc[indices, 'status'] = '征服者起吊'

                            value_11 = find_stable_value(data1, peak_L[1], peak_L[2])
                            indices = between_events.index[between_events['Ajia-5_v'] == value_11].tolist()
                            df.loc[indices, 'status'] = '缆绳解除'
                            previous_indices = [idx - 1 for idx in indices if idx > 0]
                            df.loc[previous_indices, 'status'] = '征服者入水'

                            # 找到 between_events 中 Ajia-5_v 等于 target_value 的索引
                            indices = between_events.index[between_events['Ajia-5_v'] == peak_L[2]].tolist()
                            df.loc[indices, 'status'] = 'A架摆回'
    elif L4 == [0, 1, 3]:
        events = df[(df['csvTime'] >= start) & (df['csvTime'] <= end) & (
            df['check_current_presence'].isin(['有电流', '无电流']))]
        if events.shape[0] % 2 == 0:
            if events.iloc[0]['check_current_presence'] == '有电流' and events.iloc[1][
                'check_current_presence'] == '无电流':
                start_event_time = events.iloc[0]['csvTime']
                end_event_time = events.iloc[1]['csvTime']
                between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                data1 = list(between_events['Ajia-5_v'])

                len_peaks, peak_L = find_peaks(data1)

                if len_peaks == 0:
                    if events.iloc[4]['check_current_presence'] == '有电流' and events.iloc[5][
                        'check_current_presence'] == '无电流':
                        start_event_time = events.iloc[4]['csvTime']
                        end_event_time = events.iloc[5]['csvTime']
                        between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                        data1 = list(between_events['Ajia-5_v'])

                        len_peaks, peak_L = find_peaks(data1)
                        if len_peaks == 3:
                            value_11 = find_first_increasing_value(data1)
                            indices = between_events.index[between_events['Ajia-5_v'] == value_11].tolist()
                            df.loc[indices, 'status'] = '征服者起吊'
                            value_11 = find_stable_value(data1, peak_L[1], peak_L[2])
                            indices = between_events.index[between_events['Ajia-5_v'] == value_11].tolist()
                            df.loc[indices, 'status'] = '缆绳解除'
                            previous_indices = [idx - 1 for idx in indices if idx > 0]
                            df.loc[previous_indices, 'status'] = '征服者入水'

                            # 找到 between_events 中 Ajia-5_v 等于 target_value 的索引
                            indices = between_events.index[between_events['Ajia-5_v'] == peak_L[2]].tolist()
                            df.loc[indices, 'status'] = 'A架摆回'
    elif L4 == [1, 2] or L4 == [1, 1]:
        events = df[(df['csvTime'] >= start) & (df['csvTime'] <= end) & (
            df['check_current_presence'].isin(['有电流', '无电流']))]
        if events.shape[0] % 2 == 0:
            if events.iloc[0]['check_current_presence'] == '有电流' and events.iloc[1][
                'check_current_presence'] == '无电流':
                start_event_time = events.iloc[0]['csvTime']
                end_event_time = events.iloc[1]['csvTime']
                between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                data1 = list(between_events['Ajia-5_v'])

                len_peaks, peak_L = find_peaks(data1)

                if len_peaks == 1:
                    value_11 = find_first_increasing_value(data1)
                    indices = between_events.index[between_events['Ajia-5_v'] == peak_L[0]].tolist()
                    df.loc[indices, 'status'] = 'A架摆出'
                    if events.iloc[2]['check_current_presence'] == '有电流' and events.iloc[3][
                        'check_current_presence'] == '无电流':
                        start_event_time = events.iloc[2]['csvTime']
                        end_event_time = events.iloc[3]['csvTime']
                        between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                        data1 = list(between_events['Ajia-5_v'])

                        len_peaks, peak_L = find_peaks(data1)
                        max_value = max([x for x in data1 if x <= 200])

                        if len_peaks == 2:
                            # 找到 between_events 中 Ajia-5_v 等于 target_value 的索引
                            indices = between_events.index[between_events['Ajia-5_v'] == max_value].tolist()
                            df.loc[indices, 'status'] = '征服者出水'
                            previous_indices = [idx - 1 for idx in indices if idx > 0]
                            df.loc[previous_indices, 'status'] = '缆绳挂妥'

                            value_11 = find_first_stable_after_peak(data1, max_value)
                            indices = between_events.index[between_events['Ajia-5_v'] == value_11].tolist()
                            df.loc[indices, 'status'] = '征服者落座'
                        elif len_peaks == 1:
                            # 找到 between_events 中 Ajia-5_v 等于 target_value 的索引
                            indices = between_events.index[between_events['Ajia-5_v'] == max_value].tolist()
                            df.loc[indices, 'status'] = '征服者出水'
                            previous_indices = [idx - 1 for idx in indices if idx > 0]
                            df.loc[previous_indices, 'status'] = '缆绳挂妥'

                            value_11 = find_first_stable_after_peak(data1, max_value)
                            indices = between_events.index[between_events['Ajia-5_v'] == value_11].tolist()
                            df.loc[indices, 'status'] = '征服者落座'
    else:

        events_2 = events_2.copy()
        events_2.loc[:, 'csvTime'] = pd.to_datetime(events_2['csvTime'])
        # 获取第一个值
        first_value = events_2['csvTime'].iloc[0]

        # 定义目标日期
        target_date = datetime(2024, 8, 19)  # 2024年8月19日   大模型预测测试
        is_target_date = (first_value.date() == target_date.date())

        target_date_1 = datetime(2024, 8, 19)  # 2024年8月19日   大模型预测测试
        is_target_date_1 = (first_value.date() == target_date.date())

        # 判断小时是否大于12点
        is_hour_greater_than_12 = first_value.hour > 17
        first_start_times, second_start_times = extract_daily_power_on_times(df=df)

        if is_target_date and is_hour_greater_than_12:  # 全部预测可以去掉is_target_date条件 或者根据问题传入
            events_2['new_column'] = events_2.apply(
                lambda row: row['Ajia-3_v'] if row['Ajia-5_v'] == 0 and row['Ajia-3_v'] > 0 else row['Ajia-5_v'],
                axis=1
            )
            print('----------------LLM预测的列表---------------------')
            print(str(list(events_2['new_column'])))

            try:
                a, b, c = get_result(str(list(events_2['new_column'])), 1)
            except Exception as e:
                print(f"An error occurred: {e}")
                a, b, c = -100, -100, -100
            print('----------------预测的值---------------------')
            print(a, b, c)

            indices = events_2.index[events_2['new_column'] == a].tolist()
            df.loc[indices, 'status'] = 'A架摆出'

            indices = events_2.index[events_2['new_column'] == b].tolist()
            df.loc[indices, 'status'] = '征服者出水'
            previous_indices = [idx - 1 for idx in indices if idx > 0]
            df.loc[previous_indices, 'status'] = '缆绳挂妥'

            indices = events_2.index[events_2['new_column'] == c].tolist()
            df.loc[indices, 'status'] = '征服者落座'



        elif first_value in first_start_times and 1 == 0:  # 去掉1==0由LLM判断状态  默认不开启 给大家分享参考思路。
            events_2['new_column'] = events_2.apply(
                lambda row: row['Ajia-3_v'] if row['Ajia-5_v'] == 0 and row['Ajia-3_v'] > 0 else row['Ajia-5_v'],
                axis=1
            )
            print('----------------LLM预测的列表---------------------')
            print(str(list(events_2['new_column'])))

            try:
                a, b, c = get_result(str(list(events_2['new_column'])), 0)
            except Exception as e:
                print(f"An error occurred: {e}")
                a, b, c = -100, -100, -100
            print('----------------预测的值---------------------')
            print(a, b, c)

            indices = events_2.index[events_2['new_column'] == a].tolist()
            df.loc[indices, 'status'] = '征服者起吊'

            indices = events_2.index[events_2['new_column'] == b].tolist()
            df.loc[indices, 'status'] = '缆绳解除'
            previous_indices = [idx - 1 for idx in indices if idx > 0]
            df.loc[previous_indices, 'status'] = '征服者入水'

            indices = events_2.index[events_2['new_column'] == c].tolist()
            df.loc[indices, 'status'] = 'A架摆回'

        elif first_value in second_start_times and 1 == 0:  # 去掉1==0由LLM判断状态
            events_2['new_column'] = events_2.apply(
                lambda row: row['Ajia-3_v'] if row['Ajia-5_v'] == 0 and row['Ajia-3_v'] > 0 else row['Ajia-5_v'],
                axis=1
            )
            print('----------------LLM预测的列表---------------------')
            print(str(list(events_2['new_column'])))

            try:
                a, b, c = get_result(str(list(events_2['new_column'])), 1)
            except Exception as e:
                print(f"An error occurred: {e}")
                a, b, c = -100, -100, -100
            print('----------------预测的值---------------------')
            print(a, b, c)

            indices = events_2.index[events_2['new_column'] == a].tolist()
            df.loc[indices, 'status'] = 'A架摆出'

            indices = events_2.index[events_2['new_column'] == b].tolist()
            df.loc[indices, 'status'] = '征服者出水'
            previous_indices = [idx - 1 for idx in indices if idx > 0]
            df.loc[previous_indices, 'status'] = '缆绳挂妥'

            indices = events_2.index[events_2['new_column'] == c].tolist()
            df.loc[indices, 'status'] = '征服者落座'

        print('------------------')
        print(L4)
df = df.drop(columns=['date'])  # 删除 'date' 列
df = df.drop(columns=['check_current_presence'])  # 删除 'date' 列
df.to_csv('database_in_use/Ajia_plc_1.csv', index=False)
# In[4]:


import pandas as pd

# 读取CSV文件
df = pd.read_csv('data/Port3_ksbg_9.csv')
# 将P3_33列转换为数值类型，无法转换的保留原值
df['P3_33'] = pd.to_numeric(df['P3_33'], errors='coerce')
# 初始化status列
df['status'] = 'False'
# A架开机关机
for i in range(1, df.shape[0]):
    # 开机
    if df.loc[i - 1, 'P3_33'] == 0 and df.loc[i, 'P3_33'] > 0:
        df.loc[i, 'status'] = 'ON_DP'
    # 关机
    if df.loc[i - 1, 'P3_33'] > 0 and df.loc[i, 'P3_33'] == 0:
        df.loc[i, 'status'] = 'OFF_DP'
# 保存结果
df.to_csv('database_in_use/Port3_ksbg_9.csv', index=False)
# In[5]:


# 读取CSV文件
df = pd.read_csv('data/device_13_11_meter_1311.csv')

# 将13-11-6_v列转换为数值类型，无法转换的保留原值
df['13-11-6_v'] = pd.to_numeric(df['13-11-6_v'], errors='coerce')

# 初始化status和action列
df['status'] = 'False'
df['action'] = 'False'


def sliding_window_5(arr):
    """滑动窗口大小为5的逻辑"""
    window_size = 5
    modified_arr = arr.copy()
    for i in range(len(arr) - window_size + 1):
        window = arr[i:i + window_size]
        if window[1] < 10 and window[2] < 10 and window[3] < 10 and window[0] > 10 and window[4] > 10:
            # 将 window[0] 包装成列表进行赋值
            modified_arr[i + 1:i + 4] = [window[0]] * 3
    return modified_arr


def sliding_window_4(arr):
    """滑动窗口大小为4的逻辑"""
    window_size = 4
    modified_arr = arr.copy()
    for i in range(len(arr) - window_size + 1):
        window = arr[i:i + window_size]
        if window[1] < 10 and window[2] < 10 and window[0] > 10 and window[3] > 10:
            # 将 window[0] 包装成列表进行赋值
            modified_arr[i + 1:i + 3] = [window[0]] * 2
    return modified_arr


def sliding_window_3(arr):
    """滑动窗口大小为3的逻辑"""
    window_size = 3
    modified_arr = arr.copy()
    for i in range(len(arr) - window_size + 1):
        window = arr[i:i + window_size]
        if window[1] < 10 and window[0] > 10 and window[2] > 10:
            # 直接赋值，因为只修改一个值
            modified_arr[i + 1] = window[0]
    return modified_arr


# 应用滑动窗口逻辑到 DataFrame 的某一列
df['13-11-6_v_new'] = sliding_window_5(df['13-11-6_v'].tolist())
df['13-11-6_v_new'] = sliding_window_4(df['13-11-6_v_new'].tolist())
df['13-11-6_v_new'] = sliding_window_3(df['13-11-6_v_new'].tolist())

# 检测折臂吊车的开机和关机事件
segments = []
start_time = None

for i in range(1, df.shape[0]):
    # 开机
    if df.iloc[i - 1]['13-11-6_v'] == 0 and df.iloc[i]['13-11-6_v'] > 0:
        df.at[df.index[i], 'status'] = '折臂吊车开机'
    # 关机
    if df.iloc[i - 1]['13-11-6_v'] > 0 and df.iloc[i]['13-11-6_v'] == 0:
        df.at[df.index[i], 'status'] = '折臂吊车关机'

    # 检测由待机进入工作和由工作进入待机的事件
    if df.iloc[i - 1]['13-11-6_v_new'] < 10 and df.iloc[i]['13-11-6_v_new'] > 10:
        df.at[df.index[i], 'action'] = '由待机进入工作'
    if df.iloc[i - 1]['13-11-6_v_new'] > 10 and df.iloc[i]['13-11-6_v_new'] < 10:
        df.at[df.index[i], 'action'] = '由工作进入待机'
    # 遍历DataFrame
for index, row in df.iterrows():
    if row['status'] == '折臂吊车开机':
        start_time = row['csvTime']
    elif row['status'] == '折臂吊车关机' and start_time is not None:
        end_time = row['csvTime']
        segments.append((start_time, end_time))
        start_time = None
from collections import Counter


def find_most_frequent_number(lst):
    # 使用 Counter 统计每个数的出现次数
    counter = Counter(lst)
    # 找到出现次数最多的数（如果有多个，只返回第一个）
    most_common_number = counter.most_common(1)[0][0]
    return most_common_number


# 提取每个区段内的“由待机进入工作”和“由工作进入待机”事件
for segment in segments:
    start, end = segment
    events = df[
        (df['csvTime'] >= start) & (df['csvTime'] <= end) & (df['action'].isin(['由待机进入工作', '由工作进入待机']))]
    events_2 = df[(df['csvTime'] >= start) & (df['csvTime'] <= end)]
    # 检查事件数量是否为偶数且等于6
    if events.shape[0] == 6:
        print(f"开机时间: {start}, 关机时间: {end}")
        print(f"事件数量: {events.shape[0]}")
        # 处理每一对事件
        for i in range(0, 6, 2):

            event_start = events.iloc[i]
            event_end = events.iloc[i + 1]

            if event_start['action'] == '由待机进入工作' and event_end['action'] == '由工作进入待机':
                start_event_time = event_start['csvTime']
                end_event_time = event_end['csvTime']
                between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                data1 = list(between_events['13-11-6_v'])

                # 找到最后一个大于9的值
                last_value_above_9 = next((x for x in reversed(data1) if x > 9), None)

                if last_value_above_9 is not None:
                    all_indices = between_events.index[between_events['13-11-6_v_new'] == last_value_above_9].tolist()
                    last_index = all_indices[-1] if all_indices else None

                    # 根据事件对的顺序更新status
                    if last_index is not None:
                        if i == 0:
                            df.loc[last_index, 'status'] = '小艇检查完毕'
                        elif i == 2:
                            df.loc[last_index, 'status'] = '小艇入水'
                        elif i == 4:
                            df.loc[last_index, 'status'] = '小艇落座'
                else:
                    print("列表中没有大于 9 的值")
    if events.shape[0] == 4:
        print(f"开机时间: {start}, 关机时间: {end}")
        print(f"事件数量: {events.shape[0]}")
        # 处理每一对事件
        for i in range(0, 4, 2):
            event_start = events.iloc[i]
            event_end = events.iloc[i + 1]
            if event_start['action'] == '由待机进入工作' and event_end['action'] == '由工作进入待机':
                start_event_time = event_start['csvTime']
                end_event_time = event_end['csvTime']
                between_events = df[(df['csvTime'] >= start_event_time) & (df['csvTime'] <= end_event_time)]
                data1 = list(between_events['13-11-6_v'])

                # 找到最后一个大于9的值
                last_value_above_9 = next((x for x in reversed(data1) if x > 9), None)

                if last_value_above_9 is not None:
                    all_indices = between_events.index[between_events['13-11-6_v_new'] == last_value_above_9].tolist()
                    last_index = all_indices[-1] if all_indices else None

                    # 根据事件对的顺序更新status

                    if last_index is not None and df.loc[last_index, 'status'] == "FALSE":
                        if i == 0:
                            df.loc[last_index, 'status'] = '小艇入水'
                        elif i == 2:
                            df.loc[last_index, 'status'] = '小艇落座'
                else:
                    print("列表中没有大于 9 的值")
                # 保存结果
df = df.drop(columns=['action'])
df = df.drop(columns=['13-11-6_v_new'])

df.to_csv('database_in_use/device_13_11_meter_1311.csv', index=False)


# In[6]:


# Pre3: Data Annotations
def create_annotations():
    df_desc = pd.read_csv(f'{data_path}字段释义.csv', encoding='gbk')
    df_desc['字段含义_new'] = df_desc['字段含义'] + df_desc['单位'].apply(
        lambda x: f",单位:{x}" if pd.notnull(x) else "")
    field_dict = df_desc.set_index('字段名')['字段含义_new'].to_dict()

    folder_path = 'database_in_use'
    files = [f.split('.')[0] for f in os.listdir(folder_path) if f.endswith('.csv')]

    descriptions = []
    for file_name in files:
        df = pd.read_csv(f'{folder_path}/{file_name}.csv')
        columns = df.columns.tolist()
        annotations = [field_dict.get(col, '无注释') for col in columns]
        descriptions.append({'数据表名': file_name, '字段名': columns, "字段含义": annotations})

    # Customize specific tables
    for item in descriptions:
        if item['数据表名'] == 'Ajia_plc_1':
            item['字段含义'][-2] = 'A架动作,包括关机、开机、A架摆出、缆绳挂妥、征服者出水、征服者落座、征服者起吊、征服者入水、缆绳解除、A架摆回'
        if item['数据表名'] == 'device_13_11_meter_1311':
            item['字段含义'][-1] = '折臂吊车及小艇动作,包括折臂吊车关机,折臂吊车开机,小艇检查完毕,小艇入水,小艇落座'
        if item['数据表名'] == 'Port3_ksbg_9':
            item['字段含义'][-1] = 'DP动作,包括OFF_DP,ON_DP'

    with open('dict.json', 'w', encoding='utf-8') as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=4)


create_annotations()
# In[7]:
import pandas as pd

df = pd.read_csv(f'{data_path}字段释义.csv', encoding='gbk')
# 检查某一列是否有重复值
column_name = '字段名'
value_counts = df[column_name].value_counts()
if any(value_counts > 1):
    print(f"列 '{column_name}' 中存在重复值。")
else:
    print(f"列 '{column_name}' 中没有重复值。")
df['字段含义_new'] = df['字段含义'] + df['单位'].apply(lambda x: ",单位:" + x if pd.notnull(x) else "")
# 将两列转换为字典
field_dict = df.set_index('字段名')['字段含义_new'].to_dict()


# 读取CSV文件

def aa(filename):
    df = pd.read_csv(f'database_in_use/{filename}.csv')
    if 'Unnamed: 0' in df.columns:
        del df['Unnamed: 0']
    # 获取列名
    column_names = df.columns.tolist()
    # 定义列名与中文注释的映射字典
    column_name_to_chinese = field_dict
    # 获取中文注释
    chinese_annotations = [column_name_to_chinese.get(col, '无注释') for col in column_names]

    last_dict = {'数据表名': filename, '字段名': column_names, "字段含义": chinese_annotations}
    return last_dict


def process_folder(folder_path):
    # 获取文件夹中的所有CSV文件
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

    # 初始化结果列表
    result_list = []

    # 遍历每个CSV文件
    for csv_file in csv_files:
        # 去掉文件扩展名，获取文件名
        filename = os.path.splitext(csv_file)[0]
        # 调用aa函数处理文件
        result_dict = aa(filename)
        # 将结果字典添加到列表中
        result_list.append(result_dict)

    return result_list


# 使用示例
folder_path = 'database_in_use'
os.makedirs(folder_path, exist_ok=True)
result = process_folder(folder_path)
result = [item for item in result if item['数据表名'] != '设备参数详情表']
for item in result:
    if item['数据表名'] == 'Ajia_plc_1':
        item['字段含义'][-1] = 'A架动作,包括关机、开机、A架摆出、缆绳挂妥、征服者出水、征服者落座、征服者起吊、征服者入水、缆绳解除、A架摆回'
    if item['数据表名'] == 'device_13_11_meter_1311':
        item['字段含义'][-1] = '折臂吊车及小艇动作,包括折臂吊车关机,折臂吊车开机,小艇检查完毕,小艇入水,小艇落座'
    if item['数据表名'] == 'Port3_ksbg_9':
        item['字段含义'][-1] = 'DP动作,包括OFF_DP,ON_DP'
# %%
df1 = pd.read_excel(f'{data_path}设备参数详情.xlsx', sheet_name='字段释义')
df1['含义1'] = df1['含义'].fillna('') + ',' + df1['备注'].fillna('')
dict_shebei = {'数据表名': '设备参数详情表', '字段名': list(df1['字段']), "字段含义": list(df1['含义1'])}
# 修改字段含义列表的第二个值
dict_shebei['字段含义'][1] = "参数中文名,值包含一号柴油发电机组滑油压力、停泊/应急发电机组、一号柴油发电机组滑油压力等"
result.append(dict_shebei)

# 假设这是你的列表数据
data_list = result
# 将列表存入 JSON 文件
with open('dict.json', 'w', encoding='utf-8') as f:
    json.dump(data_list, f, ensure_ascii=False, indent=4)
