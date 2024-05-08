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
from fastapi.encoders import jsonable_encoder

from app.validators import (
    LinkClientWithPromocodeFromTG as UserLinkData,
    Address as AddressValidator,
    AddressUpdate as AddressUpdateValidator,
    UserLogin as UserLoginSchema,
    AddressSchedule, CreateUserData, UpdateUserDataFromTG, AddressOut,
    RegionOut, AddressDaysWork, UserOut, RouteOut, UserRegistrationStat,
    OrderStatusStatistic, OrderRegionStatistic
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
    ROLE_ADMIN_NAME, ROLE_COURIER_NAME, ORDER_STATUS_DONE,
    Routes, RoutesOrders
    )

from app.utils import (
        send_message_through_bot, get_result_by_id, 
        generate_y_courier_json, set_timed_func
    )

from app import SCHEDULER_PORT, SCHEDULER_HOST


router = APIRouter()

@router.get('/jobs')
async def get_all_jobs():
    request = requests.get(f"http://{SCHEDULER_HOST}:{SCHEDULER_PORT}/jobs")
    return request.json()