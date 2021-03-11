import sys
import time
import numpy as np
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap
from openni import openni2
import design
import traceback as tb

# для нормального вывода ошибок, так как разрабы поленились это сделать
sys._excepthook = sys.excepthook


def my_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


sys.excepthook = my_exception_hook


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, video_path, is_color):
        super().__init__()
        self.directory = video_path
        self.is_color = is_color
        self.is_conf_color = is_color
        self.is_paused = False
        self.prev_frame = False
        self.next_frame = False
        self.slider: QtWidgets.QSlider = None

    def run(self):
        try:
            # capture from web cam
            video_path = self.directory
            openni2.initialize()
            dev = openni2.Device.open_file(video_path.encode('utf-8'))
            pbs = openni2.PlaybackSupport(dev)

            if self.is_conf_color:
                image_stream = dev.create_color_stream()
            else:
                image_stream = dev.create_depth_stream()
            image_stream.start()
            numb_frame = image_stream.get_number_of_frames()
            self.slider.setRange(0, numb_frame)
            current_frame = 0
            while True:
                if current_frame == numb_frame:
                    self.is_paused = True

                if self.is_color != self.is_conf_color:
                    self.is_conf_color = self.is_color
                    image_stream.stop()
                    if self.is_conf_color:
                        image_stream = dev.create_color_stream()
                    else:
                        image_stream = dev.create_depth_stream()
                    image_stream.start()
                    numb_frame = image_stream.get_number_of_frames()
                    self.slider.setRange(0, numb_frame)
                    pbs.seek(image_stream, current_frame)

                if self.is_paused:
                    while True:

                        if not self.is_paused:
                            break

                        if current_frame != self.slider.value():
                            current_frame = self.slider.value()

                        if self.prev_frame:
                            if current_frame > 0:
                                current_frame -= 1
                            self.prev_frame = False

                        if self.next_frame:
                            if current_frame < numb_frame:
                                current_frame += 1
                            self.next_frame = False

                        self.slider.setSliderPosition(current_frame)
                        pbs.seek(image_stream, current_frame)
                        frame_image = image_stream.read_frame()
                        self.build_frame(frame_image)

                if current_frame != self.slider.value():
                    current_frame = self.slider.value()
                    pbs.seek(image_stream, current_frame)
                else:
                    current_frame += 1
                    self.slider.setSliderPosition(current_frame)
                frame_image = image_stream.read_frame()
                self.build_frame(frame_image)
                time.sleep(0.016)  # Для вывода видеоряда в 60FPS (1000(мс)/60(кдр/с)/1000)

            image_stream.stop()
            openni2.unload()

        except Exception as ex:
            error_message = tb.format_exc()
            print(error_message)

    def build_frame(self, frame):
        if self.is_conf_color:
            frame_image_data = frame.get_buffer_as_uint8()

            image_array = np.ndarray((frame.height, frame.width, 3),
                                     dtype=np.uint8,
                                     buffer=frame_image_data)
            self.change_pixmap_signal.emit(image_array)
        else:
            frame_depth_data = frame.get_buffer_as_uint16()
            depth_array = np.ndarray((frame.height, frame.width),
                                     dtype=np.uint16,
                                     buffer=frame_depth_data)
            depth_array = np.array(depth_array, dtype=np.uint16)
            depth_array = depth_array / np.max(depth_array) * 255  # нормализация карты глубины в диапозон 0..255
            depth_array = np.array(depth_array, dtype=np.uint8)
            ch3_img = np.stack((depth_array,) * 3, axis=-1)
            self.change_pixmap_signal.emit(ch3_img)


class ExampleApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.btnBrowse.clicked.connect(self.browse_file)
        self.playBtn.clicked.connect(self.play)
        self.pauseBtn.clicked.connect(self.pause)
        self.checkBox.toggled.connect(self.switcher)
        self.prevBtn.clicked.connect(self.move_back)
        self.nextBtn.clicked.connect(self.move_forward)
        self.horizontalSlider.valueChanged[int].connect(self.value_changed)
        self.directory = None
        self.thread = None

    def browse_file(self):  # На случай, если в списке уже есть элементы
        self.directory = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите файл", "", '*.oni')
        if self.thread is not None:
            self.thread.terminate()
        self.thread = VideoThread(self.directory[0], self.checkBox.isChecked())
        self.thread.slider = self.horizontalSlider
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

        # открыть диалог выбора директории и установить значение переменной
        # равной пути к выбранной директории

    def play(self):
        try:
            self.thread.is_paused = False
        except:
            pass

    def pause(self):
        try:
            self.thread.is_paused = True
        except:
            pass

    def switcher(self):
        try:
            self.thread.is_color = self.checkBox.isChecked()
        except:
            pass

    def move_back(self):
        try:
            self.thread.prev_frame = True
        except:
            pass

    def move_forward(self):
        try:
            self.thread.next_frame = True
        except:
            pass

    def value_changed(self, value):
        try:
            self.thread.slider.setValue(value)
        except:
            pass

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.videoWidget.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img: np.ndarray):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv_img
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        # p = convert_to_Qt_format.scaled(self.videoWidget.width(), self.videoWidget.height(), Qt.KeepAspectRatio,
        #                                 Qt.SmoothTransformation)
        return QPixmap.fromImage(convert_to_Qt_format)


def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
