"""
Руты для пользователей


CRUD с пользователями
Управление подпиской
"""

from typing import Annotated
from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    Security, 
    File, 
    UploadFile)

from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes

from datetime import datetime

from sqlalchemy import desc, asc, not_, or_
from app import Tags

from ..models import (
    Users, Orders, Session, engine, Roles, Permissions, 
    Address, UsersAddress, BoxTypes, OrderStatusHistory,
    OrderStatuses, ROLE_CUSTOMER_NAME, ROLE_TELEGRAM_BOT_NAME
    )

from ..auth import (
    oauth2_scheme, 
    pwd_context, 
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_active_user,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
)

from ..validators import (
    UserSignUp as UserSignUpSchema,
    UserLogin as UserLoginSchema,
    UserCreationValidator as UserCreationData,
    UserUpdateValidator as UserUpdateData,
    UserOut, OrderOut
)

from app.utils import is_valid_uuid, get_lang_long_from_text_addres

from passlib.context import CryptContext
from datetime import timedelta

from jose import jwt

from dotenv import load_dotenv

import os, uuid, re, json

import openpyxl as xl 

load_dotenv()
router = APIRouter()

#TODO: Отправка сообщения пользователю через бота 

@router.get('/users', tags=["admins", "managers"], responses={
    200: {
        "description": "Получение всех пользователей",
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
    }
})
async def get_all_users(
        current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["manager"])],
        role_name: str = None,
        only_bot_users: bool = False,
        non_deleted: bool = True,
        #Применимо для клиентов
        with_orders: bool = False,
        with_active_orders: bool = False,
        with_inactive_orders: bool = False, #все кроме активных

        #Применимо для всех
        limit: int = 5,
        page: int = 0,
        show_deleted: bool = True
    ):
    """
    Получение пользователей по фильтру
    """

    with Session(engine, expire_on_commit=False) as session:
        
        query = session.query(Users)

        roles_query = session.query(Roles).all()
        roles_list = [role.role_name for role in roles_query]

        if not show_deleted:
            query = query.filter(Users.deleted_at == None)

        if only_bot_users:
            query = query.filter(or_(Users.link_code == None, not_(Users.telegram_username == None)))

        if (role_name != None) and (role_name in roles_list):
            roles_user_query = session.query(Users.id).\
                join(Permissions, Permissions.user_id == Users.id).\
                join(Roles, Roles.id == Permissions.role_id).\
                where(Roles.role_name == role_name).subquery()

            query = query.filter(Users.id.in_(roles_user_query))

        global_user_count = query.count()
        users = query.order_by(asc(Users.date_created)).offset(page  * limit).limit(limit).all()
        # users = session.query(Users, Roles, Permissions).filter_by(*filters).offset(page  * limit).limit(limit).all()

        total = len(users)
        data = []
        for user in users:

            user_data = UserOut(**user.__dict__)


            scopes_query = session.query(Permissions, Roles.role_name).filter_by(user_id=user.id).join(Roles).all()

            user_data.roles = [role.role_name for role in scopes_query]

            #TODO: Фильтр по статусу заявки
            if with_orders:
                orders = session.query(Orders, Address, BoxTypes, OrderStatuses).\
                    join(Address, Address.id == Orders.address_id).\
                    join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
                    join(OrderStatuses, OrderStatuses.id == Orders.status).\
                    where(Orders.from_user == user.id).order_by(asc(Orders.date_created)).all()
                
                user_data.orders = []
                for order in orders:

                    order_data = OrderOut(**order[0].__dict__)

                    try:
                        order_data.address_data = order[1]
                    except IndexError: 
                        order_data.address_data = None

                    try:
                        order_data.box_data = order[2]
                    except IndexError:
                        order_data.box_data = None

                    try:
                        order_data.status_data = order[3]
                    except IndexError:
                        order_data.status_data = None

                    user_data.orders.append(order_data)

            data.append(user_data)


        return {
            "count": total,
            "global_count": global_user_count,
            "data": data
        }

    return []



