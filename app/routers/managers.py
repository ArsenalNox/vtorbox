"""
Эндпоинты для менеждеров
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes

from app.models import (
    engine, 
    Session, 
    OrderStatuses,
)

from app.validators import (
    UserLogin as UserLoginSchema,
    StatusOut
)

from app.auth import (
    oauth2_scheme, 
    pwd_context, 
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_active_user,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
)

import os, uuid
from dotenv import load_dotenv


load_dotenv()
router = APIRouter()


@router.post('/managers/add/{user_id}')
async def add_manager_role_to_user():
    """
    Добавить роль менеджера пользователю
    """
    pass


@router.get("/managers")
async def get_managers():
    """
    Получить менеджеров
    """
    pass