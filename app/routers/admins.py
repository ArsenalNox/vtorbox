
#TODO: Пригласить пользователя по e-mail

#TODO: Платежные шлюзы (добавляем возможные варианты приема денег, 
# чтобы давать их на выбор клиентам, админ может вкл/выкл какие-то шлюзы, управлять их настройками)

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Security, Query 
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from fastapi.encoders import jsonable_encoder 

from uuid import UUID

from typing import Annotated, List, Tuple, Dict, Optional
from app.models import (
    engine, 
    Session, 
    OrderStatuses,
    Roles, Permissions, OrderStatusesAllowFromList,
    OrderStatusesAllowToList
)

from app.validators import (
    UserLogin as UserLoginSchema,
    StatusOut
)

from app.auth import (
    oauth2_scheme, 
    pwd_context, 
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_active_user,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM,
    get_current_user_variable_scopes
)

import os, uuid
from dotenv import load_dotenv
from app import Tags

load_dotenv()
router = APIRouter()


@router.get('/statuses', tags=['statuses'])
async def get_all_statueses(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)]
) -> list[StatusOut]:
    """
    Получение списка всех статусов
    """
    with Session(engine, expire_on_commit=False) as session:
        statuses = session.query(OrderStatuses).all()

        return_data = []

        for status in statuses:
            status.allow_to_list
            status.allow_from_list
            return_data.append(status)

        return return_data


@router.get('/statuses/name', tags=['statuses'])
async def get_status_info_by_name(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    status_name: str
) -> StatusOut:
    """
    Получение статуса по его названию
    """
    with Session(engine, expire_on_commit=False) as session:
        status_name = f"%{status_name}%"
        status = session.query(OrderStatuses).filter(OrderStatuses.status_name.like(status_name)).first()
        return status


@router.put('/statuses/{status_id}', tags=[Tags.statuses])
async def change_status(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    status_id: UUID,
    allow_messages: bool,
    status_allow_to: List[UUID] = Query(None),
    status_allow_from: List[UUID] = Query(None),
):
    """
    - **allow_messages**: вкл/выкл отправку сообщения при изменении статуса на указанный
    - **status_allow_to**: - лист айди статусов, к которым статус может перейти
    - **status_allow_from**: - лист айди статусов, от которых статус может перейти
    """
    with Session(engine, expire_on_commit=False) as session:
        status = session.query(OrderStatuses).filter(OrderStatuses.id == status_id).first()
        if not status:
            return JSONResponse({
                "detail": "Статус не найден"
            }, 404)

        status.message_on_update = allow_messages
        session.add(status)

        if status_allow_to:
            delete_query = session.query(OrderStatusesAllowToList).filter_by(status_id = status_id).delete()

            for status_to_id in status_allow_to:
                new_allow_to = OrderStatusesAllowToList(
                    status_id = status_id,
                    second_status_id = status_to_id
                )
                session.add(new_allow_to)

        if status_allow_from:
            delete_query = session.query(OrderStatusesAllowFromList).filter_by(status_id = status_id).delete()

            for status_from_id in status_allow_from:
                new_allow_from = OrderStatusesAllowFromList(
                    status_id = status_id,
                    second_status_id = status_from_id
                )
                session.add(new_allow_from)

        session.commit()
        return status


@router.get('/roles', tags=[Tags.roles])
async def get_avaliable_roles(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])]
):
    """
    Получение списка ролей
    """
    with Session(engine, expire_on_commit=False) as session:
        roles_query = session.query(Roles).all()
        return_data = []
        for role in roles_query:
            match role.role_name:
                case 'admin':
                    role.label = 'админ'

                case 'bot':
                    role.label = 'бот'
                    
                case 'customer':
                    role.label = 'клиент'

                case 'courier':
                    role.label = 'курьер'

                case 'manager':
                    role.label = 'менеджер'

            return_data.append(role)

        return return_data