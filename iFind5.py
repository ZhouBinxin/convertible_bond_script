import numpy as np
import pandas as pd
from iFinDPy import *
import datetime
import time
import json


class FileHandler:
    def __init__(self):
        self.directory_path = 'data'
        # 判断目录是否存在，如果不存在则创建
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path)
            print(f'创建文件夹 {self.directory_path}')

    # 保存数据到Excel
    def save_to_excel(self, file_name, str_date, premium):
        print(f'{str_date} 数据保存中...')
        while True:
            try:
                if not os.path.exists(file_name):
                    data = {"日期": [str_date], "转股溢价率%": [premium]}
                    df = pd.DataFrame(data)
                else:
                    df = pd.read_excel(file_name)
                    new_data = pd.DataFrame({"日期": [str_date], "转股溢价率%": [premium]})
                    df = pd.concat([df, new_data], ignore_index=True)

                df.to_excel(file_name, index=False)
                break  # 如果成功写入，跳出循环
            except PermissionError:
                print(f"请关闭文件 '{file_name}'")
                time.sleep(5)

    def save_to_json(self, ths_date, data):
        json_file_path = f'data/{ths_date}.json'
        # 将数据列表保存为JSON文件
        with open(json_file_path, 'w') as json_file:
            json.dump(data, json_file, indent=2)

        print(f'数据已保存到 {json_file_path}')


class Ths:
    # 登录函数
    def login(self, username, password):
        thsLogin = THS_iFinDLogin(username, password)
        if thsLogin != 0:
            print('登录失败')
        else:
            print('登录成功')

    # 获取债券余额数据和债券评级
    def get_bond(self, jydm, ths_date, consider_balance, consider_issue):
        data_balances = []
        data_issues = []

        filename = ths_date[:4] + ths_date[5:7] + ths_date[8:]
        json_file_path = f'data/{filename}.json'

        # 从文件读取 JSON 数据
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if "ths_bond_balance_cbond" not in data[0]:
            print(f'{ths_date} 债券余额数据和债券评级')
            jydm = ', '.join(jydm)

            # ths_bond_balance_cbond债券余额数据 ths_issue_credit_rating_cbond债券评级
            bond_data = THS_DS(jydm, 'ths_bond_balance_cbond;ths_issue_credit_rating_cbond', ';', '', ths_date,
                               ths_date, 'format:list')

            if bond_data.data is None:
                print(bond_data.errmsg)

            for item in bond_data.data:
                table = item.get('table', {})
                ths_bond_balance_cbond = table.get('ths_bond_balance_cbond', [])
                ths_issue_credit_rating_cbond = table.get('ths_issue_credit_rating_cbond', [])

                if isinstance(ths_bond_balance_cbond, list) and ths_bond_balance_cbond:
                    data_balances.append(ths_bond_balance_cbond[0])
                else:
                    data_balances.append(None)

                if isinstance(ths_issue_credit_rating_cbond, list) and ths_issue_credit_rating_cbond:
                    data_issues.append(ths_issue_credit_rating_cbond[0])
                else:
                    data_issues.append(None)

            data[0]["ths_bond_balance_cbond"] = data_balances
            data[0]["ths_issue_credit_rating_cbond"] = data_issues

            # 将修改后的数据写回文件
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        else:
            print(f'{ths_date} 文件读取债券余额/债券评级')
            with open(json_file_path, 'r') as json_file:
                data = json.load(json_file)

            if consider_balance:
                data_balances = data[0]["ths_bond_balance_cbond"]
            if consider_issue:
                data_issues = data[0]["ths_issue_credit_rating_cbond"]
        return data_balances, data_issues

    # 获取数据
    def get_data_basics(self, start_date, end_date):
        file_handler = FileHandler()
        data_list = []
        print("基本数据获取")

        for current_date in range((end_date - start_date).days + 1):
            current_date = start_date + timedelta(days=current_date)

            if current_date.weekday() in [5, 6]:
                data_list.append((current_date.strftime("%Y-%m-%d"), None))
                continue

            edate = current_date.strftime("%Y%m%d")
            json_file_path = f'data/{edate}.json'

            if os.path.exists(json_file_path):
                # 指定JSON文件路径
                print(f'{current_date} 文件读取')
                # 从JSON文件读取数据
                with open(json_file_path, 'r') as json_file:
                    data = json.load(json_file)

                data_list.append((current_date.strftime("%Y-%m-%d"), data))
            else:
                print(f'{current_date} 接口获取')
                get_str = 'edate=' + edate + ';zqlx=全部'
                # jydm交易代码 f027转换价值 f022转股溢价率
                data = THS_DR('p00868', get_str, 'jydm:Y,p00868_f027:Y,p00868_f022:Y', 'format:list')
                if data.data is None:
                    print(data.errmsg)
                    data_list.append((current_date.strftime("%Y-%m-%d"), None))
                else:
                    file_handler.save_to_json(edate, data.data)
                    data_list.append((current_date.strftime("%Y-%m-%d"), data.data))

        return data_list


class CPR:
    # 计算中位数
    def calculate_median(self, data, ths_date):
        ths = Ths()
        # 转换价值
        consider_value = False
        max_value = 120
        min_value = 100

        # 债券余额范围，单位为亿
        consider_balance = True
        max_balance = 10
        min_balance = 3

        # 债券评级
        consider_issue = True
        issue = "AA+"

        float_values = []

        data_jydm = data['jydm']
        data_f022 = data['p00868_f022']
        data_f027 = data['p00868_f027']

        data_balance = data_issue = None

        data_balances, data_issues = ths.get_bond(data_jydm, ths_date, consider_balance, consider_issue)

        for i in range(len(data_jydm)):
            f027 = data_f027[i]
            f022 = data_f022[i]
            if '--' in f027 or '--' in f022:
                continue

            if consider_balance:
                if len(data_balances) == 0:
                    continue
                else:
                    data_balance = data_balances[i]
                    if data_balance is None:
                        continue

            if consider_issue:
                if len(data_issues) == 0:
                    continue
                else:
                    data_issue = data_issues[i]
                    if data_issue is None:
                        continue

            f027_value = float(f027)
            f022_value = float(f022)

            value_condition = (not consider_value) or (min_value < f027_value <= max_value)
            balance_condition = (not consider_balance) or (min_balance < data_balance <= max_balance)
            issue_condition = (not consider_issue) or (data_issue == issue)

            if value_condition and balance_condition and issue_condition:
                float_values.append(f022_value)

        return np.median(float_values) if float_values else ""


# 主函数
def main():
    ths = Ths()
    file_handler = FileHandler()
    cpr = CPR()
    username = ""
    password = ""
    ths.login(username, password)

    start_date = datetime.date(2024, 1, 10)
    end_date = datetime.date(2024, 1, 10)
    data_basics = ths.get_data_basics(start_date, end_date)

    for ths_date, data_basic in data_basics:
        median_value = None
        if data_basic is not None:
            median_value = cpr.calculate_median(data_basic[0]['table'], ths_date)
        if median_value is None:
            median_value = ''
        file_handler.save_to_excel("转股溢价率记录.xlsx", ths_date, median_value)


if __name__ == '__main__':
    main()
