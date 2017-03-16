import datetime

from exceptions import MissingValueError
from modules.abstract.model import MarvinModel


class Event(MarvinModel):
    id = None

    title = ''
    description = ''
    location = ''

    datetime = None

    draft = True
    user_id = None

    users_confirmed = []
    users_not_confirmed = []
    users_to_be_confirmed = []

    def __init__(self, user_id: int):
        self.user_id = user_id

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'datetime': self.datetime,
            'draft': self.draft,
            'user_id': self.user_id,
            'users_confirmed': self.users_confirmed,
            'users_not_confirmed': self.users_not_confirmed,
            'users_to_be_confirmed': self.users_to_be_confirmed,
        }

    def formatted_date(self):
        date = datetime.datetime.fromtimestamp(self.datetime)
        return date.strftime("%d/%m/%Y %H:%M")

    @staticmethod
    def from_dict(values: dict) -> MarvinModel:
        if not values['user_id']:
            raise MissingValueError(_('No user_id found in dictionary'))

        event = Event(values['user_id'])
        event.id = values.eid
        event.title = values['title']
        event.description = values['description']
        event.location = values['location']
        event.datetime = values['datetime']
        event.draft = values['draft']
        event.users_confirmed = values['users_confirmed']
        event.users_not_confirmed = values['users_not_confirmed']
        event.users_to_be_confirmed = values['users_to_be_confirmed']

        return event