@router.post('/users', tags=["admins"])
async def create_user(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["manager"])],
    new_user_data: UserCreationData,
    send_email: bool = True
):
    """
    Ручное создание нового пользователя
    """

    with Session(engine, expire_on_commit=False) as session:
        query_user = session.query(Users).filter_by(email=new_user_data.email).first()
        if query_user: 
            return JSONResponse({
                "message": "Email already taken",
            }, status_code=400)

        new_user_data.password = get_password_hash(new_user_data.password)
        
        new_user_data = new_user_data.model_dump()
        user_role = new_user_data["role"]
        del new_user_data["role"]

        if new_user_data.send_email_invite:
            pass

        new_user = Users(**new_user_data)

        #Фикс: при flush uuid остаётся в сесси и не перегенерируется, т.е получаем Exception на unique field'е 
        new_user.link_code = str(uuid.uuid4())[:10] 

        session.add(new_user)
        session.flush()
        session.refresh(new_user)

        #Если админ - добавить все роли?

        for role in str(user_role).split(' '):
            role_query = Roles.get_role(role)
            if role_query:

                user_role = Permissions(
                    user_id = new_user.id,
                    role_id = Roles.get_role(role).id
                )

                session.add(user_role)

        session.commit()

        #TODO: Отправка приглашения на почту

        return new_user


@router.delete('/users', tags=["admins"])
async def delete_user(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["manager"])],
    tg_id: int | None = None,
    user_id: uuid.UUID | None = None 
):
    """
    Удаление пользователя (Отправляется в disabled)
    """
    if (not tg_id) and (not user_id):
        return JSONResponse({
            "message": "Required at least one type id in arguments"
        }, status_code=422)

    with Session(engine, expire_on_commit=False) as session:
        user_query = None
        if tg_id:
            user_query = session.query(Users).filter_by(telegram_id = tg_id).where(deleted_at = None).first()
        elif user_id:
            user_query = session.query(Users).filter_by(id = user_id).where(Users.deleted_at == None).first()

        if not user_query:
            return JSONResponse({
                "message": "No such user"
                }, status_code=404)

        user_query.deleted_at = datetime.now()
        session.add(user_query)
        session.commit()

        return


@router.put('/user', tags=["admin"])
async def update_user_data(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["manager"])],
    new_user_data: UserUpdateData
):
    """
    Обновление данных пользователя админом
    """
    with Session(engine, expire_on_commit=False) as session:
        user_query = Users.get_user(new_user_data.user_id)
        
        if not user_query:
            return JSONResponse({
                "message": "No such user"
                }, status_code=404)

        for attr, value in new_user_data.model_dump().items():

            print(attr)

            if attr == 'password' and value:
                #TODO: Изменение пароля
                print('Changing user password')
                continue

            #TODO: Изменение ролей
            if value:
                setattr(user_query, attr, value)

        session.add(user_query)
        session.commit()

    return 


@router.put('/users', tags=[Tags.users])
async def update_user_self_data(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["customer"])],
    new_user_data: UserUpdateData
):
    """
    Обновить свои данные пользователем
    """



@router.get('/users/bot_linked', tags=[Tags.bot, Tags.users])
async def get_bot_users():
    """
    Получение пользователей тг бота, или пользователей сайта связавших профиль с тг
    """
    with Session(engine, expire_on_commit=False) as session:
        bot_users = session.query(Users).where(Users.link_code == None, Users.telegram_id is not None).all()
        return bot_users


@router.post('/users/signup', tags=[Tags.users])
async def signup(signup_data: UserSignUpSchema):
    """
    Регистрация клиента
    """

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Users).filter_by(email=signup_data.username).first()
        if query:
            return JSONResponse({
                "message": "Email already taken"
            }, status_code=409)

        new_user = Users(
            email=signup_data.username,
            password=get_password_hash(signup_data.password)
        )  

        session.add(new_user)
        session.flush()
        session.refresh(new_user)

        new_user.link_code = str(uuid.uuid4())[:10] 
        role_query = Roles.get_role(ROLE_CUSTOMER_NAME)

        if role_query:
            user_role = Permissions(
                user_id = new_user.id,
                role_id = role_query.id
            )

            session.add(user_role)
        else:
            raise HTTPException(status_code=503, detail="Internal server error")

        session.commit()

        return new_user


