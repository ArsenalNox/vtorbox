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
from app.utils import is_valid_uuid

import uuid, re

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


class Orders(Base):
    """
    Модель заявки от пользователя
    """
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    address_id = Column(UUID(as_uuid=True), ForeignKey('address.id'))

    day = Column(String()) 
    interval = Column(String())

    #Дата последнего вывоза
    last_disposal = Column(DateTime(), default=None, nullable=True)
    
    #Планируемая дата след. вызова
    next_planned_date = Column(DateTime(), default=None, nullable=True)

    #От юр. лица или нет
    legal_entity = Column(Boolean(), default=False)
    
    #Кол-во вывозов с даты оплаты
    times_completed = Column(Integer())

    box_type_id = Column(UUID(as_uuid=True), ForeignKey('boxtypes.id'))
    box_count = Column(Integer())

    status = Column(UUID(as_uuid=True), ForeignKey('order_statuses.id'))

    date_created = Column(DateTime(), default=datetime.now())
    last_updated = Column(DateTime(), default=datetime.now())

    @staticmethod
    def get_all_orders():
        with Session(engine, expire_on_commit=False) as session: 
            return session.query(Orders).all()


class RoutedOrders(Base):
    """
    Принятые заказы на выполнении у курьера
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
    #SUGGESTION: Перенести коммента в отдельную таблицу? 
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
    password = Column(String(), nullable=True)

    telegram_id = Column(BigInteger(), unique=True, nullable=True)
    telegram_username = Column(String(), nullable=True)
    phone_number = Column(String(), unique=True, nullable=True)
    
    firstname = Column(String(), nullable=True)
    secondname = Column(String(), nullable=True)
    
    additional_info = Column(Text(), comment='доп. инфа', nullable=True)
    date_created = Column(DateTime(), default=datetime.now())
    last_action = Column(DateTime(), default=datetime.now())
    #last_login
    
    #Код для связки бота и пользователя
    link_code = Column(String(), unique=True, default=str(uuid.uuid4())[:8])
    allow_messages_from_bot = Column(Boolean(), default=True)

    # disabled = Column(Boolean(), default=True)

    def get_or_create(
            t_id: int = None,
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
                user = session.query(Users).filter_by(id = internal_id).first()

            if not user: 
                user = Users(
                    telegram_id = t_id,
                )

                user_role = Permissions(
                    user_id = new_user.id,
                    role_id = Roles.get_role(ROLE_CUSTOMER_NAME).id
                )

                session.add(user)
                session.add(user_role)
                session.commit()

        return user
    
    @staticmethod
    def get_user(user_id: str):
        """
        Получить пользователя по его uuid4 или telegram_id
        """
        user_query = None
        with Session(engine, expire_on_commit=False) as session:
            if is_valid_uuid(user_id):
                user_query = session.query(Users).filter_by(id=user_id).first()
            elif re.match(r'[\d]+', user_id):
                user_query = session.query(Users).filter_by(telegram_id=int(user_id)).first()

        return user_query


    #TODO: Свойста по ролям
    @property
    def is_admin(self):
        pass


    def update_last_access(**kwargs):
        """
        Обновить дату последнего действия пользователя
        """
        t_id = kwargs.get('t_id')
        internal_id = kwargs.get('internal_id')
        if not (t_id or internal_id):
            raise UserNoIdProvided("Excpected at least one type of user id, zero provided")

        user = Users.get_or_create(**kwargs)

        with Session(engine, expire_on_commit=False) as session:
            user.last_action = datetime.now()
            session.commit()

        return


    def set_role(self, role_name):

        pass


class Address(Base):
    """Модель для адреса"""

    __tablename__ = "address"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address = Column(String(), nullable=False)
    detail = Column(String(), nullable=True)
    latitude = Column(String(), nullable=False)
    longitude = Column(String(), nullable=False)
    main = Column(Boolean(), default=False)

    district = Column(String())
    region = Column(String())
    distance_from_mkad = Column(String())
    point_on_map = Column(String())

    comment = Column(String(), nullable=True)

    def __repr__(self):
        return f'{self.id}'


class UsersAddress(Base):
    """Модель для связки клиентов и адресов"""

    __tablename__ = "users_address"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    address_id = Column(UUID(as_uuid=True), ForeignKey('address.id'))

    def __repr__(self):
        return f'User:{self.user_id} - Address:{self.address_id}'


class Roles(Base):
    """
    Список ролей
    Клиент, курьер, менеджер, админ
    """
    
    __tablename__ = 'roles'

    id = Column(Integer(), unique=True, primary_key=True)
    role_name = Column(String(), default='')

    @staticmethod
    def get_role(role_name: str):
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name=role_name).first()
            if query:
                return query
            else:
                return None

    @property
    def customer_role(self):
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name=ROLE_CUSTOMER_NAME).first()
            return query.id

    @property
    def courier_role(self):
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name='courier').first()
            return query.id

    @property
    def manager_role(self):
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name='manager').first()
            return query.id

    @property
    def admin_role(self):
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name='admin').first()
            return query.id


class Permissions(Base):
    """
    Модель доступа у пользователей
    """

    __tablename__ = 'permissions'

    # Если у пользователя нет каких-либо прав он считается клиентом
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

    status_name = Column(String(), nullable=False)
    description = Column(String(), nullable=False)
    

class BoxTypes(Base):
    """
    Модель типов контейнеров
    """
    
    __tablename__ = "boxtypes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    box_name = Column(String(), nullable=False)
    pricing_default = Column(Float()) #За еденицу
    volume = Column(Float())
    weight_limit = Column(Float())


class Payments(Base):
    """
    Платежи
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    __tablename__ = "payments"


