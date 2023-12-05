"""
Валидаторы для рутов с описаниями входных данных

Да, придётся под каждую модель писать валидатор
Да, придётся под каждую операцию с опциональными данными писать ещё валидатор
Но как иначе? 
"""

from pydantic import BaseModel, EmailStr


#TODO: Модели под пользователей
#TODO: Модели под заявку
#TODO: Модели под админа
#TODO: Модели под менеджера


class Order(BaseModel):
    user_tg_id: int
    district: str
    region: str
    distance_from_mkad: int
    address: str
    full_adress: str | None = None 
    weekday: int 
    full_name: str | None = None
    phone_number: str
    price: float
    is_legal_entity: bool | None = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                'user_tg_id': 7643079034697,
                'district': 'МО',
                'region': 'Красногорск',
                'distance_from_mkad': 12,
                'address': 'Ул. Пушкина 8',
                'full_adress': '8-53. Домофон 53 и кнопка "вызов".' ,
                'weekday': 6,
                'full_name': 'Иванов Иван Иванович',
                'phone_number': '+7 123 2323 88 88', 
                'price': 350,
                'is_legal_entity': False,
                }
            ]
        }
    }


class OrderUpdate(BaseModel):
    """
    Валидация на обновление данных заявки
    Отдельная т.к множество полей опциональные
    """
    pass


class CourierCreationValidator(BaseModel):
    """
    Валидатор на создание курьера
    """
    tg_id: int


class User(BaseModel):
    """
    Валидатор на создание пользователя
    """
    pass


class UserUpdateValidator(BaseModel):
    """
    Валидатор на обновление данных пользователя
    Все поля кроме айди пользователя не обязательны
    """
    pass


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
    phone_number: str | None = None
    full_name: str

    role: str = "user"


class AuthToken(BaseModel):
    access_token: str
    token_type: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: EmailStr | None = None
    scopes: list[str] = []