@router.post('/token', tags=["default"])
async def login(login_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Users).filter_by(email=login_data.username).first()
        if not query: 
            return JSONResponse({
                "message": "Invalid password or email"
            }, status_code=400)

        if not verify_password(login_data.password, query.password):
            return JSONResponse({
                "message": "Invalid password or email"
            }, 400)

        #TODO: Проверка на активность

        scopes_query = session.query(Permissions, Roles.role_name).filter_by(user_id=query.id).join(Roles).all()

        scopes = [role.role_name for role in scopes_query]

        expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        if ROLE_TELEGRAM_BOT_NAME in scopes:
            expires = None

        token = create_access_token(
            data={
                "sub": login_data.username,
                "internal_id": str(query.id),
                "scopes": scopes
            }, 
            expires_delta=expires)

        return JSONResponse({
            "access_token": token,
            "token_type": "bearer"
        })


@router.get("/users/me", tags=["users"], responses={
    200: {
        "description": "Получение информации об авторизованном пользователе (себе)",
        "content": {
            "application/json": {
                "example": {
                    "user_data": {
                        "telegram_username": 'null',
                        "email": "test@mail.ru",
                        "password": "$2b$12$g9.50JMY2pLysGFeq15enuDxUKFz7LlXIgNO4mzgVW7ZgtruT2/YS",
                        "full_name": 'null',
                        "last_action": "2023-12-01T18:30:08.740109",
                        "link_code": "f191e981",
                        "telegram_id": 'null',
                        "id": "dec36dc4-109c-43d5-99b4-b801502606a7",
                        "phone_number": 'null',
                        "date_created": "2023-12-01T18:30:08.740109",
                        "allow_messages_from_bot": 'true'
                    },
                    "token_data": {
                        "sub": "test@mail.ru",
                        "internal_id": "dec36dc4-109c-43d5-99b4-b801502606a7",
                        "scopes": [
                        "users",
                        "me"
                        ],
                        "exp": 1701652303
                    }
                }
            }
        }
    },
    401: {
        "description": "Не удалось авторизировать пользователя",
        "content": {
                "application/json": {
                    "detail": "Not authenticated"
                }
            },
    }
})
async def get_current_user_info(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)]
):
    token_data = jwt.decode(token=current_user.access_token, key=SECRET_KEY, algorithms=ALGORITHM)

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Users).filter_by(email=current_user.username).first()

        return {
            "user_data": query,
            "token_data": token_data
            }


@router.get('/user/{user_id}', tags=[Tags.users, Tags.admins])
async def get_user_data(
    user_id: uuid.UUID,
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
):
    """
    Получить данные пользователя админом
    """
    with Session(engine, expire_on_commit=False) as session:
        user_query = session.query(Users).where(Users.id == user_id).first()
        if not user_query:
            return JSONResponse({
                "message": "Not found"
            }, status_code=404)
        return user_query


@router.get('/user/me', tags=[Tags.bot, Tags.users])
async def get_user_info(
    tg_id: int,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])]
):

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Users).filter_by(email=current_user.username).first()

        scopes_query = session.query(Permissions, Roles.role_name).filter_by(user_id=query.id).join(Roles).all()
        scopes = [role.role_name for role in scopes_query]
        return JSONResponse({
            "user_data": query,
            "scopes": scopes
        })
    pass


