"""
Модели + функции инита данных, персистные данные
"""

import uuid, re, json, copy, hashlib, requests
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
from app.utils import send_message_through_bot, create_tinkoff_token, set_timed_func
from app import T_BOT_URL
from app import TIKOFF_API_URL_TEST as TINKOFF_API_URL

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


def generate_link_code()->str:
    link_code = str(uuid.uuid4())[:8]
    return link_code

class Orders(Base):
    """
    Модель заявки от пользователя
    """
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # id = Column(Integer(), primary_key=True, autoincrement=True)
    from_user = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    address_id = Column(UUID(as_uuid=True), ForeignKey('address.id'))

    user = relationship("Users", backref='orders', lazy='joined', foreign_keys=[from_user])

    day = Column(DateTime(), nullable=True)

    #От юр. лица или нет
    legal_entity = Column(Boolean(), default=False)
    
    box_type_id = Column(UUID(as_uuid=True), ForeignKey('boxtypes.id'), nullable=True)
    box_count = Column(Integer(), nullable=True)
    box = relationship('BoxTypes', backref='orders', lazy='joined')

    order_num = Column(Integer(), unique=True, default=order_order_num)
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

    address = relationship('Address', backref='orders', lazy='joined')

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


    def update_status(__self__, status_id) -> Optional['Orders']:
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

            if not __self__.from_user:
                return __self__

            user = Users.get_user(str(__self__.from_user))
            if not user:
                return __self__

            if (not user.allow_messages_from_bot) or (not user.telegram_id):
                return __self__
            
            status_query = session.query(OrderStatuses).filter(OrderStatuses.id == status_id).first()
            send_message_through_bot(
                receipient_id=user.telegram_id,
                message=f"Ваша заявка №{__self__.order_num} изменила статус на '{status_query.status_name}'"
            )

            return __self__


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
    link_code = Column(String(), unique=True, default=generate_link_code)
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
            internal_id: UUID = None, 
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
                return user_query
            elif re.match(r'^[\d]*$', user_id):
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
    # region = relationship('Regions', backref='address', lazy=True)

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
    label = Column(String(), nullable=True)

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

    @staticmethod
    def status_canceled():
        with Session(engine,expire_on_commit=False) as session:
            query = session.query(OrderStatuses).\
                filter_by(status_name=ORDER_STATUS_CANCELED['status_name']).first()
            return query


class OrderStatusHistory(Base):
    """
    История статуса заявки
    """
    __tablename__ = "order_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'))
    status_id = Column(UUID(as_uuid=True), ForeignKey('order_statuses.id'))
    date = Column(DateTime(), default=default_time)

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

    regional_pricing = relationship('RegionalBoxPrices', backref='boxtypes', lazy='joined')

    @staticmethod
    def test_type():
        with Session(engine, expire_on_commit=False) as session:
            query = session.query(BoxTypes).first()
            return query


