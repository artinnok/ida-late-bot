from peewee import *

db = SqliteDatabase('sqlite.db')


class BaseModel(Model):
    class Meta:
        database = db


class Person(BaseModel):
    user_id = BigIntegerField(
        verbose_name='ID пользователя в Telegram'
    )
    username = CharField(
        verbose_name='Ник пользователя в Telegram',
        null=True
    )
    first_name = CharField(
        verbose_name='Имя',
        null=True
    )
    last_name = CharField(
        verbose_name='Фамилия',
        null=True
    )


class Delay(BaseModel):
    minute = IntegerField(
        verbose_name='Время в минутах, на которое опоздали',
    )
    reason = CharField(
        verbose_name='Причина опоздания',
        null=True
    )
    person = ForeignKeyField(
        Person,
        related_name='delays'
    )