@router.get('/users/check', tags=[Tags.admins, Tags.users])
async def check_user_roles(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])]
):
    """
    Проверить базу данных пользователей на пользователей без роли и добавить им роль customer
    """
    with Session(engine, expire_on_commit=False) as session:
        user_qeury = session.query(Users).all()
        for user in user_qeury:
            scopes_query = session.query(Permissions, Roles.role_name).filter_by(user_id=user.id).join(Roles).all()
            scopes = [role.role_name for role in scopes_query]
            if len(scopes) < 1:
                print(f"User {user.id} has no roles")
                print(scopes)
                if ROLE_CUSTOMER_NAME not in scopes:
                    #TODO: Добавить роль
                    user_role = Permissions(
                        user_id = user.id,
                        role_id = Roles.customer_role()
                    )
                    session.add(user_role)

        session.commit()


@router.post('/users/import/file', tags=["admins"])
async def import_clients(file: UploadFile):
    """
    Импорт клиентов и заявки с историей из excel таблицы
    """
    with Session(engine, expire_on_commit=False) as session:
    
        wb_obj = xl.load_workbook(file.file)
        sheet_obj = wb_obj.active

        users = []

        none_count = 0 
        #импорт самих клиентов, адресов, тарифов, подписки, интервалов
        for row in range(1, sheet_obj.max_row+1):
            print(f"row number {row} ")
        # for row in range(1, 10):
            #3840 24
            #print(sheet_obj.max_row, sheet_obj.max_column)
            cell_obj = sheet_obj.cell(row, 1)

            if cell_obj.value == None:
                none_count +=1
            else:
                none_count = 0

            if not re.match(r'[\d](.*)', str(cell_obj.value)):
                if none_count > 30:                
                    break
                continue

            # print(get_lang_long_from_text_addres(sheet_obj.cell(row,7).value))
            try:
                phone_number = int(sheet_obj.cell(row, 11).value)
            except Exception as err:
                continue

            #TODO: useraddress
            new_user = session.query(Users).filter_by(phone_number = str(phone_number)).first()
            if not new_user:
                new_user = Users(
                    phone_number = int(sheet_obj.cell(row, 11).value),
                    firstname = sheet_obj.cell(row, 9).value,
                    link_code = str(uuid.uuid4())[:8]
                )

                session.add(new_user)
                session.flush()
                session.refresh(new_user)
            
            new_address = session.query(Address).filter_by(address = sheet_obj.cell(row,7).value).first()
            if not new_address:
                latitude, longitude = get_lang_long_from_text_addres(sheet_obj.cell(row,7).value)
                if (latitude == None) or (longitude == None):
                    print(f"No data found for address {sheet_obj.cell(row, 7).value}")
                    continue

                new_address = Address(
                    region = sheet_obj.cell(row, 4).value,
                    district = sheet_obj.cell(row, 5).value,
                    distance_from_mkad = sheet_obj.cell(row, 6).value,
                    point_on_map = sheet_obj.cell(row, 8).value,
                    address = sheet_obj.cell(row, 7).value,
                    detail = sheet_obj.cell(row, 10).value,
                    main = True,
                    longitude = longitude,
                    latitude = latitude
                )

                session.add(new_address)
                session.flush()
                session.refresh(new_address)

            user_role = Permissions(
                user_id = new_user.id,
                role_id = Roles.customer_role()
            )

            count = session.query(Orders.id).where(Orders.from_user == new_user.id).count()
            new_order = Orders(
                from_user   = new_user.id,
                address_id  = new_address.id,
                box_type_id = BoxTypes.test_type().id,
                box_count   = 1,
                status      = OrderStatuses.status_default().id,
                date_created = datetime.now(),
                user_order_num = count + 1
            )

            session.add(new_order)
            session.add(user_role)
            session.flush()
            session.refresh(new_order)

            status_update = OrderStatusHistory(
                order_id = new_order.id,
                status_id = OrderStatuses.status_default().id,
                date = datetime.now()
            )

            user_address = UsersAddress(
                user_id=new_user.id,
                address_id=new_address.id,
            )

            session.add(status_update)
            session.add(new_order)

            session.commit()

    return {"filename": file.filename}