import time

from telegram import Bot, ParseMode
from telegram import ReplyKeyboardRemove
from telegram import Update
from telegram import InlineKeyboardMarkup
from telegram.ext import CommandHandler, Job
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext.jobqueue import Days, JobQueue
from typing import Tuple, Dict
from datetime import datetime

from exceptions import NoDraftExistError
from modules.events.event_model import Event
from modules.events.event_repository import EventRepository
from modules.events.event_inline import EventInline

TITLE, DESCRIPTION, DATETIME, LOCATION = range(4)


class EventCommand:
    handlers = []
    permissions = []

    def __init__(self, permissions: Dict[str, str]):
        self.handlers = [
            CommandHandler('reminder', self.reminder_command, pass_args=True, pass_job_queue=True, pass_chat_data=True),
            CommandHandler('cancel_reminder', self.cancel_reminder_command, pass_chat_data=True),
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

    def reminder_command(self, bot: Bot, update: Update, args: list, job_queue: JobQueue, chat_data):
        if len(args) < 2:
            update.message.reply_text(_("The usage of reminder command is: /reminder <hours> <event_name>"))
            return

        try:
            hour_interval = int(args[0])
        except IndexError:
            update.message.reply_text(_("The first argument must be an integer (hours)"))
            return

        del args[0]
        event_name = ' '.join(args)

        events = self.repository.find_by_name(event_name)

        if not events:
            update.message.reply_text(_('No events found with name "{}"'.format(event_name)))
            return
        else:
            event = events[0]

        if update.message.from_user.id != event.user_id:
            update.message.reply_text(_("You can't set a reminder on events created by others"))
            return

        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        job_name = str(user_id) + '_' + str(event.id) + '_' + str(chat_id)

        context = {
            "chat_id": chat_id,
            "event_id": event.id,
            "user_id": user_id
        }

        if hour_interval < 1:
            hour_interval = 1

        interval = hour_interval * 3600

        job = Job(self.reminder_message, interval=interval, repeat=True, context=context, days=Days.EVERY_DAY,
                  name=job_name)

        job_queue.put(job)
        chat_data['job'] = job

        update.message.reply_text(_(
            'Reminder set! I will text "{}" event every {} hours in this chat'.format(event.title,
                                                                                      int(interval / 3600))))

    @staticmethod
    def cancel_reminder_command(bot: Bot, update: Update, chat_data):
        if 'job' not in chat_data:
            update.message.reply_text(_('There are no active timer'))
            return
        else:
            job = chat_data['job']  # type: Job

        user_id = update.message.from_user.id

        if job.context['user_id'] != user_id:
            update.message.reply_text(_('You can\'t remove the timer'))
            return

        job.schedule_removal()
        del chat_data['job']

        update.message.reply_text(_("Reminder removed!"))

    def reminder_message(self, bot: Bot, job: Job):
        event = self.repository.find_by_id(job.context['event_id'])

        if not event:
            job.schedule_removal()
            return

        bot.sendMessage(job.context['chat_id'], text=EventInline.create_event_message(event),
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=EventInline.create_reply_keyboard(event)),
                        parse_mode=ParseMode.HTML)

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

    def skip_location_command(self, bot: Bot, update: Update) -> int:
        user_id = update.message.from_user.id

        event = self.load_draft(user_id)
        event.draft = False
        self.repository.update(event)

        update.message.reply_text(_('Yeah!!! Event created'))
        return ConversationHandler.END

    def load_draft(self, user_id):
        event = self.repository.find_draft(user_id)

        if not event:
            raise NoDraftExistError(_('There is no draft open for user {}').format(user_id))
        else:
            return event
