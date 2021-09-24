import logging
import sys
from functools import partial

import cv2
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap, QFont, QMovie, QIcon
from PyQt5.QtWidgets import *
from enum import Enum

from GUI.VideoWorker import VideoThreadWork
from Bot.TeleBotError import Mail


class SqutsState(Enum):
    Sitting = 1
    Standing = 2

class ExcersiceState(Enum):
    Waiting = 0
    Preparing = 1
    Working = 2

class App(QWidget):
    def __init__(self, cam_list):
        super().__init__()
        self.messageBot = Mail()
        self.listCam = cam_list
        self.landmarks = None
        self.excCurrentState = ExcersiceState.Waiting
        self.camFirst = False
        self.camSec = False
        self.state = SqutsState.Sitting
        self.legsPos = list()
        self.sharedMem = list()
        self.amount = 0
        self.sqatsMem = list()
        self.initUI()

    @pyqtSlot(QImage, int)
    def setImage(self, image, num):
        if self.listCam[0] == num:
            self.labelFirst.setPixmap(QPixmap.fromImage(image))
        else:
            self.labelSecond.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(tuple, int, name='text')
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

            if not self.sharedMem or self.sharedMem[0][1] == num:
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
                    resFunc.setText(f'{dataRes:.2f}, cam - {camResNum}')
        else:
            dataSolo = []
            for elem in data:
                dataSolo.append(elem[0])
            self.setText(dataSolo)

    @pyqtSlot(tuple, int, name='squats')
    def setTextSquats(self, data, num):
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
                dataSaved, camSaved = self.sqatsMem.pop()
                dataRecv, camRecv = data, num
                if self.excCurrentState == ExcersiceState.Preparing:
                    self.legsPos.clear()
                    for el, _ in data[1]:
                        self.legsPos.append(el)
                    if self.legsPos:
                        self.excCurrentState = ExcersiceState.Working
                elif self.excCurrentState == ExcersiceState.Working:
                    state = self.checkSquatMultCam(dataSaved, dataRecv)
                    if state:
                        self.amount += 1
                        print('Current - ', self.amount)
                        self.completeNum.setText(f'{self.amount}')
                        # self.isExcCorrect.setText('KRUTO!!!!')

                return None
        else:
            if self.excCurrentState == ExcersiceState.Preparing:
                self.legsPos.clear()
                for el, _ in data[1]:
                    self.legsPos.append(el)
                if self.legsPos:
                    self.excCurrentState = ExcersiceState.Working
            elif self.excCurrentState == ExcersiceState.Working:
                state = self.checkSquatSoloCam(data)
                if state:
                    self.amount += 1
                    print('Current - ', self.amount)
                    self.completeNum.setText(f'{self.amount}')
                    # self.isExcCorrect.setText('KRUTO!!!!')

            # Reaction for 1 camera data (see setModernText)
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
        # self.priorityHand.setText(currentHand)
        # self.isExcCorrect.setText(isCorrect)
        pass

    @pyqtSlot(int)
    def completeChange(self, amount):
        # print('!')
        pass

    def checkSquatSoloCam(self, saved):
        delta = 0.1  ###how to get it?
        angleFinishBorders = (60, 120)
        error_list = ('Right elbow', 'Right shoulder', 'Right hip', 'Right knee',
                      'Left elbow', 'Left shoulder', 'Left hip', 'Left knee')
        # angleErrorBorders = [(10, 70), (50, 70), (1, 100), (35, 100),
        #                      (10, 70), (50, 70), (1, 100), (35, 100)]
        angleErrorBorders = [(1, 180), (1, 180), (1, 180), (1, 180),
                             (1, 180), (1, 180), (1, 180), (5, 180)]
        lenErrorBorders = (0.2, 0.46)
        angles, legs, back = saved[0], saved[1], saved[2]
        stateVariable = False
        succ = False
        error_occured = False

        for pos, el in enumerate(angles):
            angle, vis = el
            # cam = camSaved if angle == angle1 else camResv
            if vis < 0.4:
                print(f'{error_list[pos]} in dead zone')
                error_occured = True
                self.state = SqutsState.Sitting

                # excFinished = False

            if self.state == SqutsState.Sitting:
                if angle < angleErrorBorders[pos][0] or angle > angleErrorBorders[pos][1]:
                    print(f'Error in {error_list[pos]}. Current - {angle} Waiting angle was in {angleErrorBorders[pos][0]} - {angleErrorBorders[pos][1]}')
                    error_occured = True
                if pos == 3:  ##HardCode ebaniu
                    if angle < angleFinishBorders[0]:
                        stateVariable = True
                elif pos == 7:
                    if stateVariable and angle < angleFinishBorders[0] and not error_occured :
                        self.state = SqutsState.Standing
                        print('ang - ', angle, 'border - ', angleFinishBorders[0])

            elif self.state == SqutsState.Standing:
                if angle < angleErrorBorders[pos][0] or angle > angleErrorBorders[pos][1]:
                    print(f'Error in {error_list[pos]}. Waiting angle was in {angleErrorBorders[pos][0]} - {angleErrorBorders[pos][1]}')
                    error_occured = True
                    self.state = SqutsState.Sitting


                if pos == 3:  ##HardCode ebaniu
                    if angle > angleFinishBorders[1]:
                        stateVariable = True
                elif pos == 7:
                    if stateVariable and angle > angleFinishBorders[1] and not error_occured:
                        self.state = SqutsState.Sitting
                        print('ang - ', angle, 'border - ', angleFinishBorders[0])
                        succ = True

        for pos, el in enumerate(legs):
            point, vis = el

            x, y = point
            xTar, yTar = self.legsPos[pos]
            if vis > 0.4:
                if np.sqrt((x - xTar) ** 2 + (y - yTar) ** 2) > 0.01:
                    self.isExcCorrect.setText("Problem in the heels\nDon't lift your hils of the floor")
                    # self.isExcCorrect.setText('Heels have eyes')
                    succ = False

            xNew = xTar + delta * (x - xTar)
            yNew = yTar + delta * (y - yTar)
            self.legsPos[pos] = [xNew, yNew]

        # for el in back:
        #     len, vis = el
            # if len < lenErrorBorders[0] or len > lenErrorBorders[1]:
            #     print(len, ' - LENG')
        return succ

    def checkSquatMultCam(self, saved, resv):
        error_list = ('Right elbow', 'Right shoulder', 'Right hip', 'Right knee',
                      'Left elbow', 'Left shoulder', 'Left hip', 'Left knee')
        delta = 0.1  ###how to get it?
        angleFinishBorders = (40, 70)
        # angleErrorBorders = [(10, 70), (50, 70), (1, 100), (35, 100),
        #                      (10, 70), (50, 70), (1, 100), (35, 100)]
        angleErrorBorders = [(0, 180), (0, 180), (0, 180), (0, 180),
                             (0, 180), (0, 180), (0, 180), (0, 180)]
        lenErrorBorders = (0.2, 0.46)
        anglesSaved, legsSaved, backSaved = saved[0], saved[1], saved[2]
        anglesResv, legsResv, backResv = resv[0], resv[1], resv[2]
        stateVariable = False
        error_occured = False

        succ = False

        for pos, (el1, el2) in enumerate(zip(anglesSaved, anglesResv)):
            angle1, vis1 = el1
            angle2, vis2 = el2
            angle = angle1 if vis1 > vis2 else angle2
            # cam = camSaved if angle == angle1 else camResv

            if max(vis1, vis2) < 0.5:
                print(f'{error_list[pos]} in dead zone')
                error_occured = True
                # excFinished = False

            if self.state == SqutsState.Sitting:
                if angle < angleErrorBorders[pos][0] or angle > angleErrorBorders[pos][1]:
                    print(f'Error in {error_list[pos]}. Current - {angle} Waiting angle was in {angleErrorBorders[pos][0]} - {angleErrorBorders[pos][1]}')
                    error_occured = True
                if pos == 3:  ##HardCode ebaniu
                    if angle < angleFinishBorders[0]:
                        stateVariable = True
                elif pos == 7:
                    if stateVariable and angle < angleFinishBorders[0] and not error_occured:
                        self.state = SqutsState.Standing

            elif self.state == SqutsState.Standing:
                if angle < angleErrorBorders[pos][0] or angle > angleErrorBorders[pos][1]:
                    print(f'Error in {error_list[pos]}. Waiting angle was in {angleErrorBorders[pos][0]} - {angleErrorBorders[pos][1]}')
                    error_occured = True
                    self.state = SqutsState.Sitting
                if pos == 3:  ##HardCode ebaniu
                    if angle < angleFinishBorders[1]:
                        stateVariable = True
                elif pos == 7:
                    if stateVariable and angle > angleFinishBorders[1]:
                        self.state = SqutsState.Sitting
                        print('ang - ', angle, 'border - ', angleFinishBorders[0])
                        succ = True

        # for pos, (el1, el2) in enumerate(zip(legsSaved, legsResv)):
        #     point1, vis1 = el1
        #     point2, vis2 = el2
        #
        #     point = point1 if vis1 > vis2 else point2
        #     x, y = point
        #     xTar, yTar = self.legsPos[pos]
        #     if np.sqrt((x - xTar) ** 2 + (y - yTar) ** 2) > 0.1:
        #         print('Pyatki')
        #         succ = False
        #
        #     xNew = xTar + delta * (x - xTar)
        #     yNew = yTar + delta * (y - yTar)
        #     self.legsPos[pos] = [xNew, yNew]

        # for el1, el2 in zip(backSaved, backResv):
        #     len1, vis1 = el1
        #     len2, vis2 = el2
        #     leng = len1 if vis1 > vis2 else len2
        #
        #     if leng < lenErrorBorders[0] or leng > lenErrorBorders[1]:
        #         print('Spina v govne')

        return succ

    def create_text_instance(self, labelName: QLabel, labelComment: str):
        frame = QFrame(self)
        hbox = QHBoxLayout()

        comment = QLabel(self)
        comment.setText(labelComment)
        hbox.addWidget(comment)

        hbox.addWidget(labelName)

        frame.setLayout(hbox)
        return frame

    def startEx(self):
        self.buttonSt.setEnabled(False)
        self.messageBot.sendMessage('Trouble')
        self.buttonEn.setEnabled(True)
        self.timer = QTimer(self)
        self.timer.start(3000)
        self.timer.timeout.connect(self.GetCurrentUserPosition)

    def endEx(self):
        self.excCurrentState = ExcersiceState.Waiting
        self.buttonSt.setEnabled(True)
        self.buttonEn.setEnabled(False)

    def GetCurrentUserPosition(self):
        try:
            self.timer.disconnect()
            self.excCurrentState = ExcersiceState.Preparing
        except TypeError:
            pass

    def react(self):
        pass

    def create_button(self, text, react):

        but = QPushButton(text)
        but.clicked.connect(react)
        but.setFont(QFont('Arial', 18))
        but.setFixedSize(QSize(300, 100))
        # self.start.setStyleSheet("QPushButton{border-radius: 20; border: 2px solid black; background-color: Silver;  "
        #                          "selection-color: yellow; selection-background-color: blue;}")
        but.setStyleSheet(
            """
                QPushButton {
                    background-color: #7B9DBF;
                    color: white;
                    border: 2px solid black;
                    border-radius: 20;

                }
                QPushButton:pressed {
                    border-style: inset;
                    background-color: #c2c2c2;
                }
                QPushButton:disabled {
                    background-color:#ff0000;
                }
        """)

        return but

    def initUI(self):

        hbox = QHBoxLayout()

        frameUnity = QFrame(self)
        vboxVideoUnity = QVBoxLayout()

        frameVideo = QFrame(self)
        hboxVideo = QHBoxLayout()

        self.labelFirst = QLabel()
        hboxVideo.addWidget(self.labelFirst)

        if len(self.listCam) == 2:
            self.labelSecond = QLabel()
            hboxVideo.addWidget(self.labelSecond)

        frameVideo.setLayout(hboxVideo)
        vboxVideoUnity.addWidget(frameVideo)

        hboxButtons = QHBoxLayout()

        frameButtons = QFrame(self)



        self.pause = self.create_button('Pause', self.react)
        hboxButtons.addWidget(self.pause)

        self.call = self.create_button('Call trainer', self.react)
        hboxButtons.addWidget(self.call)

        self.finish = self.create_button('Finish', self.react)
        hboxButtons.addWidget(self.finish)


        frameButtons.setLayout(hboxButtons)
        vboxVideoUnity.addWidget(frameButtons)

        hboxInform = QHBoxLayout()
        frameInform = QFrame()

        progName = QLabel("<font color=\"blue\">Digital</font> <font color=\"red\">trainer</font>")
        progName.setFont(QFont("Arial", 26, QFont.Bold))
        hboxInform.addWidget(progName)

        pict_widget = QPixmap('pictures/logo.png')
        pict_widget = pict_widget.scaledToHeight(80)
        lbl = QLabel(self)
        lbl.setPixmap(pict_widget)
        hboxInform.addWidget(lbl)

        frameInform.setLayout(hboxInform)
        vboxVideoUnity.addWidget(frameInform)

        frameUnity.setLayout(vboxVideoUnity)
        hbox.addWidget(frameUnity)

        frameFullInfrom = QFrame()
        vboxInform = QVBoxLayout()


        frameStatistic = QFrame()
        hboxText = QHBoxLayout()

        frameComplete = QFrame()
        vboxComplete = QVBoxLayout()


        CompText = QLabel("<font color=\"blue\">Completed: </font>")
        CompText.setFont(QFont("Arial", 26, QFont.Bold))
        vboxComplete.addWidget(CompText)

        self.NumberAmount = QLabel("<font color=\"red\">0</font>")
        self.NumberAmount.setFont(QFont("Arial", 40, QFont.Bold))
        self.NumberAmount.setAlignment(Qt.AlignCenter)
        vboxComplete.addWidget(self.NumberAmount)

        frameComplete.setLayout(vboxComplete)
        hboxText.addWidget(frameComplete)


        frameStatus = QFrame()
        vboxStatus = QVBoxLayout()


        StatText = QLabel("<font color=\"blue\">Status: </font>")
        StatText.setFont(QFont("Arial", 26, QFont.Bold))
        vboxStatus.addWidget(StatText)

        self.PictureStatus = QLabel()
        pict = QPixmap('pictures/status/suc.jpg')
        self.PictureStatus.setPixmap(pict.scaledToHeight(100))
        self.PictureStatus.setAlignment(Qt.AlignCenter)
        vboxStatus.addWidget(self.PictureStatus)

        frameStatus.setLayout(vboxStatus)
        hboxText.addWidget(frameStatus)

        frameStatistic.setLayout(hboxText)
        vboxInform.addWidget(frameStatistic)

        StateMess = QLabel('State')
        StateMess.setFont(QFont("Arial", 26, QFont.Bold))
        vboxInform.addWidget(StateMess)

        self.ErrorMess = QLabel('Pyatki')
        self.ErrorMess.setFont(QFont("Arial", 26, QFont.Bold))
        vboxInform.addWidget(self.ErrorMess)

        video = QLabel()
        video.setGeometry(QRect(25, 25, 200, 200))
        video.setMinimumSize(QSize(200, 200))
        video.setMaximumSize(QSize(200, 200))
        video.setObjectName("label")

        self.movie = QMovie("pictures/radio.gif")
        video.setMovie(self.movie)
        self.movie.start()

        vboxInform.addWidget(video, alignment=Qt.AlignCenter)
        frameFullInfrom.setLayout(vboxInform)

        hbox.addWidget(frameFullInfrom)

        self.setLayout(hbox)


        self.setGeometry(300, 100, 200, 200)

        th = VideoThreadWork(cam_num=self.listCam[0], parent=self)
        th.changePixmap.connect(self.setImage)
        # th.changeText.connect(self.setText)
        # th.changeTextModern.connect(self.setTextModern)
        # th.startExcercise.connect(self.handExcersice)
        # th.startExcerciseSquats.connect(self.setTextSquats)
        # th.exCounter.connect(self.completeChange)
        th.start()

        if (len(self.listCam) == 2):
            th = VideoThreadWork(cam_num=self.listCam[1], parent=self)
            th.changePixmap.connect(self.setImage)
            # th.changeText.connect(self.setText)
            # th.startExcercise.connect(self.handExcersice)
            # th.changeTextModern.connect(self.setTextModern)
            # th.startExcerciseSquats.connect(self.setTextSquats)
            #
            # th.exCounter.connect(self.completeChange)
            th.start()

        self.show()

