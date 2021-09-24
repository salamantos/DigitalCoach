import os
import pickle

from PyQt5.QtCore import QThread, pyqtSignal


class TrainerWaitThreadWork(QThread):
    getAnswer = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self):
        while (not os.path.exists('Bot/answer.pickle')) or (not os.path.getsize('Bot/answer.pickle') > 0):
            pass
        with open('Bot/answer.pickle', 'rb') as f:
            userdata = pickle.load(f)
            result = userdata[0]

        self.getAnswer.emit(int(result))

