from typing import List

from telegram import Bot
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import InlineQueryResultArticle
from telegram import InputTextMessageContent
from telegram import ParseMode
from telegram import Update
from telegram.ext import CallbackQueryHandler
from telegram.ext import InlineQueryHandler

from emoji import emojize

from modules.events.event_model import Event
from modules.events.event_repository import EventRepository


class EventInline:
    def __init__(self, permissions):
        self.handlers = [
            CallbackQueryHandler(self.callback_handler),
            InlineQueryHandler(self.inline_event_list),
        ]
        self.repository = EventRepository()
        self.permissions = permissions

    def get_handlers(self) -> list:
        return self.handlers

    def callback_handler(self, bot: Bot, update: Update):
        query = update.callback_query
        data = query.data
        user = query.from_user.__dict__

        user.pop('bot')

        (command, event_id) = tuple(data.split('_'))

        event = self.repository.find_by_id(event_id)
        event = self.register_user(user, event, command)

        # If user click on an inline message or a message
        if query.inline_message_id:
            bot.editMessageText(text=self.create_event_message(event),
                                parse_mode=ParseMode.HTML,
                                inline_message_id=query.inline_message_id,
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=self.create_reply_keyboard(event),
                                                                  parse_mode=ParseMode.HTML)
                                )
        else:
            bot.editMessageText(text=self.create_event_message(event),
                                chat_id=query.message.chat.id,
                                parse_mode=ParseMode.HTML,
                                message_id=query.message.message_id,
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=self.create_reply_keyboard(event),
                                                                  parse_mode=ParseMode.HTML)
                                )

    def inline_event_list(self, bot, update):
        query = update.inline_query.query
        user_id = update.inline_query.from_user.id

        results = events = []

        if 'anyone' == self.permissions['publish']:
            events = self.repository.find_by_name(query)  # type: List[Event]
        if 'owner' == self.permissions['publish']:
            events = self.repository.find_by_name_and_user_id(query, user_id)  # type: List[Event]

        for event in events:
            keyboard = self.create_reply_keyboard(event)
            result = InlineQueryResultArticle(id=event.id,
                                              title=event.title,
                                              description=event.formatted_date(),
                                              thumb_url='http://i.imgur.com/y1cHJm7.png',
                                              input_message_content=InputTextMessageContent(
                                                  self.create_event_message(event),
                                                  parse_mode=ParseMode.HTML
                                              ),
                                              reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
            results.append(result)

        bot.answerInlineQuery(
            update.inline_query.id,
            results=results,
            switch_pm_text=_('Create new event...'),
            switch_pm_parameter='new',
            is_personal=True
        )

    def register_user(self, user: dict, event: Event, action: str) -> Event:
        if any(u['id'] == user['id'] for u in event.users_confirmed):
            event.users_confirmed.remove(user)
        if any(u['id'] == user['id'] for u in event.users_not_confirmed):
            event.users_not_confirmed.remove(user)
        if any(u['id'] == user['id'] for u in event.users_to_be_confirmed):
            event.users_to_be_confirmed.remove(user)

        if action == 'yes':
            event.users_confirmed.append(user)
        if action == 'no':
            event.users_not_confirmed.append(user)
        if action == 'maybe':
            event.users_to_be_confirmed.append(user)

        self.repository.update(event)

        return event

    @staticmethod
    def create_event_message(event: Event) -> str:
        text = '<b>{title}</b> - {date}\n'.format(title=event.title, date=event.formatted_date())

        if event.description != '':
            text += '<i>{description}</i>\n'.format(description=event.description)

        if event.location != '':
            text += emojize(":pushpin:", use_aliases=True) + ' {location}\n'.format(location=event.location)

        text += '\n'

        if len(event.users_confirmed) > 0:
            text += _('Users confirmed (<b>{total}</b>)\n').format(total=len(event.users_confirmed))

            for u in event.users_confirmed:
                u = {k: v for k, v in u.items() if v is not None}
                text += '@' + u['username'] if u.get('username') else ''
                text += ' (' + (u['first_name'] + ' ' + u.get('last_name', '')).strip() + ')\n'

        if len(event.users_not_confirmed) > 0:
            text += _('Users not confirmed ({total})\n').format(total=len(event.users_not_confirmed))

            for u in event.users_not_confirmed:
                u = {k: v for k, v in u.items() if v is not None}
                text += '@' + u['username'] if u.get('username') else ''
                text += ' (' + (u['first_name'] + ' ' + u.get('last_name', '')).strip() + ')\n'

        if len(event.users_to_be_confirmed) > 0:
            text += _('Users maybe ({total})\n').format(total=len(event.users_to_be_confirmed))

            for u in event.users_to_be_confirmed:
                u = {k: v for k, v in u.items() if v is not None}
                text += '@' + u['username'] if u.get('username') else ''
                text += ' (' + (u['first_name'] + ' ' + u.get('last_name', '')).strip() + ')\n'

        return text

    @staticmethod
    def create_reply_keyboard(event: Event) -> List[List[InlineKeyboardButton]]:
        buttons = [
            InlineKeyboardButton(
                text=_('Join'),
                callback_data='yes_{}'.format(event.id)
            ),
            InlineKeyboardButton(
                text=_('Not go'),
                callback_data='no_{}'.format(event.id)
            ),
            InlineKeyboardButton(
                text=_('Maybe'),
                callback_data='maybe_{}'.format(event.id)
            )
        ]

        return [buttons, []]
