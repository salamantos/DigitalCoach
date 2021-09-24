import os

import telebot
import pickle

class Mail():
    def __init__(self):
        self.bot = telebot.TeleBot('1995525153:AAF5OLeRdHAMV2VHHpzL4Klu23MuNxZYWzA')


    def sendMessage(self, error, critical = False, userNum = 0):
        status_dict = self.getCurrentUsers()
        if not status_dict:
            return False
        if critical:
            if os.path.exists('Bot/help_num.pickle'):
                with open('Bot/help_num.pickle', 'rb') as f:
                    user_list = pickle.load(f)
            else:
                user_list = set()
            print(user_list)
            with open('Bot/help_num.pickle', 'wb') as f:
                user_list = set(user_list)
                user_list.add(int(userNum))
                pickle.dump(user_list, f)
        print(user_list)
        for key in status_dict.keys():
            if status_dict[key]:
                self.bot.send_message(key, error)
        return True

    def getCurrentUsers(self):
        # with open('users_status.pickle', 'rb') as f:
        with open('Bot/users_status.pickle', 'rb') as f:
            status_dict = pickle.load(f)
        print(status_dict)
        return status_dict

