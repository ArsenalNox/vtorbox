"""
Содержит в себе ендпоинты по заявкам
"""
from operator import contains
import re 

from app import Tags
from typing import Annotated, List, Union, Optional


from fastapi import APIRouter, Body, Security, Query, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from calendar import monthrange
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, asc, desc, or_

from app.validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut,
    OrderUpdate, FilteredOrderOut, UserIdMultiple
)

from app.auth import (
    get_current_user
)

from app.models import (
    engine, Orders, Users, Session, 
    Address, UsersAddress, BoxTypes,
    OrderStatuses, OrderStatusHistory,
    ORDER_STATUS_DELETED, ORDER_STATUS_AWAITING_CONFIRMATION,
    IntervalStatuses, ROLE_ADMIN_NAME, Regions, WeekDaysWork,
    DaysWork, ORDER_STATUS_AWAITING_PAYMENT, Payments, PaymentClientData,
    OrderComments, get_user_from_db_secondary, OrderChangeHistory,
    BotSettings, RegionalBoxPrices
    )

from app.utils import (
    send_message_through_bot, generate_time_intervals
    )

router = APIRouter()


@router.get('/orders/filter/', tags=[Tags.orders, Tags.admins])
async def get_filtered_orders(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],
    by_date: bool = False, 
    datetime_start: datetime = None,
    datetime_end: datetime = None,
    date_asc: bool = False,

    state: str = None,
    state_id: UUID = None,
    
    show_deleted: bool = False,

    filter_date: str = None,

    limit: int = 5,
    page: int = 0,
    region_id: UUID = None,
    
    show_only_active: bool = False
)->FilteredOrderOut:
    """
    Получение заявок по фильтру
    - **by_date**: показывать заявки на промежуток дат
    - **datetime_start**: дата начала фильтра
    - **datetime_end**: дата конца фильтра
    
    - **date_asc**: [bool] восходящий сорт по дате создание или нисходящий
    - **state**: фильтр статуса по названию статуса
    - **state_id**: фильтр статуса по id статуса
    
    - **show_deleted**: показывать удалённые заявки
    - **filter_date**: показывать заявки только на одну конкретную дату
    - **region_id**: айди региона заявки 

    - **show_only_active**: [bool] показывать только заявки категории активные
    """
    with Session(engine, expire_on_commit=False) as session:

        orders = session.query(Orders).\
            join(Address, Address.id == Orders.address_id).\
            outerjoin(BoxTypes, BoxTypes.id == Orders.box_type_id).\
            join(Users, Users.id == Orders.from_user).\
            join(Regions, Regions.id == Address.region_id).\
            enable_eagerloads(False)
        
        if state:
            status_query = session.query(OrderStatuses).filter_by(status_name=state).first()
            orders = orders.filter(Orders.status == status_query.id)

        if state_id:
            orders = orders.filter(Orders.status == state_id)

        if date_asc:
            orders = orders.order_by(asc(Orders.date_created))
        else:
            orders = orders.order_by(desc(Orders.date_created))

        if not show_deleted:
            orders = orders.filter(Orders.deleted_at == None)
        
        if by_date:
            orders = orders.filter(Orders.day >= datetime_start)
            orders = orders.filter(Orders.day <= datetime_end)

        if filter_date:
            try:
                date = datetime.strptime(filter_date, "%Y-%m-%d")
            except Exception as err:
                return JSONResponse({
                    "message": f"{err}"
                }, 422)

            date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_tommorrow = date + timedelta(days=1)
            orders = orders.filter(Orders.day >= date)
            orders = orders.filter(Orders.day <= date_tommorrow)

        if region_id:
            orders = orders.filter(Regions.id == region_id)

        if show_only_active: 
            orders = orders.filter(or_(
                Orders.status == OrderStatuses.status_accepted_by_courier().id,
                Orders.status == OrderStatuses.status_default().id,
                Orders.status == OrderStatuses.status_processing().id,
                Orders.status == OrderStatuses.status_awating_confirmation().id,
                Orders.status == OrderStatuses.status_confirmed().id,
                Orders.status == OrderStatuses.status_awaiting_payment().id,
                Orders.status == OrderStatuses.status_payed().id
            ))

        global_orders_count = orders.count()
        
        if limit == 0:
            orders = orders.all()
        else:
            orders = orders.offset(page  * limit).limit(limit).all()

        total = len(orders)

        # return_data = Orders.process_order_array([orders], simple_load=True)
        if total != 0:
            return_data = []
            for _order in orders:
                return_data.append(Orders.process_order_array([[_order]], simple_load=True)[0])
        else:
            return_data = []

        return {
            "orders": return_data,
            "global_count": global_orders_count,
            "count": total
        }


