#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from telegram.ext import Dispatcher
from telegram.ext import Updater
from modules.events.event_command import EventCommand
from modules.events.event_inline import EventInline
from services.util import *

# Set up logging config used by python-telegram-bot
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Load all handlers of specific module
def load_modules(dispatcher: Dispatcher, modules: list):
    for module in modules:
        for handler in module.get_handlers():
            dispatcher.add_handler(handler)


def main():
    updater = Updater(config['telegram']['token'])
    dispatcher = updater.dispatcher

    load_modules(dispatcher,
                 [
                     EventCommand(config['permissions']['events']),
                     EventInline(config['permissions']['events'])
                 ])

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
