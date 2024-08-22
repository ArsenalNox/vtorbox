"""
Валидаторы для рутов с описаниями входных данных

Да, придётся под каждую модель писать валидатор
Да, придётся под каждую операцию с опциональными данными писать ещё валидатор
Но как иначе? 
"""
import uuid
from operator import attrgetter       

from pydantic import BaseModel, EmailStr, UUID4, Field, ValidatorFunctionWrapHandler, validator, field_validator
from typing import Optional, Annotated, Any, List, Union, Tuple
from typing_extensions import TypedDict
from datetime import datetime

from pydantic_extra_types.phone_numbers import PhoneNumber

PhoneNumber.phone_format = 'E164'
PhoneNumber.default_region_code = 'RU'

class UserIdMultiple(BaseModel):
    user_id: Optional[UUID4|int] = None


class Order(BaseModel):
    from_user: str
    address_id: UUID4
    day: str 
    comment: Optional[str] = None
    box_type_id: Optional[UUID4] = None
    box_name: Optional[str] = None
    box_count: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    'from_user': '851230989',
                    'address_id': "1cac46a0-7635-4e01-aea4-e3b9f657ca79",
                    'day': '2024-04-07',
                    'box_name': "Пакет",
                    'box_count': 5
                }
            ]
        }
    }


class OrderUpdate(BaseModel):
    """
    Валидация на обновление данных заявки


    Отдельная т.к множество полей опциональные
    """
    address_id: Optional[UUID4] = None
    # box_type_id: UUID4
    box_name: Optional[str] = None
    box_count: Optional[int] = None
    box_type_id: Optional[UUID4] = None
    comment: Optional[str] = None
    comment_courier: Optional[str] = None
    comment_manager: Optional[str] = None
    day: Optional[datetime] = None
    manager_id: Optional[UUID4] = None


class CourierCreationValidator(BaseModel):
    """
    Валидатор на создание курьера
    """
    tg_id: int


class UserSignUp(BaseModel):
    """
    Валидация регистрации
    """
    username: EmailStr
    password: str


class UserLogin(BaseModel):
    username: EmailStr
    password: str
    email: str | None = None
    full_name: str | None = None


class UserCreationValidator(BaseModel):
    #Модель проверки данных на ручное создание пользователя
    email: EmailStr
    password: str | None = None

    telegram_id: int | None = None
    telegram_username: str | None = None
    phone_number: Optional[PhoneNumber] = None

    firstname: str | None = None
    secondname: str | None = None
    patronymic: Optional[str] = None

    role: List[str] = ["customer"]


class UserUpdateValidator(BaseModel):
    """
    Валидатор на обновление данных пользователя

    Все поля кроме айди пользователя не обязательны
    """
    user_id: str #Может быть и тг айди 

    password: Optional[str] = None
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    phone_number: Optional[PhoneNumber] = None
    firstname: Optional[str] = None
    secondname: Optional[str] = None
    patronymic: Optional[str] = None
    email: Optional[EmailStr] = None

    allow_messages_from_bot: Optional[bool] = None

    roles: Optional[list[str]] = None
    link_code: Optional[str] = None
    
    disabled: Optional[bool] = False
    additional_info: Optional[str] = None



class AuthToken(BaseModel):
    access_token: str
    token_type: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: EmailStr | None = None
    scopes: list[str] = []


class RefreshTokenData(BaseModel):
    user_id: UUID4


class CreateUserData(BaseModel):
    tg_id: int
    username: str | None = None #Опциональные т.к пользователь может скрыть или не иметь
    firstname: str | None = None 
    secondname: str | None = None


class UpdateUserDataFromTG(CreateUserData):
    user_id: str


class LinkClientWithPromocodeFromTG(CreateUserData):
    promocode: str


class RegionOut(BaseModel):
    id: UUID4
    name_short: Optional[str]
    name_full: str
    region_type: str
    is_active: bool
    #work_days: Optional[List[str]]
    work_days: Optional[Any] = None
    
    @field_validator('work_days')
    def replace_as_list(cls, v):
        if (v != None) and (type(v) == str):
            return v.split(' ')
        else:
            return v

class RegionOutWithGeoData(RegionOut):
    geodata: str


class RegionUpdate(BaseModel):
    name_short: Optional[str] = None
    name_full: Optional[str] = None
    region_type: Optional[str] = None
    is_active: Optional[bool] = None
    work_days: Optional[List[str]]


