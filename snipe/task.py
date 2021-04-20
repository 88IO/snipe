from discord import Member, User
from datetime import datetime as Datetime


class Task:
    DISCONNECT = "DISCONNECT"
    BEFORE_1MIN = "BEFORE_1MIN"
    BEFORE_3MIN = "BEFORE_3MIN"

    def __init__(self, datetime, members, type):
        self.datetime = datetime
        self.members = members
        self.type = type

    @property
    def datetime(self):
        return self.__datetime

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, Datetime):
            raise TypeError("type of 'datetime' must be datetime.datetime")
        self.__datetime = value

    @property
    def members(self):
        return self.__members

    @members.setter
    def members(self, value):
        if not isinstance(set, value) and not all(map(lambda x: isinstance(x, (User, Member)), value)):
            raise TypeError("type of 'member' must be Set[discord.Member]")
        self.__members = value

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, value):
        if value not in [Task.DISCONNECT, Task.BEFORE_1MIN, Task.BEFORE_3MIN]:
            raise TypeError("type of 'type' must be Union[Task.DISCONNECT, Task.BEFORE_1MIN, Task.BEFORE_3MIN]")
        self.__type = value

    def __lt__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return self.datetime < other.datetime

    def __eq__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return self.datetime == other.datetime

    def __hash__(self):
        return hash(self.datetime)
