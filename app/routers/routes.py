#DONE генерация кластеров через алгоритм (другой)
#TODO распределение кластеров по маршрутам
#DONE раскидывание маршрутов по курьерам
#DONE редактирование маршрутов

import requests
import os, uuid
import re 
import math
import traceback
from typing import Annotated, List, Tuple, Dict, Optional
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

import datetime as dt
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload, lazyload, raiseload

from app import CODER_KEY, CODER_SETTINGS, COURIER_KEY

from app.auth import (
    oauth2_scheme, 
    get_current_user,
    get_current_user_variable_scopes
)

from app.validators import (
    LinkClientWithPromocodeFromTG as UserLinkData,
    Address as AddressValidator,
    AddressUpdate as AddressUpdateValidator,
    UserLogin as UserLoginSchema,
    AddressSchedule, CreateUserData, UpdateUserDataFromTG, AddressOut,
    RegionOut, AddressDaysWork, UserOut, RouteOut
)

from app import Tags, logger

from fastapi import APIRouter, Body, Security, Query
from fastapi.responses import JSONResponse

from calendar import monthrange
from uuid import UUID

from sqlalchemy import desc, asc, desc
from sqlalchemy import text

from app.validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut,
    OrderUpdate, Notification
)

from app.auth import (
    get_current_user
)

from app.models import (
    Users, Session, engine, UsersAddress, 
    Address, IntervalStatuses, Roles, Permissions, Regions, WEEK_DAYS_WORK_STR_LIST,
    DaysWork, Notifications, RegionalBoxPrices
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

API_ROOT_ENDPOINT = 'https://courier.yandex.ru/vrs/api/v1'

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
                    order_id = order
                )

                # order_update = Orders.query_by_id(order['id'])[0]

                order_update = session.query(Orders).enable_eagerloads(False).filter_by(id=order).first()

                order_update.courier_id = route['courier']
                if not (order_update.status == OrderStatuses.status_accepted_by_courier().id):
                    order_update = await order_update.update_status(OrderStatuses.status_accepted_by_courier().id)

                session.add(new_route_order)
                session.commit()
                session.add(order_update)
                session.commit()

            courier_query = session.query(Users).filter(Users.id==route['courier']).first()
            if (not courier_query.allow_messages_from_bot) and (not courier_query.telegram_id):
                await send_message_through_bot(
                    receipient_id=courier_query.telegram_id,
                    message="Вам назначен маршрут"
                )

        session.commit()


