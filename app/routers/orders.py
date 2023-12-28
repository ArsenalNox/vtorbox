"""
Содержит в себе ендпоинты по заявкам
"""
from typing import Annotated

from fastapi import APIRouter, Body, Security
from fastapi.responses import JSONResponse

from datetime import datetime
from datetime import timedelta

from sqlalchemy import desc

from ..validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut
)

from ..auth import (
    get_current_user
)

from ..models import (
    engine, 
    Orders, 
    Users, 
    Session, 
    Address,
    UsersAddress,
    BoxTypes,
    OrderStatuses,
    OrderStatusHistory
    )
from uuid import UUID

import re 

router = APIRouter()


@router.get('/orders/filter/', tags=["orders", "admin"])
async def get_filtered_orders(
        by_date: bool = False, 
        datetime_start: Annotated[datetime | None, Body()] = None,
        datetime_end: Annotated[datetime | None, Body()] = None,

        date_asc: bool = False,

        only_inactive: bool = False,
        only_active: bool = False,

        limit: int | None = None,
        #TODO: Фильтр по району, округу, дистанции, курьеру итд
        ):
    """
    Получение заявок по фильтру
    """

    orders = Orders.get_all_orders()
    if orders:    
        return [orders]
    else:
        return JSONResponse(status_code=404, content={"message": "No orders found"})


@router.get('/orders', tags=["orders", "admin"], responses={
        200: {
            "description": "Получение всех заявок",
            "content": {
                "application/json": {
                    "example": [
                        {
                        "district": "МО",
                        "id": 1,
                        "from_user": 1,
                        "address": "Ул. Пушкина 8",
                        "point_on_map": 'null',
                        "weekday": "6",
                        "tariff": 'null',
                        "next_planned_date": 'null',
                        "times_completed": 'null',
                        "distance_from_mkad": "12",
                        "region": "Красногорск",
                        "full_adress": "8-53. Домофон 53 и кнопка \"вызов\".",
                        "interval": 'null',
                        "subscription": 'null',
                        "last_disposal": 'null',
                        "legal_entity": 'false',
                        "payment_day": 'null'
                        }
                    ]
                }
            }
        }   
})
async def get_all_orders(): 
    """
    Получить все заявки
    """
    #TODO: Пагинация заявок

    orders = Orders.get_all_orders()
    if orders:    
        return [orders]
    else:
        return JSONResponse(
            status_code=404, 
            content={"message": "No orders found"}
            )


@router.get('/orders/active', tags=["orders"])
async def get_active_orders():
    pass


@router.get('/orders/{order_id}', tags=["orders", "bot"], 
    responses={
        200: {
            "description": "Заявка полученная по айди",
            "content": {
                "application/json": {
                    "example": {
                        'user_tg_id': 7643079034697,
                        'district': 'МО',
                        'region': 'Красногорск',
                        'distance_from_mkad': 12,
                        'address': 'Ул. Пушкина 8',
                        'full_adress': '8-53. Домофон 53 и кнопка "вызов".' ,
                        'weekday': 6,
                        'full_name': 'Иванов Иван Иванович',
                        'phone_number': '+7 123 2323 88 88', 
                        'price': 350,
                        'is_legal_entity': False,
                    }
                }
            }
        }
    }
    )
async def get_order_by_id(order_id: UUID):
    """
    Получение конкретной заявки
    """
    with Session(engine, expire_on_commit=False) as session:
        order = session.query(Orders, Address).\
                join(Address, Address.id == Orders.address_id).\
                where(Orders.id == order_id).order_by(Orders.date_created).first()

        if not order:
            return JSONResponse({
                "message": "not found"
            },status_code=404)

        return_data = []

        user = session.query(Users).filter_by(id = order[0].from_user).first()
        order_data = OrderOut(**order[0].__dict__)
        order_data.tg_id = user.telegram_id
        order_data.address_data = order[1]

        return_data.append(order_data)

        return return_data