class Payments(Base):
    """
    Платежи
    """
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tinkoff_id = Column(String()) #Айди платежа в системе тинькофф
    order_id = Column(Integer(), ForeignKey('orders.order_num'), nullable=False) #Айди платежа в нашей системе (не уникален для тинькофф)
    order = relationship('Orders', backref='payments', lazy='joined')

    amount = Column(Integer(), nullable=True) #стоимость, в копейках

    status = Column(String()) #сатус оплаты
    is_reocurring = Column(Boolean(), default=True) #рекуррентный ли платёж

    rebill_id = Column(String(), nullable=True) #Айди платежа, если он был оплачен, по которому можно провести списание рекуррентного
    payment_url = Column(String(), nullable=True)

    terminal_id = Column(UUID(as_uuid=True), ForeignKey('payment_terminals.id'), nullable=False) #Через какой платёжный шлюз

    deleted_at = Column(DateTime(), default=None, nullable=True)
    
    date_created = Column(DateTime(), default=default_time)


    def process_status_update(order):
        #Если у пользователя есть карта с rebuill_id возвать init с charge
        #Если нет, вызвать init 
        
        with Session(engine, expire_on_commit=False) as session:
            terminal = session.query(PaymentTerminals).filter_by(default_terminal=True).first()
            rebuill_query = session.query(PaymentClientData).filter_by(user_id=order.user.id).first()
            print(rebuill_query)

            if rebuill_query:
                #TODO: Создать платёж и вызвать charge
                new_payment = Payments.create_new_payment(
                    terminal=terminal,
                    order=order,
                    without_r_c=True
                )

                print('Charging')
                Payments.bill_payment(
                    terminal,
                    order,
                    new_payment.tinkoff_id,
                    rebuill_query.rebill_id,
                )
            else:
                new_payment = Payments.create_new_payment(
                    terminal=terminal,
                    order=order,
                )


    def query(id=None, tinkoff_id=None, terminal=None, terminal_id=None, mode='single'):
        if mode not in ['single', 'multi']:
            return None

        with Session(engine, expire_on_commit=False) as session:
            if terminal_id:
                terminal = session.query(PaymentTerminals).filter_by(terminal=terminal_id).first()

            if not terminal:
                terminal = session.query(PaymentTerminals).filter_by(default_terminal=True).first()
            
            query = session.query(Payments).filter(Payments.terminal_id == terminal.id)
            
            if tinkoff_id:
                query = query.filter(Payments.tinkoff_id == str(tinkoff_id))
            
            if id:
                query = query.filter(Payments.id == id)
            
            if mode == 'single':
                query = query.first()
            
            if mode == 'multi':
                query = query.all()

            return query


    def get_order_payments(order, filter_status=None):
        with Session(engine, expire_on_commit=False) as session:
            
            order_payments = session.query(Payments).filter_by(order_id=order.id)
            if filter_status:
                order_payments = order_payments.filter_by(status=filter_status)

            order_payments = order_payments.all()
            return 
    
    def create_new_payment(terminal: 'PaymentTerminals', order: 'Orders', without_r_c=False) -> 'Payments':
        """
        Создаёт новый рекуррентный платёж пользователю
        """
        # Define the payment information as a dictionary
        terminal_key = terminal.terminal
        secret_key = terminal.password

        print(f"using terminal {terminal.terminal}")
        print(f"terminal password {terminal.password}")
        print(f"order box: {order.box.box_name}")
        print(f"order box count: {order.box_count}")
        print(f"order address: {order.address.id}, {order.address.address}")
        print(f"order region: {order.address.region.name_full}")

        box_price = None
        print(len(order.box.regional_pricing))

        if len(order.box.regional_pricing) > 0:
            for regional_price in order.box.regional_pricing:
                print(regional_price.region.id)
                print(order.address.region.id)
                if regional_price.region.id == order.address.region.id:
                    print("USING REGIONAL PRICING FOR BOX")
                    box_price = regional_price.price
        
        if box_price == None:
            print("USING DEFAULT PRICING FOR BOX")
            box_price = order.box.pricing_default
        
        box_count = order.box_count
        if not box_count:
            box_count = 1

        print('---')

        # notification_url = 'http://94.41.188.133:8000/api/payment/notify/auto'
        notification_url = 'http://5.253.62.213:8000/api/payment/notify/auto'

        payment_data = {}

        if without_r_c:
            payment_data = {
                'TerminalKey':terminal_key,
                'OrderId': str(order.order_num),
                'Amount': str(int(box_price*box_count*100)),#*100 потому что указывается сумма в копейках
                "Description": str(order.box.box_name)+' ('+str(order.box_count)+') шт.', # The order description
                "Language": "ru", # The language code (ru or en)
                "PayType": "O", # The payment type (O for one-time payment)
                'DATA': {
                        'Phone': order.user.phone_number,
                        'Email': order.user.email,
                },
                'Receipt': {
                        'Phone': str(order.user.phone_number),
                        'Email': str(order.user.email),
                        'Taxation':'usn_income',#упрощёнка
                        'Items':[{  #https://www.tinkoff.ru/kassa/develop/api/receipt/#Items
                                'Name':str(order.box.box_name),
                                'Quantity':str(box_count),
                                'Amount': str(int(box_price*box_count*100)),
                                'Tax':'none',#без НДС
                                'Price':str(int(box_price*100)),
                        },]
                        },

                "SuccessURL": f"{T_BOT_URL}/?payment=1", # The URL for successful payments
                "NotificationURL": notification_url, # The URL for payment notifications
                "FailURL": f"{T_BOT_URL}/?payment=0"  #The URL for failed payments
            }
        else:
            #TODO: Опциональное формирование чека
            payment_data = {
                    'TerminalKey':terminal_key,
                    'OrderId': str(order.order_num),
                    'Amount': str(int(box_price*box_count*100)),#*100 потому что указывается сумма в копейках
                    "Description": str(order.box.box_name)+' ('+str(order.box_count)+') шт.', # The order description
                    "Language": "ru", # The language code (ru or en)
                    "PayType": "O", # The payment type (O for one-time payment)
                    "Recurrent": "Y", # Indicates whether the payment is recurrent (N for no)
                    "CustomerKey": f"{order.user.id}",
                    'DATA': {
                            'Phone': order.user.phone_number,
                            'Email': order.user.email,
                    },
                    'Receipt': {
                            'Phone': str(order.user.phone_number),
                            'Email': str(order.user.email),
                            'Taxation':'usn_income',#упрощёнка
                            'Items':[{  #https://www.tinkoff.ru/kassa/develop/api/receipt/#Items
                                    'Name':str(order.box.box_name),
                                    'Quantity':str(box_count),
                                    'Amount': str(int(box_price*box_count*100)),
                                    'Tax':'none',#без НДС
                                    'Price':str(int(box_price*100)),
                            },]
                            },

                    "SuccessURL": f"{T_BOT_URL}/?payment=1", # The URL for successful payments
                    "NotificationURL": notification_url, # The URL for payment notifications
                    "FailURL": f"{T_BOT_URL}/?payment=0"  #The URL for failed payments
            }

        #путь по которому мы отправляем свой запрос, прописан в документации банка
        url = f"{TINKOFF_API_URL}/Init"

        headers = {
            'Content-Type': 'application/json'
        }

        values = {}

        for payment_value in payment_data:
            if (type(payment_data[payment_value]) == dict):
                continue
            values[payment_value] = payment_data[payment_value]

        values['Password'] = secret_key

        # Concatenate all values in the correct order
        keys = list(values.keys())
        keys.sort()
        values = {i: values[i] for i in keys}
        
        concatenated_values = ''.join([values[key] for key in (values.keys())])
        hash_object = hashlib.sha256(concatenated_values.encode('utf-8'))
        token = hash_object.hexdigest()

        payment_data['Token'] = token
        
        # print(values)
        # print(token)

        response = requests.post(url, json=payment_data, headers = headers)

        print(response.status_code)
        print(response.text)

        if response.json()['Success']:
            r_data = response.json()
            payment_url = response.json()['PaymentURL']

            with Session(engine, expire_on_commit=False) as session:
                new_payment = Payments(
                    tinkoff_id = r_data['PaymentId'],
                    order_id = r_data['OrderId'],
                    status = r_data['Status'],
                    is_reocurring = True,
                    terminal_id = terminal.id,
                    payment_url = payment_url,
                    amount = payment_data['Amount']
                )

                session.add(new_payment)
                session.commit()

            send_message_through_bot(
                order.user.telegram_id,
                message=f"От вас требуется оплата заявки ({order.order_num}) по адресу ({order.address.address})",
                btn={
                    "inline_keyboard" : [[{
                    "text" : "Перейти к оплате",
                    "url": payment_url,
                }]]}
            )
            try:
                set_timed_func('p', new_payment.id, 'M:01')
            except Exception as err:
                print(err)

            return new_payment

        else:
            message = response.json()['Message']+' '+response.json()['Details']
            return message
            

    def check_order_status(payment_internal_id, order_id, terminal=None):
        """
        Проверяет статус рекуррентного платежа
        """
        with Session(engine, expire_on_commit=False) as session:
            if not terminal:
                terminal = session.query(PaymentTerminals).filter_by(default_terminal=True).first()

            payment_query = session.query(Payments).filter_by(id=payment_internal_id).first()
            if not payment_query:
                return None
            payment_id = payment_query.tinkoff_id

            # url = "https://securepay.tinkoff.ru/v2/GetState"
            url = f"{TINKOFF_API_URL}/CheckOrder"

            headers = {
                'Content-Type': 'application/json'
            }

            terminal_key = '1690270113071DEMO'
            # Replace with your Tinkoff Merchant Secret Key
            secret_key = '22vjtguawas9bqw6'

            values = {
                    'OrderId': str(payment_query.order_id),
                    'Password': secret_key,
                    'TerminalKey': terminal_key
            }
            # Concatenate all values in the correct order
            concatenated_values = ''.join([values[key] for key in (values.keys())])

            # Calculate the hash using SHA-256 algorithm
            hash_object = hashlib.sha256(concatenated_values.encode('utf-8'))
            token = hash_object.hexdigest()

            payment_data = {
                    'TerminalKey': terminal_key,
                    'OrderId': payment_query.order_id,
                    'Token': token,
            }

            response = requests.post(
                url, 
                json=payment_data,
                headers=headers
                )

            print(response.status_code)
            print(response.json())
            
            return response.json()


    def check_payment_status(payment_internal_id, terminal=None):
        """
        Проверяет статус единоразового платежа
        """
        with Session(engine, expire_on_commit=False) as session:
            if not terminal:
                terminal = session.query(PaymentTerminals).filter_by(default_terminal=True).first()

            payment_query = session.query(Payments).filter_by(id=payment_internal_id).first()
            if not payment_query:
                return None
            payment_id = payment_query.tinkoff_id

            url = f"{TINKOFF_API_URL}/GetState"
            # url = "https://securepay.tinkoff.ru/v2/CheckOrder"

            headers = {
                'Content-Type': 'application/json'
            }

            terminal_key = terminal.terminal
            secret_key = terminal.password

            values = {
                    'Password': secret_key,
                    'PaymentId': payment_id,
                    'TerminalKey': terminal_key
            }
            # Concatenate all values in the correct order
            concatenated_values = ''.join([values[key] for key in (values.keys())])

            # Calculate the hash using SHA-256 algorithm
            hash_object = hashlib.sha256(concatenated_values.encode('utf-8'))
            token = hash_object.hexdigest()

            payment_data = {
                    'TerminalKey': terminal_key,
                    'PaymentId': payment_id,
                    'Token': token,
            }

            response = requests.post(
                url, 
                json=payment_data,
                headers=headers
                )

            print(response.status_code)
            print(response.json())
            r_data = response.json()

            if response.status_code == 200:
                payment_query.status = response.json()['Status']

                if r_data['Success'] and r_data['Status'] == "CONFIRMED":
                    payment_query.order.update_status(OrderStatuses.status_payed().id)

                session.commit()
            
            return response.json()


    def bill_payment(terminal, order, payment_id, rebill_id):
        """
        Провести автоплатёж
        """

        p_data = {
            "TerminalKey": terminal.terminal,
            "PaymentId": payment_id,
            "RebillId": rebill_id,
            "SendEmail": 'true',
            "InfoEmail": order.user.email
        }

        url = f"{TINKOFF_API_URL}/Charge"

        headers = {
            'Content-Type': 'application/json'
        }

        token = create_tinkoff_token(p_data, terminal.password)
        p_data['Token'] = token

        response = requests.post(url, json=p_data, headers = headers)

        print(p_data)
        print(response.status_code)
        print(response.text)


