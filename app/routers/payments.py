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

from fastapi import APIRouter, Body, Security, Query, Request
from fastapi.responses import JSONResponse

from calendar import monthrange
from uuid import UUID

from sqlalchemy import desc, asc, desc

from app.validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut,
    OrderUpdate, PaymentOut,
    PaymentTerminal, PaymentNotification
)

from app.auth import (
    get_current_user
)

from app.models import (
    Users, Session, engine, UsersAddress, 
    Address, IntervalStatuses, Roles, 
    Permissions, Regions, WEEK_DAYS_WORK_STR_LIST,
    Payments, PaymentTerminals, PaymentClientData
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
    generate_y_courier_json, set_timed_func,
    create_tinkoff_token
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
            payments_query = payments_query.filter(Payments.order_id == payment_order_num)
        
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
    with Session(engine, expire_on_commit=False) as session:
        payment_query = session.query(Payments).filter_by(id=payment_id).first()

        payment_status = Payments.check_order_status(payment_id, order_id=payment_query.order_id)

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
    - **terminal_id** UUID айти терминала, через который создастся оплата. При None используется терминал по умолчанию
    """
    with Session(engine, expire_on_commit=False) as session:
        terimnal = None
        if not terminal_id:
            terimnal = session.query(PaymentTerminals).filter(PaymentTerminals.default_terminal==True).first()
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

        if not order_query.box:
            return JSONResponse({
                "message": "No contaier set"
            })

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
    Обновить данные шлюза оплаты

    - **terminal_id**: Айди терминала, данные которого требуется обновить
    """
    with Session(engine, expire_on_commit=False) as session:
        terminal_query = session.query(PaymentTerminals).filter_by(id=terminal_id).first()
        if not terminal_id:
            return JSONResponse({
                "message": "not found"
            }, status_code=404)
        
        for attr, value in terminal_data.model_dump().items():
            if attr == 'default_terminal' and value==True:
                terminal_update = session.query(PaymentTerminals).all()
                for terminal in terminal_update: 
                    terminal.default_terminal = False


            if value != None:
                setattr(terminal_query, attr, value)

        session.add(terminal_query)
        session.commit()

        return terminal_query


@router.put('/payment-data/saved/cards/set-default')
async def set_default_payment_card(
    card_id: UUID
):
    with Session(engine, expire_on_commit=False) as session:
        card_query = session.query(PaymentClientData).filter(PaymentClientData.id==card_id).first()

        if not card_query:
            return JSONResponse({
                "message": "not found"
            }, status_code=404)
        
        card_update = session.query(PaymentClientData).filter(PaymentClientData.user_id==card_query.user_id).all()
        for card in card_update:
            card.default_card = False
        
        card_query.default_card = True

        session.commit()

        return card_query


@router.get("/payment-data/saved-cards")
async def get_user_payment_information(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    user_id: UUID|int,
):
    """
    Получить данные оплаты пользователя после успешной оплаты
    - **user_id**: UUID|int - айди пользователя (может быть как тг айди так и UUID)

    Возвращает список сохранённых карт пользователя
    """
    with Session(engine, expire_on_commit=False) as session:
        terminal = session.query(PaymentTerminals).filter_by(default_terminal=True).first()

        user = Users.get_user(str(user_id))
        
        #Обновить данные о картах пользвателя со стороны тиньки
        data = PaymentClientData.get_client_data_from_api(user, terminal)

        #Получить сохранённое в бд
        return_data = session.query(PaymentClientData).filter(PaymentClientData.user_id == user.id).all()

        return return_data


@router.delete('/payment-data/customer-data/removeCard')
async def remove_saved_card(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    id: UUID
):
    """
    Удаление сохранённой карты пользователя. Удаляет как у нас так и у тинькофф
    - **card_id**: UUID карты в нашей системе
    """
    with Session(engine, expire_on_commit=False) as session:
        card_query = session.query(PaymentClientData).filter(PaymentClientData.id==id).first()
        if not card_query:
            return JSONResponse({
                "message": "not found"
            }, status_code=404)

        url = 'https://securepay.tinkoff.ru/v2/RemoveCard'
        terminal = session.query(PaymentTerminals).filter(PaymentTerminals.default_terminal == True).first()
        r_data = {
            "TerminalKey": f"{terminal.terminal}",
            "CustomerKey": f"{card_query.user.id}",
            "CardId": f"{card_query.card_id}",
        }
        token = create_tinkoff_token(r_data, terminal.password)
        r_data['Token'] = token

        print(r_data)
        
        response = requests.post(url, json=r_data)
        print(response.status_code)
        if response.status_code == 200 and response.json()['Success'] == True:
            delete_query = session.query(PaymentClientData).filter(PaymentClientData.id == id).delete()
            session.commit()
            return 'OK'
        else:
            return JSONResponse({
                "response_data": response.json()
            }, status_code=503)


@router.post('/payment/notify/auto')
async def process_notification_from_tinkoff(requestd_data: Request):
    """
    Служебный эндпоинт для тинькофф, не трогать
    """
    with Session(engine, expire_on_commit=False) as session:
        payment_data = await requestd_data.json()
        print(payment_data)

        payment = Payments.query(
            tinkoff_id=payment_data['PaymentId'],
            terminal_id=payment_data['TerminalKey']
        )

        print(payment)

        return 'OK'
