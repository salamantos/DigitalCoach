import logging
import sys
from functools import partial

import cv2
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap, QFont, QMovie, QIcon
from PyQt5.QtWidgets import *
from enum import Enum

from GUI.App import App
from GUI.TrainerWaitWindow import TimeWindow
from GUI.TrainerWait import TrainerWait
from GUI.WaitFunc import TrainerWaitThreadWork


class ExcersiceStyle(Enum):
    Trainer = 0
    Myself = 1

class ExcersiceType(Enum):
    Hand = 0
    Squats = 1
    AnotherOne = 2
    AnotherTwo = 3
    AnotherThree = 4
    LastOne = 5


StyleSheet = '''
/* Вот общая настройка, все кнопки действительны, но следующее может изменить это */
QPushButton {
    border: none;              /* Удалить границу   */
    # background-position: center bottom;
}
/* QPushButton#xxx , задаются установкой objectName */
MainButton {
    border-radius: 5px;       /* закругленный  */
}
MainButton:hover {
    background-color: #81c784;
    color: #fff;              /*   */
}
MainButton:pressed {
    background-color: #c8e6c9;
}
'''

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.w = None
        self.className = None
        self.init_main()



    @pyqtSlot(int)
    def TrainerWait(self, amount):
        self.className.start(amount)

    def react(self):
        pass

    def trainer_button(self):
        for but in self.exButtons:
           but.setEnabled(False)

        self.soloButton.setEnabled(True)
        self.trainerButton.setEnabled(False)

        self.style = ExcersiceStyle.Trainer


    def own_button(self):
        for but in self.exButtons:
            but.setEnabled(True)

        self.soloButton.setEnabled(False)
        self.trainerButton.setEnabled(True)

        self.style = ExcersiceStyle.Myself
        self.exType = ExcersiceType.Squats
        self.exButtons[self.exType.value].setEnabled(False)


    def exc_button(self, typeEx):
        print(typeEx.value)
        self.exButtons[typeEx.value].setEnabled(False)
        self.exType = typeEx
        print(self.exButtons)
        for pos, but in enumerate(self.exButtons):
            if typeEx.value != pos:
                but.setEnabled(True)


    def create_multi_buttons(self, reaction:tuple, pictNames: tuple) -> tuple:

        frame = QFrame(self)
        hbox = QHBoxLayout()
        buttons = []
        for react, name in zip(reaction, pictNames):
            button = QPushButton('', self, objectName="MainButton", minimumHeight=24)
            button.clicked.connect(react)
            if name:
                button.setIcon(QIcon(name))
                button.setIconSize(QSize(320, 320))

                # button.setStyleSheet(f'background - image: url({name});')
                button.setFixedSize(QSize(320, 320))
                # button.setContentsMargins(0, 0, 0, 0)
            buttons.append(button)
            hbox.addWidget(button)

        frame.setLayout(hbox)
        return (buttons, frame)



    def init_main(self):
        '''
        Данная функция отвечает за создание главного меню
        :return: None
        '''

        mainWigh = QFrame(self)
        vboxMain = QVBoxLayout()

        frameInform = QFrame(self)
        hboxInform = QHBoxLayout()

        progName = QLabel("<font color=\"blue\">Digital</font> <font color=\"red\">trainer</font>")
        progName.setFont(QFont("Arial", 26, QFont.Bold))
        hboxInform.addWidget(progName)

        pict_widget = QPixmap('pictures/logo.png')
        pict_widget = pict_widget.scaledToHeight(80)
        lbl = QLabel(self)
        lbl.setPixmap(pict_widget)
        hboxInform.addWidget(lbl)

        frameInform.setLayout(hboxInform)
        vboxMain.addWidget(frameInform)

        globWidget = QFrame(self)
        hboxGlobal = QHBoxLayout()

        butWidget = QFrame()
        vboxBut = QVBoxLayout()
        self.exButtons = []

        reactions = (partial(self.exc_button, ExcersiceType.Hand), partial(self.exc_button, ExcersiceType.Squats),
                     partial(self.exc_button, ExcersiceType.AnotherOne))

        pictures = ('pictures/buttons/squats.png', 'pictures/buttons/time.png', 'pictures/buttons/run.png')
        exs, frame = self.create_multi_buttons(reactions, pictures)
        self.exButtons += exs
        vboxBut.addWidget(frame)

        reactions = (partial(self.exc_button, ExcersiceType.AnotherTwo), partial(self.exc_button, ExcersiceType.AnotherThree),
                     partial(self.exc_button, ExcersiceType.LastOne))

        pictures = ('pictures/buttons/hand.png', 'pictures/buttons/weight.png', 'pictures/buttons/chill.png')
        exs, frame = self.create_multi_buttons(reactions, pictures)
        self.exButtons += exs
        vboxBut.addWidget(frame)

        butWidget.setLayout(vboxBut)
        hboxGlobal.addWidget(butWidget)
        hboxGlobal.addStretch(1)

        WidgUserOpt = QFrame()
        vboxOpt = QVBoxLayout()


        progName = QLabel("Choose option")
        progName.setFont(QFont("Arial", 20, QFont.Bold))
        vboxOpt.addWidget(progName)
        vboxOpt.addStretch(1)


        self.trainerButton = QPushButton('Work with trainer', self, objectName="MainButton", minimumHeight=48)
        self.trainerButton.clicked.connect(self.trainer_button)
        self.trainerButton.setFont(QFont('Arial', 18))
        self.trainerButton.setStyleSheet(
            """
                QPushButton {
                    background-color: #2E4760;
                    color: white;
                    border: 2px solid black;
                    border-radius: 20;

                }
                QPushButton:pressed {
                    border-style: inset;
                    background-color: #c2c2c2;
                }
                QPushButton:disabled {
                    background-color: #757575;
                }
            """)

        self.trainerButton.setFixedSize(QSize(200, 120))
        vboxOpt.addWidget(self.trainerButton)
        vboxOpt.addStretch(2)

        self.soloButton = QPushButton('Individual work', self, objectName="MainButton", minimumHeight=48)
        self.soloButton.clicked.connect(self.own_button)
        self.soloButton.setStyleSheet(
            """
                QPushButton {
                    background-color:  #7B9DBF;
                    color: white;
                    border: 2px solid black;
                    border-radius: 20;

                }
                QPushButton:pressed {
                    border-style: inset;
                    background-color: #c2c2c2;
                }
                QPushButton:disabled {
                    background-color: #757575;
                }
            """)
        self.soloButton.setFont(QFont('Arial', 18))
        self.soloButton.setFixedSize(QSize(200, 120))
        vboxOpt.addWidget(self.soloButton)

        vboxOpt.addStretch(6)

        self.start = QPushButton('Start!')
        self.start.clicked.connect(self.react)
        self.start.setFont(QFont('Arial', 18))
        self.start.setFixedSize(QSize(200, 200))
        # self.start.setStyleSheet("QPushButton{border-radius: 20; border: 2px solid black; background-color: Silver;  "
        #                          "selection-color: yellow; selection-background-color: blue;}")
        self.start.setStyleSheet(
            """
                QPushButton {
                    background-color: #FF0000;
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

        self.start.clicked.connect(self.start_training)
        vboxOpt.addWidget(self.start)
        WidgUserOpt.setLayout(vboxOpt)



        hboxGlobal.addWidget(WidgUserOpt)
        globWidget.setLayout(hboxGlobal)
        vboxMain.addWidget(globWidget)


        # messages = ('Another One', 'Last One')
        # reactions = (partial(self.exc_button, ExcersiceType.AnotherOne), partial(self.exc_button, ExcersiceType.LastOne))
        #
        # exs, frame = self.create_multi_buttons(messages, reactions)
        # self.exButtons += exs
        # vboxMain.addWidget(frame)


        # messages = ('Start', 'End')
        # reactions = (self.start_training, lambda: `QCoreApplication.instance().quit()`)

        # vboxMain.addWidget(self.create_multi_buttons(messages, reactions)[1])

        mainWigh.setLayout(vboxMain)
        # self.trainer_button()
        self.setCentralWidget(mainWigh)
        self.setGeometry(600, 300, 120, 200)
        self.setWindowTitle('Main Window')
        self.show()



    def start_training(self):
        if self.style == ExcersiceStyle.Trainer:
            TrainerWait().send_message_to_trainer('0')
            th = TrainerWaitThreadWork()
            th.getAnswer.connect(self.TrainerWait)
            th.start()
            self.className = TimeWindow()

        elif self.style == ExcersiceStyle.Myself:
            self.camera_launch()

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
        cameras = [0, 2]
        # cameras = [0]
        # self.w = App(cameras)
        ##Add Excercise
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
