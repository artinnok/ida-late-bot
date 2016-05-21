from peewee import *

db = SqliteDatabase('late.db')


class Person(Model):
    username = CharField(
        verbose_name='Ник пользователя в Telegram'
    )


class Delay(Model):
    time = IntegerField(
        verbose_name='Время, на которое опоздали'
    )
    reason = CharField(
        verbose_name='Причина опоздания'
    )
    person = ForeignKeyField(
        Person,
        related_name='delays'
    )
