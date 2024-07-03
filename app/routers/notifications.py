"""
Эндпоинт по уведомлениям
"""

import requests
import os, uuid
import re 
import math

from typing import Annotated, List, Tuple, Dict, Optional, Union
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

import datetime as dt
from datetime import datetime, timedelta


from app import CODER_KEY, CODER_SETTINGS

from app.auth import (
    oauth2_scheme, 
    get_current_user_ws
)

from app.validators import (
    LinkClientWithPromocodeFromTG as UserLinkData,
    Address as AddressValidator,
    AddressUpdate as AddressUpdateValidator,
    UserLogin as UserLoginSchema,
    AddressSchedule, CreateUserData, UpdateUserDataFromTG, AddressOut,
    RegionOut, AddressDaysWork, UserOut, RouteOut
)

from app import Tags

from fastapi import APIRouter, Body, Security, Query
from fastapi.responses import JSONResponse

from calendar import monthrange
from uuid import UUID

from sqlalchemy import desc, asc, desc, or_, and_

from sqlalchemy.orm import joinedload

from app.validators import (
    UserLogin as UserLoginSchema,
    NotificationOut, Notification, NotificationTypes,
    NotificationCountOut
)

from app.auth import (
    get_current_user
)

from app.models import (
    Users, Session, engine, UsersAddress, 
    Address, IntervalStatuses, Roles, Permissions, 
    Regions, WEEK_DAYS_WORK_STR_LIST, Notifications, NotificationTypes,
    ROLE_ADMIN_NAME, manager, association_table
)


router = APIRouter()


@router.get('/count')
async def get_my_notification_count(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],
    user_id: int|UUID = None,
    only_unread: bool = False
):
    """
    Получить кол-во новых/непрочитанных сообщений
    """
    with Session(engine, expire_on_commit=False) as session:
        notification_query = session.query(Notifications).options(joinedload(Notifications.read_by_users))
        print(current_user.id)

        if user_id:
            if not(ROLE_ADMIN_NAME in current_user.roles):
                return JSONResponse({
                    "detail": "Недостаточно прав для просмотра сообщений пользователя"
                }, status_code=403)

            user = Users.get_user(user_id)
            if not user:
                return JSONResponse({
                    "detail": "Пользователь не найден"
                }, status_code=404)
            
            notification_query = notification_query.filter(Notifications.for_user == user.id)
        else:
            notification_query = notification_query.filter(
                or_(Notifications.for_user == current_user.id, Notifications.for_user == None),
                Notifications.for_user_group.in_(current_user.roles)
                )

        if user_id is None:
            user_id = current_user.id

        if only_unread:
            user_query = session.query(association_table.c.left_id).filter_by(right_id=user_id).subquery()
            notification_query = notification_query.filter(Notifications.id.notin_(user_query))

        notification_query = notification_query.count()

        return notification_query


@router.get("/")
async def get_my_notifications(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],
    user_id: int|UUID = None,
    page: int = 0,
    limit: int = 20,
    get_all: bool = False,
    only_unread: bool = False
)->NotificationCountOut:
    """
    Получить уведомления 

    - **user_id**: [int|UUID] - Если None то получаются уведомления текущего авторизованного пользователя
    - **get_all**: [bool] - Получить все существующие уведомления, доступно только админам (не реализовано)
    - **only_unread**: [bool] - Получить только не прочитанные уведомления
    """
    with Session(engine, expire_on_commit=False) as session:
        notification_query = session.query(Notifications).options(joinedload(Notifications.read_by_users))
        print(current_user.id)

        if get_all:
            if not(ROLE_ADMIN_NAME in current_user.roles):
                return JSONResponse({
                    "detail": "Недостаточно прав для просмотра сообщений пользователя"
                }, status_code=403)

        elif user_id:
            if not(ROLE_ADMIN_NAME in current_user.roles):
                return JSONResponse({
                    "detail": "Недостаточно прав для просмотра сообщений пользователя"
                }, status_code=403)

            user = Users.get_user(user_id)
            if not user:
                return JSONResponse({
                    "detail": "Пользователь не найден"
                }, status_code=404)
            
            notification_query = notification_query.filter(Notifications.for_user == user.id)
        else:
            notification_query = notification_query.filter(
                or_(Notifications.for_user == current_user.id, Notifications.for_user == None),
                Notifications.for_user_group.in_(current_user.roles)
                )

        if user_id is None:
            user_id = current_user.id

        if only_unread:
            user_query = session.query(association_table.c.left_id).filter_by(right_id=user_id).subquery()
            notification_query = notification_query.filter(Notifications.id.notin_(user_query))

        nt_q_count_global = notification_query.count()

        if limit == 0:
            notification_query = notification_query.all()
        else:
            notification_query = notification_query.offset(page  * limit).limit(limit).all()


        return_data = []

        for nt in notification_query:
            nt_out = NotificationOut(**jsonable_encoder(nt))
            for user in nt.read_by_users:
                if user.id == user_id:
                    nt_out.read_by_user = True
                    break
            return_data.append(nt_out)

        return {
            "count": len(return_data),
            "global_count": nt_q_count_global,
            "data": return_data
        }

@router.get('/types')
async def get_notification_types(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
):
    with Session(engine, expire_on_commit=False) as session:
        types_query = session.query(NotificationTypes).all()

        return jsonable_encoder(types_query)


@router.patch('/mark-as-read')
async def mark_notifications_as_read(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    notification_ids: List[UUID] = Query(None),
    user_id: Optional[UUID] = None
):
    """
    Отметить уведомления прочитанными
    """
    if len(notification_ids)<1:
        return JSONResponse({
            "detail": "Требуется указать как минимум одно уведомление"
        })

    if user_id is None:
        user_id = current_user.id

    with Session(engine, expire_on_commit=False) as session:
        try:
            for notification_id in notification_ids:
                print(notification_id)
                await Notifications.mark_notification_as_read(
                        notification_id=notification_id, 
                        user_id=user_id, 
                        session=session
                    )

            session.commit()

        except Exception as err:
            print(err)
            return JSONResponse({
                "detail": 'an error occured'
            }, 503)

    return


@router.post('/')
async def create_new_notification(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    notification_data: Notification,
):
    with Session(engine, expire_on_commit=False) as session:
        new_notification = await Notifications.create_notification(
            notification_data = notification_data.model_dump(),
            session=session
            )

        return jsonable_encoder(new_notification)


from fastapi import FastAPI, WebSocket, WebSocketDisconnect

@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket, 
        token: Annotated[Union[str, None], Query()] = None,
    ):

    user = await get_current_user_ws(token=token)
    print(user.id)
    

    await manager.connect(user_id = user.id, websocket=websocket, user_roles=user.roles)
    print(manager.active_connections)
    try:
        while True:
            pass
            data = await websocket.receive_text()
            # await manager.send_personal_message(f"You wrote: {data}", user.id)
            # await manager.broadcast(f"Client #{user.id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id = user.id)