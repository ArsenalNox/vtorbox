"""
Руты для бота
"""

import requests
import os, uuid


from typing import Annotated, List, Tuple, Dict
from fastapi import APIRouter, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import JSON

from app.models import (
    Users, Session, engine, UsersAddress, 
    Address, IntervalStatuses, Roles, Permissions, Regions, WEEK_DAYS_WORK_STR_LIST
    )

from app import CODER_KEY, CODER_SETTINGS

from app.auth import (
    oauth2_scheme, 
    get_current_user
)

from app.validators import (
    LinkClientWithPromocodeFromTG as UserLinkData,
    Address as AddressValidator,
    AddressUpdate as AddressUpdateValidator,
    UserLogin as UserLoginSchema,
    AddressSchedule, CreateUserData, UpdateUserDataFromTG, AddressOut,
    RegionOut, AddressDaysWork, UserOut
)


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
            firstname = body.firstname,
            secondname = body.secondname,
            link_code = str(uuid.uuid4())[:10] 
            )
        
        session.add(new_user)
        session.commit()
        
        user_role = Permissions(
            user_id = new_user.id,
            role_id = Roles.customer_role()
        )

        session.add(user_role)
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
    with Session(engine, expire_on_commit=False) as session:
        user_query = session.query(Users).filter_by(link_code=user_link_data.promocode).first()
        if not user_query:
            return JSONResponse({
                "message": f"No user with link code {user_link_data.promocode} found"
            }, status_code=404)
        
        user_query = session.query(Users).filter_by(telegram_id=user_link_data.tg_id).first()
        if user_query:
            return JSONResponse({
                "message": f"пользователь с таким айди телеграм ({user_link_data.tg_id}) уже существует"
            })

        user_query.telegram_id = user_link_data.tg_id
        user_query.telegram_username = user_link_data.username
        user_query.first_name = user_link_data.first_name
        user_query.second_name = user_link_data.second_name
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
    )->UserOut:
    """
    Поиск пользователя по промокоду (search-user-by-promocode)
    """
    with Session(engine, expire_on_commit=False) as session:
        user_query = session.query(Users).filter_by(link_code=promocode).first()


        if user_query:
            scopes_query = session.query(Permissions, Roles.role_name).filter_by(user_id=user_query.id).join(Roles).all()
            scopes = [role.role_name for role in scopes_query]
            return_data = UserOut(**user_query.__dict__)
            return_data.roles = scopes
            return return_data
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
                                "first_name": 'null',
                                "second_name": 'null',
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
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    days_list_len: int = 10,
    tg_id: int = None,
    user_id: UUID = None,
    ) -> List[AddressOut]:
    """
    Получение всех адресов пользователя
    - **tg_id**: тг айди пользователя
    - **days_list_len**: 
    """

    with Session(engine, expire_on_commit=False) as session:
        
        user = None
        if not(tg_id == None):
            user = Users.get_or_404(t_id=tg_id)
        elif not(user_id == None): 
            user = Users.get_or_404(internal_id=user_id)
        
        if not user:
            return JSONResponse({
                "message": "User not found"
                }, status_code=404)

        addresses = session.query(Address).\
            join(UsersAddress, UsersAddress.address_id == Address.id).\
            join(Users, UsersAddress.user_id == Users.id).\
            where(Users.id == user.id).\
            where(Address.deleted_at == None).all()

        return_data = []

        for address in addresses:
            address.interval = str(address.interval).split(', ')

            dates_list_passed = address.get_avaliable_days(days_list_len)
            setattr(address, 'work_dates', dates_list_passed)

            return_data.append(address)

        return return_data


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
            where(Users.telegram_id == tg_id, Address.main == True).\
            where(Address.deleted_at == None).first()

        if not address:
            return JSONResponse({
                "message": "Not found"
            }, status_code=404)        

        address.interval = str(address.interval).split(', ')

        return_data = AddressOut(**address.__dict__)
        address.region.work_days = str(address.region.work_days).split(' ')
        return_data.region = RegionOut(**address.region.__dict__)

        return return_data


