import re
import pandas as pd


def remove_upprintable_chars(s):
    """移除所有不可见字符"""
    return ''.join(x for x in s if x.isprintable())


#
def brackets_remove(df):
    """去除大括号、中括号、尖括号中的内容"""
    if df is None or df.empty:
        return None
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            df.iat[i, j] = remove_upprintable_chars(re.sub(u"{.*?}|\\[.*?]|<.*?>", "", str(df.iat[i, j])))
            # 这里我们认为-的效果和没有是一样的，并且去掉？和nan
            df.iat[i, j] = df.iat[i, j].replace('？', '').replace('nan', '')
            if df.iat[i, j] == '' or df.iat[i, j] == '－':
                df.iat[i, j] = None

    new_df_columns = []
    for item in df.columns:
        new_df_columns.append(re.sub(u"{.*?}|\\[.*?]|<.*?>", "", str(item)))
    df = df[new_df_columns]
    return df


def empty_column_remove(df, max_empty_percentage: float, min_columns, min_rows):
    """删除有效内容过少的行或列"""
    if df is None or df.empty:
        return None
    try:
        # 删除有效内容过少的列
        delete_index_list = []
        for df_index, row in df.iteritems():
            if float(sum(row.isnull() == True)) / (0.01 + df.shape[0]) > max_empty_percentage:
                delete_index_list.append(df_index)
        df.drop(delete_index_list, axis=1, inplace=True)

        # 删除有效内容过少的行
        delete_index_list = []
        for df_index, row in df.iterrows():
            if float(sum(row.isnull() == True)) / (0.01 + df.shape[1]) > max_empty_percentage:
                delete_index_list.append(df_index)
        df.drop(delete_index_list, axis=0, inplace=True)
        df.reset_index(drop=True, inplace=True)

        # 删除索引是数字或是与其他列相同的列
        delete_index_list = []
        for df_index, row in df.iteritems():
            if str(df_index).isdigit() or 'Unnamed' in str(df_index) \
                    or '参考' in str(df_index) or '来源' in str(df_index) or '#' in str(df_index):
                delete_index_list.append(df_index)
        df.drop(delete_index_list, axis=1, inplace=True)

        # 删除一行内容都相同的行
        delete_index_list = []
        for df_index, row in df.iterrows():
            flag = True
            for i in range(df.shape[1] - 1):
                if row[i] != row[i + 1]:
                    flag = False
                    break
            if flag:
                delete_index_list.append(df_index)
        df.drop(delete_index_list, axis=0, inplace=True)
        df.reset_index(drop=True, inplace=True)

        # 删除一列内容都相同的列
        if df.shape[0] >= 3:
            delete_index_list = []
            for df_index, row in df.iteritems():
                flag = True
                for i in range(df.shape[0] - 1):
                    if row[i] != row[i + 1]:
                        flag = False
                        break
                if flag:
                    delete_index_list.append(df_index)
            df.drop(delete_index_list, axis=1, inplace=True)

        if df.empty or df.shape[1] < min_columns or df.shape[0] < min_rows:
            return None
        else:
            return df
    except Exception as e:
        print(e)
        return None


# 判断重复表头，并将两个重复的表头合并
def muti_index_process(df, min_columns, min_rows):
    if df is None or df.empty:
        return None
    flag = False
    for i in range(df.shape[1]):
        if str(df.iloc[[0], [i]].values[0][0]) == str(df.columns[i]):
            flag = True
            break
    if flag:
        index_list = []
        for i in range(df.shape[1]):
            if str(df.iloc[[0], [i]].values[0][0]) != str(df.columns[i]):
                index_list.append(str(df.columns[i]) + '(' + str(df.iloc[[0], [i]].values[0][0]) + ')')
            else:
                index_list.append(str(df.columns[i]))
        df.columns = index_list
        df.drop([0], axis=0, inplace=True)
        df.reset_index(drop=True, inplace=True)

    if df.empty or df.shape[1] < min_columns or df.shape[0] < min_rows:
        return None
    else:
        return df


# 若表头均为数字，则取第一行为表头
def change_df(df):
    for item in df.columns:
        if not str(item).isdigit():
            return df
    arr = df.values
    new_df = pd.DataFrame(arr[1:, 1:], index=arr[1:, 0], columns=arr[0, 1:])
    new_df.index.name = arr[0, 0]
    return new_df


iter_time = 0


# 对第一行进行检验
def first_column_check(df):
    global iter_time
    if df is None or df.empty:
        return None
    elif df.empty:
        return None
    if iter_time <= 10:
        if str(df.iat[0, 0]).isdigit() or '.' in str(df.iat[0, 0]) or '.' in str(df.iat[0, 0]) or str(
                df.iat[0, 0]) == '':
            new_index_list = []
            for item in df.columns[1:]:
                new_index_list.append(item)
            new_index_list.append(df.columns[0])
            df = df[new_index_list]
            iter_time += 1
            return first_column_check(df)
    iter_time = 0
    return df


# 对表头做校验
def index_check(df):
    if df is None or df.empty:
        return None
    elif df.empty:
        return None
    new_index_list = []
    if '名' in df.columns[0] or '标题' in df.columns[0]:
        return df
    if '日期' in df.columns[0] or '时间' in df.columns[0] or '年' in df.columns[0] or '数' in df.columns[0]:
        for item in df.columns[1:]:
            new_index_list.append(item)
        new_index_list.append(df.columns[0])
        df = df[new_index_list]
    for df_index in df.columns:
        if '名' in df_index or '标题' in df_index:
            new_index_list = [df_index]
            for item in df.columns:
                if item != df_index:
                    new_index_list.append(item)
            df = df[new_index_list]
            return df
    return df
