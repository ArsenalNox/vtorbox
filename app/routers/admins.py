
#TODO: Пригласить пользователя по e-mail

#TODO: Указание дней работы
#TODO: Сегменты адресов (разделение городов по сегментам вывоза, туда входят улицы, районы, метро) - сложна 
#TODO: Цены для сегментов (указываем цену для сегмента и для единицы вывоза (мешок, масса, размер и др)) - в модели? 
#TODO: Курьерские настройки (добавление курьеров, тонкие настройки маршрутизации и др)
#TODO: Платежные шлюзы (добавляем возможные варианты приема денег, 
# чтобы давать их на выбор клиентам, админ может вкл/выкл какие-то шлюзы, управлять их настройками)

#TODO: Настройки ботов 
#TODO: Редактирование текстов бота
#TODO: Пул заявок

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes

from ..models import (
    engine, 
    Session, 
    OrderStatuses,
)

from ..validators import (
    UserLogin as UserLoginSchema,
    StatusOut
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

import os, uuid
from dotenv import load_dotenv


load_dotenv()
router = APIRouter()

@router.get('/statuses', tags=['admins'])
async def get_all_statueses(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)]
):
    """
    Получение списка всех статусов
    """
    with Session(engine, expire_on_commit=False) as session:
        statuses = session.query(OrderStatuses).all()
        statuses_list = [StatusOut(**status.__dict__) for status in statuses]
        return statuses_list


@router.put('/statuses/{status_id}', tags=['admins'])
async def change_status():
    pass

