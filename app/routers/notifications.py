"""
Эндпоинт по уведомлениям
"""

import requests
import os, uuid
import re 
import math
import json

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
    RegionOut, AddressDaysWork, UserOut, RouteOut, NotificationsAsRead
)

from app import Tags, logger

from fastapi import APIRouter, Body, Security, Query, WebSocketException, status
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
    only_unread: bool = True
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
    only_unread: bool = False,
    nt_type_name: str = None,
    nt_resource_name: str = None,
    date_filter_start: str = None,
    date_filter_end: str = None
#Фильтр по типу, по типу ресурса, по дате
)->NotificationCountOut:
    """
    Получить уведомления 
    - **user_id**: [int|UUID] - Если None то получаются уведомления текущего авторизованного пользователя
    - **get_all**: [bool] - Получить все существующие уведомления, доступно только админам (не реализовано)
    - **only_unread**: [bool] - Получить только не прочитанные уведомления
    """
    with Session(engine, expire_on_commit=False) as session:
        notification_query = session.query(Notifications).options(joinedload(Notifications.read_by_users)).\
            order_by(desc(Notifications.date_created))
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
                or_(
                    Notifications.for_user == current_user.id, 
                    Notifications.for_user == None,
                    Notifications.for_user_group.in_(current_user.roles))
                )

        if user_id is None:
            user_id = current_user.id

        if only_unread:
            user_query = session.query(association_table.c.left_id).filter_by(right_id=user_id).subquery()
            notification_query = notification_query.filter(Notifications.id.notin_(user_query))

        if nt_type_name:
            notification_query = notification_query.join(NotificationTypes).filter(NotificationTypes.type_name==nt_type_name)

        if nt_resource_name:
            notification_query = notification_query.filter(Notifications.resource_type==nt_resource_name)

        if date_filter_start:
            try:
                date_start = datetime.strptime(date_filter_start, "%Y-%m-%d")
                date_end = datetime.strptime(date_filter_end, "%Y-%m-%d")
            except Exception as err:
                return JSONResponse({
                    "detail": f"{err}"
                }, 422)

            date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
            logger.debug(f"start: {date_start} end: {date_end}")
            notification_query = notification_query.filter(Notifications.date_created >= date_start)
            notification_query = notification_query.filter(Notifications.date_created < date_end)


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


@router.patch('/mark-as-unread')
async def mark_notifications_as_unread(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    notification_ids: NotificationsAsRead,
    user_id: Optional[UUID] = None
):
    """
    Отметить уведомления не прочитанными
    """
    if len(notification_ids.ids)<1:
        return JSONResponse({
            "detail": "Требуется указать как минимум одно уведомление"
        })

    if user_id is None:
        user_id = current_user.id

    with Session(engine, expire_on_commit=False) as session:
        try:
            for notification_id in notification_ids.ids:
                print(notification_id)
                await Notifications.mark_notification_as_unread(
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

        nt_data = await Notifications.get_notifications(
            session=session,
            user_id=user_id,
            only_unread=True
        )

        nt_list = []
        for nt_ in nt_data:
            nt_list.append(jsonable_encoder(nt_.model_dump()))
        await Notifications.send_notification(
                user_id, 
                json.dumps(nt_list), 
                session=session,
                send_to_tg=False
        )

    return


@router.patch('/mark-as-read')
async def mark_notifications_as_read(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    notification_ids: NotificationsAsRead,
    user_id: Optional[UUID] = None
):
    """
    Отметить уведомления прочитанными
    """
    if len(notification_ids.ids)<1:
        return JSONResponse({
            "detail": "Требуется указать как минимум одно уведомление"
        })

    if user_id is None:
        user_id = current_user.id

    with Session(engine, expire_on_commit=False) as session:
        try:
            for notification_id in notification_ids.ids:
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

        nt_data = await Notifications.get_notifications(
            session=session,
            user_id=user_id,
            only_unread=True
        )

        nt_list = []
        for nt_ in nt_data:
            nt_list.append(jsonable_encoder(nt_.model_dump()))

        await Notifications.send_notification(
                user_id, 
                json.dumps(nt_list), 
                session=session,
                send_to_tg=False
        )

    return


@router.post('/')
async def create_new_notification(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    notification_data: Notification,
)->NotificationOut:
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
    print("New connection")
    user = await get_current_user_ws(token=token)
    if not user:
        print(user)
        print("User with token not found")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    await manager.connect(user_id = user.id, websocket=websocket, user_roles=user.roles)

    with Session(engine, expire_on_commit=False) as session:
        nt_data = await Notifications.get_notifications(
            session=session,
            user_id=user.id,
            only_unread=True
        )

        nt_list = []
        for nt_ in nt_data:
            nt_list.append(jsonable_encoder(nt_.model_dump()))

        await Notifications.send_notification(
                user.id, 
                json.dumps(nt_list), 
                session=session,
                send_to_tg=False
        )

    # print(manager.active_connections)
    try:
        while True:
            pass
            data = await websocket.receive_text()
            # await manager.send_personal_message(f"You wrote: {data}", user.id)
            # await manager.broadcast(f"Client #{user.id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id = user.id)