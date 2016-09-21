# -*- coding: utf-8 -*-
import logging
import os
import re

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from orm.models import db, Delay, Person, fn

# const
API_TOKEN = os.environ['API_TOKEN']
ADMIN_IDS = [845871, 948469]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def db_connect_close(func):
    """
    Decorator for start connection with database, manipulation with data and
    close connection
    """
    def wrap(*args, **kwargs):
        db.connect()
        func(*args, **kwargs)
        db.close()
    return wrap


def get_or_create_person(message):
    """
    Saves or retrieves Person from database

    Returns: Person instance

    """
    user_id = message.get('id')
    username = message.get('username')
    first_name = message.get('first_name')
    last_name = message.get('last_name')
    person, created = Person.get_or_create(
        user_id=user_id,
        defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name
        }
    )
    return person


def extract_hours(text):
    """
    Extracts hours from message

    Returns: hour count
    """
    hour = re.search('час(?iu)', text)
    half_hour = re.search('полу? ?час(?iu)', text)
    num = re.search('\d+(?u)', text)
    if half_hour:
        return 0.5
    elif num and hour and num.start() < hour.start():
        return int(num.group())
    elif hour:
        return 1
    else:
        return 0


def extract_minutes(text):
    """
    Extracts minutes from message

    Returns: minute count
    """
    minute = re.search('мин(?iu)', text)
    num = re.findall('\d+', text)
    if minute and num:
        return int(num[-1])
    else:
        return 0


def save_delay(person, hours, minutes):
    """
    Saves delay of person
    """
    minutes += hours * 60
    Delay.create(minute=minutes, person=person)


@db_connect_close
def sorry_guys(bot, update, args):
    chat_id = update.message.chat_id
    admin_id = update.message.to_dict('from').get('id')
    user_id = args[0]
    minutes = args[1]
    if admin_id in ADMIN_IDS:
        person = Person.get(user_id=user_id)
        delay = Delay.create(minute=minutes, person=person)
        bot.sendMessage(
            chat_id,
            'Опоздание {} на {} минут зарегистрировано!'.format(
                person.username,
                delay.minute
            )
        )
    else:
        bot.sendMessage(
            chat_id,
            'Недостаточно прав :('
        )


@db_connect_close
def main_handler(bot, update):
    person = get_or_create_person(update.message.to_dict().get('from'))
    text = update.message.text
    chat_id = update.message.chat_id
    debug_update(bot, update)
    if re.search('([ао]п[ао][зс]д|задерж)(?iu)', text):
        hours = extract_hours(text)
        minutes = extract_minutes(text)
        save_delay(person, hours, minutes)
        bot.sendMessage(
            chat_id,
            '*Ваше опоздание зарегистрировано!*',
            parse_mode='Markdown'
        )


# show users delay stats
@db_connect_close
def show_stats(bot, update):
    chat_id = update.message.chat_id
    for person in Person.select():
        if person.delays.count() != 0:
            bot.sendMessage(
                chat_id,
                '{} {} @{} @{}: \n'
                '*количество опозданий* - {}, \n'
                '*суммарное время опозданий* - {} минут'.format(
                    person.first_name,
                    person.last_name,
                    person.username,
                    person.user_id,
                    person.delays.count(),
                    person.delays.aggregate(fn.Sum(Delay.minute))
                ),
                parse_mode='Markdown'
            )


# debug function
def debug_update(bot, update):
    print(update.message)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(API_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("stats", show_stats))
    dp.add_handler(CommandHandler("sorry_guys", sorry_guys, pass_args=True))
    dp.add_handler(MessageHandler([Filters.text], main_handler))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
