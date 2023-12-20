"""
Содержит в себе ендпоинты по заявкам
"""
from typing import Annotated

from fastapi import APIRouter, Body, Security
from fastapi.responses import JSONResponse

from datetime import datetime

from ..validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema
)

from ..auth import (
    get_current_user
)

from ..models import Orders, Users, Session, engine

router = APIRouter()


@router.get('/orders/filter/', tags=["orders"])
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


@router.get('/orders', tags=["orders"], responses={
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
        return JSONResponse(status_code=404, content={"message": "No orders found"})


@router.get('/orders/active', tags=["orders"])
async def get_active_orders():
    pass


@router.get('/orders/{order_id}', tags=["orders"], 
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
async def get_order_by_id(order_id:int):
    """
    Получение конкретной заявки
    """
    return [{'order_id': 1, 'user_id': 1}]


@router.post('/orders/create', tags=["orders"], 
    responses={
        200: {
            "status": 'created',
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
})
async def create_order(
    order_data: OrderValidator,
    current_user: Annotated[UserLoginSchema, Security(get_current_user)]
    ):
    """
    Создание заявки админом или менеджером
    """
    #TODO: Опциональная аунтефикация на создание? 
    with Session(engine, expire_on_commit=False) as session:

        user = Users.get_or_create(t_id=order_data.user_tg_id)

        new_order = Orders(
            from_user          = user.id,
            district           = order_data.district,
            region             = order_data.region,
            distance_from_mkad = order_data.distance_from_mkad,
            address            = order_data.address, #TODO: Создание адреса 
            full_adress        = order_data.full_adress,
            weekday            = order_data.weekday,
        )

        session.add(new_order)
        session.commit()

    return {
        "status": 'created',
        "content": order_data
    }


@router.delete('/orders/{order_id}/delete', tags=["orders"])
async def delete_order_by_id(order_id:int):
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