Base.metadata.create_all(engine)

#Роли пользователей в системе
ROLE_ADMIN_NAME = 'admin'
ROLE_COURIER_NAME = 'courier'
ROLE_MANAGER_NAME = 'manager'
ROLE_CUSTOMER_NAME = 'customer'
ROLE_TELEGRAM_BOT_NAME = 'bot'


ORDER_STATUS_DEFAULT = "created"
ORDER_STATUS_PROCESSING = "processing"

#Подстатусы от в работе
ORDER_STATUS_AWAITING_CONFIRMATION = "awaiting_confirmation"
ORDER_STATUS_CONFIRMED = "confirmed"
ORDER_STATUS_COURIER_PROGRESS = "courier_progress"
ORDER_STATUS_AWAITING_PAYMENT = "awaiting_payment"
ORDER_STATUS_PAYED = "payed"

ORDER_STATUS_DONE = "done"

BOX_TYPE_TEST1 = {
    "box_name": "Пакет",
    "pricing_default": 500,
    "volume": "2",
    "weight_limit": "15"
}

BOX_TYPE_TEST2 = {
    "box_name": "Пакет тканиевый",
    "pricing_default": 20,
    "volume": "2",
    "weight_limit": "5"
}

BOX_TYPE_TEST3 = {
    "box_name": "Фасеточка",
    "pricing_default": 5,
    "volume": "1",
    "weight_limit": "1"
}


def init_role_table():
    roles = [
        ROLE_ADMIN_NAME, 
        ROLE_COURIER_NAME, 
        ROLE_CUSTOMER_NAME, 
        ROLE_MANAGER_NAME, 
        ROLE_TELEGRAM_BOT_NAME
        ]

    with Session(engine, expire_on_commit=False) as session:
        for role in roles: 
            roles_query = session.query(Roles).filter_by(role_name = role).first()
            if not roles_query:
                new_role = Roles(role_name = role)
                session.add(new_role)
        session.commit()


def init_status_table():
    statuses = [
        ROLE_ADMIN_NAME,
        ROLE_COURIER_NAME,
        ROLE_MANAGER_NAME,
        ROLE_CUSTOMER_NAME,
        ROLE_TELEGRAM_BOT_NAME,
        ORDER_STATUS_DEFAULT,
        ORDER_STATUS_PROCESSING,
        ORDER_STATUS_AWAITING_CONFIRMATION, 
        ORDER_STATUS_CONFIRMED,
        ORDER_STATUS_COURIER_PROGRESS, 
        ORDER_STATUS_AWAITING_PAYMENT,
        ORDER_STATUS_PAYED,
        ORDER_STATUS_DONE
    ]




def init_boxtype_table():
    box_types = [
        BOX_TYPE_TEST1,
        BOX_TYPE_TEST2,
        BOX_TYPE_TEST3,
    ]
    with Session(engine, expire_on_commit=False) as session:
        for box_type in box_types:
            print(box_type)
            box_query = session.query(BoxTypes).filter_by(box_name = box_type["box_name"]).first()
            if not box_query:
                new_box = BoxTypes(**box_type)
                session.add(new_box)
        session.commit()


init_role_table()
init_boxtype_table()


