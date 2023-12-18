from fastapi import APIRouter

from app.validators import CreateUserData, UpdateUserDataFromTG
from bot.services.users import UserService

router = APIRouter()


@router.get('/search-user-by-promocode')
async def search_user_by_promocode(
        promocode: str = None
):
    user = UserService.search_user_by_promocode(promocode)

    return user


@router.post('/add-user-data-from-site')
async def add_user_data_from_site(
        body: UpdateUserDataFromTG
):
    UserService.add_user_data_from_site(
        tg_id=body.tg_id,
        username=body.username,
        fullname=body.fullname
    )

    return 'User was updated'


@router.post('/create-user')
async def create_user(
        body: CreateUserData
):
    UserService.create_user(
        tg_id=body.tg_id,
        username=body.username,
        fullname=body.fullname
    )

    return 'User was created'


@router.get('/search-user-by-phone')
async def search_user_by_phone(
        phone: str
):
    user = UserService.search_user_by_phone(phone)

    return user


