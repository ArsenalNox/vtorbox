"""
Эндпоинты для курьеров
"""

from app import Tags

import re 

from typing import Annotated, List, Union, Optional

from fastapi import APIRouter, Body, Security, Query
from fastapi.responses import JSONResponse

from calendar import monthrange
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, asc, desc

from app.validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut, OrderUpdate, CourierCreationValidator,
    UserOut, CourierOut
)

from app.auth import (
    get_current_user
)

from app.models import (
    engine, Orders, Users, Session, 
    Address, UsersAddress, BoxTypes,
    OrderStatuses, OrderStatusHistory, Regions,
    ORDER_STATUS_DELETED, ORDER_STATUS_AWAITING_CONFIRMATION, 
    ORDER_STATUS_CONFIRMED, IntervalStatuses, 
    ROLE_ADMIN_NAME, ORDER_STATUS_COURIER_PROGRESS, 
    ROLE_COURIER_NAME, Permissions, Roles,
    Routes
)


router = APIRouter()

@router.get('/couriers', tags=[Tags.couriers, Tags.admins])
async def get_list_of_couriers(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin", "manager"])],
)->List[CourierOut]:
    """
    Получить список курьеров
    """
    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Users)

        roles_user_query = session.query(Users.id).\
            join(Permissions, Permissions.user_id == Users.id).\
            join(Roles, Roles.id == Permissions.role_id).\
            where(Roles.role_name == ROLE_COURIER_NAME).subquery()

        query = query.filter(Users.id.in_(roles_user_query))

        query = query.all()
        return_data = []
        for user in query:
            
            user_data = CourierOut(**user.__dict__)
            scopes_query = session.query(Permissions, Roles.role_name).filter_by(user_id=user.id).join(Roles).all()
            user_data.roles = [role.role_name for role in scopes_query]
            return_data.append(user_data)

            routes_query = session.query(Routes).filter_by(courier_id = user.id).all()
            user_data.assigned_routes = routes_query


        return return_data


@router.post('/courier', tags=[Tags.couriers])
async def create_new_courier(
        current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
        tg_id: int
    ):
    """
    Назначить роль курьера пользователю
    """
    user_query = Users.get_or_404(t_id=tg_id)
    if not user_query:
        return JSONResponse({
            "message": "User not found"
        }, status_code=404)
    
    with Session(engine, expire_on_commit=False) as session:

        scopes_query = session.query(Permissions, Roles.role_name).filter_by(user_id=user_query.id).join(Roles).all()
        roles = [role.role_name for role in scopes_query]
        if not (ROLE_COURIER_NAME in roles):
            role_query = Roles.courier_role()
            user_role = Permissions(
                user_id = user_query.id,
                role_id = role_query
            )

            session.add(user_role)
            session.commit()
        else:
            return JSONResponse({
                "message": f"User already has role {ROLE_COURIER_NAME}"
            }, 204)

    return JSONResponse({
        "message": "role added"
    }, status_code=200)


@router.get('/courier/{courier_tg_id}/info', tags=[Tags.couriers])
async def get_courier_info_by_id():
    pass


@router.get('/courier/orders', tags=[Tags.couriers, Tags.orders])
async def get_list_of_avaliable_orders(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],

    limit: int = 10,
    page: int = 0,

    regions_ids: List[UUID] = Query(None),
    regions: List[str] = Query(None),
    statuses_ids: List[UUID] = Query(None),
    statuses: List[str] = Query([ORDER_STATUS_CONFIRMED['status_name']])
):
    """
    ## УСТАРЕЛО
    Получить доступные для вывоза заявки курьером

    Опции фильтра:
    - **regions_ids**: List[UUID] - Лист UUID регионов
    - **regions**: List[str] - Лист наименований регионов
    - **statuses_ids**: List[UUID] - Лист UUID статусов 
    - **statuses**: List[str] - Лист наименований статусов (status_name). По умолчанию равен "подтверждена"

    
    для получения всех заявок без пагинации, следует указать limit=0.
    """
    #TODO Тут ведь должны быть только заявки со статусом подтверждены клиентом, да? Зачем тогда фильтр по статусу

    with Session(engine, expire_on_commit=False) as session:
        query_orders = session.query(Orders, Address, BoxTypes, OrderStatuses, Regions).\
            join(Address, Address.id == Orders.address_id).\
            outerjoin(BoxTypes, BoxTypes.id == Orders.box_type_id).\
            join(OrderStatuses, OrderStatuses.id == Orders.status).\
            join(Regions, Regions.id == Address.region_id).\
            where(Orders.deleted_at == None)

        if regions_ids:
            query_orders = query_orders.filter(Regions.id.in_(regions_ids))

        if regions:
            for region_name in regions:
                query_orders = query_orders.filter(Regions.name_full.ilike(f"%{region_name}%"))

        if statuses_ids:
            query_orders = query_orders.filter(OrderStatuses.id.in_(statuses_ids))

        if statuses:
            for status_name in statuses:
                query_orders = query_orders.filter(OrderStatuses.status_name.ilike(f"%{status_name}%"))
        
        global_orders_count = query_orders.count()

        if limit == 0:
            orders = query_orders.order_by(asc(Orders.date_created)).all()
        else:
            orders = query_orders.order_by(asc(Orders.date_created)).offset(page  * limit).limit(limit).all()

        total = len(orders)

        return_data = []

        #TODO: Рефактор сбора инфы о заявках в метод заявок?
        #Сбор инфы
        for order in orders:
            order_data = OrderOut(**order[0].__dict__)

            try:
                order_data.address_data = order[1]
                order_data.address_data.region = order[1].region
                order_data.address_data.region.work_days = str(order[1].region.work_days).split(' ')

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
            
            try:
                order_data.user_data = order[4]
            except IndexError:
                order_data.user_data = None

            return_data.append(order_data.model_dump())

        return {
            "orders": return_data,
            "global_count": global_orders_count,
            "count": total
        }


@router.get('/courier/orders/my', tags=[Tags.couriers, Tags.orders])
async def get_list_of_accepted_orders():
    pass


@router.post('/courier/order/{order_id}/accept', tags=[Tags.couriers, Tags.orders])
async def accept_order_by_courier(
        current_user: Annotated[UserLoginSchema, Security(get_current_user)],
        order_id: UUID,
        courier_tg_id: int
    ):
    """
    Принять заявку курьером
    """
    status_query = None
    with Session(engine, expire_on_commit=False) as session:
        
        status_query = session.query(OrderStatuses).filter_by(status_name = ORDER_STATUS_COURIER_PROGRESS['status_name']).first()

        courier_query = Users.get_or_404(t_id=courier_tg_id)

        if not status_query:
            return JSONResponse({
                "message": "status error (status not found)"
            }, status_code=404)

        if not courier_query:
            return JSONResponse({
                "message": f"courier not with tg id: '{courier_tg_id}' found"
            }, status_code=404)

        
        order_query = session.query(Orders).filter_by(id = order_id).\
            where(Orders.deleted_at == None).first()

        if not order_query:
            return JSONResponse({
                "message": "order not found"
            },status_code=404)

        order_query.status = status_query.id
        order_query.courier_id = courier_query.id

        status_update = OrderStatusHistory(
            order_id = order_query.id,
            status_id = status_query.id,
            date = datetime.now()
        )

        session.add(status_update)
        session.add(order_query)
        session.commit()

    pass


@router.post('/courier/order/{order_id}/comment', tags=[Tags.couriers, Tags.orders])
async def post_order_comment_by_courier():
    """
    Оставить комментарий к заявке курьером
    """