class PaymentClientData(Base):
    """
    Данные оплаты клиента
    """
    __tablename__ = 'payment_client_data'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    card_id = Column(String())

    pan = Column(String()) 
    status = Column(String())
    rebill_id = Column(String())
    card_type = Column(String())
    exp_date = Column(String())
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    user = relationship('Users', backref='payment_data', lazy='joined')

    default_card = Column(Boolean(), default=False)

    date_created = Column(DateTime(), default=default_time)

    def get_client_data_from_api(user, terminal):
        p_data = {
            "TerminalKey": terminal.terminal,
            "CustomerKey": f"{user.id}",
            "SavedCard": "true",
        }

        token = create_tinkoff_token(p_data, terminal.password)
        p_data['Token'] = token
        url = f'{TINKOFF_API_URL}/GetCardList'
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=p_data, headers = headers)
        print(len(response.json()))
        print(response.json())
        if response.status_code == 200:
            for card_data in response.json():
                j_data = card_data
                print(j_data)
                with Session(engine, expire_on_commit=False) as session:
                    try:
                        search_query = session.query(PaymentClientData).filter_by(card_id=j_data['CardId']).first()
                    except Exception as err:
                        print(err)
                        continue

                    if search_query:
                        return j_data

                    new_payment_data = PaymentClientData(
                        card_id = j_data['CardId'],
                        pan = j_data['Pan'],
                        status = j_data['Status'],
                        rebill_id = j_data['RebillId'],
                        card_type = j_data['CardType'],
                        exp_date = j_data['ExpDate'],
                        user_id = user.id
                    )

                    session.add(new_payment_data)
                    session.commit()

        return response.json()

