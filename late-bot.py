# -*- coding: utf-8 -*-
import logging

import os
from telegram.ext import Updater, MessageHandler, Filters

API_TOKEN = os.environ['API_TOKEN']

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def message_handler(bot, update):
    pass


def get_upd(bot, update):
    print(update.message)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(API_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler([Filters.text], message_handler))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
