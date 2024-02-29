import re
import pandas as pd
import math as m
from openpyxl.workbook import Workbook

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import sys
import numpy as np
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QFileDialog, QMessageBox


class MainWindow(QMainWindow):
    def __init__(self, window = None):
        super(MainWindow, self).__init__()
        loadUi("./ui/main_window.ui", self)
        self.path_file = ""
        self.pushButton_4.clicked.connect(self.openFile)
        self.pushButton_3.clicked.connect(self.calculateInputField)

        self.horizontal_layout_4 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontal_layout_4.setObjectName("horizontal_layout_4")
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.horizontal_layout_4.addWidget(self.canvas)

    def openFile(self):
        self.path_file = QFileDialog.getOpenFileName(self, "Open a file")[0]
        self.lineEdit_4.setText(str(self.path_file))

    def calculateInputField(self):
        if self.path_file != "" and self.lineEdit.text() != "" and self.lineEdit_5.text() != "":
            self.axis = get_axis(str(self.lineEdit.text()))
            self.parameter_name = str(self.lineEdit_5.text())
            self.input_param_field = get_input_data(self.path_file,
                                                    axial_axis=self.axis["axial"],
                                                    radial_axis=self.axis["radial"],
                                                    theta_axis=self.axis["theta"])

            self.number_of_sectors = get_sector_num(self.input_param_field, 0.5)

            self.full_circle_data = get_full_circle_input_data(self.input_param_field, self.number_of_sectors,
                                                               parameter=self.parameter_name,
                                                               axial_axis=self.axis["axial"],
                                                               radial_axis=self.axis["radial"],
                                                               theta_axis=self.axis["theta"])

            self.figure.clear()

            plt.scatter(self.full_circle_data[self.axis["radial"]],
                        self.full_circle_data[self.axis["theta"]],
                        c=self.full_circle_data[self.parameter_name],
                        cmap='jet',
                        s=2,
                        alpha=0.01)
            self.canvas.draw()

        else:
            self.show_msg_box_error(self, "Не все поля заполнены")

    # MessageBox с ошибкой
    def show_msg_box_error(self, error_txt):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(error_txt)
        msg.setWindowTitle("Error")
        msg.exec_()


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
def rotate_df(param_df, rotate_angle, parameter="total-temperature", axial_axis="x", radial_axis="z", theta_axis="y"):
    df = param_df[[axial_axis, "R", "fi", parameter]].copy()

    df["fi"] = df["fi"] + rotate_angle

    df.insert(1, theta_axis, round(param_df[radial_axis] * np.sin(rotate_angle) + param_df[theta_axis] * np.cos(rotate_angle), 8))
    df.insert(2, radial_axis, round(param_df[radial_axis] * np.cos(rotate_angle) - param_df[theta_axis] * np.sin(rotate_angle), 8))

    return df

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
    # print(input_df)
    for param in output_df.iterrows():
        input_df.insert(0, "distance", round(((input_df['y'] - param[1]['y'])**2 + (input_df['z'] - param[1]['z'])**2)**0.5, 8))
        input_df = input_df.sort_values(["distance"])

        temperature.append(input_df.head(4)["total-temperature"].mean())

        input_df.drop("distance", axis= 1 , inplace= True)

    output_df.insert(0, "total-temperature", temperature)

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
                               parameter="total-temperature", axial_axis="x", radial_axis="z", theta_axis="y"):
    full_circle_df = pd.DataFrame()
    for i in range(number_of_sectors):
        full_circle_df = full_circle_df._append(rotate_df(df, np.pi * 2 / number_of_sectors * i,
                                                parameter,
                                                axial_axis,
                                                radial_axis,
                                                theta_axis))

    return full_circle_df



app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
sys.exit(app.exec_())

# param_df = prepare_dataframe("./input-data/prof_Tout_3gor.prof")
# param_df = calculate_polar_coord(param_df)
#
# sector_angle = determine_sector_angle(param_df, 0.5)
#
# sector_num = int(2 * np.pi / sector_angle)
#
# fi_start = float(285.0)
# sector_angle = float(32.5)
# #
# r_min_data = min(param_df["R"].tolist())
# r_max_data = max(param_df["R"].tolist())
# #
# radial_num_pts = int(25)
# theta_num_pts = int(25)
# x_coord = float(-0.2753)
# #
# df_param = calculate_coord(fi_start, sector_angle,
#                            r_min_data, r_max_data,
#                            radial_num_pts, theta_num_pts,
#                            x_coord)
#
# df_param = get_temperature(param_df, df_param)
#
# full_circle_df = pd.DataFrame()
# for i in range(sector_num):
#     full_circle_df = full_circle_df._append(rotate_df(param_df, np.pi * 2 / sector_num * i))




