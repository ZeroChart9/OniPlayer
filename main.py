import os
import sys
import cv2
import numpy as np
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap
from openni import openni2, nite2, utils
import design


# для нормального вывода ошибок, так как разрабы поленились это сделать
sys._excepthook = sys.excepthook

def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

sys.excepthook = my_exception_hook

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, video_path):
        super().__init__()
        self.directory = video_path

    def run(self):
        try:
            # capture from web cam
            video_path = self.directory
            openni2.initialize()
            dev = openni2.Device.open_file(video_path.encode('utf-8'))

            depth_stream = dev.create_depth_stream()
            depth_stream.start()
            #test_image = cv2.imread(r'C:\Users\UserPC\PycharmProjects\testTask\whats-your-favourite-meme-panda-community-pogchamp-no-background-1280_720.png')
            while True:
                frame_depth = depth_stream.read_frame()
                frame_depth_data = frame_depth.get_buffer_as_uint16()
                depth_array = np.ndarray((frame_depth.height, frame_depth.width),
                                         dtype=np.uint16,
                                         buffer=frame_depth_data)
                depth_array = np.array(depth_array, dtype=np.uint16)
                depth_array = depth_array / np.max(depth_array) * 255
                depth_array = np.array(depth_array, dtype=np.uint8)
                ch3_img = np.stack((depth_array,) * 3, axis=-1)
                self.change_pixmap_signal.emit(ch3_img)

            depth_stream.stop()
            openni2.unload()
        except Exception as ex:
            print(ex)


class ExampleApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.btnBrowse.clicked.connect(self.browse_file)
        self.radioButton.toggled.connect(self.switcher)
        self.directory = None
        self.thread = None

    def browse_file(self):  # На случай, если в списке уже есть элементы
        self.directory = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите файл", "", '*.oni')
        self.thread = VideoThread(self.directory[0])
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

        # открыть диалог выбора директории и установить значение переменной
        # равной пути к выбранной директории

    # def read_oni(self):
    #     video_path = self.directory
    #     openni2.initialize()
    #     dev = openni2.Device.open_file(video_path.encode('utf-8'))
    #     print(dev.get_sensor_info(openni2.SENSOR_DEPTH))
    #
    #     depth_stream = dev.create_depth_stream()
    #     depth_stream.start()
    #     while True:
    #         frame_depth = depth_stream.read_frame()
    #         frame_depth_data = frame_depth.get_buffer_as_uint16()
    #         depth_array = np.ndarray((frame_depth.height, frame_depth.width),
    #                                  dtype=np.uint16,
    #                                  buffer=frame_depth_data) / 10000.
    #
    #     depth_stream.stop()
    #     openni2.unload()

    def switcher(self):
        radioButton = self.sender()
        radioButton.isChecked()


    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.videoWidget.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img: np.ndarray):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        rgb_image = cv_img
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.videoWidget.width(), self.videoWidget.height(), Qt.KeepAspectRatio)
        return QPixmap.fromImage(p) #convert_to_Qt_format)


def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
