"""
Валидаторы для рутов с описаниями входных данных

Да, придётся под каждую модель писать валидатор
Да, придётся под каждую операцию с опциональными данными писать ещё валидатор
Но как иначе? 
"""
import uuid

from pydantic import BaseModel, EmailStr, UUID4, Field, ValidatorFunctionWrapHandler, validator
from typing import Optional, Annotated, Any, List, Union, Tuple
from typing_extensions import TypedDict
from datetime import datetime
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
                    'day': 'завтра',
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
    comment_courier: Optional[str] = None
    comment_manager: Optional[str] = None
    day: Optional[datetime] = None


class CourierCreationValidator(BaseModel):
    """
    Валидатор на создание курьера
    """
    tg_id: int



class OrderFilter(BaseModel):
    """
    Валидация фильтров на получение заявка
    """


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
    phone_number: int | None = None

    firstname: str | None = None
    secondname: str | None = None
    patronymic: Optional[str] = None

    role: str = "customer"


class UserUpdateValidator(BaseModel):
    """
    Валидатор на обновление данных пользователя

    Все поля кроме айди пользователя не обязательны
    """
    user_id: str #Может быть и тг айди 

    password: Optional[str] = None
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    phone_number: Optional[int] = None
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
    
    @validator('work_days', pre=True, always=True)
    def replace_as_list(cls, v):
        if v != None:
            return v.split(' ')
        else:
            return None

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

    distance_from_mkad: int | None = None
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

    distance_from_mkad: int | None = None
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


class BoxType(BaseModel):
    """
    Модель контейнера
    """
    box_name: str
    pricing_default: float 
    volume: float
    weight_limit: float


class BoxUpdate(BaseModel):
    box_name: Optional[str]
    pricing_default: Optional[float] 
    volume: Optional[float]
    weight_limit: Optional[float]


class Status(BaseModel):
    """
    Статус
    """
    status_name: str
    description: str


class UserOrderOutData(BaseModel):
    id: UUID4
    email: Optional[EmailStr] 
    telegram_id: Optional[int]
    telegram_username: Optional[str]

    phone_number: Optional[int]

    firstname: Optional[str]
    secondname: Optional[str]
    patronymic: Optional[str]

    deleted_at: Optional[datetime] = None
    link_code: Optional[str] = None


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
    comment_manager: Optional[str] = None
    comment_courier: Optional[str] = None


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


class UserOut(BaseModel):
    """
    Возврат данных пользвателя
    """
    email: Optional[EmailStr] 

    id: UUID4
    telegram_id: Optional[int]
    telegram_username: Optional[str]

    phone_number: Optional[int]
    password_plain: Optional[str] = None

    firstname: Optional[str]
    secondname: Optional[str]
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


class StatusOut(BaseModel):
    status_name: str
    description: str
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


