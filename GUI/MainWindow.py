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

class ExrProcessing():

    def __init__(self, req_ang_start, req_ang_proc, req_ang_end, req_dist, key_angle_name, req_coord):
        self.key_angle_name = key_angle_name #['left_knee', -1]
        self.key_angle = []
        self.key_angle_new = 0
        self.key_angle_old = 0
        self.req_ang_start = req_ang_start #{left_knee: [90,120], right_knee: [90,120]}
        self.req_ang_proc = req_ang_proc #{left_knee: [90,120], right_knee: [90,120]}
        self.req_ang_end = req_ang_end #{left_knee: [90,120], right_knee: [90,120]}
        self.req_dist = req_dist # distances to be maintained [[33,32],[45,44]]
        self.req_coord = req_coord # coordinates wich have to be fixed [33,23,45]
        self.stage1 = None
        self.stage2 = None
        self.right_start_position = False
        self.dist = []
        self.start = 0
        self.fixed_distances =[]
        self.fixed_coordinates = []
        self.condition = 0
        self.done_exercises = 0
        self.start_stage = {}
        self.all_joints = {
                'left_armpit': [13, 11, 23],
                'right_ armpit': [14, 12, 24],
                'left_shoulder': [13, 11, 12],
                'right_ shoulder': [14, 12, 11],
                'left_elbow': [11, 13, 15],
                'right_elbow': [12, 14, 16],
                'left_wrist': [13, 15, 17],
                'right_wrist': [14, 16, 18],
                'left_brush': [13, 15, 21],
                'right_brush': [14, 16, 22],
                'left_carpus': [13, 15, 19],
                'right_carpus': [14, 16, 20],
                'left_pinky': [15, 17, 19],
                'right_pinky': [16, 18, 20],
                'left_hip': [11, 23, 25],
                'right_hip': [12, 24, 26],
                'left_frame': [11, 23, 24],
                'right_frame': [12, 24, 23],
                'left_knee': [23, 25, 27],
                'right_knee': [24, 26, 28],
                'left_bridge': [25, 27, 31],
                'right_bridge': [26, 28, 32],
                'left_ankle': [25, 27, 29],
                'right_ankle': [26, 28, 30],
                'left_heel': [27, 29, 31],
                'right_heel': [28, 30, 32],
                'left_foot_index': [27, 31, 29],
                'right_foot_index': [28, 32, 30],
                }

    def get_distans(self, landmark1 , landmark2, coord1, coord2):

        Error1_1 = landmark1[coord1].visibility
        Error2_2 = landmark2[coord2].visibility
        Error2_1 = landmark2[coord1].visibility
        Error1_2 = landmark1[coord2].visibility

        Error1 = Error1_2 * Error1_1
        Error2 = Error2_2 * Error2_1

        if max(Error1, Error2) < 0.5:
            #print(f'{coord2, coord1} in dead zone')
            error_occured = True
            # excFinished = False
            #####stop doing function
        if Error1 > Error2:
            landmark = landmark1
        else:
            landmark = landmark2

        x1, y1 = landmark[coord1].x, landmark[coord1].y
        x2, y2 = landmark[coord2].x, landmark[coord2].y
        dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        return dist


    def get_angle(self, joint_list, landmark1, landmark2):
        '''
        :param landmark: Counted mediapipes points
        :param joint_list: List of neighbours points, of angle what we need to count
        Middle point - top of the counted angle. Example ([1,2,3], [2,3,4]). In this case we count angle in 2, and 3.
        :return: list of counted angles with errors. Output is [(angle, errorInThisPoint), (error2, errorInThisPoint2),..., ]
        '''
        aError1 = landmark1[joint_list[0]].visibility
        bError1 = landmark1[joint_list[1]].visibility
        cError1 = landmark1[joint_list[2]].visibility

        resError1 = aError1 * bError1 * cError1


        aError2 = landmark2[joint_list[0]].visibility
        bError2 = landmark2[joint_list[1]].visibility
        cError2 = landmark2[joint_list[2]].visibility

        resError2 = aError2 * bError2 * cError2

        if max(resError1, resError2) < 0.5:
            #print(f'{joint_list} in dead zone')
            error_occured = True
            # excFinished = False
            #####stop doing function
        if resError1 > resError2:
            landmark = landmark1
        else:
            landmark = landmark2

        a = np.array([landmark[joint_list[0]].x,
                      landmark[joint_list[0]].y])  # First coordinate
        b = np.array([landmark[joint_list[1]].x,
                      landmark[joint_list[1]].y])  # Second coordinate
        c = np.array([landmark[joint_list[2]].x,
                      landmark[joint_list[2]].y])  # Third coordinate

        aError = landmark[joint_list[0]].visibility
        bError = landmark[joint_list[1]].visibility
        cError = landmark[joint_list[2]].visibility

        resError = aError * bError * cError

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(
            a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        angle = angle - 180 if angle > 180.0 else angle

        return angle

    def get_coordinates(self,landmark1, landmark2, point):
        coord = []
        Error1 = landmark1[point].visibility
        Error2 = landmark2[point].visibility

        if max(Error1, Error2) < 0.5:
            #print(f'{point} in dead zone')
            error_occured = True
            # excFinished = False
            #####stop doing function
        if Error1 > Error2:
            landmark = landmark1
        else:
            landmark = landmark2

        coord.append(landmark[point].x)
        coord.append(landmark[point].y)
        coord.append(landmark[point].z)

        return coord

    def startPosition(self, landmark1, landmark2):
        print('im in start')
        self.stage1 = landmark1
        self.stage2 = landmark2
        self.key_angle_old = self.get_angle(self.key_angle, landmark1, landmark2)
        if self.req_coord != []:
            for point in self.req_coord:
                self.fixed_coordinates.append(self.get_coordinates(landmark1, landmark2, point))
        if self.req_dist != []:
            for points in self.req_dist:
                self.fixed_distances.append(self.get_distans(landmark1,landmark2, points[0], points[1]))


    def analyzeProc(self, landmark1, landmark2):


        self.key_angle_new = self.get_angle(self.key_angle, landmark1, landmark2)

        if self.key_angle_name[1] * (self.key_angle_old - self.key_angle_new) < 0:
            #print('hand down')
            self.key_angle_old = self.key_angle_new
            self.stage1 = landmark1
            self.stage2 = landmark2


        elif self.key_angle_name[1] * (self.key_angle_old - self.key_angle_new) > 10:
            self.condition = 1
            #print('hand stop')
            stateVariable = False
            error_occured = False

            succ = False
            for key, value in self.req_ang_proc.items():
                angle = self.get_angle(self.all_joints[key], landmark1, landmark2)
                if value[1] < angle or value[0] > angle:
                    print(
                        f'Error in {key}. Current - {angle} Waiting angle was in {value[0]} - {value[1]}')
                    #print('mistake in procccccccccccccccc')
                    error_occured = True


    def analyzeEnd(self, landmark1, landmark2):
        #print('im in end')
        self.key_angle_new = self.get_angle(self.key_angle, landmark1, landmark2)
        #self.done_exercises += 1
        if self.key_angle_name[1] * (
                self.key_angle_old - self.key_angle_new) > 0:
            #print('hand up')
            self.key_angle_old = self.key_angle_new
            self.stage1 = landmark1
            self.stage2 = landmark2

        elif self.key_angle_name[1] * (
                self.key_angle_old - self.key_angle_new) < 10:
            #print('hand stop')

            stateVariable = False
            error_occured = False

            succ = False
            for key, value in self.req_ang_end.items():
                angle = self.get_angle(self.all_joints[key], landmark1,
                                       landmark2)
                if value[1] < angle or value[0] > angle:
                    print(
                        f'Error in {key}. Current - {angle} Waiting angle was in {value[0]} - {value[1]}')
                    #print('mistake in enddddddddddddddddddddd')

                    error_occured = True
            self.condition = 0
            self.done_exercises += 1
            print(self.done_exercises)

    def analyzeDist(self, landmark1, landmark2):

        delta = 0.1
        distances = []
        i = 0
        for points in self.req_dist:
            distances.append(
                self.get_distans(landmark1, landmark2, points[0],
                                 points[1]))
            #print(self.fixed_distances, distances[i])
            if abs(distances[i] - self.fixed_distances[i]) > delta:
                #print(
                #    f'Error in distance {i}.')
                continue
            i += 1
            #self.isExcCorrect.setText('Heels have eyes')
            succ = False

    def analyzeCoordinates(self, landmark1, landmark2):
        coordinates = []
        i = 0
        delta = 0.01
        for point in self.req_coord:
            coordinates.append(self.get_coordinates(landmark1, landmark2, point))
            #print(self.fixed_coordinates, coordinates)
            if (coordinates[i][0] - self.fixed_coordinates[i][0])**2 + (coordinates[i][1] - self.fixed_coordinates[i][1])**2 > delta:
                #print(f'Error in coordinate {i}.')
                continue

            self.fixed_coordinates[i][0] = self.fixed_coordinates[i][0] + 0.01 * (coordinates[i][0] - self.fixed_coordinates[i][0])
            self.fixed_coordinates[i][1] = self.fixed_coordinates[i][1] + 0.01 * (coordinates[i][1] - self.fixed_coordinates[i][1])
            i += 1

    def analyzeStart(self, landmark1, landmark2):

        for key, value in self.req_ang_start.items():
            print(value)
            self.right_start_position = True

            if self.get_angle(self.all_joints[key], landmark1,landmark2) < value[0] or self.get_angle(self.all_joints[key], landmark1,landmark2) > \
                        value[1]:
                print(f'{key} is wrong on start')

                self.right_start_position = False
            if self.right_start_position:
                print('You can start')
                self.startPosition(landmark1, landmark2)
                self.right_start_position = True


    def startAnalyze(self, landmark1, landmark2):
        self.key_angle = self.all_joints[self.key_angle_name[0]]

        #self.startPosition(landmark1, landmark2)
        #gde-to nado vivodit na ekran 1..2..3..start

    def continueAnalyze(self, landmark1, landmark2):

        if self.right_start_position == False:
            self.analyzeStart(landmark1, landmark2)
        elif self.condition == 0:
            self.analyzeProc(landmark1, landmark2)
            self.analyzeDist(landmark1, landmark2)  # smotrit na spinu i pyatki
            self.analyzeCoordinates(landmark1, landmark2)
        else:
            self.analyzeEnd(landmark1, landmark2)
            self.analyzeDist(landmark1, landmark2)  # smotrit na spinu i pyatki
            self.analyzeCoordinates(landmark1, landmark2)

class App(QWidget):
    def __init__(self, cam_list):
        super().__init__()
        self.listCam = cam_list
        self.landmarks = None
        self.val = 0
        self.exercise =  ExrProcessing(req_ang_start= {'right_elbow':[80, 110]},req_ang_proc={'right_elbow':[40, 60]},req_ang_end={'right_elbow':[80, 110]}, req_dist=[], req_coord=[], key_angle_name=['right_elbow', -1])
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

    @pyqtSlot(dict, int, name='squats')
    def setTextSquats(self, dict, num):
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
            if self.val == 0:
                self.exercise.startAnalyze(dict, dict)
                self.val = 1
            else:
                self.exercise.continueAnalyze(dict, dict)
                self.amount = self.exercise.done_exercises
                self.completeNum.setText(str(self.amount))
                self.isExcCorrect.setText(str('Message'))


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
        #error_list = ('Right elbow', 'Right shoulder', 'Right hip', 'Right knee',
        #             'Left elbow', 'Left shoulder', 'Left hip', 'Left knee')
        # angleErrorBorders = [(10, 70), (50, 70), (1, 100), (35, 100),
        #                      (10, 70), (50, 70), (1, 100), (35, 100)]
        #angleErrorBorders = [(1, 180), (1, 180), (1, 180), (1, 180),
        #                     (1, 180), (1, 180), (1, 180), (5, 180)]
        lenErrorBorders = (0.2, 0.46)
        angles, legs, back = saved[0], saved[1], saved[2]
        stateVariable = False
        succ = False
        error_occured = False

        for pos, el in enumerate(angles):
            angle, vis = el
            # cam = camSaved if angle == angle1 else camResv
            if vis < 0.4:
                #print(f'{error_list[pos]} in dead zone')
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
        #delta = 0.1  ###how to get it?
        #angleFinishBorders = (40, 70)
        #angleErrorBorders = [(10, 70), (50, 70), (1, 100), (35, 100),
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
                #print(f'{error_list[pos]} in dead zone')
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
        cameras = self.return_camera_indexes(40) ### Trying to find cameras port
        print(cameras)
        # cameras = [0, 2]
        cameras = [0]
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