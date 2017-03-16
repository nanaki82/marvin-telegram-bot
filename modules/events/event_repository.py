from typing import List

from tinydb import Query

from modules.events.event_model import Event
from services.storage import Storage


class EventRepository(Storage):
    def __init__(self):
        super().__init__('events')

    def find_draft(self, user_id: int):
        results = self.db.search((Query().user_id == user_id) & (Query().draft == True))

        if results:
            return Event.from_dict(results[0])
        else:
            return None

    def remove_draft(self, user_id: int):
        self.db.remove((Query().user_id == user_id) & (Query().draft == True))

    def update(self, event: Event):
        self.db.update(event.to_dict(), eids=[event.id])

    def find_by_id(self, event_id: int):
        if not isinstance(event_id, int):
            event_id = int(event_id)

        evt = self.db.get(eid=event_id)

        if evt:
            return Event.from_dict(evt)
        else:
            return None

    def find_all(self) -> List[Event]:
        events = self.db.all()
        results = []

        for event in events:
            results.append(Event.from_dict(event))

        return results

    def find_by_name(self, name: str):
        events = self.db.search(Query().name.test(lambda v: name in v))

        results = []

        for event in events:
            results.append(Event.from_dict(event))

        return results

    def find_by_name_and_user_id(self, name: str, user_id: int):
        events = self.db.search((Query().user_id == user_id) & (Query().name.test(lambda v: name in v)))

        results = []

        for event in events:
            results.append(Event.from_dict(event))

        return results
