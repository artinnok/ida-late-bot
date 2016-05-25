# -*- coding: utf-8 -*-
import logging

import os
import re
from orm.models import db, Delay, Person
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


def connect_close(fn):
    def wrap(*args, **kwargs):
        db.connect()
        fn(*args, **kwargs)
        db.close()
    return wrap


def get_or_create_person(message):
    username = message.to_dict().get('from').get('username')
    first_name = message.to_dict().get('from').get('first_name')
    last_name = message.to_dict().get('from').get('last_name')
    person, created = Person.get_or_create(
        username=username,
        defaults={
            'first_name': first_name,
            'last_name': last_name
        }
    )
    return person


def enter_delay(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        text='Введите время задержки в минутах'
    )


def is_delay_correct(text):
    if re.search('[^0-9](?u)', text):
        return False
    else:
        return True


def create_delay(person, minute):
    Delay.create(person=person, minute=minute)


def enter_reason(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        text='Введите причину задержки'
    )


def retry_enter_delay(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        text='Введите целое число - минуты задержки'
    )


def is_reason_correct(text):
    if re.search('[^a-zA-Zа-яА-Я](?u)', text):
        return False
    else:
        return True


def create_reason(username, text):
    person = Person.get(username=username)
    last_delay = list(person.delays)[-1]
    last_delay.reason = text
    last_delay.save()


def finish(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        text='Успех!'
    )


def retry_enter_reason(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        text='Введите словесную причину, без цифр и остальных символов'
    )


@connect_close
def main_handler(bot, update):
    person = get_or_create_person(update.message)
    username = update.message.to_dict().get('from').get('username')
    user_state = state.get(username, MENU)
    text = update.message.text

    if user_state == MENU:
        enter_delay(bot, update)
        state[username] = ENTER_DELAY
    elif user_state == ENTER_DELAY:
        if is_delay_correct(text):
            minute = int(text)
            create_delay(person, minute)
            enter_reason(bot, update)
            state[username] = ENTER_REASON
        else:
            retry_enter_delay(bot, update)

    elif user_state == ENTER_REASON:
        if is_reason_correct(text):
            create_reason(username, text)
            finish(bot, update)
            state[username] = MENU
        else:
            retry_enter_reason(bot, update)


def get_upd(bot, update):
    print(update.message)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(API_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("late", main_handler))
    dp.add_handler(MessageHandler([Filters.text], main_handler))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
