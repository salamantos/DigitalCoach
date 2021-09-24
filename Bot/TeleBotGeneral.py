#!/usr/bin/env python
# coding: utf-8

# In[22]:


import telebot
import pickle
import os

instruction = """Чтобы начать тренировку, напишите 'Cтарт'.

Во время тренировки вы будете получать уведомления о ваших ошибках.

Чтобы завершить тренировку, напишите 'Конец'."""




if __name__ == '__main__':
    print('1')
    if not os.path.exists('users_status.pickle'):
        status_dict = {}
        with open('users_status.pickle', 'wb') as f:
            pickle.dump(status_dict, f)

bot = telebot.TeleBot('1995525153:AAF5OLeRdHAMV2VHHpzL4Klu23MuNxZYWzA')


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "Добро пожаловать в бот проекта 'Digital Trainer'! Начнем занятие?")

@bot.message_handler(commands=['answer'])
def get_answer(message):
    global_err = 1
    id_user = message.chat.id

    print(message.text.lower())
    mes = message.text.lower()
    answ = mes.split(' ')
    # try:
    user, time = int(answ[1]), int(answ[2])
    print(os.path.abspath(os.curdir))
    print(user, time)
    if os.path.exists('help_num.pickle') and os.path.getsize('help_num.pickle'):
        with open('help_num.pickle', 'rb') as f:
            userSet = pickle.load(f)
    else:
        userSet = {}
    print(userSet)
    if time < 11 and user in userSet:
        bot.send_message(message.from_user.id, "Вы выбрали данного клиента")
        with open('help_num.pickle', 'wb') as f:
            userSet.remove(user)
            pickle.dump(userSet, f)
        if os.path.exists('answer.pickle'):
            os.remove('answer.pickle')
        with open('answer.pickle', 'wb') as f:
            answer = [time]
            pickle.dump(answer, f)
    else:
        if time > 11:
            bot.send_message(message.from_user.id, "Слишком долго, оставьте данного клиента другому тренеру")
        else:
            bot.send_message(message.from_user.id, "Данного клиента не существует, либо он не просил промощи")

    # except Exception as e:
    #     print('ERROR - ', e)
    #     bot.send_message(message.from_user.id, "Ответ должен быть в формате /answer X (X - число минут через которое"
    #                                            " вы сможете подойти к клиенту.")



@bot.message_handler(content_types=['text', 'document', 'audio'])
def send_errors(message, critical = False):
    global id_user
    id_user = message.chat.id
    text_lower = message.text.lower()
    # message.text.l
    # print(text_lower, str(text_lower) == "старт")

    if text_lower == "старт":
        bot.send_message(message.from_user.id, "Тренировка началась")
        with open('users_status.pickle', 'rb') as f:
            status_dict = pickle.load(f)
        print('USER ID - ', id_user)
        status_dict[id_user] = True

        with open('users_status.pickle', 'wb') as f:
            pickle.dump(status_dict, f)

    elif text_lower == "конец":
        bot.send_message(message.from_user.id, "Тренировка заночилась")
        with open('users_status.pickle', 'rb') as f:
            status_dict = pickle.load(f)

        status_dict[id_user] = False

        with open('users_status.pickle', 'wb') as f:
            pickle.dump(status_dict, f)

    elif message.text == "/help":
        bot.send_message(message.from_user.id, instruction)

    else:
        bot.send_message(message.from_user.id, "Я Вас не понимаю. Напиши /help.")


bot.polling(none_stop=True, interval=0)
