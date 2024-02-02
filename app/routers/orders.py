"""
Содержит в себе ендпоинты по заявкам
"""
from typing import Annotated, List

from calendar import monthrange

from fastapi import APIRouter, Body, Security, Query
from fastapi.responses import JSONResponse

from datetime import datetime
from datetime import timedelta

from sqlalchemy import desc, asc
from app import Tags

from ..validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut,
    OrderUpdate
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
    ORDER_STATUS_DELETED,
    ORDER_STATUS_AWAITING_CONFIRMATION,
    IntervalStatuses
    )

from app import Tags
from uuid import UUID

import re 

router = APIRouter()


@router.get('/orders/filter/', tags=["orders", "admin"])
async def get_filtered_orders(
        by_date: bool = False, 
        # datetime_start: Annotated[datetime | None, Body()] = None,
        # datetime_end: Annotated[datetime | None, Body()] = None,

        date_asc: bool = False,

        limit: int | None = None,
        state: str = None,
        state_id: UUID = None
        #TODO: Фильтр по району, округу, дистанции, курьеру итд
        ):
    """
    Получение заявок по фильтру
    """

    with Session(engine, expire_on_commit=False) as session:
        #Получение конкретной заявки

        order = session.query(Orders, Address, BoxTypes, OrderStatuses).\
            join(Address, Address.id == Orders.address_id).\
            join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
            join(OrderStatuses, OrderStatuses.id == Orders.status)
        
        if state or state_id:
            
            status_query = session.query(OrderStatuses).filter_by(status_name=state).first()
            order = order.filter_by(Orders.status == status_query.id)

        if date_asc:
            order = order.order_by(asc(Orders.date_created))
        else:
            order = order.order_by(asc(Orders.date_created))

        if limit:
            order = order.limit(limit)
        


        orders = order.all()

        if not orders:
            return JSONResponse({
                "message": "not found"
            },status_code=404)


        return_data = []
        for order in orders:
            print(order)
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




