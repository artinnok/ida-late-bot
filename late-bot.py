# -*- coding: utf-8 -*-
import logging
import os
import re

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from orm.models import db, Delay, Person, fn

# const
API_TOKEN = os.environ['API_TOKEN']
MENU, ENTER_DELAY, ENTER_REASON = range(3)

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


def extract_delay_num(text):
    


@db_connect_close
def main_handler(bot, update):
    person = get_or_create_person(update.message)
    text = update.message.text

    if re.search('([ао]п[ао][зс]д|задерж)(?iu)', text):
        num = extract_delay_num(text)
        type = extract_delay_type()
        minutes = convert_num(num, type)
        reason = extract_reason()
        save_delay(user, minutes, reason)


# show users delay stats
@db_connect_close
def show_stats(bot, update):
    chat_id = update.message.chat_id
    for person in Person.select():
        if person.delays.count() != 0:
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
def debug_update(bot, update):
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