class PaymentTerminals(Base):
    """
    Платёжные шлюзы
    """
    __tablename__ = 'payment_terminals'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    terminal = Column(String(), unique=True, nullable=False) 
    password = Column(String(), unique=True, nullable=False) 
    default_terminal = Column(Boolean(), default=False)

    payments = relationship('Payments', backref='terminal', lazy=True)


class WeekDaysWork(Base):
    """
    Указание нерабочих дней в неделю, регулярные
    """

    __tablename__ = 'week_days_work'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    weekday = Column(String(), nullable=False)


class DaysWork(Base):
    """
    Указание нерабочих дней, по дате
    """

    __tablename__ = 'days_work'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime(), default=None, nullable=False)


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
    addresses = relationship('Address', backref='region', lazy=True)
    

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
    route_link = Column(String(), nullable=True, default=None)
    route_task_id = Column(String(), nullable=True, default=None)

    #На какой день предназначен маршрут 
    date_created = Column(DateTime(), default=default_time)
    orders = relationship('RoutesOrders', backref='routes', lazy='subquery')
    
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

    order = relationship('Orders', backref='routedorders', lazy='subquery')


class BotSettingsTypes(Base):
    __tablename__ ="bot_settings_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    type_id = Column(UUID(as_uuid=True), ForeignKey('bot_settings.id'))
    setting_id = Column(UUID(as_uuid=True), ForeignKey('settings_types.id'))
    date_created = Column(DateTime(), default=default_time)


