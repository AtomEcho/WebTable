import time
from opencc import OpenCC
import logging
from bs4 import BeautifulSoup
# 若通过 from webtable.webtable import table_crawler 使用本函数：
from .process.clean_process import *
from .process.export_process import export
from .process.crawl_process import *
# 若直接运行webtable.py，请使用下面三行而不是上面的三行
# from process.clean_process import *
# from process.export_process import export
# from process.crawl_process import *

logging.captureWarnings(True)  # 去掉建议使用SSL验证的显示


def clean(df):
    columns = list(df.columns)
    if '备注' in set(columns):
        df = df.drop(columns=['备注'])
    for col in columns:
        if 'Unnamed' in col:
            df = df.rename(columns={col: ''})
        elif isinstance(col, tuple):
            length = len(col)
            df = df.drop(index=list(range(length - 1)))
            break
        elif '[' in col:
            new_col = re.sub('\[.+\]', '', col)
            df = df.rename(columns={col: new_col})
        elif len(col) > 100:
            df = df.rename(columns={col: col.split('.')[0]})
    return df


def tradition_to_simple(df):
    if df is None or df.empty:
        return None
    cc = OpenCC('t2s')
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            df.iat[i, j] = cc.convert(str(df.iat[i, j]))
    new_df_columns = []
    for item in df.columns:
        new_df_columns.append(cc.convert(str(item)))
    df.columns = new_df_columns
    return df


def table_crawler(io: str, table_name: str = 'table', option: str = 'stdout', output_file_path: str = './',
                  origin: bool = False,
                  json_orient: str = "columns", engine: str = 'requests', debug: bool = False, process_list=None,
                  max_empty_percentage: float = 0.3,
                  min_similarity: float = 0.7, min_columns: int = 1, min_rows: int = 1, if_tradition_to_simple: bool = False):
    """
    从网页中获取规范化表格
    :param if_tradition_to_simple:是否将繁体字转化为简体字
    :param io: url，或者是html
    :param table_name: 表格的存储名称
    :param output_file_path: 输出文件的路径
    :param option: 表格的输出格式，可选值有：  'stdout','csv','excel','json'
    :param origin: 是否输出原始数据, 默认为False
    :param json_orient: 若选择导出为JSON，设置索引字段. 'columns'：列名作为json索引,'index'：行名作为json索引,，默认为'columns'
    :param engine: 选择获取网页数据的方式,可选requests， pyppeteer， selenium
    :param debug: 是否打印调试信息
    :param process_list: 处理表格过程中所经历的流程
    :param min_similarity: 表示要使两个表格被合并成一个表格，二者的表头需要的最小相似程度，默认为0.7
    :param max_empty_percentage: 表示一列中能够接受的空值个数的最大百分比， 默认为0.3
    :param min_columns: 一个表格中应该含有的最少列数，默认为1
    :param min_rows: 一个表格中应该含有的最少行数，默认为1
    """
    if process_list is None:
        process_list = ['brackets_remove', 'change_df', 'empty_column_remove', 'muti_index_process',
                        'first_column_check', 'index_check']
    time_start = time.time()
    html = None

    if BeautifulSoup(io, "html.parser").find():
        html = io
    elif engine == 'requests':
        html = crawler_html(io)
    elif engine == 'selenium':
        html = crawler_html_selenium(io)
    elif engine == 'pyppeteer':
        get_future = asyncio.ensure_future(crawler_html_pyppeteer(io))
        html = asyncio.get_event_loop().run_until_complete(get_future)

    if if_tradition_to_simple:
        cc = OpenCC('t2s')
        simple_query = cc.convert(table_name)
    else:
        simple_query = table_name

    try:
        html_data = pd.read_html(html)
    except Exception as e:
        print(e)
        return
    table_list = []
    # 去除相同的dataframe
    unrepeated_html_data = []
    if len(html_data) != 0:
        unrepeated_html_data.append(html_data[0])
    for item in html_data:
        repeat_flag = False
        for new_item in unrepeated_html_data:
            if item.equals(new_item):
                repeat_flag = True
                break
        if not repeat_flag:
            unrepeated_html_data.append(item)
    html_data = unrepeated_html_data

    for i, item in enumerate(html_data):
        table_data = pd.DataFrame(item)
        # 原始数据
        if origin:
            print("原始数据：    ")
            print(table_data)
        try:
            table_list.append(clean(table_data))
        except:
            table_list.append(table_data)

    # my processes for table_list

    # 如果列表表头是元组，则取第一项作为表头
    for item in table_list:
        if item is None or item.empty:
            continue
        index_list = []
        for item_index in item.columns:
            if isinstance(item_index, tuple):
                item_index = str(item_index[0])
            index_list.append(item_index)
        item.columns = index_list

    last_item_columns = []
    union_item_list = []
    res_list = []

    # 表格的合并
    for item in table_list:
        if item is None or item.empty:
            continue
        # 繁体转化为简体
        if if_tradition_to_simple:
            item = tradition_to_simple(item)

        # 对能够合并的表格进行合并，此处设置相似度大于70%进行合并
        union_item_columns = list(set(item.columns) & set(last_item_columns))
        similary_value = 2.0 * float(len(union_item_columns)) / (len(item.columns) + len(last_item_columns))
        if similary_value > min_similarity:
            union_item_list.append(item)
        else:
            if len(union_item_list) != 0:
                res_list.append(union_item_list)
            union_item_list = [item]
        last_item_columns = item.columns

    if len(union_item_list) != 0:
        res_list.append(union_item_list)
    table_list = []
    for item in res_list:
        table_list.append(pd.concat(item, ignore_index=True))

    # 对表格进行清洗
    clean_table_list = []
    for item in table_list:
        if item is None or item.empty:
            continue
        new_item = None
        try:
            if debug:
                print("开始清洗表格：")
            if 'brackets_remove' in process_list:
                new_item = brackets_remove(item)
            if debug:
                print("移除冗余括号，得到：  ")
                print(new_item)
            if 'change_df' in process_list:
                new_item = change_df(new_item)
            if 'empty_column_remove' in process_list:
                new_item = empty_column_remove(new_item, max_empty_percentage=max_empty_percentage,
                                               min_columns=min_columns, min_rows=min_rows)
            if debug:
                print("去除空列和信息过少的列，将数字表头删去，得到：  ")
                print(new_item)
            if 'muti_index_process' in process_list:
                new_item = muti_index_process(new_item, min_columns=min_columns, min_rows=min_rows)
            if debug:
                print("合并多行表头，得到：  ")
                print(new_item)
            if 'first_column_check' in process_list:
                new_item = first_column_check(new_item)
            if debug:
                print("对第一行信息进行校验，得到：  ")
                print(new_item)
            if 'index_check' in process_list:
                new_item = index_check(new_item)
            if debug:
                print("对表头信息进行校验，得到：  ")
                print(new_item)
        except Exception as e:
            if debug:
                print("when processing tables:  ", e)
        if new_item is not None:
            clean_table_list.append(new_item)
    table_list = clean_table_list

    export(table_list, table_name, option, output_file_path, simple_query, json_orient)

    time_end = time.time()
    if debug:
        print("共计用时：" + str(time_end - time_start) + 's')


if __name__ == '__main__':
    table_crawler('https://baike.baidu.com/item/%E5%85%83%E7%B4%A0%E5%91%A8%E6%9C%9F%E8%A1%A8/282048', origin=True,
                  engine="pyppeteer", option="stdout", debug=True)