class Address(BaseModel):
    """
    Модель на создание/обновление адреса
    """
    main: bool = False
    address:   Optional[str] = None #Текст адреса
    latitude:  Optional[float] = None
    longitude: Optional[float] = None
    detail: Optional[str] = None 
    comment: Optional[str] = None

    distance_from_mkad: Optional[Any] = None
    point_on_map: str | None = None

    selected_day_of_week:  Optional[List[str]] = None
    selected_day_of_month: Optional[List[str]] = None
    interval_type: Optional[str] = None
    interval: Optional[List[str]] = None
    region_id: Optional[UUID4] = None
    region: Annotated[Optional[RegionOut], Field(None)]


    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    'main': 'true',
                    'district': 'МО',
                    'distance_from_mkad': 12,
                    'address': 'Ул. Тверская 4',
                    'detail': '8-53. Домофон 53 и кнопка "вызов".',
                    'comment': "Злая собака, много тараканов",
                }
            ]
        }
    }


class AddressDaysWork(BaseModel):
    date: str
    weekday: str


class AddressOut(BaseModel):
    id: UUID4
    main: bool
    address:   Optional[str] = None 
    latitude:  Optional[float] = None
    longitude: Optional[float] = None
    detail: Optional[str] = None 
    comment: Optional[str] = None

    distance_from_mkad: Optional[Any] = None
    point_on_map: str | None = None

    selected_day_of_week:  Optional[List[str]] = None
    selected_day_of_month: Optional[List[str]] = None
    interval_type: Optional[str] = None
    interval: Optional[List[str]] = None
    region_id: Optional[UUID4] = None
    region: Optional[RegionOut] = None
    work_dates: Optional[List[AddressDaysWork]] = None


class AddressUpdate(Address):
    """
    Модель на обновление данных адреса
    """
    main: bool | None = None
    address: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    district: str | None = None
    region: str | None = None 
    distance_from_mkad: str | None = None
    point_on_map: str | None = None
    interval:  str = None
    interval_type: str = None


class RegionalBoxPrice(BaseModel):
    region_name: str
    region_id: Optional[UUID4] = None
    price: float
    

class BoxTypeCreate(BaseModel):
    box_name: str
    pricing_default: float 
    volume: float
    weight_limit: float
    regional_prices: Optional[List[RegionalBoxPrice]] = None


class BoxType(BoxTypeCreate):
    """
    Модель контейнера
    """
    id: UUID4
    deleted_at: Optional[datetime] = None


class BoxUpdate(BaseModel):
    box_name: Optional[str] = None
    pricing_default: Optional[float] = None
    volume: Optional[float] = None
    weight_limit: Optional[float] = None
    regional_prices: Optional[List[RegionalBoxPrice]] = None


class Status(BaseModel):
    """
    Статус
    """
    status_name: str
    description: str
    message_on_update: Optional[bool] = None


class UserOrderOutData(BaseModel):
    id: UUID4
    email: Optional[EmailStr] 
    telegram_id: Optional[int]
    telegram_username: Optional[str]

    phone_number: Optional[PhoneNumber] = None

    firstname: Optional[str]
    secondname: Optional[str]
    patronymic: Optional[str]

    deleted_at: Optional[datetime] = None
    link_code: Optional[str] = None


