import os
import sys


def export(table_list: list, table_name: str, option: str, output_file_path: str, simple_query: str,
           json_orient: str = 'columns'):
    """以标准输出流或文件形式导出"""
    if len(table_list) == 0:
        print("No table found with table_name: " + table_name + " !")
    else:
        if option == 'stdout':
            print("共计" + str(len(table_list)) + "张表格： ")
            for item in table_list:
                print(item)
        elif option == 'csv':
            if len(table_list) == 1:
                table_list[0].to_csv(output_file_path + str(simple_query).replace('/', '_') + '.csv', encoding='utf-8',
                                     index=False)
            else:
                i = 0
                for item in table_list:
                    i += 1
                    item.to_csv(output_file_path + str(simple_query).replace('/', '_') + '_' + str(i) + '.csv',
                                encoding='utf-8', index=False)
        elif option == 'excel':
            if len(table_list) == 1:
                table_list[0].to_excel(output_file_path + str(simple_query).replace('/', '_') + '.xlsx',
                                       encoding='utf-8',
                                       index=False)
            else:
                i = 0
                for item in table_list:
                    i += 1
                    item.to_excel(output_file_path + str(simple_query).replace('/', '_') + '_' + str(i) + '.xlsx',
                                  encoding='utf-8', index=False)
        elif option == 'json':
            if len(table_list) == 1:
                table_list[0].to_json(output_file_path + str(simple_query).replace('/', '_') + '.json',
                                      force_ascii=False,
                                      orient=json_orient)
            else:
                i = 0
                for item in table_list:
                    i += 1
                    item.to_json(output_file_path + str(simple_query).replace('/', '_') + '_' + str(i) + '.json',
                                 force_ascii=False, orient=json_orient)
