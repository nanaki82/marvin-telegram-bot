import time

from telegram import Bot
from telegram import ReplyKeyboardRemove
from telegram import Update
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from typing import Tuple, Dict
from datetime import datetime

from exceptions import NoDraftExistError
from modules.events.event_model import Event
from modules.events.event_repository import EventRepository


TITLE, DESCRIPTION, DATETIME, LOCATION = range(4)


class EventCommand:
    handlers = []
    permissions = []

    def __init__(self, permissions: Dict[str, str]):
        self.handlers = [
            CommandHandler('reminder', self.reminder_command, pass_args=True, pass_job_queue=True, pass_chat_data=True),
            ConversationHandler(
                per_chat=False,
                entry_points=[CommandHandler('create', self.create_new_command, pass_args=True)],
                states={
                    TITLE: [MessageHandler(Filters.text, self.set_title)],
                    DESCRIPTION: [MessageHandler(Filters.text, self.set_description),
                                  CommandHandler('skip', self.skip_desc_command)],
                    DATETIME: [MessageHandler(Filters.text, self.set_datetime)],
                    LOCATION: [MessageHandler(Filters.text, self.set_location),
                               CommandHandler('skip', self.skip_location_command)],
                },
                fallbacks=[CommandHandler('cancel', self.cancel_command)]
            )
        ]
        self.permissions = permissions
        self.repository = EventRepository()

    def get_handlers(self) -> list:
        return self.handlers

    def check_permission(self, action: str, user: Tuple[int, str]):
        if action == 'create':
            permission_list = self.permissions['create']

            if 'anyone' in permission_list:
                return True
            if user[0] in permission_list or user[1] in permission_list:
                return True

            return False

    def reminder_command(self, bot: Bot, update: Update):
        pass

    def cancel_command(self, bot: Bot, update: Update) -> int:
        user_id = update.message.from_user.id

        self.repository.remove_draft(user_id)

        update.message.reply_text(_('Bye! I hope we can talk again some day'),
                                  reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    def create_new_command(self, bot: Bot, update: Update, args) -> int:
        user_name = update.message.from_user.username
        user_id = update.message.from_user.id

        can_create = self.check_permission('create', (user_id, user_name))

        if not can_create:
            bot.sendMessage(update.message.chat.id, _('You don\'t have the permission to create new event'))
            return ConversationHandler.END
        else:
            event = Event(user_id)
            event_id = self.repository.insert(event)

            event.id = event_id
            self.repository.update(event)

            update.message.reply_text(_('(1/4) Insert the title of the event'))
            return TITLE

    def set_title(self, bot: Bot, update: Update) -> int:
        title = update.message.text
        user_id = update.message.from_user.id

        # get event by user id
        event = self.load_draft(user_id)
        event.title = title
        # update event entity
        self.repository.update(event)

        update.message.reply_text(_('(2/4) Ok! Now set a description or /skip'))
        return DESCRIPTION

    def set_description(self, bot: Bot, update: Update) -> int:
        description = update.message.text
        user_id = update.message.from_user.id

        event = self.load_draft(user_id)
        event.description = description
        self.repository.update(event)

        update.message.reply_text(
            _('(3/4) Ok! Now set the date and the time (dd/mm/yyyy HH:mm format, eg 30/10/1970 15:33)'))
        return DATETIME

    @staticmethod
    def skip_desc_command(bot: Bot, update: Update) -> int:
        update.message.reply_text(
            _('(3/4) Ok! Now set the date and the time (dd/mm/yyyy HH:mm format, eg 30/10/1970 15:33)'))

        return DATETIME

    def set_datetime(self, bot: Bot, update: Update) -> int:
        timestamp = time.mktime(datetime.strptime(update.message.text, '%d/%m/%Y %H:%M').timetuple())

        if time.time() > timestamp:
            update.message.reply_text(_('The date is in the past, insert correct date!'))
            return DATETIME

        user_id = update.message.from_user.id

        event = self.load_draft(user_id)
        event.datetime = timestamp
        self.repository.update(event)

        update.message.reply_text(_('(4/4) Last step! Set the location or /skip'))
        return LOCATION

    def set_location(self, bot: Bot, update: Update) -> int:
        location = update.message.text
        user_id = update.message.from_user.id

        event = self.load_draft(user_id)
        event.location = location
        event.draft = False
        self.repository.update(event)

        update.message.reply_text(_('Yeah!!! Event created'))
        return ConversationHandler.END

    @staticmethod
    def skip_location_command(bot: Bot, update: Update) -> int:
        update.message.reply_text(_('Yeah!!! Event created'))
        return ConversationHandler.END

    def load_draft(self, user_id):
        event = self.repository.find_draft(user_id)

        if not event:
            raise NoDraftExistError(_('There is no draft open for user {}').format(user_id))
        else:
            return event
