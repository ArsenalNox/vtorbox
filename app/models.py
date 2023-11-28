
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean, BigInteger
from sqlalchemy.orm import declarative_base, relationship, backref, Session
from sqlalchemy.engine import URL
from datetime import datetime

from dotenv import load_dotenv
from os import getenv

import abc


load_dotenv()
connection_url = URL.create(
    drivername="postgresql",
    username=getenv("POSTGRES_USER"),
    host=getenv("POSTGRES_HOST"),
    port=getenv("POSTGRES_PORT"),
    database=getenv("POSTGRES_DB"),
    password=getenv("POSTGRES_PASSWORD")
)


engine = create_engine(connection_url)
Base = declarative_base()

#TODO: Модель пользователя
#TODO: Модель менеждера
#TODO: Модель Админа
#TODO: Модель заявки
#TODO: Модель курьера




class Orders(Base):
    pass


class Users(Base):
    """
    Модель пользователя
    """
    __tablename__ = "users"

    id = Column(Integer(), primary_key=True)
    telegram_id = Column(BigInteger(), unique=True, nullable=True)
    phone_number = Column(String(), unique=True, nullable=False)
    full_name = Column(String())
    email = Column(String(), unique=True)
    date_created = Column(DateTime(), default=datetime.now())
    orders = relationship('Mailing', backref='author')


class Manager(Base):
    pass


class Admin(Base):
    pass


class Courier(Base):
    pass


Base.metadata.create_all(engine)