"""
Модели + функции инита данных, персистные данные
"""

import uuid, re, json, copy
from sqlalchemy import (
    create_engine, Column, Integer, String, 
    DateTime, Text, ForeignKey, Float, 
    Boolean, BigInteger, UUID, Text)

from sqlalchemy.orm import declarative_base, relationship, backref, Session, Mapped
from sqlalchemy.engine import URL
from sqlalchemy.sql import func

from datetime import datetime, timedelta
from dotenv import load_dotenv
from os import getenv
from typing import Union, Tuple, Optional, Dict, List

from app.exceptions import UserNoIdProvided
from app.utils import is_valid_uuid
from app.validators import UserCreationValidator

from calendar import monthrange
from passlib.context import CryptContext
from shapely.geometry import Point, shape

from app.validators import OrderOut, RegionOut

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


def default_time():
    return datetime.now()


def order_order_num():
    """
    получить кол-во заявок в таблице (учитывая удалённые)
    """
    with Session(engine, expire_on_commit=False) as session:
        count = session.query(Orders.id).count()
        return count + 1


def generate_route_short_name()->str:
    """
    сгенерировать короткий код-название для машрута

    """
    short_code = str(uuid.uuid4())[:10] 
    
    return short_code


class Orders(Base):
    """
    Модель заявки от пользователя
    """
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # id = Column(Integer(), primary_key=True, autoincrement=True)
    from_user = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    address_id = Column(UUID(as_uuid=True), ForeignKey('address.id'))

    day = Column(DateTime(), nullable=True)

    #От юр. лица или нет
    legal_entity = Column(Boolean(), default=False)
    
    box_type_id = Column(UUID(as_uuid=True), ForeignKey('boxtypes.id'), nullable=True)
    box_count = Column(Integer(), nullable=True)

    order_num = Column(Integer(), default=order_order_num)
    user_order_num = Column(Integer())

    status = Column(UUID(as_uuid=True), ForeignKey('order_statuses.id'))

    comment = Column(Text(), nullable=True)

    date_created = Column(DateTime(), default=default_time)
    last_updated = Column(DateTime(), default=default_time)
    
    deleted_at = Column(DateTime(), default=None, nullable=True)

    #айди курьера, если заявка принята курьером
    courier_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    #Комментарий к выполнению от менеджера
    #SUGGESTION: Перенести коммента в отдельную таблицу? 
    comment_manager = Column(Text(), nullable=True)
    #Комментарий к выполнению от курьера
    comment_courier = Column(Text(), nullable=True)

    @staticmethod
    def get_all_orders():
        with Session(engine, expire_on_commit=False) as session: 
            return session.query(Orders).all()

    @staticmethod
    def query_by_id(order_id: UUID) -> Optional['Orders']:
        #TODO: реализовать запрос по айди внутри метода
        with Session(engine, expire_on_commit=False) as session:
            order = session.query(Orders, Address, BoxTypes, OrderStatuses, Users).\
                join(Address, Address.id == Orders.address_id).\
                outerjoin(BoxTypes, BoxTypes.id == Orders.box_type_id).\
                join(OrderStatuses, OrderStatuses.id == Orders.status).\
                join(Users, Users.id == Orders.from_user).\
                where(Orders.id == order_id).first()

            return order


    @staticmethod
    def process_order_array(orders: List[any]):
        """
        Обрабатывает лист заявок с query и формирует массив на выход по схеме OrderOut
        """
        return_data = []
        for order in orders:
            order_data = OrderOut(**order[0].__dict__)
            order_data.tg_id = order[4].telegram_id
            
            if not(type(order[1].interval) == list):
                order_data.interval = str(order[1].interval).split(', ')
            else:
                order_data.interval = order[1].interval

            try:
                order_data.address_data = order[1]
                if not(type(order[1].interval) == list):
                    order_data.address_data.interval = str(order[1].interval).split(', ')
                else:
                    order_data.address_data.interval = order[1].interval

            except IndexError: 
                order_data.address_data = None

            try:
                order_data.address_data.region = order[5]
                if order[5].work_days != None:
                    print(order[5].work_days)
                    work_days_str = copy.deepcopy(order[5].work_days)
                    if not (type(work_days_str) == list):
                        work_days_str = str(work_days_str).split(' ')

                    order_data.address_data.region.work_days = work_days_str
                else:
                    order_data.address_data.region.work_days = None
            except IndexError:
                order_data.address_data.region = None

            try:
                order_data.box_data = order[2]
            except IndexError:
                order_data.box_data = None

            try:
                order_data.status_data = order[3]
            except IndexError:
                order_data.status_data = None
            
            try:
                order_data.user_data = order[4]
            except IndexError:
                order_data.user_data = None

            return_data.append(order_data.model_dump())

        return return_data


    def update_status(__self__, status_id) -> None:
        """
        Указать новый статус зявки с записью изменения в историю заявки
        """
        with Session(engine, expire_on_commit=False) as session:
            __self__.status = status_id
            status_update = OrderStatusHistory(
                order_id = __self__.id,
                status_id = status_id
            )

            session.add(status_update)
            session.commit()

            return 


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
    patronymic = Column(String(), nullable=True)
    
    additional_info = Column(Text(), comment='доп. инфа', nullable=True)
    date_created = Column(DateTime(), default=default_time)
    last_action = Column(DateTime(), default=default_time)
    #last_login
    
    #Код для связки бота и пользователя
    link_code = Column(String(), unique=True, default=str(uuid.uuid4())[:8])
    allow_messages_from_bot = Column(Boolean(), default=True)

    disabled = Column(Boolean(), default=False)

    deleted_at = Column(DateTime(), default=None, nullable=True)

    refresh_token = relationship('UserRefreshTokens', backref='users', lazy='joined')

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
                    user_id = user.id,
                    role_id = Roles.get_role(ROLE_CUSTOMER_NAME).id
                )

                session.add(user)
                session.add(user_role)
                session.commit()

        return user
    

    def get_or_404(
            t_id: int = None,
            internal_id: int = None, 
            ):
        with Session(engine, expire_on_commit=False) as session:
            user_query = None
            if t_id:
                user_query = session.query(Users).filter_by(telegram_id = t_id).\
                    where(Users.deleted_at == None).first()

            elif internal_id:
                user_query = session.query(Users).filter_by(id = internal_id).\
                    where(Users.deleted_at == None).first()
            
            return user_query


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


