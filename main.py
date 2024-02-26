import re
import pandas as pd
import math as m
from openpyxl.workbook import Workbook
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from scipy.sparse import csr_matrix

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

    return (fi_min, fi_max, fi_max - fi_min)

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
def rotate_df(param_df, rotate_angle):
    df = param_df[["x", "R", "fi", "total-temperature"]].copy()

    df["fi"] = df["fi"] + rotate_angle

    df.insert(1, "y", round(param_df["z"] * np.sin(rotate_angle) + param_df["y"] * np.cos(rotate_angle), 8))
    df.insert(2, "z", round(param_df["z"] * np.cos(rotate_angle) - param_df["y"] * np.sin(rotate_angle), 8))

    return df

# Получение нужного сектора
# def get_sector_data(param_df, fi_start, sector_angle):
#     fi_s = fi_start * np.pi / 180
#     fi_e = (fi_start + sector_angle) * np.pi / 180
#     df = param_df[param_df["fi"].between(fi_s, fi_e)]
#
#     return df

# Определение координат
def calculate_coord(fi_start, sector_angle, r_min, r_max, radial_num_pts, theta_num_pts, x_coord):
    fi_start_rad = fi_start * np.pi / 180
    sector_angle_rad = sector_angle * np.pi / 180
    df = pd.DataFrame(columns=['R','fi', 'x', 'y', 'z'])

    radius = list()
    for i in range(radial_num_pts + 1):
        radius.append(r_min + (r_max - r_min) * (i) / (radial_num_pts))

    fi = list()
    for i in range(theta_num_pts + 1):
        fi.append(fi_start_rad + sector_angle_rad * i / theta_num_pts)

    for i in range(len(fi)):
        for j in range(len(radius)):

            y_coord = radius[j] * np.sin(fi[i])
            z_coord = radius[j] * np.cos(fi[i])

            row = {'R': radius[j], 'fi': fi[i],
                   'x': x_coord, 'y': y_coord, 'z': z_coord}
            df.loc[len(df)] = row

    return df

# Определение температуры в точках выходного DataFrame
def get_temperature(input_df, output_df, search_rad = 0.005):
    temperature = list()

    for param in output_df.iterrows():
        df = param_df.copy()
        df.insert(0, "distance", round(((df['y'] - param[1]['y'])**2 + (df['z'] - param[1]['z'])**2)**0.5, 8))
        df = df[df["distance"].between(0.0, search_rad)].sort_values(["distance"])

        if len(df["distance"].tolist()) > 4:
            df = df.head(4)

        temperature.append(df["total-temperature"].mean())

    output_df.insert(0, "total-temperature", temperature)

    return output_df




param_df = prepare_dataframe("./input-data/tvd4_outlet.prof")
param_df = calculate_polar_coord(param_df)

fi_min, fi_max, sector_angle = determine_sector_angle(param_df, 0.5)

fi_start = float(285.0)
sector_angle = float(30.0)

r_min_data = min(param_df["R"].tolist())
r_max_data = max(param_df["R"].tolist())

radial_num_pts = int(25)
theta_num_pts = int(25)
x_coord = float(-0.2753)

df_param = calculate_coord(fi_start, sector_angle,
                           r_min_data, r_max_data,
                           radial_num_pts, theta_num_pts,
                           x_coord)

df_param = get_temperature(param_df, df_param)


fig = plt.figure()
ax = fig.add_subplot()

# ax.scatter(param_df["z"], param_df["y"], c = param_df["total-temperature"], cmap = 'jet', label="input-data", s=1, marker="o")
ax.scatter(df_param["z"], df_param["y"], c = df_param["total-temperature"], cmap = 'jet', label="output-data", s=4, marker="s")


plt.show()

print("complete")
# print(radius, len(radius))
# print(r_min_data, r_max_data)
# print(fi, len(fi))
# print(fi_start * np.pi / 180, (fi_start + sector_angle) * np.pi / 180)