@router.post('/routes/generate', tags=[Tags.routes, Tags.admins, Tags.managers])
async def generate_routes_today(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    statuses_list: List[UUID] = Query(None),
    group_by: str = 'regions',
    couriers_id: List[UUID] = Query(None),
    write_after_generation: bool = False,
):
    """
    сформировать группы заявок в машруты
    - **group_by**: [str] - тип группировки заявок (по региону, по кластерам)
    - **statuses_list** [List[UUID]] - лист айди обрабатываемых статусов, по умолчанию "принят клиентом"
    - **couriers_id** [List[UUID]] - лист айди курьеров, которым выдадут маршруты
    - **write_after_generation** [bool] - записать ли результат сразу в бд
    """
    with Session(engine, expire_on_commit=False) as session:
        #TODO: Статус отменена при удалении из маршрута
        date = datetime.now()
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_tommorrow = date + timedelta(days=1)

        if not await DaysWork.is_work_day_today(session=session, date=date):
            return JSONResponse({
                "detail": "Текущая дата отмеченна как нерабочий день"
            }, status_code=422)
        

        order_pool_awaliable = [] #список доступных для вывоза заявок

        print(date, date_tommorrow)

        orders = session.query(Orders.id, Address.id, Regions.name_full).\
            join(Address, Address.id == Orders.address_id).\
            join(Regions, Regions.id == Address.region_id).\
            filter(Orders.deleted_at == None).\
            filter(Orders.status == OrderStatuses.status_confirmed().id).\
            filter(Orders.day >= date).\
            filter(Orders.day < date_tommorrow).\
            enable_eagerloads(False)


        if group_by == 'regions':
            orders = orders.order_by(asc(Regions.name_full))
        else:
            orders = orders.order_by(asc(Orders.date_created))

        global_orders_count = orders.count()

        orders = orders.all()

        total = len(orders)


        order_pool_awaliable = []
        for _order in orders:
            order_pool_awaliable.append(_order[0])
        
        couriers = session.query(Users).filter(Users.disabled==False)
        roles_user_query = session.query(Users.id).\
            join(Permissions, Permissions.user_id == Users.id).\
            join(Roles, Roles.id == Permissions.role_id).\
            where(Roles.role_name == ROLE_COURIER_NAME).\
            enable_eagerloads(False).\
            subquery()

        couriers = couriers.filter(Users.id.in_(roles_user_query))
        print(couriers_id)
        if couriers_id:
            couriers = couriers.filter(Users.id.in_((couriers_id)))
        couriers = couriers.all()

        if len(couriers)<1:
            return JSONResponse({
                "message": "В бд отсутствуют курьеры"
            }, status_code=403)

        routes = []

        i=0 #номер начальной заявки
        step = math.ceil(len(order_pool_awaliable)/len(couriers)) #сколько заявок давать курьеру

        #TODO Второй алгоритм выборки по кластерам
        #Проходим по всем курьерам 
        for courier in couriers:
            print(f"order start: {i}, step: {step}, limit: {step+i}")
            
            #делаем срез массива с заявками
            order_for_route = order_pool_awaliable[i:step+i]

            print(f"orders for route: {len(order_for_route)}")

            if len(order_for_route)==0:
                break

            print(order_pool_awaliable[i:step+i])
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
            #TODO: Сброс заявок со статусом ожидается на сегодня
            try:
                orders = session.query(Orders).\
                    filter(Orders.deleted_at == None).\
                    filter(Orders.status == OrderStatuses.status_awating_confirmation().id).\
                    filter(Orders.day >= date).\
                    filter(Orders.day < date_tommorrow).\
                    enable_eagerloads(False)

                for order_query in orders:
                    old_status_query = session.query(OrderStatuses).filter_by(id=order_query.status).enable_eagerloads(False).first()
                    new_data_change = OrderChangeHistory(
                        from_user_id = current_user.id,
                        order_id = order_query.id,
                        attribute = 'status',
                        old_content = old_status_query.status_name,
                        new_content = status_query.status_name,
                    )

                    order_query.comment = 'Пользователь не подтвердил заявку'
                    new_data_change = OrderChangeHistory(
                        from_user_id = current_user.id,
                        order_id = order_query.id,
                        attribute = 'comment',
                        new_content = 'Пользователь не подтвердил заявку',
                    )

                    order_query = await order_query.update_status(
                        OrderStatuses.status_canceled().id, 
                        OrderStatuses.status_canceled().message_on_update
                        )

                    session.add(new_data_change)
                    session.commit()

                notification_data = Notification(
                    content = f"Маршруты сформированы и требуют подтверждения.",
                    resource_type = 'маршрут',
                    sent_to_tg = True,
                    for_user_group = 'manager'
                )

            except Exception as err:
                print(err)

            if len(routes) < 1:
                return {
                    "global_count": global_orders_count,
                    "count": total,
                    "routes": routes
                }

            await Notifications.create_notification(
                notification_data = notification_data.model_dump(), 
                session = session,
                send_message = True
            )

        return {
            "global_count": global_orders_count,
            "count": total,
            "routes": routes
        }


