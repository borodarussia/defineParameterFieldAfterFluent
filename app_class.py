from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget

from functions import *

from ui.main_window_ver2 import Ui_MainWindow
from ui.selector_window import Ui_Form as Ui_SelectorWidget
from ui.coef_window import Ui_Form as Ui_CoefWidget
from ui.simple_window import Ui_Form as Ui_SimpleWidget
from ui.theta_window import Ui_Form as Ui_ThetaWidget

class MainWindow(QMainWindow, Ui_MainWindow):
    '''
    Оснонвая рабочая область приложения.
    '''
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        # loadUi("./ui/main_window_ver2.ui", self)

        self.coef_window = CoefWindow()
        self.theta_window = ThetaWindow()
        self.simple_window = SimpleWindow()

        self.axis_definition = {"axial" : "x",
                                "radial" : "y",
                                "theta" : "z"}
        self.parameter_field = "total-temperature"
        self.path_file = ""

        self.export_df = pd.DataFrame()

        self.output_layout = QtWidgets.QHBoxLayout(self.frame)
        self.output_layout.setObjectName("output_layout")

        self.selector_window = SelectorWindow()
        self.output_layout.addWidget(self.selector_window)

        self.pBtn_next.clicked.connect(self.next_window)
        self.pBtn_prev.clicked.connect(self.prev_window)

        self.act_open.triggered.connect(self.open_file)
        self.act_save.triggered.connect(self.save_file)
        self.act_exit.triggered.connect(self.close_app)

    def close_app(self):
        sys.exit()

    def save_file(self):
        self.get_export_df()
        self.save_path_file = str(QFileDialog.getSaveFileName(self,
                                                              "Save File",
                                                              "",
                                                              "Excel Files(*.xlsx)")[0])
        if self.save_path_file != "":
            self.export_df.to_excel(self.save_path_file)
        else:
            self.show_msg_box_error("Ошибка")

    def get_export_df(self):
        window_type = self.get_window_at_layout()
        if window_type != "SelectorWindow":
            if window_type == "CoefWindow":
                self.export_df = self.coef_window.export_df
            elif window_type == "ThetaWindow":
                self.export_df = self.theta_window.export_df
            elif window_type == "SimpleWindow":
                self.export_df = self.simple_window.export_df
        else:
            self.show_msg_box_error("Нельзя выполнить сохранение с данной части приложения")

    def open_file(self):
        get_open_filename = QFileDialog.getOpenFileName(self, "Open a file", "", "Prof Files(*.prof)")
        if get_open_filename[0] != "":
            self.path_file = get_open_filename[0]
            self.simple_window.path_file = self.path_file
            self.coef_window.path_file = self.path_file
            self.theta_window.path_file = self.path_file
        else:
            self.show_msg_box_error("Файл не выбран")

    def get_window_at_layout(self):
        if self.output_layout.count() == 1:
            item = self.output_layout.itemAt(0)
            window_type = item.widget().__class__.__name__
            return window_type
    
    def next_window(self):
        window_type = self.get_window_at_layout()
        if window_type == "SelectorWindow":
            if (self.selector_window.lineEdit_axis_definition.text() == ""
                    or self.selector_window.lineEdit_parameter.text() == ""):
                self.show_msg_box_error("Неверно заполнено одно из полей\n-> Оси\n->Параметр")
                return
            self.axis_definition = get_axis(str(self.selector_window.lineEdit_axis_definition.text()))
            self.parameter_field = str(self.selector_window.lineEdit_parameter.text())
            self.output_layout.itemAt(0).widget().deleteLater()
            if self.selector_window.field_type == 1:
                self.theta_window = ThetaWindow()
                self.theta_window.path_file = self.path_file
                self.theta_window.parameter = self.parameter_field
                self.theta_window.axis = self.axis_definition

                self.output_layout.addWidget(self.theta_window)
            elif self.selector_window.field_type == 2:
                self.coef_window = CoefWindow()
                self.coef_window.path_file = self.path_file
                self.coef_window.parameter = self.parameter_field
                self.coef_window.axis = self.axis_definition

                self.output_layout.addWidget(self.coef_window)
            elif self.selector_window.field_type == 3:
                self.simple_window = SimpleWindow()
                self.simple_window.path_file = self.path_file
                self.simple_window.parameter = self.parameter_field
                self.simple_window.axis = self.axis_definition

                self.output_layout.addWidget(self.simple_window)

    def prev_window(self):
        window_type = self.get_window_at_layout()
        if window_type != "SelectorWindow":
            self.output_layout.itemAt(0).widget().deleteLater()
            self.selector_window = SelectorWindow()
            self.output_layout.addWidget(self.selector_window)

    def show_msg_box_error(self, error_txt):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(error_txt)
        msg.setWindowTitle("Error")
        msg.exec_()


