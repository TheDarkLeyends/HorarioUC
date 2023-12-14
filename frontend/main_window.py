import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QLabel, QTableWidget, QTableWidgetItem, QApplication
from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtGui import QColor
from frontend.widgets import CourseFilters, CourseListElement, CourseInfoListElement, DoubleLineWidget
import frontend.constants as c
import global_constants as gc

class ScheduleWindow(QWidget):
    senal_buscar_sigla = pyqtSignal(str)
    senal_borrar_curso = pyqtSignal(str)
    senal_cambiar_seccion = pyqtSignal(str, int)
    senal_buscar_ofgs = pyqtSignal(tuple)
    senal_cambiar_campus = pyqtSignal(str)
    senal_cambiar_creditos = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setGeometry(0, 0, 1280, 720)
        self.course_list = []
        self.__current_course_index = 0
        layout = QVBoxLayout()
        self.setLayout(layout)

        filters = CourseFilters(self.senal_cambiar_campus, self.senal_cambiar_creditos)
        layout.addWidget(filters)

        layout_add = QHBoxLayout()
        self.txt_sigla = QLineEdit(self)
        self.btn_add = QPushButton("Agregar", self)
        layout_add.addWidget(self.txt_sigla)
        layout_add.addWidget(self.btn_add)
        layout.addLayout(layout_add)

        self.list_courses = QListWidget(self)
        self.lbl_combinations = QLabel(self)
        layout.addWidget(self.list_courses)
        layout.addWidget(self.lbl_combinations)

        layout_btn = QHBoxLayout()
        self.btn_previous = QPushButton("Anterior", self)
        self.btn_previous.setEnabled(False)
        self.lbl_current_index = QLabel(self)
        self.btn_next = QPushButton("Siguiente", self)
        self.btn_next.setEnabled(False)
        layout_btn.addWidget(self.btn_previous)
        layout_btn.addWidget(self.lbl_current_index)
        layout_btn.addWidget(self.btn_next)
        layout.addLayout(layout_btn)
        layout_courses = QHBoxLayout()
        self.tb_schedule = QTableWidget(self)
        self.tb_schedule.setColumnCount(5)
        self.tb_schedule.setRowCount(9)
        self.tb_schedule.setRowHeight(4, 1)
        self.tb_schedule.setVerticalHeaderLabels(c.H_LABELS_HORARIO)
        self.tb_schedule.setHorizontalHeaderLabels(c.DIAS.keys())
        self.set_lunch_line(4, QColor(224, 224, 224))
        self.list_current_courses = QListWidget(self)
        layout_courses.addWidget(self.tb_schedule)
        layout_courses.addWidget(self.list_current_courses)
        layout.addLayout(layout_courses)
        btn_ofgs = QPushButton("Buscar OFGs", self)
        layout.addWidget(btn_ofgs)

        self.update_current_index_label()
        self.update_combinations_label()
        self.btn_add.clicked.connect(self.buscar_sigla)
        self.btn_next.clicked.connect(self.increase_current_index)
        self.btn_previous.clicked.connect(self.decrease_current_index)
        btn_ofgs.clicked.connect(self.enviar_buscar_ofgs)
    
    @property
    def current_course_index(self):
        return self.__current_course_index

    @current_course_index.setter
    def current_course_index(self, value):
        self.__current_course_index = max(0, min(value, len(self.course_list) - 1))

    def set_lunch_line(self, rowIndex, color):
        for j in range(self.tb_schedule.columnCount()):
            self.tb_schedule.setItem(rowIndex, j, QTableWidgetItem())
            self.tb_schedule.item(rowIndex, j).setBackground(color)

    def add_course_schedule(self, course):
        self.add_item(course.id, course.sections, course.catedra.items(), c.COLORES[c.CATEDRA])
        self.add_item(course.id, course.sections, course.ayudantia.items(), c.COLORES[c.AYUDANTIA])
        self.add_item(course.id, course.sections, course.lab.items(), c.COLORES[c.LAB])
        self.add_item(course.id, course.sections, course.taller.items(), c.COLORES[c.TALLER])

    def add_item(self, course_id, sections, items, color):
        for dia, modulos in items:
            for modulo in modulos:
                if modulo <= 4:
                    modulo -= 1
                if self.tb_schedule.cellWidget(modulo, c.DIAS[dia]):
                    self.tb_schedule.cellWidget(modulo, c.DIAS[dia]).addLabel(f"{course_id}-{','.join(sections)}", color)
                else:
                    item = DoubleLineWidget(f"{course_id}-{','.join(sections)}", color)
                    self.tb_schedule.setCellWidget(modulo, c.DIAS[dia], item)

    def increase_current_index(self):
        self.current_course_index += 1
        if self.current_course_index == len(self.course_list) - 1:
            self.btn_next.setEnabled(False)
        self.btn_previous.setEnabled(True)
        self.update_schedule()
        self.update_current_index_label()

    def decrease_current_index(self):
        self.current_course_index -= 1
        if self.current_course_index == 0:
            self.btn_previous.setEnabled(False)
        self.btn_next.setEnabled(True)
        self.update_schedule()
        self.update_current_index_label()

    def update_schedule(self):
        self.list_current_courses.clear()
        self.tb_schedule.clearContents()
        self.set_lunch_line(4, QColor(224, 224, 224))
        for course in self.course_list[self.current_course_index]:
            self.add_course_schedule(course)
            item = QListWidgetItem()
            item.setSizeHint(QSize(100, 80))
            self.list_current_courses.addItem(item)
            self.list_current_courses.setItemWidget(item, CourseInfoListElement(course.id, course.name, course.sections, course.nrcs, course.teachers))

    def new_schedule(self, combinations):
        self.course_list = combinations
        self.current_course_index = 0
        self.update_current_index_label()
        self.update_combinations_label()
        self.update_schedule()
        self.btn_previous.setEnabled(False)
        self.btn_next.setEnabled(True)
        if self.current_course_index == len(self.course_list) - 1:
            self.btn_next.setEnabled(False)

    def update_current_index_label(self):
        self.lbl_current_index.setText(f"Combinacion {self.current_course_index + 1}")

    def update_combinations_label(self):
        self.lbl_combinations.setText(f"{len(self.course_list)} combinaciones")

    def buscar_sigla(self):
        sigla = self.txt_sigla.text()
        if sigla != "":
            self.senal_buscar_sigla.emit(sigla)

    def add_course(self, course):
        item = QListWidgetItem()
        item.setSizeHint(QSize(100, 80))
        self.list_courses.addItem(item)
        self.list_courses.setItemWidget(item, CourseListElement(course.id, course.sections, self.senal_borrar_curso, self.senal_cambiar_seccion))

    def delete_course(self, course_id):
        for i in range(self.list_courses.count()):
            item = self.list_courses.item(i)
            widget = self.list_courses.itemWidget(item)
            if widget.lbl_id.text() == course_id:
                self.list_courses.takeItem(self.list_courses.row(item))
                del item
                break

    def enviar_buscar_ofgs(self):
        self.senal_buscar_ofgs.emit(self.course_list[self.current_course_index])

if __name__ == "__main__":

    def hook(type_, value, traceback):
        print(type_)
        print(traceback)

    sys.__excepthook__ = hook

    app = QApplication(sys.argv)
    main = ScheduleWindow()
    main.show()

    sys.exit(app.exec())