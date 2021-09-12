import logging
import sys

import cv2
import mediapipe as mp
import numpy as np
import copy
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import *


class Thread(QThread):
    changePixmap = pyqtSignal(tuple)
    changeText = pyqtSignal(list)

    def __init__(self, cam_num, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cam = cam_num
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose()
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
            a = np.array([landmark[joint[0]].x,landmark[joint[0]].y]) # First coordinate
            b = np.array([landmark[joint[1]].x,landmark[joint[1]].y]) # Second coordinate
            c = np.array([landmark[joint[2]].x,landmark[joint[2]].y]) # Third coordinate

            radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
            angle = np.abs(radians*180.0/np.pi)
            angle = angle - 180 if angle > 180.0 else angle

            angle_list.append(angle)


        return angle_list

    def video_preapring(self, frame, width=640, height=480):
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

    def run(self):
        cap = cv2.VideoCapture(self.cam)

        while True:
            ret, frame = cap.read()

            if ret:
                clearQtImage = self.video_preapring(copy.deepcopy(frame))
                landmarks = self.get_new_frame_from_neuron(frame)
                markedQtImage = self.video_preapring(frame)
                imageTuple = (clearQtImage, markedQtImage)
                self.changePixmap.emit(imageTuple)
                if landmarks:
                    angList = self.get_angle(landmarks, ([16,14,12], [14,12,24], [15,13,11], [13, 11, 23]))
                    self.changeText.emit(angList)

                # bright = (
                #         int(frame[320, 240, 0]) +
                #         int(frame[320, 240, 1]) +
                #         int(frame[320, 240, 2])
                # )
                # print(frame[320, 240, 0], frame[320, 240, 1],
                #       frame[320, 240, 2], bright)
                #
                # if bright > 400:
                #     self.changeText.emit('Too bright')
                # elif bright < 120:
                #     self.changeText.emit('Too dark')
                # else:
                #     self.changeText.emit('Everything is Okay')



class App(QWidget):
    def __init__(self, cam_id=0):
        super().__init__()
        self.cam_id = cam_id
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


        frame.setLayout(vbox)
        hbox.addWidget(frame)
        self.setLayout(hbox)

        self.setGeometry(300, 100, 200, 200)
        th = Thread(cam_num=self.cam_id, parent=self)
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
        cameras = self.return_camera_indexes(4)
        # if self.w is None:
        # for el in cameras:
        self.w = App(cameras[0])
        self.w.show()

        self.c = App(cameras[1])
        self.c.show()

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
