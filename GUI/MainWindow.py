import logging
import sys
import cv2
from PyQt5.QtGui import QImage, QPixmap

from PyQt5.QtWidgets import *
# from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel, QPushButton, QApplication, QMainWindow
from PyQt5.QtCore import *
# from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, pyqtSlot


class Thread(QThread):
    changePixmap = pyqtSignal(QImage)
    changeText = pyqtSignal(str)

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if ret:
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)
                bright = int(frame[320,240,0]) + int(frame[320, 240, 1]) + int(frame[320, 240, 2])
                print(frame[320,240,0], frame[320,240,1], frame[320,240,2], bright)
                if bright > 400:
                    self.changeText.emit('Too bright')
                elif bright < 120:
                    self.changeText.emit('Too dark')
                else:
                    self.changeText.emit('Everything is Okay')

class App(QWidget):
    def __init__(self, thread_parent=None):
        super().__init__()
        self.initUI()

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(str)
    def setText(self, text):
        self.picture_indicator.setText(text)


    def initUI(self):
        hbox = QHBoxLayout()

        self.label = QLabel()
        self.setWindowTitle('Camera')
        # create a label
        hbox.addWidget(self.label)



        vbox = QVBoxLayout()
        frame = QFrame(self)

        self.resolution = QLabel(self)
        self.resolution.setText('640x480')
        vbox.addWidget(self.resolution)

        self.picture_indicator = QLabel(self)
        self.picture_indicator.setText('Everything is okay')
        vbox.addWidget(self.picture_indicator)

        frame.setLayout(vbox)
        hbox.addWidget(frame)
        self.setLayout(hbox)




        self.setGeometry(300, 100, 200, 200)
        th = Thread(parent=self)
        th.changePixmap.connect(self.setImage)
        th.changeText.connect(self.setText)
        th.start()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.w = None
        self.init_main()

    def init_main(self):
        '''
        Данная функция отвечает за создание главного меню
        :return: None
        '''
        main_wigh=QFrame(self)

        hbox = QHBoxLayout()
        pict_widget = QPixmap('pictures/eye.png')
        pict_widget = pict_widget.scaledToHeight(180)

        lbl = QLabel(self)
        lbl.setPixmap(pict_widget)
        hbox.addWidget(lbl)

        buttons_widget = QFrame(self)
        vbox = QVBoxLayout()

        camera = QPushButton('Camera')
        camera.clicked.connect(self.camera_launch)
        vbox.addWidget(camera)

        exit = QPushButton('Exit')
        exit.clicked.connect(lambda: QCoreApplication.instance().quit())
        vbox.addWidget(exit)
        buttons_widget.setLayout(vbox)
        buttons_widget.setLayout(vbox)
        hbox.addWidget(buttons_widget)

        main_wigh.setLayout(hbox)
        self.setCentralWidget(main_wigh)
        self.setGeometry(600, 300, 120, 200)
        self.setWindowTitle('Main Window')
        self.show()



    def camera_launch(self):
        # w = App(thread_parent=self)
        if self.w is None:
            self.w = App()
            self.w.show()

        # vbox.addWidget(self.picture_in_box(self.resource_path("pictures/logo_mini.jpg"), 150))



def start():
    try:
        app = QApplication(sys.argv)
        # app.setStyle('Windows')
        w = MainWindow()
        w.show()
        app.exec()
        # w = MainWindow(userdata=("Администратор", True))
        sys.exit(app.exec_())
    except Exception as e:
        logging.exception(e)