@router.get('/orders', tags=[Tags.orders, Tags.admins], responses={
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
async def get_all_orders(
    show_deleted: bool = False,
    filter_status: str = None,
    filter_date: str = None,
): 
    """
    Получить все заявки
    """
    #TODO: Пагинация заявок

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Orders, Address, BoxTypes, OrderStatuses).\
            join(Address, Address.id == Orders.address_id).\
            join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
            join(OrderStatuses, OrderStatuses.id == Orders.status)
                
        if not show_deleted:
            query = query.filter(Orders.deleted_at == None)

        orders = query.order_by(asc(Orders.date_created)).all()

        return_data = []
        for order in orders:
            order_data = OrderOut(**order[0].__dict__)

            try:
                order[1].interval = str(order[1].interval).split(', ')
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


@router.get('/orders/{order_id}', tags=[Tags.orders, Tags.bot], 
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
async def get_order_by_id(
    order_id: UUID
    
    ) -> OrderOut:
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


@router.get('/users/orders/', 
    tags=[Tags.bot, Tags.orders], 
    response_description="Список заявок пользователя")
async def get_user_orders(
    tg_id: int = None, 
    user_id: UUID = None, 
    order_id: UUID = None,
    orders_id: List[UUID] = Query(None),
    order_num: int = None,
    user_order_num: int = None,
    order_nums: List[int] = Query(None)
    ):
    """
    Получение информации о заявках пользователя
    При получении завяки обязательно нужно указать **tg_id** или **user_id**  
    - **tg_id**: айди пользователя в телеграм
    - **user_id**: внутренний uuid4 пользователя
    - **order_id**: uuid4 конкретной заявки
    - **orders_id**: список айди заявок
    - **order_num**: получение заявки по её номеру
    - **user_order_num**: получение заявки по её порядковому номеру у пользователя 
    - **order_nums**: список номером заявок
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

        elif orders_id:
            orders = session.query(Orders, Address, BoxTypes, OrderStatuses).\
                join(Address, Address.id == Orders.address_id).\
                join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
                join(OrderStatuses, OrderStatuses.id == Orders.status).\
                filter(Orders.id.in_(orders_id)).\
                where(Orders.from_user == user.id).order_by(asc(Orders.date_created)).all()

        elif order_num:
            orders = session.query(Orders, Address, BoxTypes, OrderStatuses).\
                join(Address, Address.id == Orders.address_id).\
                join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
                join(OrderStatuses, OrderStatuses.id == Orders.status).\
                where(Orders.order_num == order_num).order_by(asc(Orders.date_created)).all()
        
        elif user_order_num:
            orders = session.query(Orders, Address, BoxTypes, OrderStatuses).\
                join(Address, Address.id == Orders.address_id).\
                join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
                join(OrderStatuses, OrderStatuses.id == Orders.status).\
                where(Orders.user_order_num == user_order_num).order_by(asc(Orders.date_created)).all()
        
        elif order_nums:
            orders = session.query(Orders, Address, BoxTypes, OrderStatuses).\
                join(Address, Address.id == Orders.address_id).\
                join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
                join(OrderStatuses, OrderStatuses.id == Orders.status).\
                filter(Orders.order_num.in_(order_nums)).\
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
                order[1].interval = str(order[1].interval).split(', ')
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


@router.post('/orders/create', tags=[Tags.orders, Tags.bot])
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

        count = session.query(Orders.id).where(Orders.from_user == user.id).count()

        new_order = Orders(
            from_user   = user.id,
            address_id  = order_data.address_id,
            day         = order_data.day,
            box_type_id = container.id,
            box_count   = order_data.box_count,
            status      = OrderStatuses.status_default().id,
            date_created = datetime.now(),
            user_order_num = count + 1
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


@router.get("/orders/{order_id}/history", tags=[Tags.orders, Tags.bot])
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


@router.delete('/orders/all', tags=[Tags.bot, Tags.admins, Tags.orders])
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


@router.delete('/orders/{order_id}', tags=[Tags.orders])
async def delete_order_by_id(
    order_id:UUID,
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    ):
    """
    Удаление заявки
    """

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(OrderStatusHistory).\
            filter_by(order_id=order_id).update({"deleted_at": datetime.now()})
        query = session.query(Orders).\
            filter_by(id=order_id).update({"deleted_at": datetime.now()})

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


@router.put('/orders/{order_id}/status', tags=[Tags.orders])
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
        
        order_query = session.query(Orders).filter_by(id = order_id).\
            where(Orders.deleted_at == None).first()

        if not order_query:
            return JSONResponse({
                "message": "order not found"
            },status_code=404)

        order_query.status = status_query.id

        status_update = OrderStatusHistory(
            order_id = order_query.id,
            status_id = status_query.id,
            date = datetime.now()
        )
        session.add(status_update)

        session.add(order_query)
        session.commit()


@router.put('/orders/{order_id}/courier', tags=[Tags.orders, Tags.managers])
async def set_order_courier():
    """
    Установить курьера на заказ
    """
    pass


@router.put('/orders/{order_id}', tags=[Tags.bot, Tags.orders])
async def update_order_data(order_id: UUID, new_order_data: OrderUpdate)->OrderOut:
    """
    Обновить данные заявки
    """
    with Session(engine, expire_on_commit=False) as session:

        order_query = session.query(Orders).filter_by(id=order_id)\
            .where(Orders.deleted_at == None).first()
        if not order_query:
            return JSONResponse({
                "message": "Order not found"
            },status_code=404)

        address_query = session.query(Address).filter_by(id=new_order_data.address_id).\
            where(Address.deleted_at == None).first()

        container = session.query(BoxTypes).filter_by(box_name = new_order_data.box_name).\
            where(BoxTypes.deleted_at == None).first()

        #Обновляем данные адреса на новые  
        for attr, value in new_order_data.model_dump().items():
            if value == None:
                continue
            
            if attr == "box_name" and (not container):
                return JSONResponse({
                    "message": f"no '{new_order_data.box_name}' container found"
                }, status_code=422)

            elif attr == "box_name":
                order_query.box_type_id = container.id
                continue

            if attr == "address_id" and (not address_query):
                return JSONResponse({
                    "message": "Address not found"
                },status_code=404)

            if attr == "box_count" and (new_order_data.box_count < 1):
                return JSONResponse({
                    "message": "Cannot set box_count below 1"
                }, status_code=422)


            setattr(order_query, attr, value)

        session.commit()

        return OrderOut(**order_query.__dict__)


@router.post("/orders/{order_id}/accept", tags=[Tags.orders, Tags.bot])
async def accept_order_by_user(
    order_id: UUID,
    tg_id: int,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])]
    ):
    """
    Принять вывоз по заявке пользователем
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
        
        order_query = session.query(Orders).filter_by(id = order_id).\
            where(Orders.deleted_at == None).first()

        if not order_query:
            return JSONResponse({
                "message": "order not found"
            },status_code=404)

        order_query.status = status_query.id

        status_update = OrderStatusHistory(
            order_id = order_query.id,
            status_id = status_query.id,
            date = datetime.now()
        )
        session.add(status_update)

        session.add(order_query)
        session.commit()


@router.get("/process_orders", tags=[Tags.managers, Tags.admins])
async def process_current_orders():
    """
    Обработка всех доступных заявок, высчитывание следующего дня забора заявки без смены статуса
    """

    #TODO: Добавить в routed_orders 
    with Session(engine, expire_on_commit=False) as session:
        #TODO: Фильтр по статусу
        orders = session.query(Orders, Address, BoxTypes, OrderStatuses, Users).\
            join(Address, Address.id == Orders.address_id).\
            join(BoxTypes, BoxTypes.id == Orders.box_type_id).\
            join(OrderStatuses, OrderStatuses.id == Orders.status).\
            join(Users, Users.id == Orders.from_user).\
            filter(Orders.deleted_at == None).\
            filter(Orders.status == OrderStatuses.status_default().id).\
            order_by(asc(Orders.date_created)).all()

        date_today = datetime.now()

        day_number_now = datetime.strftime(date_today, "%d")

        month_now_str = datetime.strftime(date_today, "%m")
        year_now_str = datetime.strftime(date_today, "%Y")

        days_max = monthrange(int(year_now_str), int(month_now_str))[1]

        day_number_next = int(day_number_now)+1
        if (day_number_next>days_max):
            #если след день приходит на начало след месяца берём первое число как след день
            day_number_next = 1

        order_list = []

        date_tommorrow = date_today + timedelta(days=1)
        #TODO: Заменить формат
        # date_tommorrow = datetime.datetime.strptime(date_tommorrow, '%Y-%m-%dT%H:%M:%S')
        weekday_tomorrow = str(date_tommorrow.strftime('%A')).lower()

        print(f"date today: {date_today}\ndate tommorrow: {date_tommorrow}")
        print(f"weekday tomorrow: {weekday_tomorrow}")
        print(f"next day num {day_number_next}")

        for order in orders:
            #Преобразовать интервал в форму списка
            flag_day_set = False

            match order[1].interval_type:
                case IntervalStatuses.MONTH_DAY:
                    interval = [int(x) for x in str(order[1].interval).split(', ') ]
                    if day_number_next in interval:
                        print(f"Order {order[0].order_num} by month in interval")
                        flag_day_set = True
                        order[0].day = date_tommorrow

                case IntervalStatuses.WEEK_DAY:
                    interval = [str(order[1].interval).split(', ')]
                    if weekday_tomorrow in interval:
                        print(f"Order {order[0].order_num} by weekday in interval")
                        flag_day_set = True
                        order[0].day = date_tommorrow

                case _:
                    #TODO: Проверка остальных интервалов
                    pass
                
            if flag_day_set:
                order[0].update_status(OrderStatuses.status_awating_confirmation().id)
                #TODO: Отправить уведомление пользователю
                session.commit()
                order_list.append(order[0])

        return order_list