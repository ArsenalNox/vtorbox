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
