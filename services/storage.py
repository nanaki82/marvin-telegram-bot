from tinydb import TinyDB, Query

from modules.abstract.model import MarvinModel


class Storage:
    db = None
    db_name = ''

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.open()

    def insert(self, entity: MarvinModel):
        return self.db.insert(entity.to_dict())

    def open(self):
        self.db = TinyDB('./data/' + self.db_name + '.json', default_table='events')

    def clear_cache(self):
        self.db.table('events').clear_cache()
