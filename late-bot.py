# -*- coding: utf-8 -*-
import logging

import os
import re
import telegram
from orm.models import db, Delay, Person, fn
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# const
API_TOKEN = os.environ['API_TOKEN']
MENU, ENTER_DELAY, ENTER_REASON = range(3)

# global vars
state = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# database connect and close
def db_connect_close(func):
    def wrap(*args, **kwargs):
        db.connect()
        func(*args, **kwargs)
        db.close()
    return wrap


# checks
def is_delay_correct(text):
    if re.search('[^0-9](?u)', text):
        return False
    else:
        return True


def is_reason_correct(text):
    if re.search('[^a-zA-Zа-яА-Я](?u)', text):
        return False
    else:
        return True


# db manipulations
def get_or_create_person(message):
    message_from = message.to_dict().get('from')
    username = message_from.get('username')
    first_name = message_from.get('first_name')
    last_name = message_from.get('last_name')
    person, created = Person.get_or_create(
        username=username,
        defaults={
            'first_name': first_name,
            'last_name': last_name
        }
    )
    return person


def create_delay(person, minute):
    Delay.create(person=person, minute=minute)


def create_reason(person, text):
    last_delay = list(person.delays)[-1]
    last_delay.reason = text
    last_delay.save()


@db_connect_close
def main_handler(bot, update):
    person = get_or_create_person(update.message)
    username = person.username
    user_state = state.get(username, MENU)
    text = update.message.text
    chat_id = update.message.chat_id

    if user_state == MENU and re.search('([ао]п[ао][зс]д|задерж)(?iu)', text):
        bot.sendMessage(chat_id, 'Используйте команду /late')

    elif user_state == MENU and text[0] == '/':
        bot.sendMessage(chat_id, 'Введите время задержки в минутах')
        state[username] = ENTER_DELAY

    elif user_state == ENTER_DELAY:
        if is_delay_correct(text):
            minute = int(text)
            create_delay(person, minute)
            bot.sendMessage(chat_id, 'Введите причину задержки')
            state[username] = ENTER_REASON
        else:
            bot.sendMessage(chat_id, 'Введите целое число - минуты задержки')

    elif user_state == ENTER_REASON:
        if is_reason_correct(text):
            create_reason(person, text)
            bot.sendMessage(chat_id, 'Успех!')
            state[username] = MENU
        else:
            bot.sendMessage(chat_id, 'Введите словесную причину, без цифр и '
                                     'остальных символов')


# show users delay stats
@db_connect_close
def show_stats(bot, update):
    chat_id = update.message.chat_id
    for person in Person.select():
        bot.sendMessage(
            chat_id,
            '{} {} @{}: \n'
            '*количество опозданий* - {}, \n'
            '*суммарное время опозданий* - {} минут'.format(
                person.first_name,
                person.last_name,
                person.username,
                person.delays.count(),
                person.delays.aggregate(fn.Sum(Delay.minute))
            ),
            parse_mode='Markdown')


# debug function
def get_upd(bot, update):
    print(update.message)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(API_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("late", main_handler))
    dp.add_handler(CommandHandler("stats", show_stats))
    dp.add_handler(MessageHandler([Filters.text], main_handler))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
