import re
import pandas as pd

# Подготовка данных в виде DataFrame для дальнейших расчетов
def prepare_dataframe(path_file):
    file_data = str()   # Переменная для информации из файла
    file_list = list()  # Переменная для разбиения по отдельным строкам файла
    param_dict = dict() # Словарь для описания параметров

    with open(path_file, "r") as file:
        file_data = file.read()

    point_number = int(file_data.splitlines()[0].split(' ')[2].split(')')[0]) # Кол-во тчк

    match_end = re.findall("\)\\n", file_data)

    for i in range(len(match_end)):
        if i == 0:
            file_list = file_data.split(match_end[i])
        else:
            file_list.append(file_list[-1].split(match_end[i])[-1])

    for l in file_list:
        if len(l.splitlines()) >= point_number:
            param_dict[l.splitlines()[0].split('(')[1]] = l.splitlines()[1:-1]

    param_df = pd.DataFrame(data=param_dict)

    return param_df

# Определение координат ПСК
def calculate_polar_coord(param_df):
    pass

param_df = prepare_dataframe("./input-data/tvd4_outlet.prof")