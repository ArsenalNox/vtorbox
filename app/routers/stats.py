import requests
import os, uuid
import re 
import math

from typing import Annotated, List, Tuple, Dict, Optional
from fastapi.responses import JSONResponse

import calendar
from dateutil.relativedelta import relativedelta
import datetime as dt
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

from app import CODER_KEY, CODER_SETTINGS, COURIER_KEY

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
    ORDER_STATUS_CANCELED, IntervalStatuses, 
    ROLE_ADMIN_NAME, ROLE_COURIER_NAME,
    Routes, RoutesOrders
    )

from app.utils import (
        send_message_through_bot, get_result_by_id, 
        generate_y_courier_json, set_timed_func
    )


router = APIRouter()


@router.get('/stats/users/registration')
async def get_user_registration_stats(
    year_month: Optional[datetime] = None
):
    with Session(engine, expire_on_commit=False) as session:
        if not year_month:
            year_month = datetime.now()

        date = year_month
        month_start_date = date.replace(hour=0, minute=0, second=0, microsecond=0, day=1)
        month_end_date   = month_start_date + relativedelta(months=1)


        user_count_query = session.query(Users).filter_by(deleted_at = None).count() 
        user_deleted_count_query = session.query(Users).filter(Users.deleted_at != None).count()
        users_registered_this_month = session.query(Users).\
            filter(Users.date_created>=month_start_date, Users.date_created<=month_end_date).count()

        registration_dates_count = []

        for month_date in range(1,calendar.monthrange(date.year, date.month)[1]+1):
            month_date_query_date_start = date.replace(hour=0, minute=0, second=0, microsecond=0, day=month_date)
            month_date_query_date_end = month_date_query_date_start + relativedelta(days=+1)
            count_query = session.query(Users).filter(
                Users.date_created>=month_date_query_date_start, Users.date_created<=month_date_query_date_end
            ).count()

            registration_dates_count.append({
                "date": month_date_query_date_start,
                "count": count_query
            })

        return_data = {
            "number": user_count_query+user_deleted_count_query,
            "deleted_count": user_deleted_count_query,
            "registered_in_month": users_registered_this_month,
            "percentage": users_registered_this_month/(user_count_query+user_deleted_count_query),
            "chardData": registration_dates_count
        }

        return return_data


@router.get('/stats/orders/statuses')
async def get_user_registration_stats():
    with Session(engine, expire_on_commit=False) as session:
        statuses_query = session.query(OrderStatuses).all()
        return_data = []

        for status in statuses_query:
            order_count_by_status = session.query(Orders).filter(Orders.status == status.id).count()
            return_data.append({
                "name": status.status_name,
                "value": order_count_by_status
            })
            

        return return_data


@router.get('/stats/orders/regions')
async def get_user_registration_stats():
    with Session(engine, expire_on_commit=False) as session:
        regions_query = session.query(Regions).all()
        return_data = []

        for region in regions_query:
            order_count_by_region = session.query(Orders).join(Address).\
                filter(Address.region_id == region.id).count()
            return_data.append({
                "name": region.name_full,
                "value": order_count_by_region
            })

        return return_data


@router.get('/stats/orders/dynamic')
async def get_user_registration_stats(
    year_month: Optional[datetime] = None
):
    with Session(engine, expire_on_commit=False) as session:
        if not year_month:
            year_month = datetime.now()

        date = year_month
        month_start_date = date.replace(hour=0, minute=0, second=0, microsecond=0, day=1)
        month_end_date   = month_start_date + relativedelta(months=1)

        statuses_query = session.query(OrderStatuses).all()

        return_data = []

        for month_date in range(1,calendar.monthrange(date.year, date.month)[1]+1):
            month_date_query_date_start = date.replace(hour=0, minute=0, second=0, microsecond=0, day=month_date)
            month_date_query_date_end = month_date_query_date_start + relativedelta(days=+1)

            date_order_data = {"name": month_date_query_date_start}

            for status in statuses_query:
                order_count_by_status = session.query(Orders).filter(
                    Orders.status == status.id,
                    Orders.date_created>=month_date_query_date_start, 
                    Orders.date_created<=month_date_query_date_end
                    ).count()

                date_order_data[status.status_name] = order_count_by_status

            return_data.append(date_order_data)

        return return_data