class UserRefreshTokens(Base):
    """
    рефреш токены пользователей
    """

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    token = Column(String(), nullable=False)
    date_created = Column(DateTime(), default=default_time)

class Address(Base):
    """Модель для адреса"""

    __tablename__ = "address"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address = Column(String(), nullable=False)
    detail = Column(String(), nullable=True)
    latitude = Column(String(), nullable=False)
    longitude = Column(String(), nullable=False)
    main = Column(Boolean(), default=False)

    region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'), nullable=False)

    distance_from_mkad = Column(String())
    point_on_map = Column(String())

    #Регулярная ли заявка
    on_interval = Column(Boolean(), default=False)
    #Тип интервала (Дни недели/Дни месяца)
    interval_type = Column(String(), default='once', nullable=True)
    #Интервал заявки
    interval = Column(String(), default=None, nullable=True)
    #Дата последнего вывоза
    last_disposal = Column(DateTime(), default=None, nullable=True)
    #Планируемая дата след. вызова
    next_planned_date = Column(DateTime(), default=None, nullable=True)
    #Кол-во вывозов с даты оплаты
    times_completed = Column(Integer())

    comment = Column(String(), nullable=True)

    deleted_at = Column(DateTime(), default=None, nullable=True)


    def __repr__(self):
        return f'{self.id}'

    
    def get_avaliable_days(self, days_list_len)->List[Dict]:
        """
        Сгенерировать список дат, по которым будет прободиться проверка
        """
        address_work_days = str(self.region.work_days).split(' ')
        dates_list_passed = []
        date_today = datetime.now()

        for i in range(100):
            if self.region.work_days == None:
                break

            day_number_now = datetime.strftime(date_today, "%d")
            month_now_str = datetime.strftime(date_today, "%m")
            year_now_str = datetime.strftime(date_today, "%Y")

            days_max = monthrange(int(year_now_str), int(month_now_str))[1]

            day_number_next = int(day_number_now)+1
            if (day_number_next>days_max):
                #если след день приходит на начало след месяца берём первое число как след день
                day_number_next = 1

            date_tommorrow = date_today + timedelta(days=i)
            weekday_tomorrow = str(date_tommorrow.strftime('%A')).lower()

            for day_allowed in address_work_days:
                if day_allowed == weekday_tomorrow:
                    dates_list_passed.append({
                        "date": date_tommorrow.strftime('%Y-%m-%dT%H:%M:%S'),
                        "weekday": weekday_tomorrow
                    })

            if len(dates_list_passed)>days_list_len-1:
                break

        return dates_list_passed


