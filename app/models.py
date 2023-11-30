"""
Файл с ORM моделями данных
"""

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean, BigInteger, UUID
from sqlalchemy.orm import declarative_base, relationship, backref, Session
from sqlalchemy.engine import URL
from datetime import datetime

from dotenv import load_dotenv
from os import getenv

from .exceptions import UserNoIdProvided

import uuid

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

class BaseMixin(object):
    #TODO: Попытки в DRY
    @classmethod
    def create(cls, **kw):
        obj = cls(**kw)
        with Session(engine, expire_on_commit=False) as session:
            session.add(obj)
            session.commit()


class Orders(BaseMixin, Base):
    """
    Модель заявки от пользователя
    """
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user = Column(Integer(), ForeignKey('users.id')) 
    district = Column(String())
    region = Column(String())
    distance_from_mkad = Column(String())
    address = Column(String())
    full_adress = Column(String())
    point_on_map = Column(String())

    weekday = Column(String())

    interval = Column(String())
    subscription = Column(String(), nullable=True)
    
    #Тариф? 
    tariff = Column(String(), nullable=True)
    
    #Дата последнего вывоза
    last_disposal = Column(DateTime(), default=None, nullable=True)
    
    #Планируемая дата след. вызова
    next_planned_date = Column(DateTime(), default=None, nullable=True)

    #От юр. лица или нет
    legal_entity = Column(Boolean(), default=False)
    
    #Кол-во вывозов с даты оплаты
    times_completed = Column(Integer)

    #Дата последней оплаты
    payment_day = Column(DateTime(), nullable=True)

    def get_all_orders():
        with Session(engine, expire_on_commit=False) as session: 
            return session.query(Orders).all()


class RoutedOrders(Base):
    """
    Принятые заказы
    """

    __tablename__ = 'routed_orders'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(Integer(), ForeignKey('orders.id'))
    courier_id = Column(Integer(), ForeignKey('couriers.id'))

    #Дата сбора
    date = Column(DateTime(), nullable=True)

    #Статус заявки
    status = Column(String(), nullable=True)

    #Комментарий к выполнению от менеджера
    #SUGGESTION: Перенести коммента в отдельную таблицу
    comment_manager = Column(String(), nullable=True)
    #Комментарий к выполнению от курьера
    comment_courier = Column(String(), nullable=True)


class Users(Base):
    """
    Модель пользователя
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger(), unique=True, nullable=True)
    telegram_username = Column(String(), nullable=True)
    phone_number = Column(String(), unique=True, nullable=True)
    full_name = Column(String(), nullable=True)
    email = Column(String(), unique=True, nullable=True)
    date_created = Column(DateTime(), default=datetime.now())
    last_action = Column(DateTime(), default=datetime.now())
    link_code = Column(String(), unique=True, default=str(uuid.uuid4())[:8])
    allow_messages_from_bot = Column(Boolean(), default=True)


    def get_or_create(t_id:int | None = None, internal_id: int | None = None):
        """
        Получить или создать пользователя
        """
        if not (t_id or internal_id):
            raise UserNoIdProvided("Excpected at least one type of user id, zero provided") 

        user = None
        with Session(engine, expire_on_commit=False) as session:
            if t_id:
                user = session.query(Users).filter_by(telegram_id = t_id).first()
            elif internal_id:
                user = session.query(Users).filter_by(id = t_id).first()

            if not user: 
                user = Users(
                    telegram_id = t_id,
                )

                session.add(user)
                session.commit()

        return user

    
    def update_last_access(**kws):
        """
        Обновить дату последнего действия пользователя
        """
        if not (t_id or internal_id):
            raise UserNoIdProvided("Excpected at least one type of user id, zero provided") 

        user = Users.get_or_create(kws)

        with Session(engine, expire_on_commit=False) as session:
            user.last_action = datetime.now()
            session.commit()
        
        return 
            

class Roles(Base):
    """
    Список ролей
    """
    pass


class Premissions(Base):
    """
    Модель доступа у пользователей
    """
    pass


class Manager(Base):
    """
    Модель менеджера
    """
    __tablename__ = 'managers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Admin(Base):
    """
    Модель админа
    """
    __tablename__ = 'admins'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Courier(Base):
    """
    Модель курьера
    """

    __tablename__ = "couriers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class UserRoles(Base):
    """
    
    """


class OrderStatuses(Base):
    """
    Модель статусов заявки

    Статусы заявки:
    Создана (это свободный статус, сюда попадают заявки, если их создали например из бота, а администратор еще не включил ее в работу)
    В работе (это статус, когда заявка попадает в выдачу активных и берется сервисом в обработку, взаимодействие от клиента. У этого статуса есть еще подстатусы: Ожидаю подтверждение от клиента, Передана курьеру, Обработана курьером)
    Ожидает оплаты (заявка уже прошла активную фазу работы, клиенту выдали ссылку для оплаты и ждем поступления оплаты, этот статус попадает во вкладку Требуют внимания)
    Обработана (заявка прошла весь путь и закрыта как выполненная)
    """

    __tablename__ = 'order_statuses'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    def init_statuses():
        pass


Base.metadata.create_all(engine)