# param_df = param_df.astype(np.float16)
# print(param_df.dtypes)
# x, y = np.meshgrid(param_df["z"].tolist(), param_df["y"].tolist())
# z = np.meshgrid(param_df["total-temperature"].tolist(), param_df["total-temperature"].tolist())[0]

# fig, dens = plt.subplots()
# mpl.set_memory_limit(10000)
# dens.contour(x,y,z)
# plt.savefig("fig.png")
# plt.show()



# z_y_t = [param_df["z"].tolist(),
#          param_df["y"].tolist(),
#          param_df["total-temperature"].tolist()]

# z_y_t = [param_df["total-temperature"].tolist()]

# csr_z_y_t = csr_matrix(z_y_t)
# x, y, t = np.meshgrid(param_df["z"].tolist(), param_df["y"], param_df["total-temperature"].tolist())
# print(z_y_t[x, y].A[15])
#
# print(z_y_t[x, y].A[2005])
#
# fig, dens = plt.subplots()
# dens.contourf(x, y, t, levels = 11)
# plt.show()


# rot_param_df_1 = rotate_df(param_df, rotate_angle = sector_angle)
# rot_param_df_2 = rotate_df(param_df, rotate_angle = sector_angle * 2)
# rot_param_df_3 = rotate_df(param_df, rotate_angle = sector_angle * 3)
# rot_param_df_4 = rotate_df(param_df, rotate_angle = sector_angle * 4)
# rot_param_df_5 = rotate_df(param_df, rotate_angle = sector_angle * 5)
# rot_param_df_6 = rotate_df(param_df, rotate_angle = sector_angle * 6)
# rot_param_df_7 = rotate_df(param_df, rotate_angle = sector_angle * 7)
# rot_param_df_8 = rotate_df(param_df, rotate_angle = sector_angle * 8)
#
# number_of_sectors = m.pi * 2 / sector_angle
#
# fig = plt.figure()
# ax = fig.add_subplot()
# ax.scatter(param_df["z"], param_df["y"], c = param_df["total-temperature"], cmap = 'jet', label="input_data", s=8, marker="o")
# ax.scatter(rot_param_df_1["z"], rot_param_df_1["y"], c = param_df["total-temperature"], cmap = 'jet', label="input_data", s=8, marker="o")
# ax.scatter(rot_param_df_2["z"], rot_param_df_2["y"], c = param_df["total-temperature"], cmap = 'jet', label="input_data", s=8, marker="o")
# ax.scatter(rot_param_df_3["z"], rot_param_df_3["y"], c = param_df["total-temperature"], cmap = 'jet', label="input_data", s=8, marker="o")
# ax.scatter(rot_param_df_4["z"], rot_param_df_4["y"], c = param_df["total-temperature"], cmap = 'jet', label="input_data", s=8, marker="o")
# ax.scatter(rot_param_df_5["z"], rot_param_df_5["y"], c = param_df["total-temperature"], cmap = 'jet', label="input_data", s=8, marker="o")
# ax.scatter(rot_param_df_6["z"], rot_param_df_6["y"], c = param_df["total-temperature"], cmap = 'jet', label="input_data", s=8, marker="o")
# ax.scatter(rot_param_df_7["z"], rot_param_df_7["y"], c = param_df["total-temperature"], cmap = 'jet', label="input_data", s=8, marker="o")
# ax.scatter(rot_param_df_8["z"], rot_param_df_8["y"], c = param_df["total-temperature"], cmap = 'jet', label="input_data", s=8, marker="o")
#
# plt.show()

# fig = plt.figure()
# ax = fig.add_subplot(projection='3d')
# ax.scatter(param_df["z"], param_df["y"], param_df["total-temperature"], label="input_data", s=1.0, marker="o")
# plt.show()
#
# ax = fig.add_subplot()
# ax.tricontourf(param_df["z"], param_df["y"], param_df["total-temperature"], color="hsv")
#
# plt.show()