class UsersAddress(Base):
    """Модель для связки клиентов и адресов"""

    __tablename__ = "users_address"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    address_id = Column(UUID(as_uuid=True), ForeignKey('address.id'))

    deleted_at = Column(DateTime(), default=None, nullable=True)

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

    deleted_at = Column(DateTime(), default=None, nullable=True)

    @staticmethod
    def get_role(role_name: str):
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name=role_name).first()
            if query:
                return query
            else:
                return None

    @staticmethod
    def customer_role():
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name=ROLE_CUSTOMER_NAME).first()
            return query.id

    @staticmethod
    def courier_role():
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name=ROLE_COURIER_NAME).first()
            return query.id

    @property
    def manager_role(self):
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name=ROLE_MANAGER_NAME).first()
            return query.id

    @property
    def admin_role(self):
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Roles).filter_by(role_name=ROLE_MANAGER_NAME).first()
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

    deleted_at = Column(DateTime(), default=None, nullable=True)


class OrderStatuses(Base):
    """
    Модель статусов заявки
    """

    __tablename__ = 'order_statuses'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    status_name = Column(String(), nullable=False)
    description = Column(String(), nullable=False)

    deleted_at = Column(DateTime(), default=None, nullable=True)

    @staticmethod
    def status_default():
        with Session(engine,expire_on_commit=False) as session:
            query = session.query(OrderStatuses).\
                filter_by(status_name=ORDER_STATUS_DEFAULT["status_name"]).first()
            return query


    @staticmethod
    def status_processing():
        with Session(engine,expire_on_commit=False) as session:
            query = session.query(OrderStatuses).\
                filter_by(status_name=ORDER_STATUS_PROCESSING["status_name"]).first()
            return query

    
    @staticmethod
    def status_awating_confirmation():
        with Session(engine,expire_on_commit=False) as session:
            query = session.query(OrderStatuses).\
                filter_by(status_name=ORDER_STATUS_AWAITING_CONFIRMATION["status_name"]).first()
            return query
        

    @staticmethod
    def status_confirmed():
        with Session(engine,expire_on_commit=False) as session:
            query = session.query(OrderStatuses).\
                filter_by(status_name=ORDER_STATUS_CONFIRMED["status_name"]).first()
            return query


    @staticmethod
    def status_accepted_by_courier():
        with Session(engine,expire_on_commit=False) as session:
            query = session.query(OrderStatuses).\
                filter_by(status_name=ORDER_STATUS_COURIER_PROGRESS['status_name']).first()
            return query


    @staticmethod
    def status_awaiting_payment():
        with Session(engine,expire_on_commit=False) as session:
            query = session.query(OrderStatuses).\
                filter_by(status_name=ORDER_STATUS_AWAITING_PAYMENT['status_name']).first()
            return query

 
    @staticmethod
    def status_payed():
        with Session(engine,expire_on_commit=False) as session:
            query = session.query(OrderStatuses).\
                filter_by(status_name=ORDER_STATUS_PAYED['status_name']).first()
            return query



class OrderStatusHistory(Base):
    """
    История статуса заявки
    """
    __tablename__ = "order_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'))
    status_id = Column(UUID(as_uuid=True), ForeignKey('order_statuses.id'))
    date = Column(DateTime(), default=datetime.now())

    deleted_at = Column(DateTime(), default=None, nullable=True)


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

    deleted_at = Column(DateTime(), default=None, nullable=True)

    @staticmethod
    def test_type():
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(BoxTypes).first()
            return query


