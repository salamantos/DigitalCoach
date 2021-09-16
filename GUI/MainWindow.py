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

from GUI.VideoWorker import VideoThreadWork


class App(QWidget):
    def __init__(self, cam_list):
        super().__init__()
        self.listCam = cam_list
        self.landmarks = None
        self.camFirst = False
        self.camSec = False
        self.sharedMem = list()
        self.sqatsMem = list()
        self.initUI()

    @pyqtSlot(QImage, int)
    def setImage(self, image, num):
        if num == 0:
            self.labelFirst.setPixmap(QPixmap.fromImage(image))
        else:
            self.labelSecond.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(tuple, int)
    def setTextModern(self, data, num):
        # print(num)
        if len(self.listCam) == 2:
            if num == 0 and not self.camFirst:
                self.camFirst = True
                if not self.camSec:
                    return
            elif num != 0 and not self.camSec:
                self.camSec = True
                if not self.camFirst:
                    return

            if  not self.sharedMem or self.sharedMem[0][1] == num:
                self.sharedMem.append((data, num))
            else:
                elements = (self.rightHandElbow, self.rightHandShoulder, self.leftHandElbow, self.leftHandShoulder)
                dataSaved, savedCam = self.sharedMem.pop()
                for pos, resFunc in enumerate(elements):
                    if data[pos][1] > dataSaved[pos][1]:
                        camResNum = num
                        dataRes = data[pos][0]
                    else:
                        camResNum = savedCam
                        dataRes = dataSaved[pos][1]
                    resFunc.setText(f'{dataRes}:.2f, cam - {camResNum}')
        else:
            dataSolo = []
            for elem in data:
                dataSolo.append(elem[0])
            self.setText(dataSolo)

    @pyqtSlot(tuple, int, name='squats')
    def setTextSquats(self, data, num):
        # print(num)
        if len(self.listCam) == 2:
            if num == 0 and not self.camFirst:
                self.camFirst = True
                if not self.camSec:
                    return
            elif num != 0 and not self.camSec:
                self.camSec = True
                if not self.camFirst:
                    return

            if not self.sqatsMem or self.sqatsMem[0][1] == num:
                self.sqatsMem.append((data, num))
            else:
                ##Reaction for 2 cameras data
                return None
        else:
            #Reaction for 1 camera data (see setModernText)
            return None

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

        self.labelFirst = QLabel()
        hbox.addWidget(self.labelFirst)

        if len(self.listCam) == 2:
            self.labelSecond = QLabel()
            hbox.addWidget(self.labelSecond)

        self.setWindowTitle('Camera')
        # create a label

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

        vbox.addWidget(self.create_text_instance(self.isExcCorrect, 'State:'))

        self.completeNum = QLabel(self)
        vbox.addWidget(self.create_text_instance(self.completeNum, 'Completed - '))

        frame.setLayout(vbox)
        hbox.addWidget(frame)
        self.setLayout(hbox)

        self.setGeometry(300, 100, 200, 200)


        th = VideoThreadWork(cam_num=self.listCam[0], parent=self)
        th.changePixmap.connect(self.setImage)
        th.changeText.connect(self.setText)
        th.changeTextModern.connect(self.setTextModern)
        th.startExcercise.connect(self.handExcersice)
        th.exCounter.connect(self.completeChange)
        th.start()

        if (len(self.listCam) == 2):
            th = VideoThreadWork(cam_num=self.listCam[1], parent=self)
            th.changePixmap.connect(self.setImage)
            th.changeText.connect(self.setText)
            th.startExcercise.connect(self.handExcersice)
            th.changeTextModern.connect(self.setTextModern)

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
        cameras = self.return_camera_indexes(4) ### Trying to find cameras port
        # cameras = [0, 2]
        self.w = App(cameras)
        self.w.show()


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
