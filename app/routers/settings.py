"""
Эндпоинты настроект проекта, бота, рабочих дней, вкл/выкл автосбора пула/маршрута
"""

import requests
import os, uuid
import re 
import math

from typing import Annotated, List, Tuple, Dict, Optional
from fastapi.responses import JSONResponse

import datetime as dt
from datetime import datetime, timedelta


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
    RegionOut, AddressDaysWork, UserOut, RouteOut
)

from app import Tags

from fastapi import APIRouter, Body, Security, Query
from fastapi.responses import JSONResponse

from calendar import monthrange
from uuid import UUID

from sqlalchemy import desc, asc, desc

from app.validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut,
    OrderUpdate
)

from ..auth import (
    get_current_user
)

from app.models import (
    Users, Session, engine, UsersAddress, 
    Address, IntervalStatuses, Roles, Permissions, Regions, WEEK_DAYS_WORK_STR_LIST
    )


from app.models import (
    engine, Orders, Users, Session, 
    Address, UsersAddress, BoxTypes,
    OrderStatuses, OrderStatusHistory,
    ORDER_STATUS_DELETED, ORDER_STATUS_AWAITING_CONFIRMATION,
    IntervalStatuses, ROLE_ADMIN_NAME, ROLE_COURIER_NAME,
    Routes, RoutesOrders, WeekDaysWork, DaysWork
    )



router = APIRouter()


@router.get('/bot/settings', tags=[Tags.settings])
async def get_bot_settings(
    setting_name: Optional[str] = None
):
    """
    Получить настройки бота
    """
    pass


@router.get('/bot/messages', tags=[Tags.settings])
async def get_bot_messages(
    message_key: Optional[str] = None,
):
    """
    Получить сообщения бота
    """
    pass


@router.get("/work_days", tags=[Tags.settings])
async def get_work_days():
    """
    Получить настройки рабочих дней
    """
    with Session(engine, expire_on_commit=False) as session:
        weekdays_query = session.query(WeekDaysWork).all()
        weekdays_query = [weekday for weekday in weekdays_query]

        dates_query = session.query(DaysWork).all()
        dates_query = [day for day in dates_query]

        print(dates_query, weekdays_query)
        return {
            "date_days": dates_query,
            "weekdays": weekdays_query
        }


@router.patch('/work_days', tags=[Tags.settings])
async def edit_work_days(
    dates_add: List[datetime] = None,
    weekdays_add: List[str] = None,
    dates_remove: List[datetime] = None,
    weekdays_remove: List[str] = None
):
    """
    все datetime поля используют формат YYYY-MM-DDT00:00
    - **dates_add**: список дат для добавления в нерабочие даты
    - **weekdays_add**: список дней недели для добавление в нерабочие дни
    - **dates_remove**: список дат для удаления их нерабочих дат
    - **weekdays_remove**: список дней недели для удаления из нерабочих дней
    """
    warnings = []
    with Session(engine, expire_on_commit=False) as session:
        for date in dates_add:
            date = date.replace(hour=00, minute=0, second=0, microsecond=0)
            date_tommorrow = date + timedelta(days=1)
            date_search_query = session.query(DaysWork)
            date_search_query = date_search_query.filter(DaysWork.date >= date, DaysWork.date <= date_tommorrow)
            date_search_query = date_search_query.first()

            if date_search_query:
                warnings.append(f'date {date.strftime("%Y-%m-%d")} already exists')
                continue
            
            new_date = DaysWork(
                date = date
            )
            session.add(new_date)

        
        for weekday in weekdays_add:
            if str(weekday).lower() not in WEEK_DAYS_WORK_STR_LIST:
                return JSONResponse({
                    "message": f"weekday {weekday} is invaild"
                }, status_code=422)

            weekdays_search_query = session.query(WeekDaysWork).filter(WeekDaysWork.weekday == weekday).first()
            if weekdays_search_query:
                warnings.append(f'weekday {weekday} aleady set')
                continue
            
            new_weekday = WeekDaysWork(
                weekday = weekday
            )
            session.add(new_weekday)

        session.commit()

        return JSONResponse({
            "warnings": warnings
        }, 201)