@router.get('/orders/{order_id}', tags=[Tags.orders, Tags.bot])
async def get_order_by_id(
        current_user: Annotated[UserLoginSchema, Security(get_current_user)],
        order_id: UUID
    ) -> OrderOut:
    """
    Получение конкретной заявки
    """
    with Session(engine, expire_on_commit=False) as session:
        #Получение конкретной заявки

        order = session.query(Orders).\
            where(Orders.id == order_id).enable_eagerloads(False).first()
        
        if not order:
            return JSONResponse({
                "message": "not found"
            },status_code=404)

        return_data = Orders.process_order_array([[order]])
        return return_data[0]


@router.get('/users/orders/', tags=[Tags.bot, Tags.orders], response_description="Список заявок пользователя")
async def get_user_orders(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],
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

        #TODO: сократить то что идёт ниже, желательно на хотя бы 70%

        orders = session.query(Orders).\
            enable_eagerloads(False).\
            filter_by(from_user = user.id)

        if order_id:
            orders = orders.where(Orders.id == order_id)

        if orders_id:
            orders = orders.filter(Orders.id.in_(orders_id))
            
        if order_num:
            orders = orders.where(Orders.order_num == order_num)

        if user_order_num:
            orders = orders.where(Orders.user_order_num == user_order_num)

        if order_nums:
            orders = orders.filter(Orders.order_num.in_(order_nums))
        
        orders = orders.order_by(asc(Orders.date_created)).all()

        return_data = []
        for order in orders:
            order.manager_info
            order_parent_data = jsonable_encoder(order)
            order_data = OrderOut(**order_parent_data)

            order_data.tg_id = user.telegram_id

            order_data.address_data = order.address
            order_data.interval = str(order.address.interval).split(', ')
            order_data.user_data = user
            order_data.box_data = order.box
            
            s_query = session.query(OrderStatuses).filter_by(id=order.status).first()
            order_data.status_data = s_query

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
            
        warnings = []
        container = None
        if order_data.box_name:
            container = session.query(BoxTypes).filter_by(box_name = order_data.box_name).first()
            if not container:
                warnings.append(f"no {order_data.box_name} container found")
        if order_data.box_type_id:
            container = session.query(BoxTypes).filter_by(id = order_data.box_type_id).first()
            if not container:
                warnings.append(f"no {order_data.box_type_id} container found")

        order_data.day = datetime.strptime(order_data.day, "%Y-%m-%d").date()

        count = session.query(Orders.id).where(Orders.from_user == user.id).count()

        new_order = Orders(
            from_user   = user.id,
            address_id  = order_data.address_id,
            day         = order_data.day,
            comment     = order_data.comment,
            # box_type_id = container.id,
            # box_count   = order_data.box_count,
            status      = OrderStatuses.status_default().id,
            date_created = datetime.now(),
            user_order_num = count + 1,
            manager_id = Users.get_random_manager()
        )
        if user.telegram_id:
            new_order.tg_id = user.telegram_id

        print("adding container")
        print(container)
        if container:
            new_order.box_type_id = container.id
            if order_data.box_count:
                print(f'box count {order_data.box_count}')
                new_order.box_count = order_data.box_count
            else:
                print("default box count")
                new_order.box_count = 1

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
        "data_given": order_data,
        "warnings": warnings
    }


