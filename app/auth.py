import os

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from fastapi.exceptions import HTTPException
from fastapi import Depends, Security, status

from typing import Annotated, List, Optional
from passlib.context import CryptContext
from jose import JWTError, jwt

from datetime import datetime, timedelta
from pydantic import ValidationError, BaseModel, UUID4

from app.validators import (
    UserLogin as User,
    Token, 
    TokenData, RefreshTokenData
)

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime

from app.models import (
    engine, Users, Permissions, Roles, UserRefreshTokens,
    ROLE_ADMIN_NAME
    )


from app import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_SECRET_KEY

load_dotenv()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


class User(BaseModel):
    id: UUID4 | None = None
    username: str | None = None
    disabled: bool = False
    access_token: str | None = None
    roles: List[str] | None = None
    refresh_token: Optional[str] = None

class UserInDB(User):
    hashed_password: str
    refresh_tokens: Optional[List[str]] = None


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})

    # else:
    #     expire = datetime.utcnow() + timedelta(minutes=15)

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str = None, user_id: UUID4 = None):
    userdict = {
        "username": None,
        "hashed_password": None,
        "disabled": False,
        "roles": None,
        "refresh_tokens": []
    }

    with Session(engine, expire_on_commit=False) as session:
        query = None
        if (username == None) and (user_id == None):
            return False

        if username:
            query = session.query(Users).filter_by(email=username).first()

        if user_id:
            query = session.query(Users).filter_by(id=user_id).first()

        if not query:
            return False

        if query:
            scopes_query = session.query(Permissions, Roles.role_name).\
                filter_by(user_id=query.id).join(Roles).all()
            scopes = [role.role_name for role in scopes_query]

            refresh_tokens = session.query(UserRefreshTokens).filter_by(user_id=query.id).all()

            userdict["id"] = query.id
            userdict["username"] = query.email
            userdict["hashed_password"] = query.password
            userdict["roles"] = scopes
            userdict["refresh_tokens"] = [token.token for token in refresh_tokens]
            if query.deleted_at:
                userdict["disabled"] = True
            else:
                query.last_action = datetime.now()
                session.commit()

    return UserInDB(**userdict)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(
    security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]
):
    """
    Получение текущего пользователя
    Проверка скоупов требует полного соответствия скоупов токена и эндпоинта
    """
    #DONE: Получение скоупов из бд а не токена
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError) as error:
        raise credentials_exception

    user = get_user(username=token_data.username)

    if user is None:
        raise credentials_exception

    for scope in security_scopes.scopes:

        if ROLE_ADMIN_NAME in token_data.scopes:
            break

        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    user.access_token = token
    user.roles = token_data.scopes
    return user


async def get_current_user_refresh(
    security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]
):
    """
    Получение текущего пользователя
    Проверка скоупов требует полного соответствия скоупов токена и эндпоинта
    """
    #DONE: Получение скоупов из бд а не токена
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: UUID4 = payload.get("internal_id")
        if user_id is None:
            raise credentials_exception

        token_data = RefreshTokenData(user_id=user_id)

    except (JWTError, ValidationError) as error:
        raise credentials_exception

    user = get_user(user_id=token_data.user_id)

    if user is None:
        raise credentials_exception

    if user is False:
        raise credentials_exception


    user.refresh_token = token
    return user


async def get_current_user_variable_scopes(
    security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]
):
    """
    Получение текущего пользователя
    Проверка скоупов требует наличие одно из скоупов, а не полное соответствие :w
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError) as error:
        raise credentials_exception

    user = get_user(username=token_data.username)

    if user is None:
        raise credentials_exception

    flag_has_scope = False
    for scope in security_scopes.scopes:
        if scope in token_data.scopes:
            flag_has_scope = True
            break

    if not flag_has_scope:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": authenticate_value},
        )

    #TODO: Добавить подобие триггера на last_action 
    user.access_token = token
    user.roles = token_data.scopes
    return user


async def get_current_active_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["me"])]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
