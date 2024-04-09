import requests
import os, uuid
import re 
import math

from typing import Annotated, List, Tuple, Dict, Optional
from fastapi.responses import JSONResponse

import datetime as dt
from datetime import datetime, timedelta


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
    OrderUpdate, PaymentOut,
    PaymentTerminal
)

from app.auth import (
    get_current_user
)

from app.models import (
    Users, Session, engine, UsersAddress, 
    Address, IntervalStatuses, Roles, 
    Permissions, Regions, WEEK_DAYS_WORK_STR_LIST,
    Payments, PaymentTerminals
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

import hashlib
import requests


@router.get('/payments')
async def get_payment_info(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    payment_id: Optional[UUID] = None,
    payment_tk_id: Optional[str] = None,
    payment_order_num: Optional[str] = None,
    payment_order_id: Optional[UUID] = None,
)->List[PaymentOut]:
    """
    - **payment_id**: uuid - получить информацию по конкретной заявке, если пусто возвращаются все платежи
    - **payment_tk_id**: int - по айди в тинькофф
    - **payment_order_num**: int - по order_num заявки
    - **payment_order_id**: UUID - по uuid заявки
    """
    with Session(engine, expire_on_commit=False) as session:
        payments_query = session.query(Payments)

        if payment_id:
            payments_query = payments_query.filter(Payments.id == payment_id)

        if payment_tk_id:
            payments_query = payments_query.filter(Payments.payment_tk_id == payment_tk_id)

        if payment_order_num:
            payments_query = payments_query.filter(Payments.order_id == payment_order_id)
        
        if payment_order_id:
            payments_query = payments_query.join(Orders, Orders.order_num==Payments.order_id).\
                filter(Orders.id == payment_order_id)

        payments_query = payments_query.all()

        return payments_query


@router.get('/payment/{payment_id}/status')
async def get_payment_status(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    payment_id: UUID
):
    """
    Получение статуса первого/не рекуррентного платежа по айди
    """
    payment_status = Payments.check_payment_status(payment_id)

    return payment_status


@router.get('/payment/{payment_id}/status/order')
async def get_payment_order_status(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    payment_id: UUID
):
    payment_status = Payments.check_order_status(payment_id)

    return payment_status


@router.post('/payment')
async def create_new_payment(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    for_order: UUID,
    terminal_id: Optional[UUID] = None,
):
    """
    Ручное создание оплаты
    - **for_order** UUID заявки, для которой нужно создать оплату
    - **terminal_id** UUID айти терминала, через который создастся оплата
    """
    with Session(engine, expire_on_commit=False) as session:
        terimnal = None
        if not terminal_id:
            terimnal = session.query(PaymentTerminals).first()
        else: 
            terimnal = session.query(PaymentTerminals).filter(PaymentTerminals.id == terminal_id).first()
        
        if not terimnal:
            return JSONResponse({
                "message": "No terminal found"
            }, 500)
        
        order_query = session.query(Orders).filter_by(id=for_order).first()
        if not order_query:
            return JSONResponse({
                "message": "No order found"
            }, 404)

        new_payment = Payments.create_new_payment(
            terminal=terimnal,
            order=order_query
        )

        if not new_payment:
            return [new_payment, False]

        try:
            set_timed_func('p', new_payment.id, "M:01")
        except Exception as err:
            return [new_payment, False]

        return [new_payment, True]
        

@router.get('/terminals')
async def get_payment_terminals(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
):
    """
    Получить терминалы оплаты
    """
    with Session(engine, expire_on_commit=False) as session:
        terminal_query = session.query(PaymentTerminals).all()
        return terminal_query


@router.patch('/terminal/{terminal_id}')
async def update_terminal_data(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    terminal_id: UUID,
    terminal_data: PaymentTerminal
):
    """
    Обновить данные шлюза опталы
    """
    with Session(engine, expire_on_commit=False) as session:
        terminal_query = session.query(PaymentTerminals).filter_by(id=terminal_id).first()
        if not terminal_id:
            return JSONResponse({
                "message": "not found"
            }, status_code=404)
        
        for attr, value in terminal_data.model_dump().items():
            if value != None:
                setattr(terminal_query, attr, value)

        session.add(terminal_query)
        session.commit()

        return terminal_query


@router.get("/payment-data/my-data")
async def get_user_payment_information():
    """
    Получить данные оплаты пользователя после успешной оплаты
    """
    pass