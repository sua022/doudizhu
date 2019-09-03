import logging

from contrib.singleton import Singleton
from .table import Table


class _TableManager(object):
    __metaclass__ = Singleton

    __current_table_id = 0

    def __init__(self, allow_robot=True):
        self.__waiting_tables = {}
        self.__playing_tables = {}
        self.allow_robot = allow_robot
        logging.info('TABLE MGR INIT')

    def rsp_tables(self):
        rsp = []
        for _, t in self.waiting_tables.items():
            rsp.append([t.uid, t.size()])
        return rsp

    def new_table(self):
        t = Table(self.gen_table_id(), self.allow_robot)
        self.waiting_tables[t.uid] = t
        return t

    def find_waiting_table(self, uid) -> Table:
        if uid == -1:
            for _, table in self.waiting_tables.items():
                return table
            return self.new_table()
        return self.waiting_tables.get(uid)

    def on_table_changed(self, table):
        if table.is_full():
            self.waiting_tables.pop(table.uid, None)
            self.playing_tables[table.uid] = table
        if table.is_empty():
            self.playing_tables.pop(table.uid, None)
            self.waiting_tables[table.uid] = table

    @property
    def waiting_tables(self):
        return self.__waiting_tables

    @property
    def playing_tables(self):
        return self.__playing_tables

    @classmethod
    def gen_table_id(cls):
        cls.__current_table_id += 1
        return cls.__current_table_id


table_manager = _TableManager()
