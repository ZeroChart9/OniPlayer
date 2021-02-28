import os
import sys
import cv2
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from openni import openni2, nite2, utils
import design


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(0)
        while True:
            ret, cv_img = cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img)


class ExampleApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.btnBrowse.clicked.connect(self.browse_file)
        self.directory = None

    def browse_file(self): # На случай, если в списке уже есть элементы
        self.directory = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите файл", "", '*.oni')
        # открыть диалог выбора директории и установить значение переменной
        # равной пути к выбранной директории

    def read_oni(self):
        video_path = self.directory
        openni2.initialize()
        dev = openni2.Device.open_file(video_path.encode('utf-8'))
        print(dev.get_sensor_info(openni2.SENSOR_DEPTH))

        depth_stream = dev.create_depth_stream()
        depth_stream.start()
        while True:
            frame_depth = depth_stream.read_frame()
            frame_depth_data = frame_depth.get_buffer_as_uint16()
            depth_array = np.ndarray((frame_depth.height, frame_depth.width),
                                     dtype=np.uint16,
                                     buffer=frame_depth_data) / 10000.

        depth_stream.stop()
        openni2.unload()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)



def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
