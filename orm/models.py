from peewee import *

db = SqliteDatabase('late.db')


class BaseModel(Model):
    class Meta:
        database = db


class Person(BaseModel):
    username = CharField(
        verbose_name='Ник пользователя в Telegram'
    )
    first_name = CharField(
        verbose_name='Имя'
    )
    last_name = CharField(
        verbose_name='Фамилия'
    )


class Delay(BaseModel):
    minute = IntegerField(
        verbose_name='Время в минутах, на которое опоздали'
    )
    reason = CharField(
        verbose_name='Причина опоздания',
        null=True
    )
    person = ForeignKeyField(
        Person,
        related_name='delays'
    )
