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
    RegionOut, AddressDaysWork, UserOut, RouteOut, BotSetting, BotSettingOut,
    BotSettingUpdate
)

from app.validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut, OrderUpdate
)

from app import Tags

from fastapi import APIRouter, Body, Security, Query
from fastapi.responses import JSONResponse

from calendar import monthrange
from uuid import UUID

from sqlalchemy import desc, asc, desc



from app.auth import (
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
    Routes, RoutesOrders, WeekDaysWork, DaysWork,
    BotSettings, BotSettingsTypes, SettingsTypes
    )



router = APIRouter()


@router.get('/settings/types', tags=[Tags.settings])
async def get_settings_types(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
):
    with Session(engine, expire_on_commit=False) as session:
        query = session.query(SettingsTypes).all()
        return query


@router.get('/bot/settings', tags=[Tags.settings])
async def get_settings(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    setting_name: Optional[str] = None,
    setting_key: Optional[str] = None,
    setting_id: Optional[UUID] = None,
    setting_type: Optional[str] = None,
    setting_type_id: Optional[str] = None
)->List[BotSettingOut]:
    """
    Получить настройки проекта (и бота и бэкенда)
    """
    with Session(engine, expire_on_commit=False) as session:
        query = session.query(BotSettings)
        if setting_name:
            query = query.filter_by(name = setting_name)
        
        if setting_key:
            query = query.filter_by(key = setting_key)

        if setting_id:
            query = query.filter_by(id = setting_id)

        if setting_type:
            query = query.join(BotSettingsTypes, BotSettingsTypes.type_id==BotSettings.id).\
                join(SettingsTypes, SettingsTypes.id == BotSettingsTypes.setting_id).\
                filter(SettingsTypes.name == setting_type)
                
        if setting_type_id:
            query = query.join(BotSettingsTypes, BotSettingsTypes.type_id==BotSettings.id).\
                join(SettingsTypes, SettingsTypes.id == BotSettingsTypes.setting_id).\
                filter(SettingsTypes.id == setting_type_id)


        query = query.all()
        return query


@router.post('/bot/settings', tags=[Tags.settings])
async def create_bot_settings(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    setting_data: BotSetting,
)->BotSettingOut:
    """
    Создать новую настройку
    """
    with Session(engine, expire_on_commit=False) as session:
        print(setting_data)
        query = session.query(BotSettings).filter(BotSettings.key==setting_data.key).first()
        if query:
            return JSONResponse({
                "message": f"Setting with key {setting_data.key} already exists"
            }, 422)
        
        new_setting = BotSettings(
                key=setting_data.key,
                name=setting_data.name,
                value=setting_data.value,
                detail=setting_data.detail
            )
        
        session.add(new_setting)
        session.commit()
        types = []
        print(setting_data.types)
        for setting_type in setting_data.types:
            print(setting_type)
            setting_query = None
            if setting_type.id:
                setting_query = session.query(SettingsTypes).filter(SettingsTypes.id==setting_type.id).first()
            elif setting_type.name:
                setting_query = session.query(SettingsTypes).filter(SettingsTypes.name==setting_type.name).first()
            else:
                continue

            if not setting_query:
                if not setting_type.name:
                    continue

                setting_query = SettingsTypes(name=setting_type.name)
                session.add(setting_query)
                session.commit()

            print(setting_query.id)
            types.append(setting_query)

        print(types)
        new_setting.types = types
        session.commit()

        return new_setting


@router.put('/bot/setting/{setting_id}', tags=[Tags.settings])
async def update_bot_setting(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    setting_id: UUID,
    setting_data: BotSettingUpdate,
)->BotSettingOut:
    """
    Обновить настройку

    **Сбрасывает** старые типы настройки и устанавливает новые
    """
    with Session(engine, expire_on_commit=False) as session:
        query = session.query(BotSettings).filter(BotSettings.id==setting_id).first()
        if not query:
            return JSONResponse({
                "message": f"Setting with key {setting_data.key} does not exist"
            }, 404)
        
        for attr, value in setting_data.model_dump().items():
            if attr == 'types' and value:
                types = []
                query.types = []
                for setting_type in setting_data.types:
                    session.add(query)
                    session.commit()

                    setting_query = None
                    if setting_type.id:
                        setting_query = session.query(SettingsTypes).filter(SettingsTypes.id==setting_type.id).first()
                    elif setting_type.name:
                        setting_query = session.query(SettingsTypes).filter(SettingsTypes.name==setting_type.name).first()
                    else:
                        continue

                    if not setting_query:
                        if not setting_type.name:
                            continue
                        setting_query = SettingsTypes(name=setting_type.name)
                        session.add(setting_query)
                        session.commit()

                    types.append(setting_query)

                query.types = types
                continue

            if value:
                setattr(query, attr, value)

        session.commit()

        return query


@router.get('/bot/messages', tags=[Tags.settings])
async def get_bot_messages(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    message_key: str,
)->str:
    """
    Получить сообщения бота
    """
    with Session(engine, expire_on_commit=False) as session:
        query = session.query(BotSettings)
        
        if message_key:
            query = query.filter_by(key = message_key)

        query = query.first()
        return query.value


    pass


@router.get("/work_days", tags=[Tags.settings])
async def get_work_days(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
):
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
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    dates_add: List[datetime] = [],
    weekdays_add: List[str] = [],
    dates_remove: List[datetime] = [],
    weekdays_remove: List[str] = [],
):
    """
    все datetime поля используют формат YYYY-MM-DDT00:00
    - **dates_add**: список дат для добавления в нерабочие даты
    - **weekdays_add**: список дней недели для добавление в нерабочие дни
    - **dates_remove**: список дат для удаления их нерабочих дат
    - **weekdays_remove**: список дней недели для удаления из нерабочих дней
    """
    #TODO: Получение дат не обращая на год
    warnings = []
    result = []
    with Session(engine, expire_on_commit=False) as session:
        for date in dates_add:
            date = date.replace(hour=00, minute=0, second=0, microsecond=0)
            date_tommorrow = date + timedelta(days=1)
            date_search_query = session.query(DaysWork)
            date_search_query = date_search_query.filter(DaysWork.date == date)
            date_search_query = date_search_query.first()

            if date_search_query:
                warnings.append(f'date {date.strftime("%Y-%m-%d")} already exists')
                continue
            
            new_date = DaysWork(
                date = date
            )
            session.add(new_date)
            result.append(f'date {date.strftime("%Y-%m-%d")} added')

        
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
            result.append(f'{weekday} added')


        for weekday in weekdays_remove:
            if str(weekday).lower() not in WEEK_DAYS_WORK_STR_LIST:
                return JSONResponse({
                    "message": f"weekday {weekday} is invaild"
                }, status_code=422)

            weekdays_search_query = session.query(WeekDaysWork).filter(WeekDaysWork.weekday == weekday).delete()
            if weekdays_search_query:
                result.append(f'{weekday} removed')


        for date in dates_remove:
            date = date.replace(hour=00, minute=0, second=0, microsecond=0)
            date_tommorrow = date + timedelta(days=1)
            date_search_query = session.query(DaysWork)
            date_search_query = date_search_query.filter(DaysWork.date >= date, DaysWork.date <= date_tommorrow)
            date_search_query = date_search_query.delete()

            if date_search_query:
                result.append(f'date {date.strftime("%Y-%m-%d")} removed')

        session.commit()

        return JSONResponse({
            "warnings": warnings,
            "result": result
        }, 201)