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


class VideoWorker(QThread):
    changePixmap = pyqtSignal(tuple)
    changeText = pyqtSignal(list)
    getDict = pyqtSignal(dict)
    exCounter = pyqtSignal(int)
    startExcercise = pyqtSignal(str, str)

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
        angle_list = []
        for joint in joint_list:
            a = np.array([landmark[joint[0]].x, landmark[joint[0]].y])  # First coordinate
            b = np.array([landmark[joint[1]].x, landmark[joint[1]].y])  # Second coordinate
            c = np.array([landmark[joint[2]].x, landmark[joint[2]].y])  # Third coordinate

            radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
            angle = np.abs(radians * 180.0 / np.pi)
            angle = angle - 180 if angle > 180.0 else angle

            angle_list.append(angle)

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
        accurancy_left =landmarks[left[0]].visibility * landmarks[left[1]].visibility * landmarks[left[2]].visibility
        accurancy_right =landmarks[right[0]].visibility * landmarks[right[1]].visibility * landmarks[right[2]].visibility

        if accurancy_left > accurancy_right:
            return 'Left'
        else:
            return 'Right'

    def excersice_dumbbell(self, angList):
        elbow = angList[0]
        shoulder = angList[1]
        print(elbow, shoulder)
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
                print(self.counter)
                self.exCounter.emit(self.counter)
            self.complete = False
            return 'Complete!'

        return None


    def run(self):
        right = ([16, 14, 12], [14, 12, 24])
        left = ([15, 13, 11], [13, 11, 23])
        cap = cv2.VideoCapture(self.cam)
        while True:
            ret, frame = cap.read()
            if ret:
                # clearQtImage = self.video_preparing(frame))
                landmarks = self.get_new_frame_from_neuron(frame)
                markedQtImage = self.video_preparing(frame)
                # markedQtImage = get_new_frame_from_neuron(frame)

                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(
                    rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888
                )
                markedQtImage = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                # self.changePixmap.emit(p)
                # clearQtImage = markedQtImage
                clearQtImage = markedQtImage
                imageTuple = (clearQtImage, markedQtImage)
                self.changePixmap.emit(imageTuple)

                if landmarks:
                    if self.get_hand(landmarks, left[0], right[0]) == 'Left':
                        active_hand = 'Left'
                        active_points = left
                    else:
                        active_hand = 'Right'
                        active_points = right

                    angList = self.get_angle(landmarks, ([16, 14, 12], [14, 12, 24], [15, 13, 11], [13, 11, 23]))
                    activeAngleList = self.get_angle(landmarks, active_points) ###Fix it
                    self.changeText.emit(angList)
                    old = self.res
                    self.res = self.excersice_dumbbell(activeAngleList)
                    self.res = self.res if self.res else old
                    self.startExcercise.emit(active_hand, self.res)


                self.getDict.emit(landmarks)

