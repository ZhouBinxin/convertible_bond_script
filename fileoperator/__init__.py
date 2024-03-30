import os
import time

import pandas as pd

from . import cloud
from .cloud import CloudClient


class FileOperator:
    def __init__(self, file_path):
        self.file_path = file_path

    @classmethod
    def save_to_excel(cls, excel_name, data):
        """
        保存数据到Excel文件

        :param excel_name: Excel文件名
        :param data: 数据
        :return:
        """
        file_path = os.path.join(os.getcwd(), f'{excel_name}.xlsx')

        max_attempts = 5
        attempt = 1

        while attempt <= max_attempts:
            try:
                # 检查文件是否存在
                if os.path.exists(file_path):
                    # 如果文件存在，读取现有数据
                    df = pd.read_excel(file_path)
                    # 添加新的数据
                    new_data_df = pd.DataFrame(data)
                    df = pd.concat([df, new_data_df], ignore_index=True)

                else:
                    # 如果文件不存在，创建新的DataFrame
                    df = pd.DataFrame(data)

                # 保存DataFrame到Excel
                df.to_excel(file_path, index=False)
                print('数据保存成功')
                break
            except Exception as e:
                print(f"无法写入文件 '{excel_name}'.xlsx，请确保没有其他程序正在使用该文件。错误详情：{e}")

                if attempt < max_attempts:
                    print(f"尝试重新写入，剩余尝试次数: {max_attempts - attempt}")
                    attempt += 1
                    time.sleep(5)
                else:
                    print("写入文件失败")
                    print(data)
                    break

    @classmethod
    def upload(cls, local_file):
        CloudClient.upload(local_file)
