from app.validators import CreateUserData, UpdateUserDataFromTG
from app.models import Users


from typing import Annotated
from fastapi import APIRouter, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes

from ..models import (
    Users, Session, engine, UsersAddress, Address,
    )

from ..auth import (
    oauth2_scheme, 
    get_current_user
)

from ..validators import (
    LinkClientWithPromocodeFromTG as UserLinkData,
    Address as AddressValidator,
    AddressUpdate as AddressUpdateValidator,
    UserLogin as UserLoginSchema
)

import uuid

router = APIRouter()


@router.post('/user', tags=["users", "bot"])
async def create_user(
    body: CreateUserData,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
):
    """
    Создать нового пользователя из телеграм бота
    """
    with Session(engine, expire_on_commit=False) as session:
        user_query = session.query(Users).filter_by(telegram_id=body.tg_id).first()
        if user_query: 
            return JSONResponse({
                "message": "telegram id already taken"
                }, status_code=400)

        new_user = Users(
            telegram_id=body.tg_id,
            telegram_username = body.username,
            full_name = body.fullname,
            link_code = str(uuid.uuid4())[:10] 
            )
        
        session.add(new_user)
        session.commit()

        return new_user


@router.put('/users/botclient/link', tags=["users", "bot"])
async def create_bot_client_from_link(
    user_link_data: UserLinkData,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    ):
    """
    Привязать пользователя бота к клиенту по коду
    """
    #TODO: Проверка на занятость тг айди? 
    with Session(engine, expire_on_commit=False) as session:
        user_query = session.query(Users).filter_by(link_code=user_link_data.promocode).first()
        if not user_query:
            return JSONResponse({
                "message": f"No user with link code {user_link_data.promocode} found"
            }, status_code=404)
        
        user_query.telegram_id = user_link_data.tg_id
        user_query.telegram_username = user_link_data.username
        user_query.full_name = user_link_data.fullname
        user_query.link_code = None

        session.commit()

        return 

@router.get("/users/phone", tags=["users", "bot"])
async def check_user_by_phone(
    phone_number: str,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    ):
    """
    Поиск пользователя по номеру телефона (search-user-by-phone)
    """

    with Session(engine, expire_on_commit=False) as session:
        user_query = session.query(Users).filter_by(phone_number=phone_number).first()
        if user_query:
            return user_query
        else:
            return JSONResponse({
                "message": "not found"
            }, status_code=404)


@router.get('/users/promocode', tags=["users", "bot"])
async def check_user_by_promocode(
    promocode: str,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    ):
    """
    Поиск пользователя по промокоду (search-user-by-promocode)
    """
    with Session(engine, expire_on_commit=False) as session:
        user_query = session.query(Users).filter_by(link_code=promocode).first()
        if user_query:
            return user_query
        else:
            return JSONResponse({
                "message": "not found"
            }, status_code=404)


@router.get('/users/telegram', tags=["users", "bot"], 
    responses={
        200: {
            "description": "Получение пользователя по телеграм айди",
            "content": {
                    "application/json": {
                        "example": 
                            [   
                                {
                                    "full_name": 'null',
                                    "date_created": "2023-11-29T00:57:57.654800",
                                    "phone_number": 'null',
                                    "email": 'null',
                                    "telegram_id": 7643079034697,
                                    "id": 1
                                }
                            ]
                    }
            }
        },
        404: {
            "description": "User not was not found",
            "content": {
                    "application/json": {
                        "example": {"message": "Not found"}
                    }
                },
        }
    }
)
async def get_user_by_tg_id(
    tg_id:int,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    ):
    with Session(engine, expire_on_commit=False) as session:
        user = session.query(Users).filter_by(telegram_id=tg_id).first()
        if user:
            return user

    return JSONResponse({
        "message": "Not found"
    }, status_code=404)



@router.get('/user/addresses/all', tags=['addresses', "bot"])
async def get_addresses(
    tg_id: int,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    ):
    """
    Получение всех адресов пользователя
    """
    with Session(engine, expire_on_commit=False) as session:
        addresses = session.query(Address).\
            join(UsersAddress, UsersAddress.address_id == Address.id).\
            join(Users, UsersAddress.user_id == Users.id). \
            where(Users.telegram_id == tg_id).all()

        return addresses