class SelectorWindow(QWidget, Ui_SelectorWidget):
    '''
    Окно с выбором необходимого типа расчета поля распределения
    '''
    def __init__(self):
        super(SelectorWindow, self).__init__()
        self.setupUi(self)
        self.field_type = int(1)
        self.rB_theta.toggle()
        self.rB_coef.toggled.connect(self.get_field_export_type)
        self.rB_theta.toggled.connect(self.get_field_export_type)
        self.rB_simple.toggled.connect(self.get_field_export_type)

    def get_field_export_type(self):
        if self.rB_coef.isChecked():
            self.field_type = 2
        elif self.rB_simple.isChecked():
            self.field_type = 3
        elif self.rB_theta.isChecked():
            self.field_type = 1


class ThetaWindow(QWidget, Ui_ThetaWidget):
    '''
    Окно с расчетом через Тету
    '''
    def __init__(self):
        super(ThetaWindow, self).__init__()
        self.setupUi(self)
        # loadUi("./ui/theta_window.ui", self)

        self.axis = dict()
        self.parameter = ""
        self.path_file = ""

        self.btn_draw.clicked.connect(self.get_fulll_circle_df)
        self.btn_check.clicked.connect(self.get_sector_df)
        self.btn_calc.clicked.connect(self.get_export_df)

        self.full_circle_data = pd.DataFrame()
        self.sector_df = pd.DataFrame()
        self.export_df = pd.DataFrame()

        self.layout = QtWidgets.QHBoxLayout(self.frame)
        self.layout.setObjectName("layout_for_plot")
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

    def get_fulll_circle_df(self):
        if self.path_file != "" and self.parameter != "" and len(self.axis.keys()) == 3:
            input_param_field = get_input_data(self.path_file,
                                               axial_axis=self.axis["axial"],
                                               radial_axis=self.axis["radial"],
                                               theta_axis=self.axis["theta"])
            number_of_sectors = get_sector_num(input_param_field, 0.5)

            self.full_circle_data = get_full_circle_input_data(input_param_field, number_of_sectors,
                                                               parameter=self.parameter,
                                                               axial_axis=self.axis["axial"],
                                                               radial_axis=self.axis["radial"],
                                                               theta_axis=self.axis["theta"])
            self.draw_inpt_field()
        else:
            self.show_msg_box_error("Отсутствуют:"
                                    "-> Путь к файлу"
                                    "-> Название параметра"
                                    "-> Название осей")

    def get_sector_df(self):
        if (len(self.numPtsTheta.text()) > 0
                and len(self.numPtsRadius.text()) > 0
                and len(self.startAngle.text()) > 0
                and len(self.sectorAngle.text()) > 0):
            fi_start = self.startAngle.text()
            sector_angle = self.sectorAngle.text()
            radial_num_pts = self.numPtsRadius.text()
            theta_num_pts = self.numPtsTheta.text()

            if len(self.sector_df.columns) > 0:
                self.sector_df = clear_df(self.sector_df)
                self.draw_inpt_field()

            self.sector_df = get_output_data(input_df=self.full_circle_data,
                                             r_min=min(self.full_circle_data["R"].tolist()),
                                             r_max=max(self.full_circle_data["R"].tolist()),
                                             fi_start=float(fi_start),
                                             sector_angle=float(sector_angle),
                                             radial_num_pts=int(radial_num_pts),
                                             theta_num_pts=int(theta_num_pts),
                                             axial_axis=self.axis["axial"],
                                             radial_axis=self.axis["radial"],
                                             theta_axis=self.axis["theta"],
                                             parameter_name=self.parameter)

            self.sector_df = self.sector_df.sort_values(["R"])
            self.draw_calc_field()
        else:
            self.show_msg_box_error(self, "Введите параметры для определения выходного поля")

    def get_export_df(self):
        if (self.shrRadius.text() != ""
                and self.hubRadius.text() != ""
                and self.lineEdit_prm3.text() != ""
                and self.lineEdit_prm4.text() != ""
                and self.lineEdit_newPrm3.text() != ""
                and self.lineEdit_newPrm4.text() != ""):

            self.export_df = get_scale_field(self.sector_df,
                                             new_r_max=float(self.shrRadius.text()),
                                             new_r_min=float(self.hubRadius.text()),
                                             radial_axis=self.axis["radial"],
                                             theta_axis=self.axis["theta"])

            prm3 = float(self.lineEdit_prm3.text())
            prm4 = float(self.lineEdit_prm4.text())
            new_prm3 = float(self.lineEdit_newPrm3.text())
            new_prm4 =  float(self.lineEdit_newPrm4.text())

            self.export_df[self.parameter] = (self.export_df[self.parameter] - prm3)/(prm4 - prm3) * (new_prm4 - new_prm3) + new_prm4
        else:
            self.show_msg_box_error("Не заполнены следующие параметры:"
                                    "-> Периферийный радиус"
                                    "-> Втулочный радиус"
                                    "-> Параметры для пересчета поля параметров")

    def draw_inpt_field(self):
        self.figure.clear()
        plt.scatter(self.full_circle_data[self.axis["radial"]],
                    self.full_circle_data[self.axis["theta"]],
                    c=self.full_circle_data[self.parameter],
                    cmap='jet',
                    s=1,
                    alpha=0.05)
        plt.colorbar(orientation="vertical")
        self.canvas.draw()

    def draw_calc_field(self):
        plt.scatter(self.sector_df[self.axis["radial"]],
                    self.sector_df[self.axis["theta"]],
                    color="red",
                    marker="+",
                    s=3,
                    alpha=1)
        self.canvas.draw()

    def show_msg_box_error(self, error_txt):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(error_txt)
        msg.setWindowTitle("Error")
        msg.exec_()