class PaymentOut(BaseModel):
    id: UUID4
    tinkoff_id: int
    order_id: int
    amount: Optional[int] = None
    # order = relationship('Orders', backref='payments', lazy='joined')

    status: str
    is_reocurring: bool

    rebill_id: Optional[str] = None
    payment_url: Optional[str] = None

    terminal_id: UUID4

    deleted_at: Optional[datetime] = None
    
    date_created: datetime

    @field_validator('status')
    def replace_as_list(cls, v):
        statuses= {
            "NEW":	'Платёж создан',
            "FORM_SHOWED":	'Страница загрузилась у клиента в браузере',
            "AUTHORIZING":	'Платеж обрабатывается MAPI и платежной системой',
            "3DS_CHECKING":	'Платеж проходит проверку 3D-Secure',
            "3DS_CHECKED":	'Платеж успешно прошел проверку 3D-Secure',
            "AUTHORIZED":	'Платеж авторизован, деньги заблокированы на карте клиента',
            "CONFIRMING":	'Подтверждение платежа обрабатывается MAPI и платежной системой',
            "CONFIRMED":	    'Платеж подтвержден, деньги списаны с карты клиента',
            "REVERSING":	    'Мерчант запросил отмену авторизованного, но еще не подтвержденного платежа. Возврат обрабатывается MAPI и платежной системой',
            "PARTIAL_REVERSED":	'Частичный возврат по авторизованному платежу завершился успешно',
            "REVERSED":	'Полный возврат по авторизованному платежу завершился успешно',
            "REFUNDING":	'Мерчант запросил отмену подтвержденного платежа. Возврат обрабатывается MAPI и платежной системой',
            "PARTIAL_REFUNDED":	'Частичный возврат по подтвержденному платежу завершился успешно',
            "REFUNDED":	'Полный возврат по подтвержденному платежу завершился успешно',
            "СANCELED":	'Мерчант отменил платеж',
            'DEADLINE_EXPIRED':	'Срок платежа истёк',
            "REJECTED":	'Банк отклонил платеж',
            "AUTH_FAIL":	'Платеж завершился ошибкой или не прошел проверку 3D-Secure'
        }
        if (v != None) and (v in statuses.keys()) :
            return statuses[v]
        else:
            return v





class OrderDataChange(BaseModel):
    id: UUID4
    from_user: Optional[UserOrderOutData] = None

    attribute: Optional[str] = None
    new_content: Optional[str] = None
    old_content: Optional[str] = None

    date_created: datetime

    @field_validator('from_user')
    def replace_tel(cls, v):
        return v

        if v == None:
            return UserOrderOutData(
                id= "6f240f96-acb0-4f98-8f0a-534a592ee062",
                email= "user3@example.com",
                telegram_id= None,
                telegram_username= None,
                phone_number= None,
                firstname=  None,
                secondname= None,
                patronymic= None,
                deleted_at= None,
                link_code= "ca740518-6"
            )




class OrderOut(BaseModel):
    id: UUID4
    order_num: Optional[int] = None
    user_order_num: Optional[int] = None

    last_disposal: Optional[datetime] = None
    times_completed: int | None = None
    day: Optional[datetime] = None
    date_created: datetime
    last_updated: datetime
    legal_entity: bool
    
    courier_id: Optional[UUID4] = None
    manager_id: Optional[UUID4] = None
    manager_info: Optional[UserOrderOutData] = None

    comment: Optional[str] = None
    comment_manager: Optional[str] = None
    comment_courier: Optional[str] = None
    time_window: Optional[str] = None
    comment_history: Optional[Any] = None

    interval_type: Optional[str] = None
    interval: Optional[Any] = None

    tg_id: Optional[int] = None
    user_data: Annotated[Optional[UserOrderOutData], Field(None)]

    address_id: UUID4
    address_data: Annotated[Optional[AddressOut], Field(None)]

    box_type_id: Optional[UUID4] = None
    box_count: Optional[int] = None
    box_data: Annotated[Optional[BoxType], Field(None)]

    status: UUID4
    status_data: Annotated[Optional[Status], Field(None)]
    deleted_at: Optional[datetime] = None

    payments: Annotated[Optional[List[PaymentOut]], Field(None)]
    data_changes: Annotated[Optional[List[OrderDataChange]], Field(None)]

    @field_validator("data_changes")
    def sort_data_changes_by_date(cls, v):
        if v == None:
            return v

        sorted_list = sorted(v, key=attrgetter('date_created'), reverse=True)
        return sorted_list

class UserOut(BaseModel):
    """
    Возврат данных пользвателя
    """
    email: Optional[EmailStr] 

    id: UUID4
    telegram_id: Optional[int]
    telegram_username: Optional[str]

    phone_number: Optional[str] = None
    password_plain: Optional[str] = None

    firstname: Optional[str] = None
    secondname: Optional[str] = None
    patronymic: Optional[str] = None
    allow_messages_from_bot: bool

    # orders: Optional[list[Annotated[Optional[OrderOut], Field(None)]]]
    orders: Optional[list[OrderOut]] = None
    roles: Optional[list[str]] = None
    deleted_at: Optional[datetime] = None
    last_action: Optional[datetime] = None

    link_code: Optional[str] = None
    
    disabled: bool = False
    additional_info: Optional[str] = None
    date_created: datetime

    code: Optional[int] = None

    @field_validator('roles')
    def only_unique_roles(cls, v):
        if (v != None):
            set_v = set(v)
            unique_roles = list(set_v)
            return unique_roles
        else:
            return v

    @field_validator('phone_number')
    def replace_tel(cls, v):
        if v == None:
            return
        if "tel:" in v:
            v = str(v).replace('tel:', '')
        return v


