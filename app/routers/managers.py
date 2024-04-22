"""
Эндпоинты для менеждеров
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes

from app.models import (
    engine, 
    Session, 
    OrderStatuses,
)

from app.validators import (
    UserLogin as UserLoginSchema,
    StatusOut, ManagerOut
)

from app.auth import (
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

from app import Tags

import re 

from typing import Annotated, List, Union, Optional

from fastapi import APIRouter, Body, Security, Query
from fastapi.responses import JSONResponse

from calendar import monthrange
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, asc, desc

from app.validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut, OrderUpdate, CourierCreationValidator,
    UserOut, CourierOut
)

from app.auth import (
    get_current_user
)

from app.models import (
    engine, Orders, Users, Session, 
    Address, UsersAddress, BoxTypes,
    OrderStatuses, OrderStatusHistory, Regions,
    ORDER_STATUS_DELETED, ORDER_STATUS_AWAITING_CONFIRMATION, 
    ORDER_STATUS_CONFIRMED, IntervalStatuses, 
    ROLE_ADMIN_NAME, ORDER_STATUS_COURIER_PROGRESS, 
    ROLE_COURIER_NAME, Permissions, Roles,
    Routes, ROLE_MANAGER_NAME
)



load_dotenv()
router = APIRouter()


@router.post('/managers/add/{user_id}')
async def add_manager_role_to_user():
    """
    Добавить роль менеджера пользователю
    """
    pass


@router.get('/managers', tags=[Tags.couriers, Tags.admins])
async def get_list_of_managers(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin", "manager"])],
    show_deleted: bool = False
)->List[ManagerOut]:
    """
    Получить список менеджеров
    """
    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Users)

        roles_user_query = session.query(Users.id).\
            join(Permissions, Permissions.user_id == Users.id).\
            join(Roles, Roles.id == Permissions.role_id).\
            where(Roles.role_name == ROLE_MANAGER_NAME).subquery()

        query = query.filter(Users.id.in_(roles_user_query))

        if not show_deleted:
            query = query.filter(Users.deleted_at == None)

        query = query.all()

        return_data = []
        for user in query:
            
            user_data = ManagerOut(**user.__dict__)
            scopes_query = session.query(Permissions, Roles.role_name).filter_by(user_id=user.id).join(Roles).all()
            user_data.roles = [role.role_name for role in scopes_query]
            return_data.append(user_data)

            order_query = session.query(Orders).filter_by(manager_id = user.id).all()
            user_data.assigned_orders = order_query

        return return_data


@router.get("/managers/orders")
async def get_manager_assigned_orders(

):
    pass