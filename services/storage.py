from tinydb import TinyDB, Query

from modules.abstract.model import MarvinModel


class Storage:
    def __init__(self, db_name: str):
        self.db = TinyDB('./data/' + db_name + '.json')

    def insert(self, entity: MarvinModel):
        return self.db.insert(entity.to_dict())
