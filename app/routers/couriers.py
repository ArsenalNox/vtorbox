"""
Эндпоинты для курьеров
"""

from fastapi import APIRouter
from ..validators import CourierCreationValidator
from app import Tags

router = APIRouter()


@router.post('/courier', tags=[Tags.couriers])
async def create_new_courier(courier_data: CourierCreationValidator):
    return


@router.get('/courier/{courier_tg_id}', tags=[Tags.couriers])
async def get_courier_by_id():
    pass



@router.get('/courier/orders', tags=[Tags.couriers, Tags.orders])
async def get_list_of_accepted_orders():
    pass


@router.post('/courier/order/{order_id}/accept', tags=[Tags.couriers, Tags.orders])
async def accept_order_by_courier():
    """
    Принять заявку курьером
    """
    pass


@router.post('/courier/order/{order_id}/comment', tags=[Tags.couriers, Tags.orders])
async def post_order_comment_by_courier():
    """
    Оставить комментарий к заявке курьером
    """
    pass