@router.get("/routes", tags=[Tags.routes, Tags.admins, Tags.managers])
async def get_routes(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    date: Optional[datetime] = None,
    courier_id: Optional[UUID] = None,
    courier_tg_id: Optional[int] = None
# )->List[RouteOut]:
):
    """
    получить маршруты

    - **date**: [datetime] - дата на получение маршрутов, по умолчанию получаются все маршруты
    """
    with Session(engine, expire_on_commit=False) as session:
        routes = session.query(
            Routes
            ).outerjoin(RoutesOrders, Routes.id==RoutesOrders.route_id,         ).\
            outerjoin(Orders,  Orders.id==RoutesOrders.order_id ,               ).\
            outerjoin(BoxTypes, BoxTypes.id == Orders.box_type_id,              ).\
            outerjoin(RegionalBoxPrices, BoxTypes.id==RegionalBoxPrices.box,    ).\
            outerjoin(Regions, Regions.id == RegionalBoxPrices.region_id,       ).\
            outerjoin(Address, Address.id == Orders.address_id,                 ).\
            order_by(asc(Routes.date_created))

        # FROM routes LEFT OUTER JOIN routed_orders AS routed_orders_1 ON routes.id = routed_orders_1.route_id 
        # LEFT OUTER JOIN orders AS orders_1 ON orders_1.id = routed_orders_1.order_id 
        # LEFT OUTER JOIN boxtypes AS boxtypes_1 ON boxtypes_1.id = orders_1.box_type_id 
        # LEFT OUTER JOIN regional_box_prices AS regional_box_prices_1 ON boxtypes_1.id = regional_box_prices_1.box 
        # LEFT OUTER JOIN regions AS regions_1 ON regions_1.id = regional_box_prices_1.region_id 
        # LEFT OUTER JOIN users AS users_2 ON users_2.id = orders_1.manager_id 
        # LEFT OUTER JOIN address AS address_1 ON address_1.id = orders_1.address_id
        if date:
            date = date.replace(hour=0, minute=0)
            date_tommorrow = date + timedelta(days=1)
            routes = routes.filter(Routes.date_created > date)
            routes = routes.filter(Routes.date_created < date_tommorrow)
            

        if courier_id: 
            routes = routes.filter(Routes.courier_id == courier_id)

        if courier_tg_id:
            courier = Users.get_user(str(courier_tg_id), update_last_action=True)
            routes = routes.filter(Routes.courier_id == courier.id)

        # routes = routes.order_by(asc(Routes.date_created)).all()
        start = datetime.now()
        routes = routes.all()
        end = datetime.now() - start

        if len(routes)<1:
            return JSONResponse({
                "detail": "Not found"
            }, 404)

        # return routes
        return jsonable_encoder(routes)
    