@router.post('/user/addresses', tags=["addresses", "bot"])
async def add_user_address(
        address_data: AddressValidator, 
        bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
        tg_id: int = None,
        user_id: UUID = None
    ) -> AddressOut:
    """
    Создание адреса пользователя
    """

    user = Users.get_or_404(t_id=tg_id, internal_id=user_id)
    if not user:
        return JSONResponse({
            "message": "User not found"
        }, status_code=404)

    with Session(engine, expire_on_commit=False) as session:

        #Получаем текст адреса по координатам если они есть 
        if address_data.longitude and address_data.latitude:

            #Проверяем есть ли такой адресс с коордами
            #TODO: Проверка адреса не по всем адреса а только у пользователя
            address = session.query(Address).filter_by(
                latitude=str(address_data.latitude),
                longitude=str(address_data.longitude)
            ).\
            where(Address.deleted_at == None).\
            join(UsersAddress, UsersAddress.address_id == Address.id).\
            where(UsersAddress.user_id == user.id).\
            first()
        
            if address:
                return JSONResponse({
                    "message": "Address already exists"
                }, 403)

            if not address_data.address:
                #Если не предоставили текстовый адрес получаем через геокодер
                url = f"https://geocode-maps.yandex.ru/1.x/?apikey={CODER_KEY}&geocode={address_data.longitude},{address_data.latitude}{CODER_SETTINGS}"
                
                data = requests.request("GET", url).json()
                data = dict(data)

                try:
                    address_data.address = data.get('response', {}). \
                        get('GeoObjectCollection', {}). \
                        get('featureMember')[0]. \
                        get('GeoObject', {}). \
                        get('metaDataProperty', {}). \
                        get('GeocoderMetaData', {}). \
                        get('text')
                except:
                    return JSONResponse({
                        "message": "Out of bounds coodrinates provided"
                    }, status_code=422)

        elif address_data.address:
            #Если предоставили только текстовый адрес получаем коорды
            address = session.query(Address).filter_by(
                address = address_data.address
            ).where(Address.deleted_at == None).first()
        
            if address:
                return JSONResponse({
                    "message": "Address already exists"
                }, 403)
            
            url = f"https://geocode-maps.yandex.ru/1.x/?apikey={CODER_KEY}&geocode={address_data.address}{CODER_SETTINGS}"
            
            data = requests.request("GET", url).json()
            data = dict(data)

            try:
                address_data.longitude, address_data.latitude = str(data.get('response', {}). \
                    get('GeoObjectCollection', {}). \
                    get('featureMember')[0]. \
                    get('GeoObject', {}).\
                    get('Point').get('pos')).split()

            except Exception as err: 
                return JSONResponse({
                    "message": "No such address in allowed area"
                }, 422)

        else:
            #Если не предоставили ни коордов ни адреса
            return JSONResponse({
                "message": "Either field address or longtitude with lattitude are required"
                },status_code=422)


        if address_data.main:
        #Сбросить статус главного у всех адресов
            update_query = session.query(Address).\
                join(UsersAddress, UsersAddress.address_id == Address.id).\
                join(Users, UsersAddress.user_id == Users.id). \
                where(Users.telegram_id == tg_id).where(Address.deleted_at == None).all()

            for address in update_query: 
                address.main = False

        #создаем новый адрес

        interval = None
        if address_data.selected_day_of_week:
            interval = ', '.join(address_data.selected_day_of_week)
            if address_data.interval_type == None:
                address_data.interval_type = INTERVAL_TYPE_WEEK_DAY
            
        if address_data.selected_day_of_month:
            interval = ', '.join(address_data.selected_day_of_month)

            if address_data.interval_type == None:
                address_data.interval_type = INTREVAL_TYPE_MONTH_DAY
        
        #почистить данные в переданной схеме
        address_data_dump = address_data.model_dump()
        del address_data_dump["selected_day_of_month"]
        del address_data_dump["selected_day_of_week"]
        del address_data_dump["region"]

        print(address_data)
        region = Regions.get_by_coords(
            float(address_data.longitude),
            float(address_data.latitude)
        )

        #попытаться найти регион по названию, если не нашёлся по координатам
        if not region == None:
            address_data_dump['region_id'] = region.id
        else:
            region = Regions.get_by_name(address_data.region)
            if not region:
                print("region still not found")

            return JSONResponse({
                "message": "Данный адрес находится во вне рабочих регионах"
            }, status_code=422)

        address_data_dump['interval'] = interval
        address = Address(**address_data_dump)
        address.inteval = interval
        
        session.add(address)
        session.commit()

        user_address = UsersAddress(
            user_id=user.id,
            address_id=address.id,
        )
        session.add(user_address)
        session.commit()
        
        dates_list_passed = address.get_avaliable_days(5)
        setattr(address, 'work_dates', dates_list_passed)

        # return_data = AddressOut(**address.__dict__)
        # return_data.region = RegionOut(**region.__dict__)
        # return_data.region.work_days = str(return_data.region.work_days).split(' ')

        return address


