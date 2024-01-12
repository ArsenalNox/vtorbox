"""
Эндпоинты для курьеров
"""

from fastapi import APIRouter
from ..validators import CourierCreationValidator

router = APIRouter()


@router.post('/courier', tags=["couriers"])
async def create_new_courier(courier_data: CourierCreationValidator):
    return


@router.get('/courier/{courier_tg_id}', tags=["couriers"])
async def get_courier_by_id():
    pass


@router.post('/courier/order/{order_id}/accept', tags=["couriers", "orders"])
async def accept_order_by_courier():
    """
    Принять заявку курьером
    """
    pass


@router.post('/courier/order/{order_id}/comment', tags=["couriers", "orders"])
async def post_order_comment_by_courier():
    """
    Оставить комментарий к заявке курьером
    """
    pass