@router.get("/orders/{order_id}/history", tags=[Tags.orders, Tags.bot])
async def get_order_status_history(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],
    order_id: UUID,
    tg_id: Optional[int] = None
    ):
    """
    Получение истории изменения статуса заявки
    - **tg_id**: int телеграм айди пользователя (при наличии админской роли параметр необязателен)
    - **user_id**:  UUID пользователя (при наличии админской роли параметр необязателен)

    История возвращается с датой по убыванию (новое сначала)
    """

    with Session(engine, expire_on_commit=False) as session:
        if ROLE_ADMIN_NAME in current_user.roles:
            order = session.query(Orders).\
                join(Users, Users.id == Orders.from_user).\
                where(Orders.id == order_id).\
                where(Orders.deleted_at == None).\
                first()
        else:
            if tg_id == None:
                print("NONE")

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
    order_id: UUID,
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    ):
    """
    Удаление заявки
    **order_id** - UUID заявки
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
    send_message: bool = True
):
    """
    Обновление/Установка статуса заявки
    - **order_id**: UUID заявки
    - **status_text**: status_name статсуа в бд
    - **status_id**: UUID статуса в бд
    в запросе обязательно нужно передать либо **status_text** либо **status_id**
    """
    if (not status_text) and (not status_id):
        raise HTTPException(
            status_code=422,
            detail="необходимо поле status_text или status_id"
        )
    
    status_query = None
    with Session(engine, expire_on_commit=False) as session:
        
        if status_text:
            status_query = session.query(OrderStatuses).filter_by(status_name = status_text).enable_eagerloads(False).first()
        elif status_id:
            status_query = session.query(OrderStatuses).filter_by(id = status_id).enable_eagerloads(False).first()

        if not status_query:
            return JSONResponse({
                "detail": "status not found"
            },status_code=404)
        
        order_query = session.query(Orders).filter_by(id = order_id).\
            where(Orders.deleted_at == None).enable_eagerloads(False).first()

        if not order_query:
            return JSONResponse({
                "detail": "order not found"
            },status_code=404)

        if order_query.status == status_query.id:
            return JSONResponse({
                "detail": "Status is identical, change not saved"
            }, 200)

        error_sending_message = False

        #если статус меняется в "ожидается оплата" - отправить сообщение об оплате
        if status_query.status_name == ORDER_STATUS_AWAITING_PAYMENT['status_name']: 
            if not (order_query.box_type_id and order_query.box_count):
                return JSONResponse({
                    "detail": "Перед вызовом оплаты необходимо указать тип контейнера и кол-во контейнера"
                }, 422)

            try:
                if order_query.user.allow_messages_from_bot:

                    message_text = str(BotSettings.get_by_key('MESSAGE_PAYMENT_REQUIRED_ASK').value)
                    message_text = message_text.replace("%ORDER_NUM%", str(order_query.order_num))
                    message_text = message_text.replace("%ADDRESS_TEXT%", str(order_query.address.address))
                    amount = 0
                    box_price = None

                    if not (order_query.box_count == None) and not (order_query.box_type_id == None):
                        reg_price = session.query(RegionalBoxPrices).filter_by(box = order_query.box_type_id).\
                            filter_by(region_id = order_query.address.region_id).enable_eagerloads(False).first()
                        if reg_price:
                            box_price = reg_price.price
                        
                        if box_price == None:
                            print("USING DEFAULT PRICING FOR BOX")
                            box_price = order_query.box.pricing_default
                        
                        print(order_query.box_count)
                        amount = box_price*order_query.box_count
                        print(f"AMOUNT: {amount}")

                    message_text = message_text.replace("%AMOUNT%", f'{amount} руб.')

                    #"От вас требуется оплата заявки (%ORDER_NUM%) по адресу (%ADDRESS_TEXT%) на сумму %AMOUNT%"

                    send_message_through_bot(
                        order_query.user.telegram_id,
                        message=message_text,
                        btn={
                            "inline_keyboard" : [
                                [{
                                    "text" : "❌ Не согласен",
                                    "callback_data": f'accept_deny_False_False_{order_id}',
                                }],
                                [{
                                    "text" : "Перейти к оплате",
                                    "callback_data": f"payment_False_{order_query.id}",
                                }],
                        ]}
                    )

            except Exception as err:
                error_sending_message = True
                print(f"Не удалось отправить сообщение пользователю: {err}")

        old_status_query = session.query(OrderStatuses).filter_by(id=order_query.status).enable_eagerloads(False).first()
        new_data_change = OrderChangeHistory(
            from_user_id = current_user.id,
            order_id = order_query.id,
            attribute = 'status',
            old_content = old_status_query.status_name,
            new_content = status_query.status_name,
        )
        order_query = order_query.update_status(status_query.id, (status_query.message_on_update and send_message))
        session.add(new_data_change)
        session.commit()

        return


@router.put('/orders/{order_id}', tags=[Tags.bot, Tags.orders])
async def update_order_data(
        current_user: Annotated[UserLoginSchema, Security(get_current_user)],
        order_id: UUID, 
        new_order_data: OrderUpdate,
        change_from_user: Annotated[UserIdMultiple, Depends(get_user_from_db_secondary)]
    )->OrderOut:
    """
    Обновить данные заявки
    - **order_id**: uuid заявки
    """
    with Session(engine, expire_on_commit=False) as session:

        order_query = session.query(Orders).filter_by(id=order_id)\
            .where(Orders.deleted_at == None).first()

        if not order_query:
            return JSONResponse({
                "detail": "Order not found"
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
                    "detail": f"no '{new_order_data.box_name}' container found"
                }, status_code=422)

            elif attr == "box_name":
                order_query.box_type_id = container.id
                continue

            if attr == "address_id" and (not address_query):
                return JSONResponse({
                    "detail": "Address not found"
                },status_code=404)

            if attr == "box_count" and (new_order_data.box_count < 1):
                return JSONResponse({
                    "detail": "Cannot set box_count below 1"
                }, status_code=422)

            comment_types = ["comment_manager", "comment_courier", "comment"]
            if attr in comment_types and value:
                print("Setting new comment to order")
                from_user_id = None
                if change_from_user:
                    print(f"comment from {change_from_user.id}")
                    from_user_id = change_from_user.id

                old_comment = getattr(order_query, attr)
                if old_comment:
                    old_comment_to_history = OrderComments(
                        order_id = order_query.id,
                        from_user = from_user_id,
                        content = getattr(order_query, attr),
                        type = attr
                    )
                    session.add(old_comment_to_history)             

            if not(getattr(order_query, attr) == value):
                new_data_change = OrderChangeHistory(
                    from_user_id = change_from_user.id if change_from_user else current_user.id,
                    order_id = order_query.id,
                    attribute = attr,
                    old_content = getattr(order_query, attr),
                    new_content = value,
                    date_created = datetime.now()
                )
                session.add(new_data_change)
                setattr(order_query, attr, value)

        session.commit()

        order_query = session.query(Orders, Address, BoxTypes, OrderStatuses, Users).\
            join(Address, Address.id == Orders.address_id).\
            outerjoin(BoxTypes, BoxTypes.id == Orders.box_type_id).\
            join(OrderStatuses, OrderStatuses.id == Orders.status).\
            join(Users, Users.id == Orders.from_user).\
            where(Orders.id == order_id).\
            order_by(asc(Orders.date_created)).first()

        return_data = Orders.process_order_array([order_query])

        return return_data[0]


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
async def process_current_orders(

):
    """
    Обработка всех доступных заявок, высчитывание следующего дня забора заявки
    """
        
    with Session(engine, expire_on_commit=False) as session:
        orders = session.query(Orders).\
            filter(Orders.deleted_at == None).\
            filter(Orders.status == OrderStatuses.status_processing().id).\
            order_by(asc(Orders.date_created)).enable_eagerloads(False).all()

        date_today = datetime.now()
        date_today = date_today.replace(hour=0, minute=0, second=0, microsecond=0)

        day_number_now = datetime.strftime(date_today, "%d")
        month_now_str = datetime.strftime(date_today, "%m")
        year_now_str = datetime.strftime(date_today, "%Y")

        days_max = monthrange(int(year_now_str), int(month_now_str))[1]

        day_number_next = int(day_number_now)+1
        if (day_number_next>days_max):
            #если след день приходит на начало след месяца берём первое число как след день
            day_number_next = 1

        order_list_to_generate_time_ranges = []

        date_tommorrow = date_today + timedelta(days=1)
        weekday_tomorrow = str(date_tommorrow.strftime('%A')).lower()
        date_num_tommorrow = datetime.strftime(date_tommorrow, "%d-%m-%Y")

        print(f"date today: {date_today}\ndate tommorrow: {date_tommorrow}")
        print(f"weekday tomorrow: {weekday_tomorrow}")
        print(f"next day num {day_number_next}")

        date_search_query = session.query(DaysWork)
        date_search_query = date_search_query.filter(
                DaysWork.date >= date_today, 
                DaysWork.date <= date_tommorrow
            ).first()
        
        weekday_search_query = session.query(WeekDaysWork).\
            filter(WeekDaysWork.weekday == date_today.strftime('%A')).\
            first()

        if date_search_query or weekday_search_query:
            return JSONResponse({
                "detail": "Текущая дата помечена как нерабочий день. Генерация пула не запущена"
            })

        for order in orders:
            flag_day_set = False

            if order.address.region.work_days == None:
                continue

            days_allowed = str(order.address.region.work_days).split(' ')

            
            print("Allowed days in order region:")
            print(days_allowed)
            print(order.day, date_today)
            print(order.day > date_today)
            if order.day > date_today:
                print("DAY LARGER")
                order_day_num = datetime.strftime(order.day, "%d-%m-%Y")
                print(order_day_num, date_num_tommorrow)
                if order_day_num == date_num_tommorrow:
                    print("ORDER DATE ALREADY SET TO TOMMORROW")
                    flag_day_set = True
            else:
                match order.address.interval_type:
                    case IntervalStatuses.MONTH_DAY:
                        interval = [int(x) for x in str(order.address.interval).split(', ') ]
                        if day_number_next in interval:
                            print(f"Order {order.order_num} by month in interval")
                            flag_day_set = True
                            order.day = date_tommorrow

                    case IntervalStatuses.WEEK_DAY:
                        interval = [str(order.address.interval).split(', ')]

                        if not(weekday_tomorrow in days_allowed):
                            continue

                        if not(weekday_tomorrow in interval):
                            continue
                        
                        print(f"Order {order[0].order_num} by weekday in interval")
                        flag_day_set = True
                        order.day = date_tommorrow

                    case _:
                        if order.day == None:
                            continue
                        order_day_num = datetime.strftime(order.day, "%d-%m-%Y")
                        print("Checking if order date is set to tommorrow")
                        print(order_day_num, date_num_tommorrow)
                        if order_day_num == date_num_tommorrow:
                            print("ORDER DATE ALREADY SET TO TOMMORROW")
                            flag_day_set = True
            

            if flag_day_set:
                order_list_to_generate_time_ranges.append(order)

        if len(order_list_to_generate_time_ranges) < 1:
            print("No orders to process, skip generation")
            return order_list_to_generate_time_ranges

        class Route_data():
            orders: List

        route_data = Route_data()
        route_data.orders = order_list_to_generate_time_ranges

        order_list_to_generate_time_ranges = generate_time_intervals(route_data)

        for order in order_list_to_generate_time_ranges:
            print("Updating order status")

            old_status_query = session.query(OrderStatuses).filter_by(id=order.status).first()
            new_data_change = OrderChangeHistory(
                order_id = order.id,
                attribute = 'status',
                old_content = old_status_query.status_name,
                new_content = OrderStatuses.status_awating_confirmation().status_name,
            )
            print('---oldstatus')
            print(order.status)
            print(OrderStatuses.status_awating_confirmation().id)
            print(OrderStatuses.status_awating_confirmation().status_name)
            query = session.query(Orders).\
            filter_by(id=order.id).update({"status": OrderStatuses.status_awating_confirmation().id})

            session.add(new_data_change)
            print(order.status)

            
            if not order.user.allow_messages_from_bot and order.user.telegram_id:
                continue
            else:
                send_message_through_bot(
                    order.user.telegram_id,
                    message=f"От вас требуется подверждение заявки ({order.order_num}) по адресу ({order.address.address}) по временному итервалу {order.time_window}",
                    btn={
                        "inline_keyboard" : [
                        [{
                            "text" : "Подтвердить",
                            "callback_data": f"confirm_order_{order.id}",
                        }],
                        [{
                            "text" : "Отказаться",
                            "callback_data": f"deny_order_{order.id}",
                        }]
                    ]}
                )

        session.commit()

        return order_list_to_generate_time_ranges


@router.get('/check-intervals')
async def check_order_intervals():
    """
    Идентичная генерации пула, только создаёт заявку из интервала адресов
    """
    with Session(engine, expire_on_commit=False) as session:
        date_today = datetime.now()
        date_today = date_today.replace(hour=0, minute=0, second=0, microsecond=0)

        day_number_now = datetime.strftime(date_today, "%d")
        month_now_str = datetime.strftime(date_today, "%m")
        year_now_str = datetime.strftime(date_today, "%Y")

        date_tommorrow = date_today + timedelta(days=1)
        weekday_tomorrow = str(date_tommorrow.strftime('%A')).lower()

        addresses_query = session.query(Address).filter(Address.interval != None).all()
        for address in addresses_query:
            print(f"address: {address.address}")
            print(f"inteval: {address.interval}")
            print(f"region work days: {address.region.work_days}")
            
            if not address.region.is_active:
                print("Region is not active")
                continue

            #Проверить, есть ли заявка на этот адрес (созданная)
            order_exists = False
            if len(address.orders)>0:
                for order in address.orders:
                    #Проверить, на сегодня ли эта заявка
                    order_day = order.day
                    order_day = order_day.replace(hour=0, minute=0, second=0, microsecond=0)
                    if order_day == date_tommorrow:
                        order_exists = True
                        break
            
            if order_exists: 
                print("Order exists, skipping")
                continue
            
            if not (weekday_tomorrow in address.interval):
                print("weekday tomorrow not in addres intreval")
                continue

            if not weekday_tomorrow in address.region.work_days:
                print("weekday tomorrow not in region workd days")
                continue

            #Если заявки нет - создать её в статус в работе
            user_id = session.query(UsersAddress).filter_by(address_id=address.id).first().user_id
            count = session.query(Orders.id).where(Orders.from_user == user_id).count()
            new_order = Orders(
                from_user   = user_id,
                address_id  = address.id,
                day         = date_tommorrow,
                comment     = 'Создана из интервала',
                status      = OrderStatuses.status_processing().id,
                date_created = datetime.now(),
                user_order_num = count + 1,
                manager_id = Users.get_random_manager()
            )
            session.add(new_order)
            session.commit()

            print('')




@router.post('/resend-notify')
async def resend_order_confirm_notify(
    final_check: bool = False
):
    with Session(engine, expire_on_commit=False) as session:
        orders = session.query(Orders).\
            filter(Orders.deleted_at == None).\
            filter(Orders.status == OrderStatuses.status_awating_confirmation().id).\
            order_by(asc(Orders.date_created)).all()
        
        for order in orders:
            if not order.user.allow_messages_from_bot and order.user.telegram_id:
                continue
            else:
                send_message_through_bot(
                    order.user.telegram_id,
                    message=f"От вас требуется подверждение заявки ({order.order_num}) по адресу ({order.address.address}) по временному итервалу {order.time_window}",
                    btn={
                        "inline_keyboard" : [
                        [{
                        "text" : "Подтвердить",
                        "callback_data": f"confirm_order_{order.id}",
                        }],
                        [{
                            "text" : "Отказаться",
                            "callback_data": f"deny_order_{order.id}",
                        }]
                    ]}
                )