class SimpleWindow(QWidget, Ui_SimpleWidget):
    '''
    Окно с упрощением поля
    '''
    def __init__(self):
        super(SimpleWindow, self).__init__()
        self.setupUi(self)
        # loadUi("./ui/simple_window.ui", self)

        self.axis = dict()
        self.parameter = ""
        self.path_file = ""

        self.btn_draw.clicked.connect(self.get_fulll_circle_df)
        self.btn_check.clicked.connect(self.get_sector_df)
        self.btn_calc.clicked.connect(self.get_export_df)

        self.full_circle_data = pd.DataFrame()
        self.sector_df = pd.DataFrame()
        self.export_df = pd.DataFrame()

        self.layout = QtWidgets.QHBoxLayout(self.frame)
        self.layout.setObjectName("layout_for_plot")
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

    def get_fulll_circle_df(self):
        if self.path_file != "" and self.parameter != "" and len(self.axis.keys()) == 3:
            input_param_field = get_input_data(self.path_file,
                                               axial_axis=self.axis["axial"],
                                               radial_axis=self.axis["radial"],
                                               theta_axis=self.axis["theta"])
            number_of_sectors = get_sector_num(input_param_field, 0.5)

            self.full_circle_data = get_full_circle_input_data(input_param_field, number_of_sectors,
                                                               parameter=self.parameter,
                                                               axial_axis=self.axis["axial"],
                                                               radial_axis=self.axis["radial"],
                                                               theta_axis=self.axis["theta"])
            self.draw_inpt_field()
        else:
            self.show_msg_box_error("Отсутствуют:"
                                    "-> Путь к файлу"
                                    "-> Название параметра"
                                    "-> Название осей")

    def get_sector_df(self):
        if (len(self.numPtsTheta.text()) > 0
                and len(self.numPtsRadius.text()) > 0
                and len(self.startAngle.text()) > 0
                and len(self.sectorAngle.text()) > 0):
            fi_start = self.startAngle.text()
            sector_angle = self.sectorAngle.text()
            radial_num_pts = self.numPtsRadius.text()
            theta_num_pts = self.numPtsTheta.text()

            if len(self.sector_df.columns) > 0:
                self.sector_df = clear_df(self.sector_df)
                self.draw_inpt_field()

            self.sector_df = get_output_data(input_df=self.full_circle_data,
                                                r_min=min(self.full_circle_data["R"].tolist()),
                                                r_max=max(self.full_circle_data["R"].tolist()),
                                                fi_start=float(fi_start),
                                                sector_angle=float(sector_angle),
                                                radial_num_pts=int(radial_num_pts),
                                                theta_num_pts=int(theta_num_pts),
                                                axial_axis=self.axis["axial"],
                                                radial_axis=self.axis["radial"],
                                                theta_axis=self.axis["theta"],
                                                parameter_name=self.parameter)

            self.sector_df = self.sector_df.sort_values(["R"])
            self.draw_calc_field()
        else:
            self.show_msg_box_error(self, "Введите параметры для определения выходного поля")

    def get_export_df(self):
        if (self.shrRadius.text() != "" and self.hubRadius.text() != ""):
            self.export_df = get_scale_field(self.sector_df,
                                                new_r_max=float(self.shrRadius.text()),
                                                new_r_min=float(self.hubRadius.text()),
                                                radial_axis=self.axis["radial"],
                                                theta_axis=self.axis["theta"])
        else:
            self.show_msg_box_error("Не заполнены следующие параметры:"
                                    "-> Периферийный радиус"
                                    "-> Втулочный радиус")

    def draw_inpt_field(self):
        self.figure.clear()
        plt.scatter(self.full_circle_data[self.axis["radial"]],
                    self.full_circle_data[self.axis["theta"]],
                    c=self.full_circle_data[self.parameter],
                    cmap='jet',
                    s=1,
                    alpha=0.05)
        plt.colorbar(orientation="vertical")
        self.canvas.draw()

    def draw_calc_field(self):
        plt.scatter(self.sector_df[self.axis["radial"]],
                    self.sector_df[self.axis["theta"]],
                    color="red",
                    marker="+",
                    s=3,
                    alpha=1)
        self.canvas.draw()

    def show_msg_box_error(self, error_txt):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(error_txt)
        msg.setWindowTitle("Error")
        msg.exec_()