class BotSettings(Base):
    __tablename__ ="bot_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(), nullable=True) #Имя в чел-ом формате
    key = Column(String(), unique=True) #название в боте
    value = Column(String()) #текст
    detail = Column(String(), nullable=True) #коммент

    #TODO: Добавить типы данных
    types = relationship('SettingsTypes', secondary='bot_settings_types', backref='botsettings', lazy='joined')
    date_created = Column(DateTime(), default=default_time)


class SettingsTypes(Base):
    __tablename__ ="settings_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(), nullable=False)

    settings = relationship('BotSettings', secondary='bot_settings_types', backref='settingstypes')
    date_created = Column(DateTime(), default=default_time)


class RegionalBoxPrices(Base):
    __tablename__ = 'regional_box_prices'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'))
    box = Column(UUID(as_uuid=True), ForeignKey('boxtypes.id'))
    price = Column(Float())
    region = relationship('Regions', backref='regionalboxprices', lazy='joined')


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
    print("Adding default roles")
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

    print("Done adding default roles")


def init_status_table():
    """
    инициализировать таблицу статусов
    """
    print("Adding default statuses")
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

    print("Done adding default statuses")


def init_boxtype_table():
    """
    инициализировать таблицу контейнеров
    """
    print("Adding default box types")
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

    print("Done adding box types")

def create_admin_user():
    """
    Создать админского пользователя
    """
    print("Creating default admin user")

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
            print("Default admin exists, skipping...")
            return
        print(f"User data: {new_user_data}")

        new_user_data.password = get_password_hash(new_user_data.password)
        new_user_data = new_user_data.model_dump()
        user_role = new_user_data["role"]
        del new_user_data["role"]

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

        print("Done adding default admin user")
        return