@router.get('/user/addresses/main', tags=["addresses", "bot"])
async def get_main_address(
    tg_id: int,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    ):
    """
    Получение главного адреса пользователя
    """
    with Session(engine, expire_on_commit=False) as session:
        address = session.query(Address).\
            join(UsersAddress, UsersAddress.address_id == Address.id).\
            join(Users, UsersAddress.user_id == Users.id). \
            where(Users.telegram_id == tg_id, Address.main == True).first()
        
        return address


@router.post('/user/addresses', tags=["addresses", "bot"])
async def add_user_address(
    address_data: AddressValidator, 
    tg_id: int,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])]
    ):
    """
    Создание адреса пользователя
    """

    user = Users.get_or_create(t_id=int(tg_id))

    with Session(engine, expire_on_commit=False) as session:

        # получаем адрес по координатам и если его нет, создаем новый
        address = session.query(Address).filter_by(
            latitude=address_data.latitude,
            longitude=address_data.longitude
        ).first()
        
        if address:
            return JSONResponse({
                "message": "Address already exists"
            }, 403)

        if address_data.main:
        #Сбросить статус главного у всех адресов
            update_query = session.query(Address).\
                join(UsersAddress, UsersAddress.address_id == Address.id).\
                join(Users, UsersAddress.user_id == Users.id). \
                where(Users.telegram_id == tg_id).all()

            #TODO: Update в query
            for address in update_query: 
                address.main = False

        #создаем новый адрес
        address = Address(**address_data.model_dump())
        session.add(address)
        session.commit()

        user_address = UsersAddress(
            user_id=user.id,
            address_id=address.id
        )
        session.add(user_address)
        session.commit()

        return address


@router.get('/user/addresses/{address_id}', tags=["addresses", "bot"])
async def get_address_information_by_id(
    address_id: str, 
    tg_id: int,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])]
    ):
    """
    Получение информации об адресе пользователя по айди
    """
    with Session(engine, expire_on_commit=False) as session:
        addresses = session.query(Address).\
            join(UsersAddress, UsersAddress.address_id == Address.id).\
            join(Users, UsersAddress.user_id == Users.id). \
            where(Users.telegram_id == tg_id, Address.id == address_id).first()

        return addresses


@router.put('/user/addresses/{address_id}', tags=["addresses", "bot"])
async def update_user_addresses(
    address_id:str, 
    new_address_data: AddressUpdateValidator, 
    tg_id: int,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])]
    ):
    """
    Обновить данные адреса
    """
    
    with Session(engine, expire_on_commit=False) as session:

        if new_address_data.main:
        #Сбросить статус главного у всех адресов
            update_query = session.query(Address).\
                join(UsersAddress, UsersAddress.address_id == Address.id).\
                join(Users, UsersAddress.user_id == Users.id). \
                where(Users.telegram_id == tg_id).all()

            #TODO: Update в query
            for address in update_query: 
                address.main = False

        address_query = session.query(Address).filter_by(id=address_id).first()

        #Обновляем данные адреса на новые  
        for attr, value in new_address_data.model_dump().items():
            #TODO: Обновление данных в None 
            if not (value == None):
                setattr(address_query, attr, value)

        session.commit()

        return address_query


@router.delete('/user/addresses/{address_id}', tags=["addresses", "bot"])
async def delete_user_address(
    adress_id: str, 
    tg_id: int,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])]
    ):
    with Session(engine, expire_on_commit=False) as session:

        select_query = session.query(Address).\
                    join(UsersAddress, UsersAddress.address_id == Address.id).\
                    join(Users, UsersAddress.user_id == Users.id). \
                    where(Users.telegram_id == tg_id, Address.id == adress_id).first()

        if not select_query:
            return JSONResponse({
                "message": "No address found"
            }, status_code=404)


        delete_query = session.query(UsersAddress).filter_by(address_id = adress_id).delete()
        delete_query = session.query(Address).filter_by(id = adress_id).delete()

        session.commit()

    return