"""
Содержит в себе ендпоинты по заявкам
"""

from fastapi import APIRouter

router = APIRouter()


#TODO: Получение заявок по фильтру
@router.get('/orders/filter/{}')
async def get_filtered_orders():
    pass



@router.get('/orders', tags=["orders"])
async def get_all_orders():
    return [{'order_id': 1, 'user_id': 1}]


@router.get('/orders/{order_id}', tags=["orders"])
async def get_order_by_id(order_id:int):
    return [{'order_id': 1, 'user_id': 1}]


@router.post('/orders')
async def create_order():
    pass


@router.delete('/orders/{order_id}', tags=["orders"])
async def delete_order_by_id(order_id:int):
    pass