@router.put('/user/addresses/{address_id}/schedule')
async def set_address_schedule(
        address_id: uuid.UUID,
        tg_id: int,
        bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
        address_schedule: AddressSchedule
    )->AddressOut:
    """
    Указать расписание адреса
    """

    with Session(engine, expire_on_commit=False) as session:

        address_query = session.query(Address).\
            filter_by(id=address_id).\
            join(UsersAddress, UsersAddress.address_id == Address.id).\
            join(Users, UsersAddress.user_id == Users.id).\
            join(Regions, Address.region_id == Regions.id).\
            where(Address.deleted_at == None).\
            where(Users.telegram_id == tg_id).\
            first()

        if not address_query:
            return JSONResponse({
                "message": "Not found"
            },status_code=404)

        #Обновляем расписание адреса на новое  
        interval = None

        allowed_days = str(address_query.region.work_days).split(' ')

        if address_schedule.selected_day_of_week:
            for day in address_schedule.selected_day_of_week:
                if day not in allowed_days:
                    return JSONResponse({
                        "message": "cannot set given date in interval. Date not allowed",
                        "date": day,
                        "allowed_days": allowed_days
                    })
                # days_given_date_formatted.append(day)

            interval = ', '.join(address_schedule.selected_day_of_week)
            address_schedule.interval_type = IntervalStatuses.WEEK_DAY

        if address_schedule.selected_day_of_month:
            for day in address_schedule.selected_day_of_month:
                #TODO: Проверку для дат
                # weekday = str(date.strftime('%A')).lower()
                print(day)

            interval = ', '.join(address_schedule.selected_day_of_month)
            address_schedule.interval_type = IntervalStatuses.MONTH_DAY

        address_query.interval = interval
        address_query.interval_type = address_schedule.interval_type

        session.add(address_query)
        session.flush()
        session.commit()
        
        address_query.interval = str(interval).split(', ')

        return address_query


@router.get('/user/addresses/{address_id}', tags=["addresses", "bot"])
async def get_address_information_by_id(
        address_id: uuid.UUID, 
        tg_id: int,
        bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
        days_list_len: int = 5,
    ) -> AddressOut:
    """
    Получение информации об адресе пользователя по айди
    """
    with Session(engine, expire_on_commit=False) as session:
        addresses = session.query(Address).\
            join(UsersAddress, UsersAddress.address_id == Address.id).\
            join(Users, UsersAddress.user_id == Users.id). \
            where(Users.telegram_id == tg_id, Address.id == address_id).\
            where(Address.deleted_at == None).first()

        if addresses:
            addresses.interval = str(addresses.interval).split(', ')
            #return_data = AddressOut(**addresses.__dict__)
            #return_data.region = RegionOut(**addresses.region.__dict__)

            dates_list_passed = addresses.get_avaliable_days(days_list_len)
            setattr(addresses, 'work_dates', dates_list_passed)

            return addresses

        else:
            return JSONResponse({
                "message": "Not found"
            }, status_code=404)


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
                where(Users.telegram_id == tg_id).\
                where(Address.deleted_at == None).all()

            for address in update_query: 
                address.main = False

        address_query = session.query(Address).filter_by(id=address_id).\
            where(Address.deleted_at == None).first()

        if not address_query:
            return JSONResponse({
                "message": "Not found"
            },status_code=404)

        #Обновляем данные адреса на новые  
        for attr, value in new_address_data.model_dump().items():
            #TODO: Обновление данных в None 
            if not (value == None):
                setattr(address_query, attr, value)

        session.commit()

        return address_query


@router.delete('/user/addresses/{address_id}', tags=["addresses", "bot"])
async def delete_user_address(
    address_id: str, 
    tg_id: int,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])]
    ):
    with Session(engine, expire_on_commit=False) as session:

        select_query = session.query(Address).\
                    join(UsersAddress, UsersAddress.address_id == Address.id).\
                    join(Users, UsersAddress.user_id == Users.id).\
                    where(Users.telegram_id == tg_id, Address.id == address_id).\
                    where(Address.deleted_at == None).first()

        if not select_query:
            return JSONResponse({
                "message": "No address found"
            }, status_code=404)

        delete_user_address_query = session.query(UsersAddress).filter_by(address_id = address_id).\
            update({"deleted_at": datetime.now()})

        delete_address_query = session.query(Address).filter_by(id = address_id).\
            update({"deleted_at": datetime.now()})

        session.commit()

    return