class SubStatusOut(BaseModel):
    id: UUID4
    status_name: str
    description: str


class SubStatusListOut(BaseModel):
    id: UUID4
    status_to: SubStatusOut


class StatusOut(BaseModel):
    status_name: str
    description: str
    message_on_update: Optional[bool] = None
    allow_from_list: Optional[List[SubStatusListOut]] = None
    allow_to_list: Optional[List[SubStatusListOut]] = None
    id: UUID4


class AddressSchedule(BaseModel):
    selected_day_of_week:  Optional[List[str]] = None
    selected_day_of_month: Optional[List[str]] = None
    selected_dates: Optional[List[datetime]] = None

    interval_type: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    'selected_day_of_month': ['1', '23', '24'],
                    'interval_type': 'month_day'
                }
            ]}}


class OrderRouteOut(BaseModel):
    order_id: UUID4
    route_id: UUID4
    order: OrderOut


class RouteOut(BaseModel):
    id: UUID4
    courier_id: UUID4
    short_name: str
    route_link: Optional[str] = None
    route_task_id: Optional[str] = None

    #На какой день предназначен маршрут 
    date_created: datetime
    orders: Optional[List[OrderRouteOut]] = None
    

class CourierOut(UserOut):
    assigned_orders: Optional[List[OrderOut]] = None
    assigned_routes: Optional[List[RouteOut]] = None


class ManagerOut(UserOut):
    assigned_orders: Optional[List[OrderOut]] = None


class BotSettingType(BaseModel):
    id: Optional[UUID4] = None
    name: Optional[str] = None

class BotSetting(BaseModel):
    """
    Схема на создание настройки
    """
    
    key: str
    value: str
    name: Optional[str] = None
    detail: Optional[str] = None
    types: List[BotSettingType] = None


class BotSettingOut(BotSetting):
    id: UUID4


class BotSettingUpdate(BaseModel):
    value: Optional[str] = None
    name: Optional[str] = None
    detail: Optional[str] = None
    types: List[BotSettingType] = None

class PaymentTerminal(BaseModel):

    terminal: Optional[str] = None
    password: Optional[str] = None
    default_terminal: Optional[bool] = None


class PaymentNotification(BaseModel):
    TerminalKey: Optional[str] = None
    Amount: Optional[int] = None
    OrderId: Optional[str] = None
    Success: Optional[bool] = None
    Status: Optional[str] = None
    PaymentId: Optional[int] = None
    ErrorCode: Optional[str] = None
    Message: Optional[str] = None
    Details: Optional[str] = None
    RebillId: Optional[int] = None
    CardId: Optional[str] = None
    Pan: Optional[str] = None
    ExpDate: Optional[str] = None
    Token: Optional[str] = None
    DATA: Optional[Any] = None


class FilteredOrderOut(BaseModel):
    global_count: int
    count: int
    orders: List[OrderOut]


class UserRegistrationStatChartData(BaseModel):
    date: datetime
    count: int


class UserRegistrationStat(BaseModel):
    number: int
    deleted_count: int
    registered_in_month: int
    percentage: float
    chartData: List[UserRegistrationStatChartData]


class OrderStatusStatistic(BaseModel):
    name: str
    value: int


class OrderRegionStatistic(OrderStatusStatistic):
    pass



class NotificationTypes(BaseModel):
    id: Optional[UUID4] = None
    type_name: Optional[str] = None


class Notification(BaseModel):
    content: str
    resource_id: Optional[UUID4] = None
    resource_type: Optional[str] = None
    sent_to_tg: bool = False
    for_user: Optional[UUID4] = None
    for_user_group: Optional[str] = None

    n_type: Optional[NotificationTypes] = None
    date_created: Optional[datetime] = None
    read_by_user: Optional[bool] = False


class NotificationOut(Notification):
    id: UUID4


class NotificationCountOut(BaseModel):
    global_count: int
    count: int
    data: Optional[List[NotificationOut]]


class NotificationsAsRead(BaseModel):
    ids: List[UUID4]