@router.patch("/routes/{route_id}", tags=[Tags.routes, Tags.admins, Tags.managers])
async def update_route_orders(
    route_id: UUID,
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    orders_to_delete: List[UUID] = Query(None),
    orders_to_add: List[UUID] = Query(None),
    new_courier_id: UUID|int = None
)->RouteOut:
    """
    Обновить заявки в маршруте
    - **orders_to_delete**: [List[UUID]] - Лист заявок, которые перенесутся в отменённые и удалятся из маршрута
    - **orders_to_add**: [List[UUID]] - Лист заявок, которые удалятся из остальных маршрутов на сегодня и добавяться в этот указанный маршрут

    Заявки перебрасываются только из маршрутов, чей день совпадает с сегодняшней датой
    """
    date_today = dt.date.today()
    print(f"date today: {date_today}")
    with Session(engine, expire_on_commit=False) as session:

        #TODO: Повторная генерация я.маршрута при изменении заявок маршрута

        route_query = session.query(Routes).options(
            joinedload(Routes.orders).\
            joinedload(RoutesOrders.order).\
            joinedload(Orders.payments)
            ).where(Routes.id==route_id).first()
        if not route_query:
            return JSONResponse({
                "detail": f"Route {route_id} not found"
            },status_code=404)

        routes_today = session.query(Routes).\
            filter(Routes.date_created > date_today).all()

        route_query.route_task_id = None
        route_query.route_link = None

        if orders_to_delete:
            for route in routes_today:
                for order_id in orders_to_delete:
                    for order_route in route.orders:
                        if order_route.order_id == order_id:
                            delete_query = session.query(RoutesOrders).where(RoutesOrders.id==order_id).delete()
                            session.commit()

            for order_id in orders_to_delete:
                delete_query = session.query(RoutesOrders).where(RoutesOrders.order_id == order_id).delete()

                order_query = session.query(Orders).where(Orders.id==order_id).first()
                order_query = await order_query.update_status(OrderStatuses.status_confirmed().id)
                session.add(order_query)

                session.commit()

        if orders_to_add:   
            for route in routes_today:
                for order_id in orders_to_add:
                    for order_route in route.orders:
                        if order_route.order_id == order_id:
                            delete_query = session.query(RoutesOrders).where(RoutesOrders.id==order_id).delete()
                            session.commit()


            for order_id in orders_to_add:
                
                delete_query = session.query(RoutesOrders).where(RoutesOrders.order_id == order_id).delete()
                session.commit()

                new_route_order = RoutesOrders(
                    route_id = route_id,
                    order_id = order_id
                )

                session.add(new_route_order)

                update_query = session.query(Orders).where(Orders.id == order_id).first()
                
                if not (update_query.status == OrderStatuses.status_accepted_by_courier().id):
                    update_query = await update_query.update_status(OrderStatuses.status_accepted_by_courier().id)

                update_query.courier_id = route_query.courier_id
                session.commit()

        if new_courier_id: 
            user = Users.get_user(str(new_courier_id))
            if not user:
                return JSONResponse({
                    "detail": "Courier not found"
                }, 404)

            route_query.courier_id = new_courier_id
            session.commit()

        session.refresh(route_query)
        # route_query = session.query(Routes).where(Routes.id==route_id).first()
        return jsonable_encoder(route_query)


@router.post('/route', tags=[Tags.routes, Tags.admins, Tags.managers])
async def create_route(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
):
    """
    Создать маршрут вручную
    """
    pass


@router.delete('/route/{route_id}', tags=[Tags.routes, Tags.admins, Tags.managers])
async def delete_route(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    route_id: UUID
):
    """
    Удалить маршрут
    """
    with Session(engine, expire_on_commit=False) as session:
        route_query = session.query(Routes).filter(Routes.id==route_id).first()
        if not route_query:
            return JSONResponse({
                "detail": "not found"
            }, 404)

        #TODO: Сброс статуса заявки 
        routed_orders = session.query(RoutesOrders).filter(RoutesOrders.route_id==route_id).delete()
        route_query = session.query(Routes).filter(Routes.id==route_id).delete()
        session.commit()
        return


@router.get('/route/{route_id}/courier_map', tags=[Tags.routes, Tags.admins])
async def get_route_y_map(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])],
    route_id: UUID
):
    """
    Получить маршрутизацию от яндекса, создать её если нет
    """
    try:

        with Session(engine, expire_on_commit=False) as session:
            route_query = session.query(Routes).options(
                joinedload(Routes.orders).\
                joinedload(RoutesOrders.order).\
                joinedload(Orders.payments)
                ).filter(Routes.id==route_id).first()

            if not route_query:
                return JSONResponse({
                    "detail": "not found"
                }, 404)
            
            if route_query.route_link:
                return route_query.route_link
            
            if route_query.route_task_id:
                result = await get_result_by_id(route_query.route_task_id)
                route_query.route_link = result
                session.commit()
                return result
            
            payload = generate_y_courier_json(route_query)

            response = requests.post(
                API_ROOT_ENDPOINT + '/add/mvrp',
                params={'apikey': COURIER_KEY}, json=payload)

            print(response.status_code)
            if response.status_code == 400:
                return response.json()

            try:
                result = await set_timed_func('r', route_query.id, 'M:01')
                print(result)
            except Exception as err:
                print(err)

            request_id = response.json()['id']

            route_query.route_task_id = request_id
            session.commit()

            return response.json()

    except Exception as err:
        print(traceback.format_exc())