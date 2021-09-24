from Bot.TeleBotError import Mail


class TrainerWait():
    def __init__(self):
        self.messageBot = Mail()


    def send_message_to_trainer(self, camNum):
        if (self.messageBot.sendMessage(f'We need help on camera {camNum}', critical=True, userNum=camNum) ):
            return True

        else:
            return False