class Payments(Base):
    """
    Платежи
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    deleted_at = Column(DateTime(), default=None, nullable=True)

    __tablename__ = "payments"


class WeekDaysWork(Base):
    """
    Указание нерабочих дней в неделю, регулярные
    """

    __tablename__ = 'week_days_work'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_num = Column(Integer(), nullable=False)
    day_status = Column(Boolean(), default=False)

    deleted_at = Column(DateTime(), default=None, nullable=True)

    region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'))


class DaysWork(Base):
    """
    Указание нерабочих дней, по дате
    """

    __tablename__ = 'days_work'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    deleted_at = Column(DateTime(), default=None, nullable=True)


class Notifications(Base):
    """
    Пользовательские уведомления
    """

    __tablename__ = 'notifications'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deleted_at = Column(DateTime(), default=None, nullable=True)


class NotificationTypes(Base):
    """
    Типы уведомлений
    """

    __tablename__ = 'notification_types'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type_name = Column(String(), nullable=False)
    deleted_at = Column(DateTime(), default=None, nullable=True)


class Regions(Base):
    """
    Регионы, в которых доступен вывоз
    """
    __tablename__ = 'regions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_short = Column(String(), nullable=True)
    name_full = Column(String(), nullable=False)

    region_type = Column(String(), nullable=False)

    is_active = Column(Boolean(), default=True)
    
    geodata = Column(Text(), nullable=True)

    # work_days = relationship(
    #         'Regions',
    #         backref=backref('WeekDaysWork', lazy='joined'), 
    #         lazy='dynamic'
        # )

    work_days = Column(String(), nullable=True)
    addresses = relationship('Address', backref='region', lazy='joined')
    

    def contains(self, point:Point)->bool:
        """
        Проверить, содержит ли регион указанную точку
        """
        data_points = str(self.geodata).replace('\'','\"')
        data_points = json.loads(data_points)
        feature = shape(data_points)

        return feature.contains(point)
    

    @staticmethod
    def get_by_coords(lat: float, long: float)-> Optional['Regions']:
        """
        Получить регион по координатам
        """
        point = Point(lat, long)
        region = None

        with Session(engine, expire_on_commit=False) as session:
            regions_query = session.query(Regions).all()
            for region_query in regions_query:

                data_points = str(region_query.geodata).replace('\'','\"')
                data_points = json.loads(data_points)
                feature = shape(data_points)

                if not region_query.contains(point):
                    continue
                else:
                    region = region_query
                    break

        return region

    
    @staticmethod
    def get_by_name(name: str) -> Optional['Regions']:
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(Regions).\
                filter(Regions.name_full.ilike(f"%{name}%")).first()
            return query


class Routes(Base):
    """
    Модель маршрутов 
    """

    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    courier_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    short_name = Column(String(), default=generate_route_short_name)

    #На какой день предназначен маршрут 
    date_created = Column(DateTime(), default=default_time)
    orders = relationship('RoutesOrders', backref='routes', lazy='joined')
    
    @staticmethod
    def get_all_routes(today_only: bool = True):
        pass

    
class RoutesOrders(Base):
    """
    Связь маршрута с заявками 
    """ 

    __tablename__ ="routed_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'))
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.id'))

    order = relationship('Orders', backref='routedorders', lazy='joined')


# === персистные данные/конфигурации
Base.metadata.create_all(engine)

#Роли пользователей в системе
ROLE_ADMIN_NAME = 'admin'
ROLE_COURIER_NAME = 'courier'
ROLE_MANAGER_NAME = 'manager'
ROLE_CUSTOMER_NAME = 'customer'
ROLE_TELEGRAM_BOT_NAME = 'bot'


#Статусы заявок
ORDER_STATUS_DEFAULT = {
    "status_name": "создана",
    "description": "заявка не включена в работу"
    }
ORDER_STATUS_PROCESSING = {
    "status_name": "в работе",
    "description": "заявка находится в выдаче активных"
    }
#Подстатусы заявок от в работе
ORDER_STATUS_AWAITING_CONFIRMATION = {
    "status_name": "ожидается подтверждение",
    "description": "ожидается подтверждение от клиента"
    }
ORDER_STATUS_CONFIRMED = {
    "status_name": "подтверждена",
    "description": "подтверждена клиентом"
    }
ORDER_STATUS_COURIER_PROGRESS = {
    "status_name": "передана курьеру",
    "description": "передана курьеру на выполнение"
    }
ORDER_STATUS_AWAITING_PAYMENT = {
    "status_name": "ожидается оплата",
    "description": "обработанно курьером, ожидается оплата"
    }
ORDER_STATUS_PAYED = {
    "status_name": "оплаченна",
    "description": "заявка оплаченна"
    }
ORDER_STATUS_DONE = {
    "status_name": "обработанна",
    "description": "обработанна"
    }
ORDER_STATUS_DELETED = {
    "status_name": "удалена",
    "description": "заявка была удалена"
}
ORDER_STATUS_CANCELED = {
    "status_name": "отменена",
    "description": "заявка была отменена"
}


#Типы контейнеров (временные)
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


#Типы интервалов
class IntervalStatuses():
    MONTH_DAY = 'month_day'
    WEEK_DAY = 'week_day'
    DAY_ONCE = 'day_once'
    ON_REQUEST = 'on_request'


#Типы регионов
class RegionTypes():
    DISTRICT='district'
    REGION='region'

WEEK_DAYS_WORK_STR_LIST = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "sunday",
    "saturday",
]

def init_role_table():
    """
    инициализировать таблицу ролей
    """
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
    """
    инициализировать таблицу статусов
    """
    statuses = [
        ORDER_STATUS_DEFAULT,
        ORDER_STATUS_PROCESSING,
        ORDER_STATUS_AWAITING_CONFIRMATION, 
        ORDER_STATUS_CONFIRMED,
        ORDER_STATUS_COURIER_PROGRESS, 
        ORDER_STATUS_AWAITING_PAYMENT,
        ORDER_STATUS_PAYED,
        ORDER_STATUS_DONE,
        ORDER_STATUS_DELETED,
        ORDER_STATUS_CANCELED
    ]

    with Session(engine, expire_on_commit=False) as session:
        for status in statuses:
            status_query = session.query(OrderStatuses).filter_by(status_name = status['status_name']).first()
            if not status_query:
                new_status = OrderStatuses(**status)
                session.add(new_status)
        session.commit()


def init_boxtype_table():
    """
    инициализировать таблицу статусов
    """
    box_types = [
        BOX_TYPE_TEST1,
        BOX_TYPE_TEST2,
        BOX_TYPE_TEST3,
    ]
    with Session(engine, expire_on_commit=False) as session:
        for box_type in box_types:
            box_query = session.query(BoxTypes).filter_by(box_name = box_type["box_name"]).first()
            if not box_query:
                new_box = BoxTypes(**box_type)
                session.add(new_box)
        session.commit()


def create_admin_user():
    """
    Создать админского пользователя
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def get_password_hash(password):
        return pwd_context.hash(password)

    new_user_data = UserCreationValidator(
        email="user3@example.com",
        password="string",
        role= ['customer', 'user', 'admin', 'bot', 'manager', 'courier']
    )

    with Session(engine, expire_on_commit=False) as session:
        query_user = session.query(Users).filter_by(email=new_user_data.email).first()
        if query_user: 
            return

        new_user_data.password = get_password_hash(new_user_data.password)
        new_user_data = new_user_data.model_dump()
        user_role = new_user_data["role"]
        del new_user_data["role"]
        del new_user_data["send_email_invite"]

        new_user = Users(**new_user_data)

        #Фикс: при flush uuid остаётся в сесси и не перегенерируется, т.е получаем Exception на unique field'е 
        new_user.link_code = str(uuid.uuid4())[:10] 

        session.add(new_user)
        session.flush()
        session.refresh(new_user)

        #Если админ - добавить все роли?

        for role in user_role:
            role_query = Roles.get_role(role)
            if role_query:
                user_role = Permissions(
                    user_id = new_user.id,
                    role_id = Roles.get_role(role).id
                )

                session.add(user_role)

        session.commit()

        return


# if __name__ == "__main__":
init_role_table()
init_boxtype_table()
init_status_table()
create_admin_user()