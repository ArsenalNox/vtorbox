"""
Содержит в себе ендпоинты по заявкам
"""
from typing import Annotated

from fastapi import APIRouter, Body, Security
from fastapi.responses import JSONResponse

from datetime import datetime
from datetime import timedelta

from sqlalchemy import desc, asc

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
    OrderStatusHistory,
    ORDER_STATUS_DELETED
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
                        "tg_id": 851230989,
                        "day": "2024-01-14T00:00:00",
                        "last_disposal": 'null',
                        "times_completed": 'null',
                        "status": "32c9cfba-7774-4fb1-95be-76a897dc2e54",
                        "date_created": "2024-01-12T14:15:57.364705",
                        "last_updated": "2024-01-12T14:15:34.617734",
                        "id": "5a56a39a-11f7-4a99-9c99-e90043c8b754",
                        "address_id": "e2dbda30-0593-4d67-a7bc-cf56b406eb2c",
                        "next_planned_date": 'null',
                        "legal_entity": 'false',
                        "box_type_id": "a6996b4d-ef7d-4054-8340-5f850d1543e6",
                        "box_count": 1,
                        "on_interval": 'false',
                        "interval_type": 'null',
                        "intreval": 'null',
                        "address_data": {
                            "address": "Москва Пушкина 10",
                            "district": 'null',
                            "distance_from_mkad": 'null',
                            "comment": 'null',
                            "detail": 'null',
                            "longitude": "37.210662",
                            "latitude": "55.609151",
                            "main": 'false',
                            "region": 'null',
                            "point_on_map": 'null'
                        },
                        "box_data": {
                            "pricing_default": 500,
                            "box_name": "Пакет",
                            "volume": 2,
                            "weight_limit": 15
                        },
                        "status_data": {
                            "status_name": "подтверждена",
                            "description": "подтверждена клиентом"
                        }
                    }
                }
            }
        }
    }
    )
async def get_order_by_id(order_id: UUID) -> OrderOut:
    """
    Получение конкретной заявки
    """
    with Session(engine, expire_on_commit=False) as session:
        #Получение конкретной заявки
        order = session.query(Orders, Address, BoxTypes, OrderStatuses).\
            join(Address, Address.id == Orders.address_id).\
            join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
            join(OrderStatuses, OrderStatuses.id == Orders.status).\
            where(Orders.id == order_id).\
            order_by(asc(Orders.date_created)).first()

        if not order:
            return JSONResponse({
                "message": "not found"
            },status_code=404)


        order_data = OrderOut(**order[0].__dict__)
        order_data.tg_id = session.query(Users).filter_by(id=order[0].from_user).first().telegram_id

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

        return order_data


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
                where(Orders.from_user == user.id).order_by(asc(Orders.date_created)).all()
        else:
            orders = session.query(Orders, Address, BoxTypes, OrderStatuses).\
                join(Address, Address.id == Orders.address_id).\
                join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
                join(OrderStatuses, OrderStatuses.id == Orders.status).\
                where(Orders.from_user == user.id).order_by(asc(Orders.date_created)).all()

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

        if (len(return_data) < 1):
            return False

        return return_data


@router.post('/orders/create', tags=["orders", "bot"])
async def create_order(
    order_data: OrderValidator,
    current_user: Annotated[UserLoginSchema, Security(get_current_user)]
    ):
    """
    Создание заявки
    """
    #TODO: Оповещение менеджера при создании заявки

        
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

        order_data.day = datetime.strptime(order_data.day, "%d-%m-%Y").date()

        new_order = Orders(
            from_user   = user.id,
            address_id  = order_data.address_id,
            day         = order_data.day,
            box_type_id = container.id,
            box_count   = order_data.box_count,
            status      = OrderStatuses.status_default().id,
            date_created = datetime.now()
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


@router.get("/orders/{order_id}/history", tags=['bot', 'orders'])
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
            where(Orders.deleted_at == None).\
            first()

        if not order:
            return JSONResponse({
                "message": "user's order not found"
            }, status_code=404)

        history = session.query(OrderStatusHistory, OrderStatuses).\
            join(OrderStatuses, OrderStatuses.id == OrderStatusHistory.status_id).\
            where(OrderStatusHistory.order_id == order_id).order_by(desc(OrderStatusHistory.date)).all()

        return_data = [(r[0].date, r[1].status_name, r[1].description) for r in history]

        return return_data


@router.delete('/orders/all', tags=['bot', 'admin', 'orders'])
async def delete_all_orders(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],
):
    """
    Удаление всех заявок (Именно чистка)
    """
    with Session(engine, expire_on_commit=False) as session:
        query = session.query(OrderStatusHistory).delete()
        query = session.query(Orders).delete()
        session.commit()

        return 


@router.delete('/orders/{order_id}', tags=["orders"])
async def delete_order_by_id(order_id:UUID):
    """
    Удаление заявки
    """

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(OrderStatusHistory).filter_by(order_id=order_id).update({"deleted_at": datetime.now()})
        query = session.query(Orders).filter_by(id=order_id).update({"deleted_at": datetime.now()})

        order_query = session.query(Orders).filter_by(id=order_id).first()

        status_query = session.query(OrderStatuses).\
            filter_by(status_name=ORDER_STATUS_DELETED["status_name"]).first()

        order_query.status = status_query.id

        status_update = OrderStatusHistory(
            order_id = order_query.id,
            status_id = status_query.id
        )

        session.add(status_update)

        session.add(order_query)
        session.commit()

        if query:
            return JSONResponse({
                "message": 'deleted'
            }, status_code=200)
    

    return JSONResponse({
        "message": "not found"
    }, status_code=404)


@router.put('/orders/{order_id}/status', tags=["orders"])
async def set_order_status(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],
    order_id: UUID,
    status_text: str = None,
    status_id: UUID = None,
):
    """
    Обновление/Установка статуса заявки
    """
    if (not status_text) and (not status_id):
        return JSONResponse({
            "message": "status_text or status_id required"
        },status_code=422)
    
    status_query = None
    with Session(engine, expire_on_commit=False) as session:
        
        if status_text:
            status_query = session.query(OrderStatuses).filter_by(status_name = status_text).first()
        elif status_id:
            status_query = session.query(OrderStatuses).filter_by(id = status_id).first()

        if not status_query:
            return JSONResponse({
                "message": "status not found"
            },status_code=404)
        
        order_query = session.query(Orders).filter_by(id = order_id).where(Orders.deleted_at == None).first()
        if not order_query:
            return JSONResponse({
                "message": "order not found"
            },status_code=404)

        order_query.status = status_query.id

        status_update = OrderStatusHistory(
            order_id = order_query.id,
            status_id = status_query.id
        )
        session.add(status_update)

        session.add(order_query)
        session.commit()



@router.put('/orders/{order_id}/courier', tags=["orders"])
async def set_order_courier():
    """
    Установить курьера на заказ
    """
    pass


@router.get("/orders/process", tags=['managers', 'admins'])
async def process_current_orders():
    """
    Обработка всех доступных заказов
    """