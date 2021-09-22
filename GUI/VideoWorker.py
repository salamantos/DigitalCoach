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

from typing import Tuple, List

right_elbow = [16, 14, 12]
right_shoulder = [14, 12, 24]
left_elbow = [15, 14, 11]
left_shoulder = [13, 11, 23]
right_knee = [24, 26, 28]
right_hip = [12, 24, 26]
left_knee = [23, 25, 27]
left_hip = [11, 23, 25]
left_heel = [29, 31]
right_heel = [30, 32]
right_back = [12, 24]
left_back = [11, 23]


class VideoThreadWork(QThread):
    changePixmap = pyqtSignal(QImage, int)
    changeText = pyqtSignal(list)
    changeTextModern = pyqtSignal(tuple, int, name='text')
    getDict = pyqtSignal(dict)
    exCounter = pyqtSignal(int)
    startExcercise = pyqtSignal(str, str)
    startExcerciseSquats = pyqtSignal(tuple, int, name='squats')


    def __init__(self, cam_num, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cam = cam_num
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose()
        self.stage = -1
        self.res = 'Preparing'
        self.counter = 0
        self.complete = False
        self.mpDraw = mp.solutions.drawing_utils

    def get_new_frame_from_neuron(self, img):
        """
        This function founds pose landmarks, draws them on img and returns them

        Ids from doc: https://google.github.io/mediapipe/solutions/pose.html

        :return: found landmarks
        """
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.pose.process(img_rgb)
        landmarks = {}
        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(
                img, results.pose_landmarks, self.mpPose.POSE_CONNECTIONS
            )
            for mark_id, lm in enumerate(results.pose_landmarks.landmark):
                h, w, c = img.shape
                landmarks[mark_id] = lm
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)

        return landmarks

    def get_angle(self, landmark, joint_list):
        '''

        :param landmark: Counted mediapipes points
        :param joint_list: List of neighbours points, of angle what we need to count
        Middle point - top of the counted angle. Example ([1,2,3], [2,3,4]). In this case we count angle in 2, and 3.
        :return: list of counted angles with errors. Output is [(angle, errorInThisPoint), (error2, errorInThisPoint2),..., ]
        '''
        angle_list = []
        for joint in joint_list:
            a = np.array([landmark[joint[0]].x, landmark[joint[0]].y])  # First coordinate
            b = np.array([landmark[joint[1]].x, landmark[joint[1]].y])  # Second coordinate
            c = np.array([landmark[joint[2]].x, landmark[joint[2]].y])  # Third coordinate

            aError = landmark[joint[0]].visibility
            bError = landmark[joint[1]].visibility
            cError = landmark[joint[2]].visibility

            resError = aError * bError * cError

            radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
            angle = np.abs(radians * 180.0 / np.pi)
            angle = angle - 180 if angle > 180.0 else angle

            angle_list.append((angle, resError))

        return angle_list

    def video_preparing(self, frame, width=640, height=480):
        """
        This function processes video and converting it to QtVideoFormat

        Ids from doc: https://google.github.io/mediapipe/solutions/pose.html

        :return: found landmarks
        """
        rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(
            rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888
        )
        return convertToQtFormat.scaled(width, height, Qt.KeepAspectRatio)

    def get_hand(self, landmarks, left, right):
        accurancy_left = landmarks[left[0]].visibility * landmarks[left[1]].visibility * landmarks[left[2]].visibility
        accurancy_right = landmarks[right[0]].visibility * landmarks[right[1]].visibility * landmarks[
            right[2]].visibility

        if accurancy_left > accurancy_right:
            return 'Left'
        else:
            return 'Right'

    def excersice_dumbbell(self, angList):
        elbow = angList[0][0]
        shoulder = angList[0][1]
        if self.stage == -1 and (shoulder < 15 or shoulder > 170) and elbow > 75:
            self.stage = 0
            return 'Preparation'

        elif self.stage == 0 and (shoulder < 15 or shoulder > 170) and elbow < 75 and elbow > 45:
            self.stage = 1
            self.complete = True
            return 'Upp'
        elif self.stage == 1 and elbow < 45:
            self.stage = -1
            if self.complete:
                self.counter += 1
                self.exCounter.emit(self.counter)
            self.complete = False
            return 'Complete!'

        return None

    def get_leng(self, landmark, joint_list):
        len_list = []
        for joint in joint_list:
            a = np.array([landmark[joint[0]].x, landmark[joint[0]].y])  # First coordinate
            b = np.array([landmark[joint[1]].x, landmark[joint[1]].y])  # Second coordinate

            aError = landmark[joint[0]].visibility
            bError = landmark[joint[1]].visibility

            resError = aError * bError
            len_list.append((int(np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) * 100) / 100, resError))

        return len_list

    def excersice_squats(self, landmark, angList, footPoint: Tuple[List[int], List[int]],
                         backPoint: Tuple[List[int], List[int]]):
        '''
        In this function u need to write functional of squats.
        Use function self.get_angle() to get needed angles

        In result add footPoints(only coordinates)
        Also add len of backPoint (use func get_leng for back)


        :param angList: List with angles, which we need to count
        :param footPoint: Coordinates of foot points.
        :param backPoint: Len of back
        :return:
        '''

        angles = self.get_angle(landmark, angList)
        back = self.get_leng(landmark, backPoint)

        foot_list = []
        for foot in footPoint:
            a = np.array([landmark[foot].x, landmark[foot].y])  # First coordinate

            aError = landmark[foot].visibility

            foot_list.append((a, aError))

        return (angles, foot_list,  back)

        # return Tuple[Counted values: List[...], self.cam]


    def run(self):
        right = ([16, 14, 12], [14, 12, 24])
        left = ([15, 13, 11], [13, 11, 23])
        cap = cv2.VideoCapture(self.cam)
        fps = cap.get(cv2.CAP_PROP_FPS)
        print (f'Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {fps} in camera {self.cam}')
        while True:
            ret, frame = cap.read()
            if ret:
                landmarks = self.get_new_frame_from_neuron(frame)
                # markedQtImage = get_new_frame_from_neuron(frame)

                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(
                    rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888
                )
                markedQtImage = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(markedQtImage, self.cam)

                if landmarks:
                    if self.get_hand(landmarks, left[0], right[0]) == 'Left':
                        active_hand = 'Left'
                        active_points = left
                    else:
                        active_hand = 'Right'
                        active_points = right

                    angList = self.get_angle(landmarks, ([16, 14, 12], [14, 12, 24], [15, 13, 11], [13, 11, 23]))
                    activeAngleList = self.get_angle(landmarks, active_points)  ###Fix it
                    result = self.excersice_squats(landmarks, angList=(right_elbow, right_shoulder, right_hip, right_knee,
                                           left_elbow, left_shoulder, left_hip, left_knee),
                                          footPoint=(right_heel + left_heel), backPoint= (right_back, left_back))
                    self.startExcerciseSquats.emit(result, self.cam)
                    self.changeTextModern.emit(tuple(angList), self.cam)

                    old = self.res
                    self.res = self.excersice_dumbbell(activeAngleList)
                    self.res = self.res if self.res else old
                    self.startExcercise.emit(active_hand, self.res)

                self.getDict.emit(landmarks)