@router.get('/users/orders/', tags=['bot', 'orders'])
async def get_user_orders(tg_id: int = None, user_id: UUID = None, order_id: UUID = None):
    """
    Получение заявок пользователя 
    """
    user = None

    with Session(engine, expire_on_commit=False) as session:
        if tg_id:
            user = session.query(Users).filter_by(telegram_id=tg_id).first()
        elif user_id:
            user = session.query(Users).filter_by(id=user_id).first()
        else:
            return JSONResponse({
                "message": "At least one type of user id is required"
            }, status_code=422)

        if not user:
            return JSONResponse({
                "message": "No user found"
            }, status_code=422)

        orders = None
        if not (order_id == None):
            #Получение конкретной заявки
            orders = session.query(Orders, Address, BoxTypes, OrderStatuses).\
                join(Address, Address.id == Orders.address_id).\
                join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
                join(OrderStatuses, OrderStatuses.id == Orders.status).\
                where(Orders.id == order_id).\
                where(Orders.from_user == user.id).order_by(desc(Orders.date_created)).all()
        else:
            orders = session.query(Orders, Address, BoxTypes, OrderStatuses).\
                join(Address, Address.id == Orders.address_id).\
                join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
                join(OrderStatuses, OrderStatuses.id == Orders.status).\
                where(Orders.from_user == user.id).order_by(desc(Orders.date_created)).all()


        return_data = []

        for order in orders:
            order_data = OrderOut(**order[0].__dict__)
            order_data.tg_id = user.telegram_id

            try:
                order_data.address_data = order[1]
            except IndexError: 
                order_data.address_data = None

            try:
                order_data.box_data = order[2]
            except IndexError:
                order_data.box_data = None

            try:
                order_data.status_data = order[3]
            except IndexError:
                order_data.status_data = None

            return_data.append(order_data)

        return return_data


@router.post('/orders/create', tags=["orders", "bot"])
async def create_order(
    order_data: OrderValidator,
    current_user: Annotated[UserLoginSchema, Security(get_current_user)]
    ):
    """
    Создание заявки
    """
    #TODO Переделать под новые адреса 
    #TODO Добавить поддержку добавления контейнера
    #TODO Оповещение менеджера при создании заявки

        
    with Session(engine, expire_on_commit=False) as session:
        user = Users.get_user(order_data.from_user)
        if not user:
            return JSONResponse({
                "message": f"No user with id '{order_data.from_user}' found"
            }, status_code=422)
        else:
            order_data.from_user = user.id 

        # user_id: int
        # address_id: str
        # day: str 
        # box_type_id: int
        # bot_count: int

        address = session.query(Address).\
            join(UsersAddress, UsersAddress.address_id == Address.id).\
            join(Users, UsersAddress.user_id == Users.id). \
            where(Users.id == user.id, Address.id == order_data.address_id).first()
        if not address:
            return JSONResponse({
                "message": f"No user address with id '{order_data.from_user}' found"
            }, status_code=422)

        container = session.query(BoxTypes).filter_by(box_name = order_data.box_name).first()
        if not container:
            return JSONResponse({
                "message": f"no {order_data.box_name} container found"
            }, status_code=422)

        order_date = datetime.now()
        match order_data.day:

            case 'сегодня':
                pass

            case 'завтра':
                order_date += timedelta(days=1)

            case 'послезавтра':
                order_date += timedelta(days=2)

            case _:
                #TODO: регулярка на дату
                pass
        
        print(order_date)

        new_order = Orders(
            from_user   = user.id,
            address_id  = order_data.address_id,
            day         = order_date,
            box_type_id = container.id,
            box_count   = order_data.box_count,
            status      = OrderStatuses.status_default().id
        )

        session.add(new_order)
        session.commit()

        status_update = OrderStatusHistory(
            order_id = new_order.id,
            status_id = new_order.status
        )
        session.add(status_update)
        session.commit()

    return {
        "status": 'created',
        "content": new_order,
        "data_given": order_data
    }


@router.get("/orders/{order_id}/history")
async def get_order_status_history(
    order_id: UUID,
    tg_id: int,
    current_user: Annotated[UserLoginSchema, Security(get_current_user)]
    ):
    """
    Получение истории изменения статуса заявки
    """
    #TODO: Проверка владения заявки пользователя
    with Session(engine, expire_on_commit=False) as session:
        order = session.query(Orders).\
            join(Users, Users.id == Orders.from_user).\
            where(Users.telegram_id == tg_id).\
            where(Orders.id == order_id).\
            first()

        if not order:
            return JSONResponse({
                "message": "User order not found"
            }, status_code=404)

        history = session.query(OrderStatusHistory, OrderStatuses).\
            join(OrderStatuses, OrderStatuses.id == OrderStatusHistory.status_id).\
            where(OrderStatusHistory.order_id == order_id).order_by(desc(OrderStatusHistory.date)).all()

        return_data = [(r[0].date, r[1].status_name, r[1].description) for r in history]

        return return_data


@router.delete('/orders/{order_id}', tags=["orders"])
async def delete_order_by_id(order_id:UUID):
    """
    Удаление заявки
    """

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Orders).filter_by(id=order_id).delete()
        session.commit()
        if query:
            return JSONResponse({
                "message": 'deleted'
            }, status_code=200)
    

    return JSONResponse({
        "message": "not found"
    }, status_code=404)


@router.put('/orders/{order_id}/status', tags=["orders"])
async def set_order_status():
    """
    Обновление/Установка статуса заявки
    """
    pass


@router.put('/orders/{order_id}/courier', tags=["orders"])
async def set_order_courier():
    """
    Установить курьера на заказ
    """
    pass