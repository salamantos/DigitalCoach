import logging
import sys

import cv2
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import *
from enum import Enum

from GUI.VideoWorker import VideoThreadWork


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
        if num == 0:
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
        self.buttonStHand.setEnabled(False)
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



    def initUI(self):

        hbox = QHBoxLayout()

        self.labelFirst = QLabel()
        hbox.addWidget(self.labelFirst)

        if len(self.listCam) == 2:
            self.labelSecond = QLabel()
            hbox.addWidget(self.labelSecond)

        self.setWindowTitle('Camera')
        # create a label

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

        self.buttonSt = QPushButton('Start squats')
        self.buttonSt.clicked.connect(self.startEx)
        vbox.addWidget(self.buttonSt)

        self.buttonStHand = QPushButton('Start hand exc')
        self.buttonStHand.clicked.connect(self.startEx)
        vbox.addWidget(self.buttonStHand)

        self.buttonEn = QPushButton('End exc')
        self.buttonEn.clicked.connect(self.endEx)
        self.buttonEn.setEnabled(False)
        vbox.addWidget(self.buttonEn)

        self.setGeometry(300, 100, 200, 200)

        th = VideoThreadWork(cam_num=self.listCam[0], parent=self)
        th.changePixmap.connect(self.setImage)
        th.changeText.connect(self.setText)
        th.changeTextModern.connect(self.setTextModern)
        th.startExcercise.connect(self.handExcersice)
        th.startExcerciseSquats.connect(self.setTextSquats)
        th.exCounter.connect(self.completeChange)
        th.start()

        if (len(self.listCam) == 2):
            th = VideoThreadWork(cam_num=self.listCam[1], parent=self)
            th.changePixmap.connect(self.setImage)
            th.changeText.connect(self.setText)
            th.startExcercise.connect(self.handExcersice)
            th.changeTextModern.connect(self.setTextModern)
            th.startExcerciseSquats.connect(self.setTextSquats)

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
        # cameras = [0]
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