class CoefWindow(QWidget, Ui_CoefWidget):
    '''
    Окно с расчетом через коэффициент
    '''
    def __init__(self):
        super(CoefWindow, self).__init__()
        self.setupUi(self)
        # loadUi("./ui/coef_window.ui", self)

        self.axis = dict()
        self.parameter = ""
        self.path_file = ""

        self.btn_draw.clicked.connect(self.get_fulll_circle_df)
        self.btn_check.clicked.connect(self.get_sector_df)
        self.btn_calc.clicked.connect(self.get_export_df)

        self.full_circle_data = pd.DataFrame()
        self.sector_df = pd.DataFrame()
        self.export_df = pd.DataFrame()

        self.layout = QtWidgets.QHBoxLayout(self.frame)
        self.layout.setObjectName("layout_for_plot")
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

    def get_fulll_circle_df(self):
        if self.path_file != "" and self.parameter != "" and len(self.axis.keys()) == 3:
            input_param_field = get_input_data(self.path_file,
                                               axial_axis=self.axis["axial"],
                                               radial_axis=self.axis["radial"],
                                               theta_axis=self.axis["theta"])
            number_of_sectors = get_sector_num(input_param_field, 0.5)

            self.full_circle_data = get_full_circle_input_data(input_param_field, number_of_sectors,
                                                               parameter=self.parameter,
                                                               axial_axis=self.axis["axial"],
                                                               radial_axis=self.axis["radial"],
                                                               theta_axis=self.axis["theta"])
            self.draw_inpt_field()
        else:
            self.show_msg_box_error("Отсутствуют:"
                                    "-> Путь к файлу"
                                    "-> Название параметра"
                                    "-> Название осей")

    def get_sector_df(self):
        if (len(self.numPtsTheta.text()) > 0
                and len(self.numPtsRadius.text()) > 0
                and len(self.startAngle.text()) > 0
                and len(self.sectorAngle.text()) > 0):
            fi_start = self.startAngle.text()
            sector_angle = self.sectorAngle.text()
            radial_num_pts = self.numPtsRadius.text()
            theta_num_pts = self.numPtsTheta.text()

            if len(self.sector_df.columns) > 0:
                self.sector_df = clear_df(self.sector_df)
                self.draw_inpt_field()

            self.sector_df = get_output_data(input_df=self.full_circle_data,
                                             r_min=min(self.full_circle_data["R"].tolist()),
                                             r_max=max(self.full_circle_data["R"].tolist()),
                                             fi_start=float(fi_start),
                                             sector_angle=float(sector_angle),
                                             radial_num_pts=int(radial_num_pts),
                                             theta_num_pts=int(theta_num_pts),
                                             axial_axis=self.axis["axial"],
                                             radial_axis=self.axis["radial"],
                                             theta_axis=self.axis["theta"],
                                             parameter_name=self.parameter)

            self.sector_df = self.sector_df.sort_values(["R"])
            self.draw_calc_field()
        else:
            self.show_msg_box_error(self, "Введите параметры для определения выходного поля")

    def get_export_df(self):
        if (self.shrRadius.text() != ""
                and self.hubRadius.text() != ""
                and self.prm.text() != ""
                and self.newPrm.text() != ""):
            self.export_df = get_scale_field(self.sector_df,
                                             new_r_max=float(self.shrRadius.text()),
                                             new_r_min=float(self.hubRadius.text()),
                                             radial_axis=self.axis["radial"],
                                             theta_axis=self.axis["theta"])

            prm = float(self.prm.text())
            new_prm = float(self.newPrm.text())

            self.export_df[self.parameter] = self.export_df[self.parameter] * new_prm / prm
        else:
            self.show_msg_box_error("Не заполнены следующие параметры:"
                                    "-> Периферийный радиус"
                                    "-> Втулочный радиус"
                                    "-> Параметры для пересчета поля параметров")

    def draw_inpt_field(self):
        self.figure.clear()
        plt.scatter(self.full_circle_data[self.axis["radial"]],
                    self.full_circle_data[self.axis["theta"]],
                    c=self.full_circle_data[self.parameter],
                    cmap='jet',
                    s=1,
                    alpha=0.05)
        plt.colorbar(orientation="vertical")
        self.canvas.draw()

    def draw_calc_field(self):
        plt.scatter(self.sector_df[self.axis["radial"]],
                    self.sector_df[self.axis["theta"]],
                    color="red",
                    marker="+",
                    s=3,
                    alpha=1)
        self.canvas.draw()

    def show_msg_box_error(self, error_txt):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(error_txt)
        msg.setWindowTitle("Error")
        msg.exec_()

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec_()

if __name__ == '__main__':
    sys.exit(main())