from typing import Type

from sqlalchemy.orm import Session

from app.models import engine, Address, UsersAddress, Users
from bot.services.base import BaseService


class UserService(BaseService):
    @classmethod
    def create_user(cls, tg_id: int, username: str, fullname: str):
        """Создание пользователей"""

        user = cls.get_user_by_tg_id(tg_id)

        with Session(engine, expire_on_commit=False) as session:
            if not user:
                user = Users(
                    telegram_id=tg_id,
                    telegram_username=username,
                    full_name=fullname
                )
                session.add(user)
                session.commit()

    @classmethod
    def get_users_addresses(cls, tg_id):
        """Получение всех адресов данного пользователя"""

        with Session(engine, expire_on_commit=False) as session:
            addresses = session.query(Address). \
                join(UsersAddress, UsersAddress.address_id == Address.id). \
                join(Users, UsersAddress.user_id == Users.id). \
                where(Users.telegram_id == tg_id).all()

            return addresses

    @classmethod
    def get_users_addresses_without_main(cls, tg_id):
        """Получение всех адресов данного пользователя"""

        with Session(engine, expire_on_commit=False) as session:
            addresses = session.query(Address). \
                join(UsersAddress, UsersAddress.address_id == Address.id). \
                join(Users, UsersAddress.user_id == Users.id). \
                where(Users.telegram_id == tg_id, Address.main == False).all()

            return addresses

    @classmethod
    def get_users_address_by_address_id(cls, address_id: str):
        with Session(engine, expire_on_commit=False) as session:
            users_address = session.query(UsersAddress).filter_by(
                address_id=address_id
            ).first()

            if users_address:
                return users_address

    @classmethod
    def change_user_data(cls, user: Users, new_fullname: str = None, comment: str = None,
                         phone_number: str = None, email: str = None):
        """Изменение данных о пользовательской анкете"""

        with Session(engine, expire_on_commit=False) as session:
            if new_fullname:
                user.full_name = new_fullname

            # сценарий, когда пользователь нажал на 'Не добавлять комментарий'
            if comment == 'delete':
                user.additional_info = None
            elif comment:
                user.additional_info = comment

            if phone_number:
                user.phone_number = phone_number

            if email:
                user.email = email

            session.add(user)
            session.commit()

    @classmethod
    def search_user_by_promocode(cls, promocode: str):
        """Поиск пользователя по промокоду"""

        with Session(engine, expire_on_commit=False) as session:
            user = session.query(Users).filter_by(
                link_code=promocode
            ).first()

            return user

    @classmethod
    def add_user_data_from_site(cls, user: Users, tg_id: int, username: str, fullname: str):
        """Добавление к юзеру, который пришел с сайта, телеграм id"""

        with Session(engine, expire_on_commit=False) as session:
            user.telegram_id = tg_id
            user.full_name = fullname
            user.telegram_username = username
            session.add(user)
            session.commit()


