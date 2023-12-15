import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QListWidget,
    QListWidgetItem,
    QApplication,
    QAbstractItemView,
)
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QColor
import frontend.constants as p
import global_constants as gc
from frontend.widgets import DoubleLineWidget, CourseInfoListElement
from backend.models import GroupedSection


class OFGWindow(QWidget):
    senal_cambiar_area = pyqtSignal(str)
    senal_volver = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setGeometry(0, 0, 1280, 720)
        self.course_list = []
        self.__current_course_index = 0
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.setStyleSheet(p.DARK_MODE)

        self.btn_back = QPushButton("Volver", self)
        layout.addWidget(self.btn_back)
        self.qcb_ofg_areas = QComboBox(self)
        self.qcb_ofg_areas.addItem("-")
        for area in gc.OFG:
            self.qcb_ofg_areas.addItem(area)
        self.lbl_combinations = QLabel("0", self)
        self.lbl_combinations.setStyleSheet("background-color: #2b2b2b;")
        layout.addWidget(self.qcb_ofg_areas)
        layout.addWidget(self.lbl_combinations)

        layout_btn = QHBoxLayout()
        self.btn_previous = QPushButton("Anterior", self)
        self.btn_previous.setEnabled(False)
        self.lbl_current_ofg = QLabel("0", self)
        self.lbl_current_ofg.setAlignment(Qt.AlignCenter)
        self.lbl_current_ofg.setStyleSheet("background-color: #2b2b2b;")
        self.btn_next = QPushButton("Siguiente", self)
        self.btn_next.setEnabled(False)
        layout_btn.addWidget(self.btn_previous)
        layout_btn.addWidget(self.lbl_current_ofg)
        layout_btn.addWidget(self.btn_next)
        layout.addLayout(layout_btn)
        layout_courses = QHBoxLayout()
        self.tb_schedule = QTableWidget(self)
        self.tb_schedule.setColumnCount(5)
        self.tb_schedule.setRowCount(9)
        self.tb_schedule.setRowHeight(4, 1)
        self.tb_schedule.setVerticalHeaderLabels(p.H_LABELS_HORARIO)
        self.tb_schedule.setHorizontalHeaderLabels(p.DIAS.keys())
        self.tb_schedule.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.set_lunch_line()
        self.list_current_courses = QListWidget(self)
        layout_courses.addWidget(self.tb_schedule)
        layout_courses.addWidget(self.list_current_courses)
        layout.addLayout(layout_courses)

        self.qcb_ofg_areas.currentTextChanged.connect(self.enviar_cambiar_area)
        self.btn_back.clicked.connect(lambda x: self.senal_volver.emit())

    @property
    def current_course_index(self):
        return self.__current_course_index

    @current_course_index.setter
    def current_course_index(self, value):
        self.__current_course_index = max(0, min(value, len(self.course_list) - 1))

    def iniciar(self):
        self.lbl_combinations.clear()
        self.lbl_current_ofg.clear()
        self.list_current_courses.clear()
        self.tb_schedule.clearContents()
        self.qcb_ofg_areas.setCurrentIndex(0)
        self.btn_next.setEnabled(False)
        self.btn_previous.setEnabled(False)
        self.show()

    def set_lunch_line(self):
        color = QColor("#5a5a5a")
        for j in range(self.tb_schedule.columnCount()):
            self.tb_schedule.setItem(4, j, QTableWidgetItem())
            self.tb_schedule.item(4, j).setBackground(color)

    def add_course_schedule(self, course):
        for sigla_type in [
            gc.SIGLA_CATEDRA,
            gc.SIGLA_AYUDANTIA,
            gc.SIGLA_LAB,
            gc.SIGLA_TALLER,
        ]:
            self.add_item(
                course[gc.SIGLA],
                course[gc.SECCIONES],
                course[gc.HORARIO][sigla_type].items(),
                p.COLORES[sigla_type],
            )

    def add_item(self, course_id, sections, items, color):
        sections = [str(section) for section in sections]
        for dia, modulos in items:
            for modulo in modulos:
                if modulo <= 4:
                    modulo -= 1
                cell_widget = self.tb_schedule.cellWidget(modulo, p.DIAS[dia])
                label = f"{course_id}-{','.join(sections)}"
                if cell_widget:
                    cell_widget.addLabel(label, color)
                else:
                    item = DoubleLineWidget(label, color)
                    self.tb_schedule.setCellWidget(modulo, p.DIAS[dia], item)

    def update_schedule(self, combinacion: list[GroupedSection]):
        self.list_current_courses.clear()
        self.tb_schedule.clearContents()
        self.set_lunch_line()
        for course in combinacion:
            self.add_course_schedule(course)
            item = QListWidgetItem()
            item.setSizeHint(QSize(100, 80))
            self.list_current_courses.addItem(item)
            self.list_current_courses.setItemWidget(
                item,
                CourseInfoListElement(
                    course[gc.ID_CURSO],
                    course[gc.SIGLA],
                    course[gc.SECCIONES],
                    course[gc.NRCS],
                    course[gc.PROFESORES],
                ),
            )

    def new_schedule(
        self,
        combination: list[GroupedSection],
        cantidad_combinaciones,
        combinacion_actual,
    ):
        self.update_combinations_label(cantidad_combinaciones)
        self.update_current_index_label(combinacion_actual)
        self.update_schedule(combination)
        self.btn_previous.setEnabled(False)
        self.btn_next.setEnabled(False)

    def update_current_index_label(self, combinacion_actual):
        self.lbl_current_ofg.setText(f"Combinacion {combinacion_actual}")

    def update_combinations_label(self, cantidad_combinaciones):
        self.lbl_combinations.setText(f"{cantidad_combinaciones} combinaciones")

    def enviar_cambiar_area(self, area):
        self.senal_cambiar_area.emit(area)


if __name__ == "__main__":

    def hook(type_, value, traceback):
        print(type_)
        print(traceback)

    sys.__excepthook__ = hook

    app = QApplication(sys.argv)
    main = OFGWindow()
    main.show()

    sys.exit(app.exec())