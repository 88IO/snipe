from discord import Member, User
from datetime import datetime as Datetime
import typing


class Task:
    def __init__(self, datetime, member):
        self.datetime = datetime
        self.member = member

    @property
    def datetime(self):
        return self.__datetime

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, Datetime):
            raise TypeError("type of 'datetime' must be datetime.datetime")
        self.__datetime = value

    @property
    def member(self):
        return self.__member

    @member.setter
    def member(self, value):
        if not isinstance(value, (Member, User)):
            raise TypeError("type of 'member' must be Union[discord.Member, discord.User]")
        self.__member = value

    def __lt__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return self.datetime < other.datetime
