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


class Orders(Base):
    """
    Модель заявки от пользователя
    """
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user = Column(UUID(as_uuid=True), ForeignKey('users.id')) 
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

    disabled = Column(Boolean(), default=False)

    def get_all_orders():
        with Session(engine, expire_on_commit=False) as session: 
            return session.query(Orders).all()


class RoutedOrders(Base):
    """
    Принятые заказы
    """

    __tablename__ = 'routed_orders'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'))
    courier_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))

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
    Модель пользователей

    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(), unique=True, nullable=True)
    password = Column(String(), nullable=False)
    #

    telegram_id = Column(BigInteger(), unique=True, nullable=True)
    telegram_username = Column(String(), nullable=True)
    phone_number = Column(String(), unique=True, nullable=True)
    full_name = Column(String(), nullable=True)
    date_created = Column(DateTime(), default=datetime.now())
    last_action = Column(DateTime(), default=datetime.now())
    #last_login

    link_code = Column(String(), unique=True, default=str(uuid.uuid4())[:8])
    allow_messages_from_bot = Column(Boolean(), default=True)


    def get_or_create(
            t_id:int = None, 
            internal_id: int = None, 
            ):
        """
        Получить или создать пользователя, создаётся как клиент
        """
        if not (t_id or internal_id):
            raise UserNoIdProvided("Excpected at least one type of user id, zero provided") 

        user = None
        with Session(engine, expire_on_commit=False) as session:
            if t_id:
                user = session.query(Users).filter_by(telegram_id = t_id).first()
            elif internal_id:
                user = session.query(Users).filter_by(id = t_id).first()

            #TODO: Автоматическое назначение роли
            if not user: 
                user = Users(
                    telegram_id = t_id,
                )

                session.add(user)
                session.commit()

        return user

    

    #TODO: Свойста по ролям
    @property
    def is_admin(self):
        pass

    
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


    def authenticate_user():
        pass 


class Roles(Base):
    """
    Список ролей
    Клиент, курьер, менеджер, админ
    """
    
    __tablename__ = 'roles'

    id = Column(Integer(), unique=True, primary_key=True)
    role_name = Column(String(), default='')


    @property
    def customer_role() -> int:
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name='customer').first()
            return query.id
    

    @property
    def courier_role():
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name='courier').first()
            return query.id


    @property
    def manager_role():
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name='manager').first()
            return query.id


    @property
    def admin_role():
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name='admin').first()
            return query.id


class Premissions(Base):
    """
    Модель доступа у пользователей
    """

    __tablename__ = 'premissions'    

    #Если у пользователя нет каких-либо прав он считается клиентом
    id = Column(Integer(), unique=True, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    role_id = Column(Integer(), ForeignKey('roles.id'))


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


Base.metadata.create_all(engine)


def init_role_table():
    roles = ['customer', 'courier', 'manager', 'admin']
    with Session(engine, expire_on_commit=False) as session:
        for role in roles: 
            roles_query = session.query(Roles).filter_by(role_name = role).first()
            if not roles_query:
                new_role = Roles(role_name = role)
                session.add(new_role)
        session.commit()


def init_status_table():
    pass

init_role_table()