"""
Эндпоинты по коробкам

"""
from typing import Annotated

from fastapi import APIRouter, Body, Security
from fastapi.responses import JSONResponse

from datetime import datetime

from app.validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut, BoxUpdate,
    BoxType, RegionalBoxPrice
)

from app.auth import (
    get_current_user
)

from app.models import (
    engine, Session, BoxTypes,
    RegionalBoxPrices, Regions
    )

from uuid import UUID

import os, uuid
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


@router.get('/boxes', tags=['bot', 'boxes'])
async def get_box_types(
    bot: Annotated[UserLoginSchema, Security(get_current_user)]
):
    """
    Получение списка доступных контейнеров
    """
    with Session(engine, expire_on_commit=False) as session:
        boxes_query = session.query(BoxTypes).where(BoxTypes.deleted_at == None).all()

        return_data = []
        if boxes_query:
            for box in boxes_query:
                box_data = BoxType(**box.__dict__)

                regional_box_prices_qeury = session.query(RegionalBoxPrices, Regions).\
                    join(Regions, Regions.id == RegionalBoxPrices.region_id).\
                    where(RegionalBoxPrices.box == box.id).all()
                
                box_prices = []
                for price in regional_box_prices_qeury:

                    box_prices.append(RegionalBoxPrice(
                        region_name = str(price[1].name_full),
                        price = str(price[0].price)
                    ))
                    
                box_data.regional_prices = box_prices
                return_data.append(box_data)

            return return_data

        return None


@router.post('/boxes', tags=["boxes", "admin"])
async def create_new_box_type(
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    box_data: BoxType
):
    """
    Создание нового контейнера
    """
    with Session(engine, expire_on_commit=False) as session:
        new_box = BoxTypes(**box_data.model_dump())
        session.add(new_box)
        session.commit()
        return new_box


@router.put('/boxes/{box_id}', tags=["boxes", "admin"])
async def update_box_data(
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    box_data: BoxUpdate,
    box_id: uuid.UUID
)->BoxType:
    """
    Обновление данных контейнера
    - **box_id**: UUID контейнера
    """
    
    with Session(engine, expire_on_commit=False) as session:
        box_query = session.query(BoxTypes).filter_by(id=box_id).where(BoxTypes.deleted_at == None).first()
        if not box_query:
            return JSONResponse({
                "message": "not found"
            },status_code=404)

        for attr, value in box_data.model_dump().items():
            if attr == 'regional_prices' and not(value == None):
                prices_query = session.query(RegionalBoxPrices).filter(RegionalBoxPrices.box == box_query.id).delete()
                for price in value:
                    region_query = session.query(Regions).\
                        filter(Regions.name_full.ilike(f"%{price['region_name']}%")).first()
                    if not region_query:
                        continue

                    new_reg_price = RegionalBoxPrices(
                        region_id = region_query.id,
                        box = box_query.id,
                        price = price['price']
                    ) 
                    session.add(new_reg_price)

                    print(price)
                continue

            if value:
                setattr(box_query, attr, value)

        # session.add(box_query)
        session.commit()

        box_data = BoxType(**box_query.__dict__)

        regional_box_prices_qeury = session.query(RegionalBoxPrices, Regions).\
            join(Regions, Regions.id == RegionalBoxPrices.region_id).\
            where(RegionalBoxPrices.box == box_query.id).all()
        
        box_prices = []
        for price in regional_box_prices_qeury:

            box_prices.append(RegionalBoxPrice(
                region_name = str(price[1].name_full),
                price = str(price[0].price)
            ))
            
        box_data.regional_prices = box_prices

        return box_data


@router.delete('/boxes/{box_id}')
async def delete_box(
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    box_id: uuid.UUID
):
    """
    Удаление контейнера
    """