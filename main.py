import json
import os
from datetime import datetime, timedelta

import requests
from tqdm import tqdm

from bondday import BondDay
from fileoperator import FileOperator


def main():
    # 配置文件地址
    config_list = [

    ]

    # 配置文件目录
    src_dir = 'config'
    file_list = os.listdir(src_dir)
    for file in file_list:
        if file.endswith('.json'):
            config_list.append(os.path.join(src_dir, file))

    # 错误监控
    send_error = True

    for config_file in config_list:
        print(f'{config_file}')
        try:
            parse(config_file)
        except Exception as e:
            if send_error:
                cf_worker(f'{config_file}\n' + str(e))
            else:
                print(e)


def parse(config_file):
    # 读取JSON配置文件
    with open(config_file, 'r', encoding='utf-8') as file:
        config = json.load(file)

    # 起始日期
    start_date_str = config['start_date']
    start_date = datetime.strptime(start_date_str, "%Y%m%d")
    # 结束日期
    end_date_str = config["end_date"]
    end_date = datetime.strptime(end_date_str, "%Y%m%d")

    ctype = config["ctype"]
    column = config["column"]

    # 文件名
    excel_name = config["file_name"]
    file_name_format = config["file_name_format"]

    # 筛选条件
    conditions = config["conditions"]
    if conditions["limit"] != -1:
        RED = '\033[91m'
        RESET = '\033[0m'

        print(RED + f"仅返回前{conditions['limit']}条数据" + RESET)

    column_name = config["column_name"]

    # 文件名附加日期
    if file_name_format or not excel_name:
        if start_date == end_date:
            excel_name = excel_name + start_date_str
        else:
            excel_name = excel_name + start_date_str + "~" + end_date_str

    # 设置列名
    try:
        data_list = [column_name[ctype]]
    except KeyError:
        print("不存在方法：", ctype)
        return

    BondDay.db_init()

    total_days = (end_date - start_date).days + 1
    with tqdm(total=total_days, desc="进度", dynamic_ncols=True) as pbar:
        for current_date in range(total_days):
            current_date = start_date + timedelta(days=current_date)

            str_date = current_date.strftime('%Y%m%d')
            pbar.set_postfix_str(str_date)

            # 计算数据
            if ctype == "ratio":
                data_tuple = BondDay.ratio(current_date, conditions)
            else:
                if column == "":
                    column = input("请输入列名：")
                data_tuple = BondDay.bond_math(current_date, column, conditions, ctype)

            if data_tuple:
                data_list.append(data_tuple)
            pbar.update(1)

    # 保存数据到Excel
    if len(data_list) > 1:
        FileOperator.save_to_excel(excel_name, data_list)


def cf_worker(message, method='qywx', api_type='default', worker_url='https://qyapi.bxin.top/'):
    # 构建POST请求的数据
    data = {
        'method': method,
        'content': {
            'type': api_type,
            'message': message,
        }
    }

    # 发送POST请求到Cloudflare Worker
    response = requests.post(worker_url, json=data)

    # 检查响应状态码
    if response.ok:
        print('Message sent successfully')
    else:
        print('Failed to send message')


if __name__ == '__main__':
    main()
