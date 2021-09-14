import logging
import sys

import cv2
import mediapipe as mp
import numpy as np
import copy
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import *
import signal
import os
import time

from GUI.VideoWorker import VideoWorker


class App(QWidget):
    def __init__(self, cam_id=0):
        super().__init__()
        self.cam_id = cam_id
        self.landmarks = None
        self.initUI()

    @pyqtSlot(tuple)
    def setImage(self, imageTuple):
        self.labelClear.setPixmap(QPixmap.fromImage(imageTuple[0]))
        self.labelMarked.setPixmap(QPixmap.fromImage(imageTuple[1]))

    @pyqtSlot(list)
    def setText(self, elementList):
        elements = (self.rightHandElbow, self.rightHandShoulder, self.leftHandElbow, self.leftHandShoulder)
        for pos, el in enumerate(elements):
            el.setText(f'{elementList[pos]:.2f}')

    @pyqtSlot(dict)
    def getDict(self, point_dict):
        self.landmarks = point_dict

    @pyqtSlot(str, str)
    def handExcersice(self, currentHand, isCorrect):
        self.priorityHand.setText(currentHand)
        self.isExcCorrect.setText(isCorrect)

    @pyqtSlot(int)
    def completeChange(self, amount):
        print(amount)
        self.completeNum.setText(f'{amount}')




    def create_text_instance(self, labelName: QLabel, labelComment: str):
        frame = QFrame(self)
        hbox = QHBoxLayout()

        comment = QLabel(self)
        comment.setText(labelComment)
        hbox.addWidget(comment)

        hbox.addWidget(labelName)

        frame.setLayout(hbox)
        return frame



    def initUI(self):


        hbox = QHBoxLayout()

        self.labelClear = QLabel()
        self.labelMarked = QLabel()
        self.setWindowTitle('Camera')
        # create a label
        hbox.addWidget(self.labelClear)
        hbox.addWidget(self.labelMarked)

        button = QPushButton('Start squats')


        vbox = QVBoxLayout()
        frame = QFrame(self)


        self.rightHandElbow = QLabel(self)
        vbox.addWidget(self.create_text_instance(self.rightHandElbow, 'Right hand elbow:'))

        self.rightHandShoulder = QLabel(self)
        vbox.addWidget(self.create_text_instance(self.rightHandShoulder, 'Right hand shoulder:'))


        self.leftHandElbow = QLabel(self)
        vbox.addWidget(self.create_text_instance(self.leftHandElbow, 'Left hand elbow:'))

        self.leftHandShoulder = QLabel(self)
        vbox.addWidget(self.create_text_instance(self.leftHandShoulder, 'Left hand shoulder:'))

        self.priorityHand = QLabel(self)
        vbox.addWidget(self.create_text_instance(self.priorityHand, 'Current detected active hand is:'))

        self.isExcCorrect = QLabel(self)
        vbox.addWidget(self.create_text_instance(self.isExcCorrect, 'State:'))

        self.completeNum = QLabel(self)
        vbox.addWidget(self.create_text_instance(self.completeNum, 'Completed - '))

        frame.setLayout(vbox)
        hbox.addWidget(frame)
        self.setLayout(hbox)

        self.setGeometry(300, 100, 200, 200)
        th = VideoWorker(cam_num=self.cam_id, parent=self)
        th.changePixmap.connect(self.setImage)
        th.changeText.connect(self.setText)
        th.startExcercise.connect(self.handExcersice)
        th.exCounter.connect(self.completeChange)
        th.start()
        self.show()

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
        main_wigh = QFrame(self)

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
        hbox.addWidget(buttons_widget)

        main_wigh.setLayout(hbox)
        self.setCentralWidget(main_wigh)
        self.setGeometry(600, 300, 120, 200)
        self.setWindowTitle('Main Window')
        self.show()

    def return_camera_indexes(self, start=10):
        # checks the first 10 indexes.
        index = 0
        arr = []
        i = start
        while i > 0:
            cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                arr.append(index)
                cap.release()
            index += 1
            i -= 1
        return arr


    def camera_launch(self):
        # w = App(thread_parent=self)
        # cameras = self.return_camera_indexes(4)
        # if self.w is None:
        # for el in cameras:
        # print(cameras)
        self.w = App(0)
        self.w.show()

        # if len(cameras) == 2:
        #     self.c = App(cameras[1])
        #     self.c.show()

        # lst = []
        # lst.append(App())
        # lst[0].show()

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