def add_default_messages_bot():
    start_text = """
    Добро пожаловать в бота по удобному сбору и вывозу мусора.
    Мы поможем вам легко и быстро сделать свое пространство чище и свободнее.
    Работать с ботом просто!
    """

    registration_menu_text = """
    Приветствуем вас в нашем боте.
    Если вы ранее уже пользовались ранее нашими услугами, то вы можете авторизоваться двумя способами:
    По номеру телефона, просто отправьте в чат боту свой номер телефона (через кнопку Поделиться номером), либо просто текстом в формате 79124567898, бот проверит и авторизуем вам
    Через промокод, вы можете запросить его у менеджера, с которым взаимодействовали ранее. Полученный промокод просто отправьте боту в чат
    Если вы ранее не пользовались нашими услугами, то нажмите ниже кнопку Начать использовать бота для перехода к главное меню и выбора услуги

    Если по каким-то причинам у вас не получается авторизоваться, то напишите об этом менеджеру, он поможет решить возникшую ситуацию
    Контакты менеджера:
    @ссылка_на_телеграм_аккаунте_менежера
    +79124567899
    """

    order_info_text = """
    Заявка: № <b>{}</b>
    Адрес: <b>{}</b>
    День вывоза: <b>{}</b>
    Комментарий к заявке: <b>{}</b>
    Статус: <b>{}</b>
    Тип контейнера: <b>{}</b>
    Количество контейнеров: <b>{}</b>
    Сумма заказа: <b>{}</b>
    Заявка создана: <b>{}</b>
    """

    questionnaire_text = """
    Анкета:
    Имя: <b>{}</b>
    Фамилия: <b>{}</b>
    Телефон: <b>{}</b>
    Е-мейл: <b>{}</b>
    """

    schedule_text = """
    Есть два варианта:
    По запросу - вывезем мусор по вашей заявке. Для этого нужно будет каждый раз создавать заявку
    По расписанию - будем вывозить мусор в определенные дни недели/месяца, заявки будут создаваться автоматически, бот будет вас уведомлять

    """

    MESSAGES = {
        'START': "Добро пожаловать в бота по удобному сбору и вывозу мусора.\nМы поможем вам легко и быстро сделать свое пространство чище и свободнее.\nРаботать с ботом просто!",
        'REGISTRATION_MENU': "Приветствуем вас в нашем боте.\nЕсли вы ранее уже пользовались ранее нашими услугами, то вы можете авторизоваться двумя способами:\nПо номеру телефона, просто отправьте в чат боту свой номер телефона (через кнопку Поделиться номером), либо просто текстом в формате 79124567898, бот проверит и авторизуем вам\nЧерез промокод, вы можете запросить его у менеджера, с которым взаимодействовали ранее. Полученный промокод просто отправьте боту в чат\nЕсли вы ранее не пользовались нашими услугами, то нажмите ниже кнопку Начать использовать бота для перехода к главное меню и выбора услуги\n\nЕсли по каким-то причинам у вас не получается авторизоваться, то напишите об этом менеджеру, он поможет решить возникшую ситуацию\nКонтакты менеджера:\n@ссылка_на_телеграм_аккаунте_менежера +79124567899",
        'MENU': 'Главное меню',
        'SETTINGS': 'В данном меню вы можете управлять настройками сервиса',
        'CREATE_ORDER': 'В какой день вам удобно принять курьера?',
        'APPLICATIONS_HISTORY': 'HERE История заявок',
        'MY_ADDRESSES': 'HERE Мои адреса',
        'ADD_ADDRESS': 'В данном меню вы можете управлять своими адресами:',
        'PAYMENTS': 'Данный раздел находится в разработке',
        'QUESTIONNAIRE': "Анкета:\nИмя: <b>{}</b>\nФамилия: <b>{}</b>\nТелефон: <b>{}</b>\nЕ-мейл: <b>{}</b>",
        'CHANGE_QUESTIONNAIRE': 'Выберите, что хотите изменить:',
        'NOTIFICATIONS': 'HERE Уведомления',
        'ABOUT': 'Для вашего удобства мы записали небольшое видео по использованию бота, не забудьте с ним ознакомится.',
        'GO_TO_MENU': 'Для возврата в главное меню нажмите кнопку ниже',
        'EMPTY_ADDRESS_RESULT': 'К сожалению, по вашему запросу не удалось найти нужный адрес\nПопробуйте еще раз',
        'CHOOSE_DEFAULT_ADDRESS': 'Выберите адрес по умолчанию',
        'CHOOSE_DELETE_ADDRESS': 'Выберите адрес для удаления',
        'DEFAULT_ADDRESS_IS_SELECTED': 'Адрес: <b>{}</b> выбран по умолчанию',
        'ADDRESS_WAS_ADDED': 'Адрес: <b>{}</b> успешно добавлен',
        'WRITE_YOUR_FIRSTNAME': 'Напишите ваше имя',
        'WRITE_YOUR_LASTNAME': 'Напишите вашу фамилию',
        'WRITE_YOUR_PHONE_NUMBER': 'Напишите номер телефон, начиная с 8',
        'WRITE_YOUR_EMAIL': 'Напишите адрес электронный почты',
        'WRITE_YOUR_DETAIL_ADDRESS': 'Введите ваш подъезд и номер квартиры',
        'WRITE_COMMENT_ADDRESS': 'Напишите комментарий к адресу\nЕсли его нет, то нажмите кнопку ниже',
        'WRITE_COMMENT_ORDER': 'Напишите комментарий к заявке\nЕсли его нет, то нажмите кнопку ниже',
        'PHONE_NOT_FOUND': 'Не найден указанный номер телефона\nПопробуйте ввести номер текстом',
        'PROMOCODE_NOT_FOUND': 'Промокод не найден, можете обратиться к менеджеру',
        'ORDER_INFO': "Заявка: № <b>{}</b>\nАдрес: <b>{}</b>\nКомментарий к адресу: <b>{}</b>\nДень вывоза: <b>{}</b>\nКомментарий к заявке: <b>{}</b>\nСтатус: <b>{}</b>\nТип контейнера: <b>{}</b>\nКоличество контейнеров: <b>{}</b>\nСумма заказа: <b>{}</b>\nЗаявка создана: <b>{}</b>",
        'SEND_SMS': 'На указанный номер телефона придет код(123)',
        'SEND_EMAIL': 'На указанный email придет код(123)',
        'WRONG_CODE': 'Неверный код',
        'SCHEDULE': "Есть два варианта:\nПо запросу - вывезем мусор по вашей заявке. Для этого нужно будет каждый раз создавать заявку\nПо расписанию - будем вывозить мусор в определенные дни недели/месяца, заявки будут создаваться автоматически, бот будет вас уведомлять",
        'CHANGE_SCHEDULE': 'Адрес: <b>{}</b>\nРасписание: <b>{}</b>',
        'CHANGE_SCHEDULE_ADDRESS': 'Изменить расписание у <b>{}</b>',
        'WRONG_PHONE_NUMBER': 'Неверный номер телефона! Введите номер, начиная с 8',
        'WRONG_EMAIL': 'Неверный email!',
        'WRONG_FIRSTNAME': 'Неверное имя! Оно должно состоять из букв',
        'WRONG_LASTNAME': 'Неверная фамилия! Она должно состоять из букв',
        'WRONG_ADDRESS': 'К сожалению, ваш адрес сейчас не поддерживается нашим сервисом\n\nБот работает только в Москве(<b>Преображенское, Люблино, Орехово-Борисово Северное, Раменки</b>)\nПожалуйста, выберите адрес в пределах данных районов',
        'CHOOSE_SCHEDULE_PERIOD': 'Выберите по каким дням вывозить мусор:',
        'CHOOSE_DAY_OF_WEEK': 'Выберите дни недели',
        'CHOOSE_DAY_OF_MONTH': 'Выберите дни месяца',
        'SAVE_SCHEDULE': 'Ваше расписание сохранено',
        'ADD_NEW_ADDRESS': 'Отправьте адрес в виде строки (город улица дом подъезд квартира) или по кнопке с геопозицией',
        'CHOOSE_DATE_ORDER': 'Выберите дату вывоза:',
        'WRONG_ORDER_DATE': 'Неверный формат даты',
        'CHOOSE_ADDRESS_ORDER': 'Выберите адрес:',
        'CHOOSE_CONTAINER': 'Выберите тип контейнера для вывоза:',
        'CHOOSE_COUNT_CONTAINER': 'Введите количество контейнеров:',
        'ORDER_WAS_CREATED': 'Заявка создана! В ближайшее время она будет взята в работу',
        'ADDRESS_INFO_DEDAULT': '<b>Адрес № {}</b> (по умолчанию)\n{}',
        'ADDRESS_INFO_NOT_DEDAULT': '<b>Адрес № {}</b> \n{}',
        'YOU_HAVE_ACTIVE_ORDERS': 'У вас есть активные заявки ({})',
        'PAYMENT_ORDER': 'Для оплаты заказа: {} перейдите по ссылке: {}',
        'ORDER_HISTORY': 'История изменения статуса заказа: <b>{}</b>\n\n {}',
        'QUESTION_YES_NO': 'Уверены?',
        'YOUR_ORDERS': 'Список ваших заявок: ',
        'YOUR_ORDERS_BY_MONTH': 'Список ваших заявок по месяцам: ',
        'WRITE_TO_MANAGER': 'Добрый день!\n У меня есть вопрос по заявке {}',
        'CANCEL_ORDER_MESSAGE': 'Добрый день!\n Хочу отменить заявку {}',
        'CHOOSE_CHANGE_CONTAINER': 'Выберите что изменить: ',
        'ERROR_IN_HANDLER': 'Произошла ошибка! Пожалуйста, перезапустите бота по кнопке или перейдите персональной ссылке',
        'API_ERROR': 'Произошла ошибка на сервере!\nПожалуйста, попробуйте снова',
        'COURIER': 'Вы являетесь курьером сервиса\nДля просмотра маршрута нажмите кнопку ниже:',
        'NO_ROUTES': 'Hа текущий момент маршрута нет',
        'CURRENT_ROUTE': 'Текущий маршрут:',
        'ROUTE_INFO': 'Точка: {}',
        'COMMENT_TO_POINT': 'Причина:',
        'NO_ORDER': 'Список заявок пока пуст...',
        'NO_WORK_DAYS_FOR_ADDRESS': 'Мы добавили ваш адрес\nКак только наш сервис будет работать в вашем районе, то мы вам сообщим)\n\nСейчас работают районы: <b>Преображенское, Люблино, Орехово-Борисово Северное, Раменки</b>',
        'UNAVAILABLE_DAY': 'В данный день мы не можем вывозить(((',
        'YOUR_CHANGE_WAS_ADDED': 'Ваши изменения успешно применены',
        'ORDER_WAS_APPROVED': 'Заявка # <b>{}</b> успешно подтверждена',
        'ANY_TEXT': 'Главное меню',
        'NO_SCHEDULE_ADDRESS': '<b>Адресов пока нет</b>.\nДобавьте адреса, после этого сможете настроить расписание',
        'YOUR_ADD_ADDRESS': 'Адрес: <b>{}</b>',
        'ADDRESS_FOUND_BY_YANDEX': 'Найденный адрес: <b>{}</b>\n\nВерно?',
        'TRY_AGAIN_ADD_ADDRESS': 'Пожалуйста, попробуйте еще раз)',
        'NO_WORK_DAYS': 'На данный момент у адреса: <b>{}</b> отсутствуют дни вывоза\nВсе равно добавить адрес?',
        'NO_WORK_AREA': 'На данный момент в этом районе не принимаются заявки\nВсе равно добавить адрес?',
    }
    
    with Session(engine, expire_on_commit=False) as session:
        #Проверить тэг для сообщений бота
        type_query = session.query(SettingsTypes).filter(SettingsTypes.name=='бот').first()
        if not type_query:
            type_query = SettingsTypes(name='бот')
            session.add(type_query)
            session.commit()

        for message in MESSAGES:
            message_key_query = session.query(BotSettings).\
                filter(BotSettings.key == message).first()

            if message_key_query:
                continue
            print(f"adding setting {message}")

            new_message = BotSettings(
                key = message,
                value = MESSAGES[message]
            )               
            new_message.types = [type_query]
            session.add(new_message)

        session.commit()
        print('Done adding messages')


