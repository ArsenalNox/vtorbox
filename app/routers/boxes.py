"""
Эндпоинты по коробкам

"""
from typing import Annotated

from fastapi import APIRouter, Body, Security
from fastapi.responses import JSONResponse

from datetime import datetime

from ..validators import (
    Order as OrderValidator,
    UserLogin as UserLoginSchema,
    OrderOut,
    BoxType
)

from ..auth import (
    get_current_user
)

from ..models import (
    engine, 
    Session, 
    BoxTypes
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
        if boxes_query:
            return boxes_query

        return None


@router.post('/boxes', tags=["boxes", "admin"])
async def create_new_box_type(
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    box_data: BoxType
):
    with Session(engine, expire_on_commit=False) as session:
        new_box = BoxTypes(**box_data.model_dump())
        session.add(new_box)
        session.commit()
        return new_box


@router.put('/boxes/{box_id}', tags=["boxes", "admin"])
async def update_box_data(
    bot: Annotated[UserLoginSchema, Security(get_current_user, scopes=["bot"])],
    box_data: BoxType,
    box_id: uuid.UUID
):
    pass
    with Session(engine, expire_on_commit=False) as session:
        box_query = session.query(BoxTypes).filter_by(id=box_id).where(BoxTypes.deleted_at == None).first()
        if not box_query:
            return JSONResponse({
                "message": "not found"
            },status_code=404)

        for attr, value in box_data.model_dump().items():
            if value:
                setattr(box_query, attr, value)

        session.add(box_query)
        session.commit()

        return box_query
