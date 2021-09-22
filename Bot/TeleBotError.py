#!/usr/bin/env python
# coding: utf-8

# In[1]:


import telebot
import pickle


def mailing(error, chat_id):
    bot = telebot.TeleBot('1995525153:AAF5OLeRdHAMV2VHHpzL4Klu23MuNxZYWzA')
    # @bot.message_handler(content_types=['text', 'document', 'audio'])
    bot.send_message(chat_id, error)


with open('users_status.pickle', 'rb') as f:
    status_dict = pickle.load(f)


error = 'пятки оторвал'
chat_id = 263835049

if chat_id in status_dict.keys() and status_dict[chat_id]:
    mailing(error, chat_id)
