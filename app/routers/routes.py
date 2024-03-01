#DONE генерация кластеров через алгоритм (другой)
#TODO распределение кластеров по маршрутам
#DONE раскидывание маршрутов по курьерам
#DONE редактирование маршрутов

import requests
import os, uuid
import re 
import math

from typing import Annotated, List, Tuple, Dict, Optional
from fastapi.responses import JSONResponse

import datetime as dt
from datetime import datetime, timedelta


from app import CODER_KEY, CODER_SETTINGS

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
    RegionOut, AddressDaysWork, UserOut
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

from ..auth import (
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
    IntervalStatuses, ROLE_ADMIN_NAME, ROLE_COURIER_NAME,
    Routes, RoutesOrders
    )



router = APIRouter()


async def write_routes_to_db(routes):
    """
    Записать список маршрутов в бд
    """
    errors = []
    with Session(engine, expire_on_commit=False) as session:
        for route in routes:
            new_route = Routes(
                courier_id = route['courier']
            )

            session.add(new_route)
            session.commit()

            for order in route['orders']:
                new_route_order = RoutesOrders(
                    route_id = new_route.id,
                    order_id = order['id']
                )

                order_update = Orders.query_by_id(order['id'])[0]
                order_update.courier_id = route['courier']
                if not (order_update.status == OrderStatuses.status_accepted_by_courier().id):
                    order_update.update_status(OrderStatuses.status_accepted_by_courier().id)

                session.add(new_route_order)
                session.add(order_update)

        session.commit()


@router.post('/routes/generate', tags=[Tags.routes, Tags.admins, Tags.managers])
async def generate_routes_today(
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    group_by: str = 'regions',
    statuses_list = List[UUID],
    couriers_id = List[UUID],
    write_after_generation: bool = False
):
    """
    сформировать группы заявок в машруты
    - **group_by**: [str] - тип группировки заявок (по региону, по кластерам)
    - **statuses_list** [List[UUID]] - лист айди обрабатываемых статусов, по умолчанию "принят клиентом"
    - **couriers_id** [List[UUID]] - лист айди курьеров, которым выдадут маршруты
    - **write_after_generation** [bool] - записать ли результат сразу в бд
    """
    with Session(engine, expire_on_commit=False) as session:
        order_pool_awaliable = [] #список доступных для вывоза заявок

        orders = session.query(Orders, Address, BoxTypes, OrderStatuses, Users, Regions).\
            join(Address, Address.id == Orders.address_id).\
            outerjoin(BoxTypes, BoxTypes.id == Orders.box_type_id).\
            join(OrderStatuses, OrderStatuses.id == Orders.status).\
            join(Users, Users.id == Orders.from_user).\
            join(Regions, Regions.id == Address.region_id).\
            filter(Orders.deleted_at == None).\
            filter(Orders.status == OrderStatuses.status_confirmed().id)

        
        if group_by == 'regions':
            orders = orders.order_by(asc(Regions.name_full))
        else:
            orders = orders.order_by(asc(Orders.date_created))


        global_orders_count = orders.count()

        orders = orders.all()

        total = len(orders)

        order_pool_awaliable = Orders.process_order_array(orders)
        
        couriers = session.query(Users)
        roles_user_query = session.query(Users.id).\
            join(Permissions, Permissions.user_id == Users.id).\
            join(Roles, Roles.id == Permissions.role_id).\
            where(Roles.role_name == ROLE_COURIER_NAME).subquery()
        couriers = couriers.filter(Users.id.in_(roles_user_query)).all()
        
        if len(couriers)<1:
            return JSONResponse({
                "message": "В бд отсутствуют курьеры"
            }, status_code=403)

        print(couriers)
        
        routes = []

        i=0 #номер начальной заявки
        step = math.ceil(len(order_pool_awaliable)/len(couriers)) #сколько заявок давать курьеру

        #TODO Второй алгоритм выборки по кластерам
        #Проходим по всем курьерам 
        for courier in couriers:
            print(i, step, step+i)
            
            #делаем срез массива с заявками
            order_for_route = order_pool_awaliable[i:step+i]

            print(len(order_for_route))

            if len(order_for_route)==0:
                break

            routes.append({
                "courier": courier.id,
                "orders": order_for_route
            })

            i += step
        
        #Если есть остаток заявок, которые не попали в пул, добавить их в последний маршрут
        if step+i < len(order_pool_awaliable):
            routes[-1]['orders'].append(order_pool_awaliable[step+i:-1])

        if write_after_generation:
            await write_routes_to_db(routes)

        return {
            "global_count": global_orders_count,
            "count": total,
            "routes": routes
        }


@router.get("/routes", tags=[Tags.routes, Tags.admins, Tags.managers])
async def get_routes(
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    date: Optional[datetime] = None,
    courier_id: Optional[UUID] = None
):
    """
    получить маршруты

    - **date**: [datetime] - дата на получение маршрутов, по умолчанию получаются все маршруты
    """
    with Session(engine, expire_on_commit=False) as session:
        routes = session.query(Routes)

        if date:
            routes = routes.filter(Routes.date_created > date)
        
        if courier_id: 
            routes = routes.filter(Routes.courier_id == courier_id)

        routes = routes.order_by(asc(Routes.date_created)).all()

        return routes
    

@router.patch("/routes/{route_id}", tags=[Tags.routes, Tags.admins, Tags.managers])
async def update_route_orders(
    route_id: UUID,
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    orders_to_delete: List[UUID] = Query(None),
    orders_to_add: List[UUID] = Query(None),
):
    """
    Обновить заявки в маршруте
    - **orders_to_delete**: [List[UUID]] - Лист заявок, которые перенесутся в отменённые и удалятся из маршрута
    - **orders_to_add**: [List[UUID]] - Лист заявок, которые удалятся из остальных маршрутов на сегодня и добавяться в этот указанный маршрут

    Заявки перебрасываются только из маршрутов, чей день совпадает с сегодняшней датой
    """
    date_today = dt.date.today()
    print(f"date today: {date_today}")
    with Session(engine, expire_on_commit=False) as session:

        route_query = session.query(Routes).where(Routes.id==route_id).first()
        if not route_query:
            return JSONResponse({
                "message": f"Route {route_id} not found"
            },status_code=404)

        routes_today = session.query(Routes).\
            filter(Routes.date_created > date_today).all()

        if orders_to_delete:
            for route in routes_today:
                for order_id in orders_to_delete:
                    for order_route in route.orders:
                        if order_route.order_id == order_id:
                            delete_query = session.query(RoutesOrders).where(RoutesOrders.id==order_route.id).delete()
                            session.commit()

        if orders_to_add:   
            for route in routes_today:
                for order_id in orders_to_add:
                    for order_route in route.orders:
                        if order_route.order_id == order_id:
                            delete_query = session.query(RoutesOrders).where(RoutesOrders.id==order_route.id).delete()
                            session.commit()

            for order_id in orders_to_add:
                new_route_order = RoutesOrders(
                    route_id = route_id,
                    order_id = order_id
                )

                session.add(new_route_order)

                update_query = session.query(Orders).where(Orders.id == order_id).first()
                update_query.courier_id = route_query.courier_id
                print(update_query.courier_id)
                session.commit()


        route_query = session.query(Routes).where(Routes.id==route_id).first()
        return route_query