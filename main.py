import re
import pandas as pd
import math as m
from openpyxl.workbook import Workbook
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

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
    df_heading = param_df.head()

    for head in df_heading:
        param_df[head] = pd.to_numeric(param_df[head])

    return param_df

# Определение координат ПСК
def calculate_polar_coord(param_df):
    param_df.insert(0, "R", round((param_df["z"]**2 + param_df["y"]**2)**0.5, 8))

    coord_x = param_df["z"].tolist()
    coord_y = param_df["y"].tolist()
    fi = list()

    for i in range(len(coord_x)):
        if coord_x[i] >= 0:
            if coord_y[i] >= 0:
                fi.append(round(m.atan(coord_y[i] / coord_x[i]), 8))
            else:
                fi.append(round(m.atan(coord_y[i] / coord_x[i]) + m.pi, 8))
        else:
            if coord_y[i] >= 0:
                fi.append(round(m.atan(coord_y[i] / coord_x[i]) + 2 * m.pi, 8))
            else:
                fi.append(round(m.atan(coord_y[i] / coord_x[i]) + m.pi, 8))

    param_df.insert(1, "fi", fi)

    param_df = param_df.sort_values(["R"])

    return param_df

# Определение угла сектора
def determine_sector_angle(param_df, percent):
    r_max = max(param_df['R'])
    r_min = min(param_df['R'])
    h_sector = r_max - r_min
    delta_h = h_sector * percent / 100
    r_i = r_max - delta_h

    sel_params = param_df[param_df["R"].between(r_i, r_max)].sort_values(["fi"])
    fi_max = max(sel_params['fi'].tolist())
    fi_min = min(sel_params['fi'].tolist())

    return fi_max - fi_min

# Определение углов сектора
def determine_angles(param_df, percent):
    r_max = max(param_df['R'])
    r_min = min(param_df['R'])
    h_sector = r_max - r_min
    delta_h = h_sector * percent / 100

    sel_params = param_df[param_df["R"].between(r_max - delta_h, r_max)].sort_values(["fi"])
    fi_max = [max(sel_params['fi'].tolist())]
    fi_min = [min(sel_params['fi'].tolist())]

    sel_params = param_df[param_df["R"].between(r_min, r_min + delta_h)].sort_values(["fi"])
    fi_max.append(max(sel_params['fi'].tolist()))
    fi_min.append(min(sel_params['fi'].tolist()))

    # return (max(fi_min), min(fi_max))
    return round(min(fi_max) - max(fi_min), 8)

# Поворот сектора
def rotate_df(param_df, rotate_angle):
    df = param_df[["R", "fi", "total-temperature"]].copy()

    df["fi"] = df["fi"] + rotate_angle

    return df



param_df = prepare_dataframe("./input-data/tvd4_outlet.prof")
param_df = calculate_polar_coord(param_df)

sector_angle = determine_sector_angle(param_df, 1)

min_sector_angle = determine_angles(param_df, 1)

number_of_sectors = int(round(m.pi * 2 / min_sector_angle, 0))
print(number_of_sectors)

