#!/usr/bin/env python
# coding: utf-8

# In[22]:


import telebot
import pickle

instruction = """Чтобы начать тренировку, напишите 'Cтарт'.

Во время тренировки вы будете получать уведомления о ваших ошибках.

Чтобы завершить тренировку, напишите 'Конец'."""

bot = telebot.TeleBot('1995525153:AAF5OLeRdHAMV2VHHpzL4Klu23MuNxZYWzA')


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "Добро пожаловать в бот проекта 'Digital Trainer'! Начнем занятие?")


@bot.message_handler(content_types=['text', 'document', 'audio'])
def send_errors(message):
    global id_user
    id_user = message.chat.id
    active = False
    text_lower = message.text.lower()
    # message.text.l
    # print(text_lower, str(text_lower) == "старт")

    if text_lower == "старт":
        active = True
        bot.send_message(message.from_user.id, "Тренировка началась")
        with open('users_status.pickle', 'rb') as f:
            status_dict = pickle.load(f)

        status_dict[id_user] = active

        with open('users_status.pickle', 'wb') as f:
            pickle.dump(status_dict, f)

    elif text_lower == "конец":
        active = False
        bot.send_message(message.from_user.id, "Тренировка заночилась")
        with open('users_status.pickle', 'rb') as f:
            status_dict = pickle.load(f)

        status_dict[id_user] = active

        with open('users_status.pickle', 'wb') as f:
            pickle.dump(status_dict, f)

    elif message.text == "/help":
        bot.send_message(message.from_user.id, instruction)

    else:
        bot.send_message(message.from_user.id, "Я Вас не понимаю. Напиши /help.")


bot.polling(none_stop=True, interval=0)

# In[ ]:



