from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class TimeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.sec = 0
        self.openWaitProcess()

    def openWaitProcess(self):
        # setting geometry of main window
        self.setGeometry(100, 100, 800, 400)

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setStyleSheet("border : 3px solid black")
        self.label.setFont(QFont('Times', 40))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setText('Waiting for Love(Coach)')

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.showTime)

        self.video = QLabel()
        self.video.setGeometry(QRect(25, 25, 200, 200))
        self.video.setMinimumSize(QSize(200, 200))
        self.video.setMaximumSize(QSize(200, 200))
        self.video.setObjectName("label")

        self.movie = QMovie("pictures/radio.gif")
        self.video.setMovie(self.movie)
        self.movie.start()

        layout.addWidget(self.label)
        layout.addWidget(self.video, alignment=Qt.AlignCenter)
        self.setLayout(layout)

        # update the timer every second
        # method called by timer
        self.show()

    def start(self, waitTime):
        self.min = waitTime
        self.sec = 0
        self.movie.stop()

        self.movie = QMovie("pictures/spinner.gif")
        self.video.setMovie(self.movie)
        self.movie.start()
        self.timer.start(1000)



    def showTime(self):
        if self.min == 0 and self.sec == 0:
            print('Pezda')
        if self.sec == 0:
            self.min -= 1
            self.sec = 59
        else:
            self.sec -= 1

        text = f'{self.min} : {"0" if self.sec < 10 else ""}{self.sec}'
        # showing text
        self.label.setText(text)