def add_default_settings():
    TYPES_SYSTEM = [
        'буловый',
        'целочисленный',
        'строка',
        'система'
    ]


    DEFAULT_SETTINGS = [
        {
            "KEY": "POLL_GENERATION_ACTIVE",
            "VALUE": "1",
            "NAME": "автоматическая генерация пула",
            "DETAIL": "Вкл/выкл автоматическую генерацию пула",
            "TYPE": TYPES_SYSTEM[0]
        },
        {
            "KEY": "ACCEPT_NEW_ORDERS_FROM_BOT",
            "VALUE": "1", 
            "NAME": "принятие заявок через бота",
            "DETAIL": "Вкл/выкл возможность создавать заявки через тг бота",
            "TYPE": TYPES_SYSTEM[0]
        },
        {
            "KEY": "ROUTE_GENERATION_ACTIVE",
            "VALUE": "1", 
            "NAME": "автоматическая генарация маршрутов",
            "DETAIL": "Вкл/выкл автоматическую генерацию маршрутов",
            "TYPE": TYPES_SYSTEM[0]
        }
    ]

    with Session(engine, expire_on_commit=False) as session:
        #Проверить тэг для типа сообщений
        for type_setting in TYPES_SYSTEM:
            print(type_setting)
            type_query = session.query(SettingsTypes).filter(SettingsTypes.name==type_setting).first()
            if not type_query:
                type_query = SettingsTypes(name=type_setting)
                session.add(type_query)
            session.commit()

        for setting in DEFAULT_SETTINGS:
            message_key_query = session.query(BotSettings).\
                filter(BotSettings.key == setting['KEY']).first()

            if message_key_query:
                continue
            print(f"adding setting {setting}")

            new_message = BotSettings(
                key = setting["KEY"],
                value = setting["VALUE"],
                name = setting["NAME"],
                detail = setting["DETAIL"]
            )               
            new_message.types = session.query(SettingsTypes).\
                filter(SettingsTypes.name.in_(
                    [TYPES_SYSTEM[3], setting["TYPE"]]
            )).all()

            session.add(new_message)

        session.commit()
        print('Done adding settings')


def create_demo_terminal():
    with Session(engine, expire_on_commit=False) as session:
        terminal_key = '1690270113071DEMO'
        secret_key = '22vjtguawas9bqw6'

        term_query = session.query(PaymentTerminals).filter(PaymentTerminals.terminal==terminal_key).first()
        if term_query:
            return
        
        new_terminal = PaymentTerminals(
            terminal = terminal_key,
            password = secret_key,
            default_terminal = True
        )
        session.add(new_terminal)
        session.commit()

if __name__ == "__main__":
    init_role_table()
    init_boxtype_table()
    init_status_table()
    create_admin_user()
    add_default_messages_bot()
    add_default_settings()
