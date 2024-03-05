import re
import pandas as pd
import math as m
from openpyxl.workbook import Workbook

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import sys
import numpy as np

#region Func
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
def calculate_polar_coord(param_df, radial_axis, theta_axis):
    param_df.insert(0, "R", round((param_df[theta_axis]**2 + param_df[radial_axis]**2)**0.5, 8))

    coord_x = param_df[radial_axis].tolist()
    coord_y = param_df[theta_axis].tolist()
    fi = list()

    for i in range(len(coord_x)):
        if coord_x[i] >= 0:
            if coord_y[i] >= 0:
                fi.append(round(m.atan(coord_y[i] / coord_x[i]), 8))
            else:
                fi.append(round(m.atan(coord_y[i] / coord_x[i]) + 2 * np.pi, 8))
        else:
            if coord_y[i] >= 0:
                fi.append(round(m.atan(coord_y[i] / coord_x[i]) + np.pi, 8))
            else:
                fi.append(round(m.atan(coord_y[i] / coord_x[i]) + np.pi, 8))

    param_df.insert(1, "fi", fi)

    param_df = param_df.sort_values(["fi"])

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

    return np.abs(fi_max - fi_min)

# Определение угла минимального сектора
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

    return (round(min(fi_max) - max(fi_min), 8), max(fi_min), min(fi_max))

# Поворот сектора
def rotate_df(param_df, rotate_angle, parameter="total-temperature", axial_axis="x", radial_axis="y", theta_axis="z"):
    df = param_df[[axial_axis, "R", "fi", parameter]].copy()

    df["fi"] = df["fi"] + rotate_angle

    df.insert(1, theta_axis, round(param_df[radial_axis] * np.cos(rotate_angle) + param_df[theta_axis] * np.sin(rotate_angle), 8))
    df.insert(2, radial_axis, round(param_df[radial_axis] * np.sin(rotate_angle) - param_df[theta_axis] * np.cos(rotate_angle), 8))

    return df

# Определение координат
def calculate_coord(fi_start, sector_angle, r_min, r_max, radial_num_pts, theta_num_pts, axial_coord,
                    axial_axis="x", radial_axis="y", theta_axis="z"):
    fi_start_rad = fi_start * np.pi / 180
    sector_angle_rad = sector_angle * np.pi / 180
    df = pd.DataFrame(columns=['R','fi', axial_axis, radial_axis, theta_axis])

    radius = list()
    for i in range(radial_num_pts):
        radius.append(r_min + (r_max - r_min) * (i) / (radial_num_pts - 1))

    fi = list()
    for i in range(theta_num_pts):
        fi.append(fi_start_rad + sector_angle_rad * i / (theta_num_pts - 1))

    for i in range(len(fi)):
        for j in range(len(radius)):

            radial_coord = radius[j] * np.cos(fi[i])
            theta_coord = radius[j] * np.sin(fi[i])

            row = {'R': radius[j],
                   'fi': fi[i],
                   axial_axis: axial_coord,
                   radial_axis: radial_coord,
                   theta_axis: theta_coord}

            df.loc[len(df)] = row

    return df

# Определение температуры в точках выходного DataFrame
def get_temperature(input_df, output_df,  axial_axis="x", radial_axis="y", theta_axis="z", parameter_name="total-temperature"):
    temperature = list()
    # print(input_df)
    for param in output_df.iterrows():
        if "distance" in input_df.columns:
            input_df.drop("distance", axis=1, inplace=True)

        input_df.insert(0, "distance", round(((input_df[radial_axis] - param[1][radial_axis])**2 + (input_df[theta_axis] - param[1][theta_axis])**2)**0.5, 8))
        input_df = input_df.sort_values(["distance"])
        temperature.append(input_df.head(4)[parameter_name].mean())
        input_df.drop("distance", axis= 1 , inplace= True)

    output_df.insert(0, parameter_name, temperature)

    return output_df

# Определение исходного датафрейма с которым необходимо работать
def get_input_data(path_file, axial_axis="x", radial_axis="z", theta_axis="y"):
    df = prepare_dataframe(path_file)
    df = calculate_polar_coord(df, radial_axis, theta_axis)
    return df

# Определение осей в эпюре
def get_axis(input_text):
    axis = dict()
    axis["axial"] = input_text.split(", ")[0]
    axis["radial"] = input_text.split(", ")[1]
    axis["theta"] = input_text.split(", ")[2]

    return axis

# Определение количества секторов
def get_sector_num(df, relative_height_percent):
    sector_angle = determine_sector_angle(df, relative_height_percent)
    sector_number = int(2 * np.pi / sector_angle)
    return sector_number

# Определение полноокружной эпюры
def get_full_circle_input_data(df, number_of_sectors,
                               parameter="total-temperature", axial_axis="x", radial_axis="y", theta_axis="z"):
    full_circle_df = pd.DataFrame()
    for i in range(number_of_sectors):
        full_circle_df = full_circle_df._append(rotate_df(df, np.pi * 2 / number_of_sectors * i,
                                                parameter,
                                                axial_axis,
                                                radial_axis,
                                                theta_axis))

    return full_circle_df

# Получение выходной эпюры
def get_output_data(input_df, fi_start, sector_angle,
                    r_min, r_max,
                    radial_num_pts, theta_num_pts,
                    x_coord=0.0,
                    axial_axis="x", radial_axis="y", theta_axis="z", parameter_name="total-temperature"):
    df = calculate_coord(fi_start, sector_angle,
                         r_min, r_max,
                         radial_num_pts, theta_num_pts,
                         x_coord,
                         axial_axis, radial_axis, theta_axis)
    df = get_temperature(input_df, df, axial_axis, radial_axis, theta_axis, parameter_name)
    return df

# Очистка DataFrame
def clear_df(df):
    columns_name = list()
    for column_name in df.columns:
        columns_name.append(str(column_name))

    for c_name in columns_name:
        df.drop(columns=c_name)

    return df

# Отмасштабированная эпюра
def get_scale_field(df, new_r_max, new_r_min, radial_axis="y", theta_axis="z"):
    r_max = max(df['R'].tolist())
    r_min = min(df['R'].tolist())

    if "relative_height" in df.columns.values.tolist():
        df["relative_height"] = round((df['R'] - r_min)/(r_max - r_min), 8)
    else:
        df.insert(0, "relative_height", round((df['R'] - r_min)/(r_max - r_min), 8))

    df['R'] = (new_r_max - new_r_min) * df['relative_height'] + new_r_min
    df[radial_axis] = df['R'] * np.cos(df['fi'])
    df[theta_axis] = df['R'] * np.sin(df['fi'])

    return df



#endregion